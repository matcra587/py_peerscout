Feature: PeerScout Tests
  As a user of peerscout, I want to verify that when I am receiving peers from Polkachu
  that these are suitable for use, not only geographically but also in terms of latency.

  Scenario: Validate peer is within our required parameters
    Given the polkachu API returns the following chains: axelar,cosmos,dydx
    When I specify the network: cosmos
    And I specify the target countries: CA,US
    And I specify the maximum allowed latency to: 150ms
    And the location of the peer is: CA
    And the latency of the peer is: 100ms
    Then the number of peers I expect to receive is: 1

  Scenario: Validate peer is outside our required parameters (geographically)
    Given the polkachu API returns the following chains: axelar,cosmos,dydx
    When I specify the network: cosmos
    And I specify the target countries: CA,US
    And the location of the peer is: GB
    Then the number of peers I expect to receive is: 0

  Scenario: Validate peer is outside our required parameters (latency)
    Given the polkachu API returns the following chains: axelar,cosmos,dydx
    When I specify the network: cosmos
    And I specify the target countries: CA,US
    And I specify the maximum allowed latency to: 50ms
    And the location of the peer is: US
    And the latency of the peer is: 100ms
    Then the number of peers I expect to receive is: 0

  Scenario: Validate incorrect network being used
    Given the polkachu API returns the following chains: axelar,cosmos
    When I specify the network: dydx
    Then I should receive an error
