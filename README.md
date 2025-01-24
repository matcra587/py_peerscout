# PeerScout
PeerScout is a tool for retrieving and filtering peers from Polkachu's live peer list. It checks each peer's latency and geolocation, then returns only those peers matching your desired region and performance criteria.

## Purpose

Whilst you can visit Polkachu's website to retrieve a list of peers, there's no built-in way to check each peer's physical location or measure your latency to it. As a result, you might inadvertently connect to a peer halfway around the world. PeerScout leverages Polkachu's API (alongside geolocation and latency checks) to give you greater confidence that you're choosing peers better suited for your node's performance needs.

*Note*: Currently, PeerScout is narrowly focused, as it was initially built for a specific use case. However, it could be extended to:

* Return additional peer data
* Poll different APIs
* Offer more flexible filtering options
  * Maybe check if we can communicate on the port if we can't ping the endpoint 

## Prerequisites
An IPinfo API access token. You can [sign up](https://ipinfo.io/signup) for a free account to obtain one.

## Installation

```bash
Clone the repository
gh repo clone matcra587/py_peerscout

Navigate into the project folder
cd py_peerscout

Install in editable mode
pip install -e .
```

## Usage
Once installed, you can run peerscout directly from your terminal. For example:

<details>
<summary>Click to see example output (standard)</summary>

```bash
export IPINFO_ACCESS_TOKEN

peerscout --network cosmos --target_country CA,US,GB,DE

INFO: Starting PeerScout. Looking for 5 peers over 5 attempts
WARNING: After 1 attempts, we have not found a suitable peer. Retrying...
INFO: After 2 attempts, we currently have 2 peers (need 5). Retrying...
INFO: After 3 attempts, we currently have 2 peers (need 5). Retrying...
INFO: After 4 attempts, we currently have 3 peers (need 5). Retrying...
INFO: After 5 attempts, we currently have 3 peers (need 5). Retrying...
WARNING: Only 3 out of 5 peers were found.
- 6a40fcafbf98a8d0cae4437c76486a6cb88576dc@140.235.158.24:26656
- 8220e8029929413afff48dccc6a263e9ac0c3e5e@204.16.247.237:26656
- 8f25b414e80b7fc8d8c07ef2bb78dd8dcd64be3a@51.79.78.30:26656
```
</details>

<details>
<summary>Click to see example output (debug)</summary>

```bash
export IPINFO_ACCESS_TOKEN

peerscout --network cosmos --target_country CA,US,GB,DE --debug

INFO: Starting PeerScout. Looking for 5 peers over 5 attempts
DEBUG: Peer bc73bedb1044e1453a2d7651ab32be4000d3d958@34.195.124.95:26656 is in a target country (US).
DEBUG: Peer 8eb9545668648234cbd25bc9501bd377d7aaf682@49.12.174.62:26656 is in a target country (DE).
DEBUG: Skipping dfc9f2646b05bd9e0159fa52c20b4ed885558ce5@162.19.56.16:26656 (country=FR not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Skipping 613a62ce380c5da84119bc5a6d495391c01a67cc@35.210.193.98:26656 (country=BE not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Skipping 36ad7bacc3a18b4deb647c60a0c1d8bbd24fde39@82.113.25.131:26656 (country=MC not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Timeout for bc73bedb1044e1453a2d7651ab32be4000d3d958@34.195.124.95:26656: Request timeout for ICMP packet. (Timeout=0.05s)
DEBUG: Timeout for 8eb9545668648234cbd25bc9501bd377d7aaf682@49.12.174.62:26656: Request timeout for ICMP packet. (Timeout=0.05s)
WARNING: After 1 attempts, we have not found a suitable peer. Retrying...
DEBUG: Skipping ce345ae23f0d16e5d843c1f84f8e410d732b5bd8@46.105.71.65:26656 (country=FR not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Peer e829d4764a5cecc44b3414777853b34407b36601@198.244.202.140:26656 is in a target country (GB).
DEBUG: Skipping b0a8b753f31d6ed1307aed8cb9012d755e25368e@148.113.0.100:26656 (country=IN not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Peer 84869e7d8712715bfcb54805a8b87760b6dfe19c@142.132.193.194:26656 is in a target country (DE).
DEBUG: Skipping fe21dd474640247888fc7c4dce82da8da08a8bfd@135.181.113.227:26656 (country=FI not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Timeout for e829d4764a5cecc44b3414777853b34407b36601@198.244.202.140:26656: Request timeout for ICMP packet. (Timeout=0.05s)
DEBUG: Timeout for 84869e7d8712715bfcb54805a8b87760b6dfe19c@142.132.193.194:26656: Request timeout for ICMP packet. (Timeout=0.05s)
WARNING: After 2 attempts, we have not found a suitable peer. Retrying...
DEBUG: Skipping 42541224049c05da9b37631b618d7f96875e320a@185.137.173.156:26656 (country=CH not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Peer 0b724ace53341638fcef348469a11d2987be738d@3.231.68.59:26656 is in a target country (US).
DEBUG: Skipping aa70e2cc756b8dd9e265e578197d3049d67d731f@93.189.30.109:26656 (country=AT not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Peer bc73bedb1044e1453a2d7651ab32be4000d3d958@34.195.124.95:26656 is in a target country (US).
DEBUG: Peer ffe59753569c6547972cbf4decc786895e43db91@67.218.8.88:26656 is in a target country (US).
DEBUG: Timeout for 0b724ace53341638fcef348469a11d2987be738d@3.231.68.59:26656: Request timeout for ICMP packet. (Timeout=0.05s)
DEBUG: Timeout for bc73bedb1044e1453a2d7651ab32be4000d3d958@34.195.124.95:26656: Request timeout for ICMP packet. (Timeout=0.05s)
DEBUG: Timeout for ffe59753569c6547972cbf4decc786895e43db91@67.218.8.88:26656: Request timeout for ICMP packet. (Timeout=0.05s)
WARNING: After 3 attempts, we have not found a suitable peer. Retrying...
DEBUG: Peer 69fddfdb0df303964b0115bfd4b969ef49dcade6@3.217.133.209:26656 is in a target country (US).
DEBUG: Skipping d65b06ba3af80a504d70bef8fc86e4f3f7d00ec6@176.103.222.165:26656 (country=NL not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Peer 63f1915e9d052a04cb11243bb90ff67879dd972c@141.98.219.28:26656 is in a target country (US).
DEBUG: Skipping 155ee9292bf5212c9577841018131428939e0a85@128.199.128.15:26090 (country=SG not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Peer 4f2f4a2df4ace3387c30925db75147e52eab2532@35.212.175.163:26656 is in a target country (US).
DEBUG: Timeout for 69fddfdb0df303964b0115bfd4b969ef49dcade6@3.217.133.209:26656: Request timeout for ICMP packet. (Timeout=0.05s)
DEBUG: 63f1915e9d052a04cb11243bb90ff67879dd972c@141.98.219.28:26656 is good: latency=38.70 ms <= 50.00 ms.
DEBUG: Timeout for 4f2f4a2df4ace3387c30925db75147e52eab2532@35.212.175.163:26656: Request timeout for ICMP packet. (Timeout=0.05s)
INFO: After 4 attempts, we currently have 1 peers (need 5). Retrying...
DEBUG: Skipping 2b7a7a6044a26bc7e74b0252d0a7d551e8939bd7@74.118.136.19:26656 (country=NL not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Peer 6681cee74de13aaac561442bcbc420bdb025aacc@116.202.85.179:26656 is in a target country (DE).
DEBUG: Skipping 793a5c79d2eae09b11c5feed5e945c30f3ccc706@64.130.55.5:26656 (country=NL not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Skipping ce345ae23f0d16e5d843c1f84f8e410d732b5bd8@46.105.71.65:26656 (country=FR not in ['CA', 'US', 'GB', 'DE']).
DEBUG: Peer 48c5af84afc9e25f62a7189f0260fd907aac5f68@204.16.247.246:26656 is in a target country (US).
DEBUG: Timeout for 6681cee74de13aaac561442bcbc420bdb025aacc@116.202.85.179:26656: Request timeout for ICMP packet. (Timeout=0.05s)
DEBUG: 48c5af84afc9e25f62a7189f0260fd907aac5f68@204.16.247.246:26656 is good: latency=38.06 ms <= 50.00 ms.
INFO: After 5 attempts, we currently have 2 peers (need 5). Retrying...
WARNING: Only 2 out of 5 peers were found.
- 63f1915e9d052a04cb11243bb90ff67879dd972c@141.98.219.28:26656
- 48c5af84afc9e25f62a7189f0260fd907aac5f68@204.16.247.246:26656
```
</details>

## Options
Below are the available command-line arguments for peerscout:

  * `-h, --help`: Display the help message and exit.
  * `--desired_count DESIRED_COUNT` (default: 5): The desired number of peers to find.
  * `--max_attempts MAX_ATTEMPTS` (default: 5): The maximum number of attempts to find peers.
  * `--max_latency MAX_LATENCY` (default: 50): The maximum latency (in milliseconds).
  * `--network NETWORK` (default: None): The network to scout peers for.
  * `--output OUTPUT` (default: list): The format in which you want the data returned. Choices:
    * `list`: List of peers suitable for an ansible `vars` file.
    * `string`: Comma-separated string of peers.
  * `--target_country TARGET_COUNTRY` (default: CA,US): Comma-separated list of target countries (e.g. 'CA,US' or 'DE')
  * `--debug`: Enable debug logging.

## Development
A Dev Container configuration (`devcontainer.json`) is provided at the root of the project. If you open this project in VSCode, you will be prompted to reopen it in the dev container, which sets up a container with all the necessary dependencies for development.

## License
This project is licensed under the MIT License.

## Author
Matt Craven
