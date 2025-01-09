import pytest
from peerscout import main


@pytest.mark.parametrize(
    "network",
    [
        "dydx",
    ],
)
def test_get_live_peers(network):
    try:
        network = main.get_live_peers(network)
        print("\nTesting Valid Peers:")
        print(f"Input network: {network}")

        assert network is not None, (
            f"Expected list of peers, got None for network {network}"
        )
        assert len(network) == 5, (
            f"Expected 5 peers , got {len(network)} for network {network}"
        )

    except Exception as e:
        pytest.fail(f"Unexpected error testing {network}: {str(e)}")


@pytest.mark.parametrize(
    "test_peer",
    [
        "node1@1.1.1.1:8080",
    ],
)
def test_check_peer_latency(test_peer):
    try:
        latency = main.check_peer_latency(test_peer)
        print("\nTesting valid peer connection:")
        print(f"Input peer: {test_peer}")
        print(f"Measured latency: {latency:.3f} milliseconds")

        assert latency is not None, (
            f"Expected latency measurement, got None for peer {test_peer}"
        )
        assert latency > 0, (
            f"Expected positive latency, got {latency} for peer {test_peer}"
        )

    except Exception as e:
        pytest.fail(f"Unexpected error testing {test_peer}: {str(e)}")


@pytest.mark.parametrize(
    "test_peer",
    [
        "node1@123.456.789.123:8080",
    ],
)
def test_check_peer_latency_invalid_peer(test_peer):
    print("\nTesting invalid peer connection:")
    print(f"Input peer: {test_peer}")

    try:
        latency = main.check_peer_latency(test_peer)
        pytest.fail(
            f"Expected ValueError for invalid peer {test_peer}, but got latency: {latency}"
        )
    except ValueError as e:
        print(f"Caught expected ValueError: {str(e)}")
    except Exception as e:
        pytest.fail(f"Expected ValueError but got different exception: {str(e)}")


@pytest.mark.parametrize("test_peer", ["node1@1.1.1.1:8080", "node2@2.2.2.2:9091"])
def test_check_peer_latency_multiple_peers(test_peer):
    try:
        latency = main.check_peer_latency(test_peer)
        print("\nTesting multiple peers:")
        print(f"Input peer: {test_peer}")
        print(f"Measured latency: {latency:.3f} milliseconds")

        assert latency is not None, (
            f"Expected latency measurement, got None for peer {test_peer}"
        )
        assert isinstance(latency, (int, float)), (
            f"Expected numeric latency, got {type(latency)} for peer {test_peer}"
        )

    except Exception as e:
        pytest.fail(f"Unexpected error testing multiple peer {test_peer}: {str(e)}")
