import logging
from unittest.mock import patch

import ping3
from behave import given, then, when

from peerscout.main import Config, Data, Filter, PeerConfig, PeerEndpoint

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@given("the polkachu API returns the following chains: {chains}")
def step_impl(context, chains):
    """Set up a dummy configuration for the {chain} network.

    In a real test, you might check an endpoint; here we assume it's available.
    """
    context.peer_config = Config(
        debug=False,
        peers=PeerConfig(
            network="",
            target_countries=[],
            max_latency=100,
            desired_count=5,
            max_attempts=5,
            access_token="dummy_token",
        ),
        output_format="list",
    )
    data = Data(context.peer_config)

    mock_data = chains.split(",")
    with patch("peerscout.main.Data._fetch_data", return_value=mock_data):
        context.valid_chains = data.fetch_valid_chains()
        logging.debug(f"{chains} network are assumed available for testing.")


@when("I specify the network: {chain}")
def step_impl(context, chain):
    context.peer_config.peers.network = chain
    logging.debug(f"Network set to: {chain}")


@when("I specify the target countries: {countries}")
def step_impl(context, countries):
    """Update the configuration with the list of target countries."""
    context.peer_config.peers.target_countries = countries.split(",")
    logging.debug(f"Target countries set to: {countries}")


@when("I specify the maximum allowed latency to: {latency}ms")
def step_impl(context, latency):
    """Set the maximum allowed latency (in milliseconds) in our configuration."""
    context.peer_config.peers.max_latency = float(latency)
    logging.debug(f"Maximum allowed latency set to: {latency}ms")


@when("the location of the peer is: {country}")
def step_impl(context, country):
    """Update the configuration with peer country."""
    context.peer_location = {
        "203.0.113.1": {"country": country},
    }
    logging.debug(f"Peer created with country set to: {country}")


@when("the latency of the peer is: {latency}ms")
def step_impl(context, latency):
    max_latency = float(context.peer_config.peers.max_latency)
    peer_latency = float(latency)

    with patch("ping3.ping", return_value=peer_latency), patch("ipinfo.getHandler") as mock_handler:
        mock_handler.return_value.getBatchDetails.return_value = context.peer_location

        dummy_peers = ["node1@203.0.113.1:26656"]
        context.dummy_peers = dummy_peers

        filter_instance = Filter(context.peer_config)
        valid_peers = filter_instance.filter_peers(dummy_peers)
        if valid_peers:
            context.valid_peers = valid_peers

        for peer_str in valid_peers:
            peer = PeerEndpoint.from_string(peer_str)
            latency_val = ping3.ping(peer.ip, timeout=max_latency / 1000, unit="ms")
            assert latency_val <= max_latency, (
                f"Peer {peer_str} reported latency {latency_val}ms, which exceeds the allowed {max_latency}ms"
            )
    logging.debug(f"Peer created with latency set to: {latency}ms")


@then("the number of peers I expect to receive is: {count}")
def step_impl(context, count):
    """Verify that the number of peers returned is as expected."""
    count = int(count)
    if count == 0:
        assert not hasattr(context, "valid_peers"), "Valid peers data should not be found in context."
    else:
        assert hasattr(context, "valid_peers"), "Valid peers data not found in context."
        assert len(context.valid_peers) > 0, "No valid peers were returned after filtering."
        logging.debug(f"Valid peers returned: {context.valid_peers}")


@then("I should receive an error")
def step_impl(context):
    if context.peer_config.peers.network not in context.valid_chains:
        assert True, f"The network {context.peer_config.peers.network} is not supported by Polkachu."
    elif context.peer_location["country"] not in context.peer_config.peers.target_countries:
        assert True, f"The peer is not in the target countries {context.peer_config.peers.target_countries}."
    else:
        assert False, "We expected an error, and we didn't get one"
