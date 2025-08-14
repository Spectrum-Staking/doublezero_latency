import json
import subprocess
import re
import csv

# --- Configuration ---
OUTPUT_FILE = 'dz_latency_result.csv'
DZ_INTERFACE = 'doublezero0'

def ping_ip(ip_address):
    """
    Pings an IP address to get its latency. Handles different OS commands.

    Args:
        ip_address (str): The IP address to ping.

    Returns:
        str: The latency in ms, or 'unreachable' if the ping fails.
    """
    try:
        command = ['ping', '-c', '3', '-i', '0.2', '-W', '0.5', ip_address]
        latency_pattern = r"min/avg/max/mdev = [\d.]+/([\d.]+)/[\d.]+/[\d.]+ ms"

        # Execute the ping command
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            # Search for the latency in the output
            match = re.search(latency_pattern, result.stdout)
            if match:
                latency = match.group(1)
                print(f"Ping successful for {ip_address}: {latency} ms")
                return latency
        
        print(f"Ping failed for {ip_address}.")
        return 'unreachable'

    except subprocess.TimeoutExpired:
        print(f"Ping timed out for {ip_address}.")
        return 'unreachable'
    except Exception as e:
        print(f"An error occurred during ping for {ip_address}: {e}")
        return 'unreachable'


def get_ips_from_rt():
    """
    Gets a list of IP addresses by running a shell command.

    Returns:
        list: A list of IP addresses.
    """
    command = "ip route show dev %s | awk '{print $1}'" % DZ_INTERFACE
    print(f"Running command to get IPs: \"{command}\"")
    try:
        # Execute the shell command
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            print(f"Error running command to get IPs: {result.stderr}")
            return []

        # Process the output
        ips = result.stdout.strip().split('\n')
        # Filter out any empty strings
        return [ip for ip in ips if ip]

    except subprocess.TimeoutExpired:
        print("Error: Command to get IPs timed out.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while getting IPs: {e}")
        return []

def load_gossip_data():
    """
    Runs the 'solana gossip' command and loads the output as JSON.

    Returns:
        list or None: A list of gossip entries if successful, otherwise None.
    """
    try:
        # Execute the solana gossip command
        command = ['solana', 'gossip', '--output=json']
        print(f"Running command to load gossip data: `{' '.join(command)}`")
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Error running 'solana gossip': {result.stderr}")
            return None

        return json.loads(result.stdout)
    except FileNotFoundError:
        print("Error: 'solana' command not found. Make sure it's installed and in your PATH.")
        return None
    except subprocess.TimeoutExpired:
        print("Error: 'solana gossip' command timed out.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from `solana gossip` command.")
        return None

def get_identity_from_gossip(ip_address, gossip_data):
    """
    Runs the 'solana gossip' command and parses the output to find
    the identity for a given IP address.

    Args:
        ip_address (str): The IP address to check.

    Returns:
        str or None: The identity public key if found, otherwise None.
    """
    try:
        # Iterate through the gossip data to find the matching IP
        for entry in gossip_data:
            if entry.get("ipAddress") == ip_address:
                identity_pubkey = entry.get("identityPubkey")
                if identity_pubkey:
                    print(f"Found identity '{identity_pubkey}' for IP: {ip_address}")
                    return identity_pubkey
        
        print(f"IP {ip_address} not found in gossip.")
        return None
    except Exception as e: # Catch any other unexpected errors during data processing
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def load_active_validators():
    """
    Loads the list of active validator identity pubkeys by running
    the `solana validators` command.

    Returns:
        set: A set of active validator identity pubkeys for efficient lookup.
    """
    command = ['solana', 'validators', '--output=json']
    print(f"Running command to get active validators: `{' '.join(command)}`")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Error running command to get active validators: {result.stderr}")
            return set()
        
        data = json.loads(result.stdout)
        validator_list = data.get("validators", [])
        active_identities = {v.get("identityPubkey") for v in validator_list if v.get("identityPubkey")}
        print(f"Loaded {len(active_identities)} active validator identities.")
        return active_identities
    except FileNotFoundError:
        print("Error: 'solana' command not found. Make sure it's installed and in your PATH.")
        return set()
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from `solana validators` command.")
        return set()
    except subprocess.TimeoutExpired:
        print("Error: `solana validators` command timed out.")
        return set()
    except Exception as e:
        print(f"An unexpected error occurred while loading active validators: {e}")
        return set()

def load_validator_details():
    """
    Loads validator information by running the `solana validator-info get` command
    and creates a mapping from identity public key to validator name.

    Returns:
        dict: A dictionary mapping identity pubkeys to validator names.
    """
    command = ['solana', 'validator-info', 'get', '--output=json']
    print(f"Running command to get validator details: `{' '.join(command)}`")
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Error running command to get validator details: {result.stderr}")
            return {}

        validators_data = json.loads(result.stdout)
        validator_map = {
            v.get("identityPubkey"): v.get("info", {}).get("name")
            for v in validators_data
            if v.get("identityPubkey") and v.get("info", {}).get("name")
        }
        print(f"Loaded {len(validator_map)} validator details.")
        return validator_map
    except FileNotFoundError:
        print("Error: 'solana' command not found. Make sure it's installed and in your PATH.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from `solana validator-info` command.")
        return {}
    except subprocess.TimeoutExpired:
        print("Error: `solana validator-info` command timed out.")
        return {}
    except Exception as e:
        print(f"An unexpected error occurred while loading validator details: {e}")
        return {}

def get_ip_location(ip_address):
    """
    Fetches the city and country for a given IP address using ip-api.com.

    Args:
        ip_address (str): The IP address to look up.

    Returns:
        tuple: A tuple containing (city, country) or ('Unknown', 'Unknown') if lookup fails.
    """
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        if data.get("status") == "success":
            city = data.get("city", "Unknown")
            country = data.get("country", "Unknown")
            print(f"Location for {ip_address}: {city}, {country}")
            return city, country
        else:
            print(f"Could not get location for {ip_address}: {data.get('message', 'Unknown error')}")
            return 'Unknown', 'Unknown'
    except requests.exceptions.RequestException as e:
        print(f"Error fetching location for {ip_address}: {e}")
        return 'Unknown', 'Unknown'
    except Exception as e:
        print(f"An unexpected error occurred during location lookup for {ip_address}: {e}")
        return 'Unknown', 'Unknown'

import requests
def main():
    """
    Main function to orchestrate the validator checking process.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Check validator status and latency.")
    parser.add_argument("--ip_list", help="Path to a file containing a list of IP addresses, one per line.")
    parser.add_argument("--no_geo", action="store_true", help="Enable geolocation lookup.")
    args = parser.parse_args()

    print("Starting validator check...")
    
    # Load necessary data by running CLI commands
    if args.ip_list:
        with open(args.ip_list, 'r') as f:
            ip_addresses = [line.strip() for line in f if line.strip()]
    else:
        ip_addresses = get_ips_from_rt()
    active_validator_identities = load_active_validators()
    validator_info = load_validator_details()
    gossip_data = load_gossip_data()
    if not ip_addresses:
        print("No IP addresses to process. Exiting.")
        return
        
    if not active_validator_identities:
        print("Warning: No active validators loaded. IPs cannot be confirmed as validators.")
        return

    if not validator_info:
        print("Warning: No validator details loaded. IPs cannot be confirmed as validators.")
        return
    
    if not gossip_data:
        print("Warning: No gossip data loaded. IPs cannot be confirmed as validators.")
        return
    results = []
    
    # Process each IP address
    for ip in ip_addresses:
        print(f"\n--- Checking IP: {ip} ---")
        
        latency = ping_ip(ip)
        identity_key = get_identity_from_gossip(ip, gossip_data)
        
        status = 'gossip_not_found'
        name = ''

        if identity_key:
            # Check if the found identity is in the set of active validators
            if identity_key in active_validator_identities:
                status = 'validator'
                # Look up the validator name from the details map
                name = validator_info.get(identity_key, "Unknown")                
                print(f"SUCCESS: IP {ip} with identity {identity_key} is an active validator named '{name}'.")
            else:
                status = 'gossip'
                print(f"INFO: IP {ip} has an identity ({identity_key}) but is NOT in the active validator list.")
        
        if args.no_geo:
            results.append([ip, status, name, latency])
        else:
            city, country = get_ip_location(ip)
            results.append([ip, status, name.replace(',', ''), latency, city, country])

    # Save the results to a CSV file
    try:
        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write the header
            if args.no_geo:
                writer.writerow(['IP', 'Status', 'Validator Name', 'Latency', 'City', 'Country'])
            else:
                writer.writerow(['IP', 'Status', 'Validator Name', 'Latency'])
            # Write the data rows
            writer.writerows(results)
        print(f"\nProcess complete. Results saved to '{OUTPUT_FILE}'")
    except IOError as e:
        print(f"Error writing to output file '{OUTPUT_FILE}': {e}")

if __name__ == "__main__":
    main()
