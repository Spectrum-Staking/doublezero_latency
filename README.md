# Solana Gossip Latency Checker for Doublezero

This script checks the status and latency of Solana validators connected to the `doublezero0` network interface. It correlates IP addresses from the local routing table with Solana's gossip and validator information to determine if an IP belongs to an active validator.

## Features

-   Fetches IP addresses from the `doublezero0` network interface.
-   Retrieves validator information using the `solana` CLI.
-   Pings each IP to measure latency.
-   Identifies if an IP address belongs to an active Solana validator.
-   Outputs the results to a CSV file for easy analysis.


## How to Use

    ```bash
    python3 dz_latency.py
    ```

Flags:
- `--ip_list <file_name>` - Use to read a list of IPs using instead of routing table. This is useful
for back-to-back latency comparison between Internet and Doublezero network.
- `--no_geo` - Disable geolocation.

The script will then execute the necessary commands and generate a `dz_latency_result.csv` file in the same directory.

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
    -   Looks up geolocation using ip-api.com and adds city/country to CSV file.
4.  **Generate CSV:** The results are compiled and saved to `dz_latency_result.csv`.
