# Solana Gossip Latency Checker for Doublezero

This script checks the status and latency of Solana validators connected to the `doublezero0` network interface. It correlates IP addresses from the local routing table with Solana's gossip and validator information to determine if an IP belongs to an active validator.

## Features

-   Fetches IP addresses from the `doublezero0` network interface.
-   Retrieves validator information using the `solana` CLI.
-   Pings each IP to measure latency.
-   Identifies if an IP address belongs to an active Solana validator.
-   Outputs the results to a CSV file for easy analysis.

## Prerequisites

Before running this script, ensure you have the following installed and configured:

-   **Python 3:** The script is written in Python 3.
-   **Solana CLI:** The `solana` command-line tool must be installed and accessible in your system's PATH. You can find installation instructions [here](https://docs.solana.com/cli/install-solana-cli-tools).
-   **`ip` command:** This script uses the `ip` command (from `iproute2`) to get local IP routes. This is standard on most Linux distributions.
-   **Network Interface:** The script is hardcoded to look for the `doublezero0` network interface. You may need to modify the `get_ips_from_cli` function if your interface has a different name.

## How to Use

1.  **Clone the repository or download the script.**
2.  **Ensure all prerequisites are met.**
3.  **Run the script from your terminal:**

    ```bash
    python3 dz_latency.py
    ```

The script will then execute the necessary commands and generate a `validator_status.csv` file in the same directory.

## Output

The script generates a CSV file named `validator_status.csv` with the following columns:

-   **IP:** The IP address of the machine.
-   **Status:** The status of the IP, which can be one of the following:
    -   `validator`: The IP is associated with an active validator.
    -   `gossip`: The IP was found in the gossip protocol but is not in the active validator set.
    -   `gossip_not_found`: The IP was not found in the gossip protocol.
-   **Validator Name:** The name of the validator if it's an active validator.
-   **Latency:** The latency to the IP address in milliseconds (ms).

## How it Works

The script performs the following steps:

1.  **Get Local IPs:** It runs `ip route show dev doublezero0` to get a list of IP addresses associated with the `doublezero0` interface.
2.  **Fetch Solana Data:** It uses the `solana` CLI to get three sets of data:
    -   A list of all nodes in the gossip table (`solana gossip`).
    -   A list of all active validators (`solana validators`).
    -   A list of validator information, including names (`solana validator-info get`).
3.  **Process IPs:** For each IP address, the script:
    -   Pings the IP to measure latency.
    -   Looks up the IP in the gossip data to find its associated validator identity public key.
    -   Checks if the identity public key is in the list of active validators.
4.  **Generate CSV:** The results are compiled and saved to `validator_status.csv`.
