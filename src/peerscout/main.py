"""A Python script for retrieving and filtering network peers based on latency and geographical location.

Uses the Polkachu API to fetch live peers and filters them based on specified criteria.
"""

import difflib
import logging
import re
import socket
import sys
import time
from dataclasses import dataclass
from operator import itemgetter
from typing import TypedDict

import configargparse
import ipinfo
import ping3

# Enable exceptions mode for ping3
ping3.EXCEPTIONS = True


class UnsupportedNetworkError(ValueError):
    """Exception raised for unsupported networks."""


class ServiceUnavailableError(Exception):
    """Exception raised for service unavailability."""


class NoValidPeersError(Exception):
    """Exception raised for no valid peers."""


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
class PeerEndpoint:
    """Represents a peer endpoint with parsed components."""

    node_id: str
    ip: str
    port: int

    @classmethod
    def from_string(cls, endpoint: str) -> "PeerEndpoint":
        """Parse peer endpoint string."""
        node_id, address = endpoint.split("@")
        ip, port = address.split(":")
        return cls(node_id=node_id, ip=ip, port=int(port))

    def __str__(self) -> str:
        """Convert back to nodeID@ip:port format."""
        return f"{self.node_id}@{self.ip}:{self.port}"


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

    def __post_init__(self) -> None:
        """Clean up target countries after initialisation."""
        combined = " ".join(self.target_countries)
        split_countries = re.split(r"[\s,]+", combined)
        self.target_countries = [country.strip() for country in split_countries if country.strip()]

    @classmethod
    def from_args(cls, args: configargparse.Namespace) -> "PeerConfig":
        """Create PeerCriteria from command line arguments."""
        return cls(
            network=args.network,
            target_countries=args.target_countries,
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

    @classmethod
    def parse_args(cls) -> configargparse.Namespace:
        """Parse command line arguments."""
        parser = configargparse.ArgParser(
            config_file_parser_class=configargparse.YAMLConfigFileParser,
            default_config_files=["config.yaml"],
            description="A tool for gathering and filtering peers for a given network from Polkachu.",
            add_help=True,
        )

        parser.add("-c", "--config", required=False, is_config_file=True, help="config file path")
        parser.add_argument(
            "--network", type=str, required=True, env_var="NETWORK", help="The network to scout peers for"
        )
        parser.add_argument(
            "--target_countries",
            type=str,
            nargs="*",
            default=["CA", "US"],
            required=False,
            env_var="TARGET_COUNTRIES",
            help="List of target countries. Can be comma or space separated (e.g. 'CA,US,GB' or 'CA US GB').",
        )
        parser.add_argument(
            "--desired_count",
            type=int,
            default=5,
            required=False,
            env_var="DESIRED_COUNT",
            help="The desired number of peers to find",
        )
        parser.add_argument(
            "--max_latency",
            type=int,
            default=50,
            required=False,
            env_var="MAX_LATENCY",
            help="The maximum latency in milliseconds",
        )
        parser.add_argument(
            "--max_attempts",
            type=int,
            default=5,
            required=False,
            env_var="MAX_ATTEMPTS",
            help="The maximum number of attempts to find peers",
        )
        parser.add_argument(
            "--format",
            dest="output_format",
            type=str,
            choices=["list", "string"],
            default="list",
            env_var="FORMAT",
            help="Output format (list/string)",
        )
        parser.add_argument(
            "--access_token",
            type=str,
            required=False,
            env_var="ACCESS_TOKEN",
            help="IPinfo API access token",
        )
        parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")

        args = parser.parse_args()
        logging.debug("All config values: %s", args)
        return args

    @classmethod
    def initialise(cls) -> "Config":
        """Initialise complete monitoring setup and return config."""
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

        args = cls.parse_args()

        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.INFO)

        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        return cls.from_args(args)

    @classmethod
    def from_args(cls, args: configargparse.Namespace) -> "Config":
        """Create config from parsed arguments."""
        return cls(
            debug=args.debug,
            peers=PeerConfig.from_args(args),
            output_format=args.output_format,
        )


class Data:
    """A class to interact with the Polkachu API."""

    def __init__(self, config: Config, base_url: str = "https://polkachu.com") -> None:
        """Initialize the Poller with the base URL of the Polkachu API."""
        self.config = config
        self.base_url = base_url

    def _fetch_data(self, endpoint: str) -> dict:
        """Retrieve data from the Polkachu API."""
        import requests

        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.warning("Error fetching data from %s: %s", url, e)
            return {}

    def fetch_valid_chains(self) -> list[str]:
        """Retrieve a list of chains supported by Polkachu."""
        return self._fetch_data("api/v2/chains")

    def fetch_chain_details(self) -> ChainDetails:
        """Retrieve detailed information of a chain."""
        data = self._fetch_data(f"api/v2/chains/{self.config.peers.network}")
        return ChainDetails.from_dict(data)

    def fetch_live_peers(self) -> ChainLivePeers:
        """Retrieve live peers of a chain."""
        unique_peers = set()
        peer_amount = 25
        attempts = 0
        last_data = None

        while attempts < self.config.peers.max_attempts and len(unique_peers) < peer_amount:
            data = self._fetch_data(f"api/v2/chains/{self.config.peers.network}/live_peers")
            if "live_peers" in data:
                last_data = data
                unique_peers.update(data["live_peers"])
                logging.debug("Found %d unique peers out of %d desired", len(unique_peers), peer_amount)
            attempts += 1

        if not last_data:
            return ChainLivePeers(network=self.config.peers.network, polkachu_peer="", live_peers=[])

        final_peers = list(unique_peers)[:peer_amount]
        logging.info("Starting with %d peers", len(final_peers))
        return ChainLivePeers(
            network=self.config.peers.network, polkachu_peer=last_data["polkachu_peer"], live_peers=final_peers
        )

    def fetch_polkachu_peer(self) -> ChainLivePeers:
        """Retrieve the Polkachu internal live state-sync peer of a chain.

        Note:
            Not actively used. Added for potential future use.

        Args:
            network (str): The network name (e.g., 'dydx', 'osmosis').

        Returns:
            ChainLivePeers: Polkachu internal live state-sync peer.

        """
        data = self._fetch_data(f"api/v2/chains/{self.config.peers.network}/live_peers")
        return ChainLivePeers(network=self.config.peers.network, polkachu_peer=data["polkachu_peer"], live_peers=None)


class Filter:
    """Filter peers based on location and latency criteria."""

    def __init__(self, config: Config) -> None:
        """Initialise filter with configuration."""
        self.config = config

    def filter_peers(self, peers: list[str]) -> list[str]:
        """Apply all filters in sequence with timing metrics."""
        start_total = time.perf_counter()
        peer_endpoints = [PeerEndpoint.from_string(peer) for peer in peers]

        start = time.perf_counter()
        filtered_peers = self._filter_invalid_peers(peer_endpoints)
        invalid_time = time.perf_counter() - start
        logging.debug("Invalid peer filtering took %.2f seconds", invalid_time)

        start = time.perf_counter()
        filtered_peers = self._filter_by_country(filtered_peers)
        country_time = time.perf_counter() - start
        logging.debug("Country filtering took %.2f seconds", country_time)

        start = time.perf_counter()
        filtered_peers = self._filter_by_latency(filtered_peers)
        latency_time = time.perf_counter() - start
        logging.debug("Latency filtering took %.2f seconds", latency_time)

        total_time = time.perf_counter() - start_total
        logging.debug("Total filtering took %.2f seconds", total_time)

        return [str(peer) for peer in filtered_peers][: self.config.peers.desired_count]

    def _filter_invalid_peers(self, peers: list[PeerEndpoint]) -> list[PeerEndpoint]:
        """Remove entities that we know are not presenting the correct p2p address.

        >>> 127.0.0.1, localhost, ::1
        """
        filtered_peers = [peer for peer in peers if peer.ip not in ["127.0.0.1", "localhost", "::1"]]
        if len(peers) - len(filtered_peers) > 0:
            logging.info("Filtered out %d localhost peers", len(peers) - len(filtered_peers))
        return filtered_peers

    def _filter_by_country(self, peers: list[PeerEndpoint]) -> list[PeerEndpoint]:
        """Filter peers by geographic location using batch processing."""
        handler = ipinfo.getHandler(self.config.peers.access_token)
        peer_map = {peer.ip: peer for peer in peers}

        try:
            batch_details = handler.getBatchDetails(list(peer_map.keys()))
            filtered_peers = []
            for ip, details in batch_details.items():
                country = details.get("country") if isinstance(details, dict) else details
                if country in self.config.peers.target_countries:
                    filtered_peers.append(peer_map[ip])
                    logging.debug("Peer %s is in target country (%s)", peer_map[ip], country)
        except ipinfo.error.APIError as e:
            logging.warning("Batch location lookup failed: %s", e)
            return []
        else:
            if len(peers) - len(filtered_peers) > 0:
                logging.info("Filtered out %d peers not in target country", len(peers) - len(filtered_peers))
            return filtered_peers

    def _filter_by_latency(self, peers: list[PeerEndpoint]) -> list[PeerEndpoint]:
        """Filter peers by latency."""
        peer_latencies = []
        high_latency_peers = []
        closed_ports = []
        error_peers = []

        for peer in peers:
            try:
                latency = ping3.ping(str(peer.ip), timeout=self.config.peers.max_latency / 1000, unit="ms")
                if latency is None:
                    logging.debug("ICMP appears blocked for %s, trying TCP", peer.ip)
                    if self._test_port_open(peer):
                        peer_latencies.append((peer, self.config.peers.max_latency))
                        logging.debug("TCP connection successful to %s:%d", peer.ip, peer.port)
                    else:
                        closed_ports.append(peer)
                        logging.debug("TCP connection failed to %s:%d", peer.ip, peer.port)
                elif latency <= self.config.peers.max_latency:
                    peer_latencies.append((peer, latency))
                    logging.debug("Peer %s has good latency: %.2f ms", peer, latency)
                else:
                    high_latency_peers.append(peer)
                    logging.debug("Peer %s latency too high: %.2f ms", peer, latency)
            except (ping3.errors.HostUnknown, ping3.errors.PingError) as e:
                error_peers.append(peer)
                logging.debug("Ping error for %s: %s", peer.ip, e)

        peer_latencies.sort(key=itemgetter(1))
        filtered_peers = [peer for peer, _ in peer_latencies]

        if len(peers) - len(filtered_peers) > 0:
            msg = (
                "Summary: %d total peers processed:\n"
                "- %d passed\n"
                "- %d high latency\n"
                "- %d closed ports\n"
                "- %d ping errors"
            )
            logging.debug(
                msg, len(peers), len(filtered_peers), len(high_latency_peers), len(closed_ports), len(error_peers)
            )

        return filtered_peers

    def _test_port_open(self, peer: PeerEndpoint) -> bool:
        """Test if a port is open on a peer in the event that the ping times out."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex((peer.ip, peer.port)) == 0
        except OSError:
            return False


def main() -> None:
    """Run peerscout against desired network."""
    config = Config.initialise()
    data = Data(config)

    try:
        valid_chains = data.fetch_valid_chains()

        if config.peers.network not in valid_chains:
            close_matches = difflib.get_close_matches(config.peers.network, valid_chains)
            msg = f"The network '{config.peers.network}' is not supported by Polkachu."
            if close_matches:
                msg += f" Did you mean {', '.join(close_matches)}?"
            raise UnsupportedNetworkError(msg)  # noqa: TRY301
    except UnsupportedNetworkError as e:
        logging.error(e)  # noqa: TRY400
        sys.exit(1)

    try:
        chain_details = data.fetch_chain_details()

        if not chain_details.polkachu_services["live_peers"]["active"]:
            msg = "Live peers service not available for %s"
            logging.error(msg, chain_details.name)
            raise ServiceUnavailableError(msg)  # noqa: TRY301
    except ServiceUnavailableError as e:
        logging.error(e)  # noqa: TRY400
        sys.exit(1)

    peers_data = data.fetch_live_peers()
    peers = peers_data.live_peers

    filtered_data = Filter(config)
    try:
        valid_peers = filtered_data.filter_peers(peers)

        if valid_peers:
            match config.output_format:
                case "list":
                    if len(valid_peers) < config.peers.desired_count:
                        logging.warning(
                            "Only %d out of %d peers were found.", len(valid_peers), config.peers.desired_count
                        )
                    else:
                        logging.info("Found %d peers that meet the criteria:", len(valid_peers))
                    for peer in valid_peers:
                        msg = f"- {peer}"
                        print(msg)
                case "string":
                    cs_output = ",".join(valid_peers)
                    msg = f"Comma-Separated Peers:\n{cs_output}"
                    print(msg)
        else:
            msg = "No valid peers found based on the given criteria."
            raise NoValidPeersError(msg)  # noqa: TRY301
    except NoValidPeersError as e:
        logging.error(e)  # noqa: TRY400
        sys.exit(1)


if __name__ == "__main__":
    main()
