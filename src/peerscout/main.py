"""A Python script for retrieving and filtering network peers based on latency and geographical location.

Uses the Polkachu API to fetch live peers and filters them based on specified criteria.
"""

import difflib
import ipaddress
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

import configargparse
import ipinfo
import ping3
import requests

# Enable exceptions mode for ping3
ping3.EXCEPTIONS = True


class PolkachuService(TypedDict):
    """Type definition for a single Polkachu service.

    Attributes:
        active: Whether the service is available
        details: URL to service details page

    """

    active: bool
    details: str


class PolkachuServices(TypedDict):
    """Type definition for Polkachu services.

    Attributes:
        live_peers: Service information for live peers

    """

    live_peers: PolkachuService


@dataclass
class ChainDetails:
    """Details about a blockchain network from Polkachu API.

    Attributes:
        network: Network identifier (e.g., "cosmos")
        name: Human-readable name (e.g., "CosmosHub")
        chain_id: Chain identifier (e.g., "cosmoshub-4")
        polkachu_services: Dictionary of available Polkachu services

    """

    network: str
    name: str
    chain_id: str
    polkachu_services: PolkachuServices

    @classmethod
    def from_dict(cls, data: dict) -> "ChainDetails":
        """Create ChainDetails from API response dictionary."""
        return cls(
            network=data["network"],
            name=data["name"],
            chain_id=data["chain_id"],
            polkachu_services=data["polkachu_services"],
        )


@dataclass
class ChainLivePeers:
    """Details about a blockchain network's live peers from Polkachu API.

    Attributes:
        network: Network identifier (e.g., "cosmos")
        polkachu_peer: Polkachu specific state-sync peer
        live_peers: List of 5 random live peers

    """

    network: str
    polkachu_peer: str
    live_peers: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> "ChainLivePeers":
        """Create ChainLivePeers from API response dictionary."""
        return cls(network=data["network"], polkachu_peer=data["polkachu_peer"], live_peers=data["live_peers"])


@dataclass
class PeerConfig:
    """Configuration for peer filtering.

    Attributes:
        network: Network identifier (e.g., "cosmos")
        target_countries: List of target countries (e.g., ['CA', 'US'])
        max_latency: Maximum acceptable latency in milliseconds
        desired_count: Number of peers to find
        max_attempts: Maximum number of attempts to find peers

    """

    network: str
    target_countries: list[str]
    max_latency: float
    desired_count: int
    max_attempts: int
    access_token: str

    @classmethod
    def from_args(cls, args: configargparse.Namespace) -> "PeerConfig":
        """Create PeerCriteria from command line arguments."""
        return cls(
            network=args.network,
            target_countries=[c.strip().upper() for c in args.target_country.split(",")],
            max_latency=args.max_latency,
            desired_count=args.desired_count,
            max_attempts=args.max_attempts,
            access_token=args.access_token,
        )


class Config:
    """Configuration for the peer scout."""

    def __init__(
        self,
        debug: bool,  # noqa: FBT001
        peers: PeerConfig,
        output_format: str,
    ) -> None:
        """Initialise configuration with monitoring parameters."""
        self.debug = debug
        self.peers = peers
        self.output_format = output_format

    @staticmethod
    def setup_logging(debug: bool = False) -> None:  # noqa: FBT001, FBT002
        """Set up basic logging.

        If debug is True, sets the logger level to DEBUG; otherwise INFO.
        """
        if debug:
            logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        else:
            logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def parse_args() -> configargparse.Namespace:
        """Parse command line arguments."""
        parser = configargparse.ArgParser(default_config_files=[Path(__file__).joinpath("config.yaml")])

        parser.add("-c", "--config", required=False, is_config_file=True, help="config file path")

        parser.add("--network", type=str, required=True, env_var="NETWORK", help="The network to scout peers for")

        parser.add(
            "--target-country",
            type=str,
            required=False,
            default="CA,US",
            env_var="TARGET_COUNTRY",
            help="Comma-separated list of target countries (e.g. 'CA,US' or 'DE')",
        )

        parser.add(
            "--desired-count",
            type=int,
            default=5,
            required=False,
            env_var="DESIRED_COUNT",
            help="The desired number of peers to find",
        )

        parser.add(
            "--max-latency",
            type=int,
            default=50,
            required=False,
            env_var="MAX_LATENCY",
            help="The maximum latency in milliseconds",
        )

        parser.add(
            "--max-attempts",
            type=int,
            default=5,
            required=False,
            env_var="MAX_ATTEMPTS",
            help="The maximum number of attempts to find peers",
        )

        parser.add(
            "--format",
            dest="output_format",
            type=str,
            choices=["list", "string"],
            default="list",
            env_var="FORMAT",
            help="Output format (list/string)",
        )

        parser.add(
            "--access-token",
            type=str,
            required=False,
            env_var="ACCESS_TOKEN",
            help="IPinfo API access token",
        )

        parser.add("-d", "--debug", action="store_true", help="Enable debug logging.")
        return parser.parse_args()

    @classmethod
    def initialise(cls) -> "Config":
        """Initialise complete monitoring setup and return config."""
        cls.setup_logging()
        args = cls.parse_args()
        return cls.from_args(args)

    @classmethod
    def from_args(cls, args: configargparse.Namespace) -> "Config":
        """Create config from parsed arguments."""
        return cls(
            debug=args.debug,
            peers=PeerConfig.from_args(args),
            output_format=args.output_format,
        )


class PolkachuData:
    """A class to interact with the Polkachu API."""

    def __init__(self, base_url: str = "https://polkachu.com") -> None:
        """Initialize the Poller with the base URL of the Polkachu API."""
        self.base_url = base_url

    def fetch_data(self, endpoint: str) -> dict:
        """Retrieve data from the Polkachu API.

        Args:
            endpoint (str): The endpoint to fetch data from.

        Returns:
            dict: The JSON response from the Polkachu API.

        """
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.request("GET", url, timeout=15)
            response.raise_for_status()
            json_data = response.json()
        except requests.exceptions.RequestException as e:
            logging.warning("Error fetching data from %s: %s", url, e)
            return {}
        else:
            return json_data

    def fetch_valid_chains(self) -> dict:
        """Retrieve a list of chains supported by Polkachu.

        Returns:
            dict: List of supported chains

        """
        return self.fetch_data("api/v2/chains")

    def fetch_chain_details(self, network: str) -> ChainDetails:
        """Retrieve detailed information of a chain.

        Args:
            network (str): The network name (e.g., 'dydx', 'osmosis').

        Returns:
            ChainDetails: Detailed information of a chain.

        """
        data = self.fetch_data(f"api/v2/chains/{network}")
        return ChainDetails.from_dict(data)

    def fetch_live_peers(self, network: str) -> ChainLivePeers:
        """Retrieve live peers of a chain.

        Args:
            network (str): The network name (e.g., 'dydx', 'osmosis').

        Returns:
            ChainLivePeers: 5 random live peers of a chain.

        """
        data = self.fetch_data(f"api/v2/chains/{network}/live_peers")
        return ChainLivePeers.from_dict(data)

    def fetch_polkachu_peer(self, network: str) -> ChainLivePeers:
        """Retrieve the Polkachu internal live state-sync peer of a chain.

        Note:
            Not actively used. Added for potential future use.

        Args:
            network (str): The network name (e.g., 'dydx', 'osmosis').

        Returns:
            ChainLivePeers: Polkachu internal live state-sync peer.

        """
        data = self.fetch_data(f"api/v2/chains/{network}/live_peers")
        return ChainLivePeers(network=network, polkachu_peer=data["polkachu_peer"], live_peers=None)


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
    except ValueError:
        return None

    return ping3.ping(str(ip), timeout=timeout_ms / 1000, unit="ms")


def check_peer_location(peer: str, access_token: str) -> str:
    """Retrieve the geolocation information of an IP address using the ipinfo.io API.

    Args:
        peer (str): The peer endpoint in the format nodeID@ip:port.
        access_token (str): The IPinfo API access token.

    Returns:
        str: Two-letter country code (e.g., 'US', 'CA').

    Raises:
        ipinfo.error.APIError: If the IPinfo API token is missing or invalid.

    """
    _, address = peer.split("@")
    ip, _ = address.split(":")

    handler = ipinfo.getHandler(access_token)
    details = handler.getDetails(ip).details

    return details["country"]


def filter_peers_by_country(peers: list, target_country: list, access_token: str) -> list:
    """Filter a list of peers to only include those located in target_country.

    Args:
        peers (list): List of peer endpoints (nodeID@ip:port).
        target_country (list): List of valid country codes (e.g., ['CA', 'US']).
        access_token (str): The IPinfo API access token.

    Returns:
        list: List of peers located in one of the target countries.

    """
    filtered_peers = []
    for peer in peers:
        try:
            location = check_peer_location(peer, access_token)
        except ipinfo.error.APIError as e:
            logging.warning("Error retrieving location for %s: %s", peer, e)
            continue

        if location in target_country:
            filtered_peers.append(peer)
            logging.debug("Peer %s is in a target country (%s).", peer, location)
        else:
            logging.debug("Skipping %s (country=%s not in %s).", peer, location, target_country)
    return filtered_peers


def filter_peers_by_latency(peers: list, max_latency_ms: float) -> list:
    """Filter a list of peers to only include those with latency below or equal to max_latency.

    Args:
        peers (list): List of peer endpoints (nodeID@ip:port).
        max_latency_ms (float): The maximum acceptable latency in milliseconds.

    Returns:
        list: List of peers that meet the latency requirement.

    """
    filtered_peers = []
    for peer in peers:
        try:
            latency = check_peer_latency(peer, timeout_ms=max_latency_ms)

        except ping3.errors.Timeout as e:
            logging.debug("Timeout for %s: %s", peer, e)
            continue

        except ping3.errors.HostUnknown as e:
            logging.debug("HostUnknown for %s: %s", peer, e)
            continue

        except ping3.errors.PingError as e:
            logging.debug("PingError for %s: %s", peer, e)
            continue
        else:
            if latency is None:
                logging.debug("No latency data for %s.", peer)
                continue

            if latency <= max_latency_ms:
                logging.debug("%s is good: latency=%.2f ms <= %.2f ms.", peer, latency, max_latency_ms)
                filtered_peers.append(peer)
            else:
                logging.debug("Skipping %s: latency=%.2f ms > %.2f ms.", peer, latency, max_latency_ms)
    return filtered_peers


def is_valid_peer(peer: str) -> bool:
    """Check if a peer is valid (not localhost).

    Args:
        peer: Peer endpoint in format nodeID@ip:port

    Returns:
        bool: True if peer is valid, False if localhost

    """
    return not any(x in peer for x in ["127.0.0.1", "localhost", "::1"])


def get_qualified_peers(
    polkachu_data: PolkachuData,
    config: PeerConfig,
) -> list:
    """Find peers meeting the specified config."""
    qualified_peers = []
    attempts = 0

    while len(qualified_peers) < config.peers.desired_count and attempts < config.peers.max_attempts:
        attempts += 1
        if attempts == 1:
            logging.info(
                "Starting PeerScout. Looking for %d peers over %d attempts",
                config.peers.desired_count,
                config.peers.max_attempts,
            )

        all_peers = polkachu_data.fetch_live_peers(config.peers.network).live_peers

        new_peers = []
        for peer in all_peers:
            if is_valid_peer(peer):
                new_peers.append(peer)
            else:
                logging.info("Skipping %s: invalid peer", peer)

        country_filtered = filter_peers_by_country(new_peers, config.peers.target_countries, config.access_token)

        latency_filtered = filter_peers_by_latency(country_filtered, config.peers.max_latency)

        qualified_peers.extend(latency_filtered)

        qualified_peers = list(set(qualified_peers))

        if len(qualified_peers) >= config.peers.desired_count:
            break

        if len(qualified_peers) == 0:
            logging.warning(
                "After %d attempts, we have not found a suitable peer. Retrying...",
                attempts,
            )
        elif len(qualified_peers) < config.peers.desired_count:
            logging.info(
                "After %d attempts, we currently have %d peers (need %d). Retrying...",
                attempts,
                len(qualified_peers),
                config.peers.desired_count,
            )

    return qualified_peers[: config.peers.desired_count]


def peers_to_comma_separated(peers: list) -> str:
    """Convert a list of peers to a comma-separated string.

    Args:
        peers (list): List of peer endpoints (nodeID@ip:port).

    Returns:
        str: Comma-separated string of peers.

    """
    return ",".join(peers)


def main() -> None:  # noqa: D103
    config = Config.initialise()

    polkachu_data = PolkachuData()

    valid_chains = polkachu_data.fetch_valid_chains()

    if config.peers.network not in valid_chains:
        close_matches = difflib.get_close_matches(config.peers.network, valid_chains)
        msg = "The network '%s' is not supported by Polkachu."
        if close_matches:
            msg += f" Did you mean {', '.join(close_matches)}?"
        logging.error(msg, config.peers.network)
        return

    chain_details = polkachu_data.fetch_chain_details(config.peers.network)

    if not chain_details.polkachu_services["live_peers"]["active"]:
        logging.error("Live peers service not available for %s", chain_details.name)
        return

    final_peers = get_qualified_peers(polkachu_data, config)

    if final_peers:
        match config.output_format:
            case "list":
                if len(final_peers) < config.peers.desired_count:
                    logging.warning("Only %d out of %d peers were found.", len(final_peers), config.peers.desired_count)
                else:
                    logging.info("Found %d peers that meet the criteria:", len(final_peers))
                for peer in final_peers:
                    msg = f"- {peer}"
                    print(msg)
            case "string":
                cs_output = peers_to_comma_separated(final_peers)
                msg = f"Comma-Separated Peers:\n{cs_output}"
                print(msg)
    else:
        logging.error("No qualified peers found based on the given criteria.")


if __name__ == "__main__":
    main()
