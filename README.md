# PeerScout
PeerScout is a tool for retrieving and filtering peers from Polkachu’s live peer list. It checks each peer’s latency and geolocation, then returns only those peers matching your desired region and performance criteria.

*Note*: Currently, PeerScout is narrowly focused, as it was initially built for a specific use case. However, it could be extended to:

* Return additional peer data
* Poll different APIs
* Offer more flexible filtering options

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

```bash
export IPINFO_ACCESS_TOKEN

peerscout --network dydx --target_country CA,US,UK,DE

Skipping 6d2bda12d7dbeabff7aee0ec561b594e06fcb537@142.93.138.76:26180 because it's not in ['CA', 'US', 'UK', 'DE']
Skipping 8a88a0a0226ef888f3208a869e9bb4dc48b4cd67@65.21.198.18:23856 because it's not in ['CA', 'US', 'UK', 'DE']
Skipping d294a7dc2bf83cb151e94d314baf3905914708e0@18.176.224.64:26656 because it's not in ['CA', 'US', 'UK', 'DE']
Skipping c48a2c4aa69611cf0a252b64955f447b4c8b22ce@13.230.226.117:26656 because it's not in ['CA', 'US', 'UK', 'DE']
Latency for d4bc351eda36bfee170d56258820302e3792cf5a@34.107.5.148:26656: 0.268 milliseconds
Found 1 suitable peers, fetching more...
Skipping f8ca78a518a6ac7ac1186005ab84c51ecd8b2c00@47.129.138.206:26656 because it's not in ['CA', 'US', 'UK', 'DE']
Skipping 9456d5c67ee46d4daa9cecdd6392326152cabb15@23.227.222.215:26656 because it's not in ['CA', 'US', 'UK', 'DE']
Skipping 8c171e14db66171d411c0a097701b2e14cfcdd8a@23.227.220.248:26656 because it's not in ['CA', 'US', 'UK', 'DE']
Latency for b93a086f94f651dd33c0cea12806de973f23d252@144.76.98.17:26656: 0.635 milliseconds
Latency for 9388f26a5ab25de666ecbb4f6c3738e8c73dedd7@141.95.99.111:20008: 0.207 milliseconds Found 3 suitable peers, fetching more...
Skipping ffdff29609e065c2d987097b1ebc62b6dfd14bad@65.108.71.119:26656 because it's not in ['CA', 'US', 'UK', 'DE']
Skipping 371e90a6e1109430fe97796c43546c5a4bfaeefa@65.109.118.94:23856 because it's not in ['CA', 'US', 'UK', 'DE']
Skipping 8f11801c9af307c3df13f50f27840fdf131e05d6@31.223.195.128:26656 because it's not in ['CA', 'US', 'UK', 'DE']
Latency for a954026048132a18afe8e1e6073110d5364b6251@51.195.7.7:26656: 2.242 milliseconds
Latency for 5469c584b8befb8d278867e4e93ade4559248cf8@49.12.150.216:26656: 0.073 milliseconds
Found 5 peers that meet our criteria:
b93a086f94f651dd33c0cea12806de973f23d252@144.76.98.17:26656
a954026048132a18afe8e1e6073110d5364b6251@51.195.7.7:26656
d4bc351eda36bfee170d56258820302e3792cf5a@34.107.5.148:26656
9388f26a5ab25de666ecbb4f6c3738e8c73dedd7@141.95.99.111:20008
5469c584b8befb8d278867e4e93ade4559248cf8@49.12.150.216:26656
```

## Options
Below are the available command-line arguments for peerscout:

  * `-h, --help`: Display the help message and exit.
  * `--desired_count DESIRED_COUNT` (default: 5): The desired number of peers to find.
  * `--max_attempts MAX_ATTEMPTS` (default: 5): The maximum number of attempts to find peers.
  * `--max_latency MAX_LATENCY` (default: 50): The maximum latency (in milliseconds).
  * `--network NETWORK` (default: None): The network to scout peers for.
  * `--output OUTPUT` (default: list): The format in which you want the data returned. Choices:
    * `list`: Detailed list with emojis and colored text.
    * `string`: Comma-separated string of peers.
    * `raw`: List of peers without emojis or colors.
  * `--target_country TARGET_COUNTRY` (default: CA,US): Comma-separated list of target countries (e.g. 'CA,US' or 'DE').

## Development
A Dev Container configuration (`devcontainer.json`) is provided at the root of the project. If you open this project in VSCode, you will be prompted to reopen it in the dev container, which sets up a container with all the necessary dependencies for development.

## License
This project is licensed under the MIT License.

## Author
Matt Craven
