from unittest.mock import MagicMock, patch

import pytest
import requests
from ping3 import errors

from peerscout import main


@pytest.mark.parametrize(
    ("network", "expected_peer_count"),
    [
        ("dydx", 5),
    ],
)
@patch("peerscout.main.get_live_peers")
def test_get_live_peers(mock_get_live_peers: MagicMock, network: str, expected_peer_count: int) -> None:
    mock_peers = [
        "8a675a29f7ef@1.2.3.4:1234",
        "91f8f5671140@5.6.7.8:5678",
        "2e5b1ec612ea@9.10.11.12:9101",
        "642f31ad23ce@13.14.15.16:2345",
        "d0647680c646@17.18.19.20:6789",
    ]
    mock_get_live_peers.return_value = mock_peers

    try:
        result = main.get_live_peers(network)

        assert result is not None, f"Expected list of peers, got None for network {network}"
        assert len(result) == expected_peer_count, (
            f"Expected {expected_peer_count} peers, got {len(result)} for network {network}"
        )
        mock_get_live_peers.assert_called_once_with(network)

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Network connection error while testing {network}: {e!s}")


@pytest.mark.parametrize(
    ("test_peer", "mock_latency"),
    [
        ("node1@1.1.1.1:8080", 100),
    ],
)
@patch("peerscout.main.check_peer_latency")
def test_check_peer_latency(mock_check_peer_latency: MagicMock, test_peer: str, mock_latency: int) -> None:
    mock_check_peer_latency.return_value = mock_latency

    try:
        latency = main.check_peer_latency(test_peer)

        assert latency is not None, f"Expected latency measurement, got None for peer {test_peer}"
        assert latency > 0, f"Expected positive latency, got {latency} for peer {test_peer}"
        mock_check_peer_latency.assert_called_once_with(test_peer)

    except (ValueError, errors.PingError) as e:
        pytest.fail(f"Unexpected error testing {test_peer}: {e!s}")


@pytest.mark.parametrize(
    "test_peer",
    [
        "node1@123.456.789.123:8080",
    ],
)
@patch("peerscout.main.check_peer_latency")
def test_check_peer_latency_invalid_peer(mock_check_peer_latency: MagicMock, test_peer: str) -> None:
    mock_check_peer_latency.side_effect = ValueError("Invalid peer address")

    try:
        latency = main.check_peer_latency(test_peer)
        pytest.fail(f"Expected ValueError for invalid peer {test_peer}, but got latency: {latency}")
    except ValueError:
        pass
    except (errors.PingError, requests.exceptions.RequestException) as e:
        pytest.fail(f"Unexpected exception for invalid peer {test_peer}: {e!s}")


@pytest.mark.parametrize(
    ("test_peer", "mock_latency"),
    [
        ("node1@1.1.1.1:8080", 150),
        ("node2@2.2.2.2:9091", 200),
    ],
)
@patch("peerscout.main.check_peer_latency")
def test_check_peer_latency_multiple_peers(
    mock_check_peer_latency: MagicMock, test_peer: str, mock_latency: int
) -> None:
    mock_check_peer_latency.return_value = mock_latency

    try:
        latency = main.check_peer_latency(test_peer)

        assert latency is not None, f"Expected latency measurement, got None for peer {test_peer}"
        assert isinstance(latency, (int, float)), f"Expected numeric latency, got {type(latency)} for peer {test_peer}"
        assert latency > 0, f"Expected positive latency, got {latency} for peer {test_peer}"

    except (ValueError, errors.PingError) as e:
        pytest.fail(f"Unexpected error testing multiple peer {test_peer}: {e!s}")
