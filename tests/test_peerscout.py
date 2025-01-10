import pytest
import requests
from ping3 import EXCEPTIONS

from peerscout import main


@pytest.mark.parametrize(
    "network",
    [
        "dydx",
    ],
)
def test_get_live_peers(network: str) -> None:
    expected_peer_count = 5

    try:
        network = main.get_live_peers(network)

        assert network is not None, f"Expected list of peers, got None for network {network}"
        assert len(network) == expected_peer_count, f"Expected 5 peers , got {len(network)} for network {network}"

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Network connection error while testing {network}: {e!s}")


@pytest.mark.parametrize(
    "test_peer",
    [
        "node1@1.1.1.1:8080",
    ],
)
def test_check_peer_latency(test_peer: str) -> None:
    try:
        latency = main.check_peer_latency(test_peer)

        assert latency is not None, f"Expected latency measurement, got None for peer {test_peer}"
        assert latency > 0, f"Expected positive latency, got {latency} for peer {test_peer}"

    except (ValueError, EXCEPTIONS) as e:
        pytest.fail(f"Unexpected error testing {test_peer}: {e!s}")


@pytest.mark.parametrize(
    "test_peer",
    [
        "node1@123.456.789.123:8080",
    ],
)
def test_check_peer_latency_invalid_peer(test_peer: str) -> None:
    try:
        latency = main.check_peer_latency(test_peer)
        pytest.fail(f"Expected ValueError for invalid peer {test_peer}, but got latency: {latency}")
    except ValueError:
        pass


@pytest.mark.parametrize("test_peer", ["node1@1.1.1.1:8080", "node2@2.2.2.2:9091"])
def test_check_peer_latency_multiple_peers(test_peer: str) -> None:
    try:
        latency = main.check_peer_latency(test_peer)

        assert latency is not None, f"Expected latency measurement, got None for peer {test_peer}"
        assert isinstance(latency, (int, float)), f"Expected numeric latency, got {type(latency)} for peer {test_peer}"

    except (ValueError, EXCEPTIONS) as e:
        pytest.fail(f"Unexpected error testing multiple peer {test_peer}: {e!s}")
