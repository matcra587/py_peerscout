"""A Python script for retrieving and filtering network peers based on latency and geographical location.

Uses the Polkachu API to fetch live peers and filters them based on specified criteria.
"""

import argparse
import ipaddress
import os

import ipinfo
import ping3
import requests
from ping3 import errors
from termcolor import colored

# Enable exceptions mode for ping3
ping3.EXCEPTIONS = True


def check_peer_latency(peer: str, timeout_ms: float = 50) -> float | None:
    """Make a simple ICMP request to measure the latency to a peer.

    Args:
        peer (str): The peer endpoint in the format `nodeID@ip:port`.
        timeout_ms (float, optional): Timeout in milliseconds for the ICMP request. Defaults to 50 ms.

    Returns:
        float | None:
            - **float**: Round-trip time in milliseconds if the ping is successful.
            - **None**: If the peer format is invalid, the host is unknown, the request times out,
              or any ping error occurs.

    """
    try:
        _, address = peer.split("@")
        ip, _ = address.split(":")
        ip = ipaddress.ip_address(ip)
    except ValueError as e:
        msg = colored(f"❌ Invalid peer format or IP: {e}", "red")
        print(msg)
        return None

    try:
        result = ping3.ping(str(ip), timeout=timeout_ms / 1000, unit="ms")
        # With ping3.EXCEPTIONS = True, result should not be None
        msg = colored(f"✅ Latency for {peer}: {result:.3f} milliseconds", "green")
        print(msg)

    except errors.Timeout as e:
        msg = colored(f"⏰ Timeout for {peer}: {e}", "red")
        print(msg)
        return None

    except errors.HostUnknown as e:
        msg = colored(f"🔍 HostUnknown for {peer}: {e}", "red")
        print(msg)
        return None

    except errors.PingError as e:
        msg = colored(f"❌ PingError for {peer}: {e}", "red")
        print(msg)
        return None

    else:
        return result


def check_peer_location(peer: str) -> str:
    """Retrieve the geolocation information of an IP address using the ipinfo.io API.

    Args:
        peer (str): The peer endpoint in the format nodeID@ip:port.

    Returns:
        str: Two-letter country code (e.g., 'US', 'CA').

    Raises:
        ipinfo.error.APIError: If the IPinfo API token is missing or invalid.

    """
    _, address = peer.split("@")
    ip, _ = address.split(":")
    access_token = os.getenv("IPINFO_ACCESS_TOKEN")

    if not access_token:
        error_message = "No API token provided. Set IPINFO_ACCESS_TOKEN environment variable."
        raise ipinfo.error.APIError(403, error_message)

    handler = ipinfo.getHandler(access_token)
    result = handler.getDetails(ip)

    return result.country


def get_live_peers(network: str) -> list:
    """Retrieve a list of live peers for the specified network from the Polkachu API.

    Args:
        network (str): The network name (e.g., 'dydx', 'osmosis').

    Returns:
        list: A list of live peer strings (e.g., ["nodeID@1.2.3.4:26656", ...]).

    """
    base_url = "https://polkachu.com"
    network = network.lower()
    url = f"{base_url}/api/v2/chains/{network}/live_peers"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        json_data = response.json()
    except requests.exceptions.RequestException as e:
        msg = colored(f"❌ Error fetching live peers: {e}", "red")
        print(msg)
        return []
    else:
        return json_data.get("live_peers", [])


def filter_peers_by_country(peers: list, target_country: list) -> list:
    """Filter a list of peers to only include those located in target_country.

    Args:
        peers (list): List of peer endpoints (nodeID@ip:port).
        target_country (list): List of valid country codes (e.g., ['CA', 'US']).

    Returns:
        list: List of peers located in one of the target countries.

    """
    filtered_peers = []
    for peer in peers:
        try:
            location = check_peer_location(peer)
        except ipinfo.error.APIError as e:
            msg = colored(f"❌ Error retrieving location for {peer}: {e}", "red")
            print(msg)
            continue

        if location in target_country:
            filtered_peers.append(peer)
        else:
            msg = colored(f"⚠️ Skipping {peer} because it's not in our target countries", "yellow")
            print(msg)
    return filtered_peers


def filter_peers_by_latency(peers: list, max_latency: float) -> list:
    """Filter a list of peers to only include those with latency below or equal to max_latency.

    Args:
        peers (list): List of peer endpoints (nodeID@ip:port).
        max_latency (float): The maximum acceptable latency in milliseconds.

    Returns:
        list: List of peers that meet the latency requirement.

    """
    filtered_peers = []
    for peer in peers:
        latency = check_peer_latency(peer)
        if latency is not None and latency <= max_latency:
            filtered_peers.append(peer)
    return filtered_peers


def get_qualified_peers(
    network: str,
    target_country: list,
    max_latency: float,
    desired_count: int,
    max_attempts: int,
) -> list:
    """Call the necessary functions to find a list of qualified peers that meet the criteria.

    Args:
        network (str): The network to scout peers for.
        target_country (list): List of target countries (e.g., ['CA', 'US']).
        max_latency (float): The maximum acceptable latency in milliseconds.
        desired_count (int): The desired number of peers to find.
        max_attempts (int): The maximum number of attempts to find peers.

    Returns:
        list: List of qualified peers that meet the criteria.

    """
    qualified_peers = []

    attempts = 0

    while len(qualified_peers) < desired_count and attempts < max_attempts:
        attempts += 1
        msg = colored(f"🔄 Attempt {attempts} to find peers...", "cyan")
        print(msg)
        new_peers = get_live_peers(network)

        country_filtered = filter_peers_by_country(new_peers, target_country)

        latency_filtered = filter_peers_by_latency(country_filtered, max_latency)

        qualified_peers.extend(latency_filtered)

        qualified_peers = list(set(qualified_peers))

        if len(qualified_peers) >= desired_count:
            return qualified_peers[:desired_count]

        msg = colored(f"Found {len(qualified_peers)} suitable peers (attempt {attempts}/{max_attempts})...", "blue")
        print(msg)

    # Optional: Inform if desired_count not met
    if len(qualified_peers) < desired_count:
        msg = colored(f"⚠️ Only found {len(qualified_peers)} peers after {max_attempts} attempts.", "yellow")
        print(msg)

    return qualified_peers


def peers_to_comma_separated(peers: list) -> str:
    """Convert a list of peers to a comma-separated string.

    Args:
        peers (list): List of peer endpoints (nodeID@ip:port).

    Returns:
        str: Comma-separated string of peers.

    """
    return ",".join(peers)


def main() -> None:  # noqa: D103
    parser = argparse.ArgumentParser(description="Scout for peers based on latency and location")

    parser.add_argument("--network", type=str, required=True, help="The network to scout peers for")

    parser.add_argument(
        "--target_country",
        type=str,
        required=False,
        default="CA,US",
        help="Comma-separated list of target countries (e.g. 'CA,US' or 'DE')",
    )

    parser.add_argument(
        "--desired_count",
        type=int,
        default=5,
        required=False,
        help="The desired number of peers to find",
    )

    parser.add_argument(
        "--max_latency",
        type=float,
        default=50,
        required=False,
        help="The maximum latency in milliseconds",
    )

    parser.add_argument(
        "--max_attempts",
        type=int,
        default=5,
        required=False,
        help="The maximum number of attempts to find peers",
    )

    parser.add_argument(
        "--output",
        type=str,
        choices=["list", "raw", "string"],
        default="list",
        help=(
            "The format in which you want the data returned. Choices:\n"
            "  list   : Detailed list with emojis and colored text.\n"
            "  string : Comma-separated string of peers.\n"
            "  raw    : List of peers without emojis or colors."
        ),
    )

    args = parser.parse_args()

    target_countries = [country.strip().upper() for country in args.target_country.split(",")]

    final_peers = get_qualified_peers(
        args.network,
        target_countries,
        args.max_latency,
        args.desired_count,
        args.max_attempts,
    )

    if final_peers:
        match args.output:
            case "list":
                msg = colored(f"✅ Found {len(final_peers)} peers that meet our criteria:", "green")
                print(msg)
                for peer in final_peers:
                    msg = colored(f"🖧 {peer}", "green")
                    print(msg)
            case "string":
                cs_output = peers_to_comma_separated(final_peers)
                msg = colored(f"📄 Comma-Separated Peers:\n{cs_output}", "cyan")
                print(msg)
            case "raw":
                print(f"Found {len(final_peers)} peers that meet our criteria:")
                for peer in final_peers:
                    msg = "- " + peer
                    print(msg)
    else:
        msg = colored("❌ No qualified peers found based on the given criteria.", "red")
        print(msg)


if __name__ == "__main__":
    main()
