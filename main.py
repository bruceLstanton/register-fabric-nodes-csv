# CREDIT
# The original code is licensed under the BSD 3-Clause License.
# The original code is copyright (c) 2022, Osama Abbas
# The original code is available here:
# https://github.com/Tes3awy/register-fabric-nodes

# -*- coding: utf-8 -*-
from getpass import getpass
from warnings import filterwarnings

from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    InvalidURL,
    Timeout,
)

import auth
import nodes

filterwarnings(action="ignore", message=r"Unverified\sHTTPS\srequest\s.*")

NODES_CSV_FILE = nodes.NODES_CSV_FILE


def get_input(prompt: str, default: str = None):
    """Helper function to get user input with an optional default value"""
    value = input(prompt).strip()
    return default if value == "" else value


def main():
    # Read CSV and get sites
    try:
        sites = nodes.get_sites(NODES_CSV_FILE)
    except FileNotFoundError as e:
        raise SystemExit(f"{NODES_CSV_FILE} is not found! Check the file exists.") from e

    if not sites:
        raise SystemExit(
            f"No sites found in {NODES_CSV_FILE}. Ensure the CSV has Site and APIC IP columns."
        )

    # Present numbered list of sites
    print("\nSelect a site:")
    for i, (site, apic_ip) in enumerate(sites, start=1):
        print(f"  {i}. {site} ({apic_ip})")

    while True:
        choice = get_input("\nEnter site number: ")
        try:
            idx = int(choice)
            if 1 <= idx <= len(sites):
                selected_site, apic = sites[idx - 1]
                break
        except ValueError:
            pass
        print("Invalid selection. Please enter a valid number.")

    # Credentials
    usr = get_input("Username: ", default="admin")
    pwd = getpass(prompt="Password: ") or "!v3G@!4@Y"

    ## Processing
    # Accessing APIC
    print(f"\nAccessing {apic}...", end="\r")
    try:
        r = auth.login(apic=apic, usr=usr, pwd=pwd)
    except (InvalidURL, HTTPError, ConnectionError, Timeout) as e:
        raise SystemExit(e) from e
    else:
        print(f"Accessed {apic} successfully")

        headers = {
            "cookie": r.headers.get("set-cookie"),
            "apic-challenge": r.json()
            .get("imdata")[0]
            .get("aaaLogin")
            .get("attributes")
            .get("urlToken"),
        }

        try:
            # Read nodes from CSV file for selected site
            fab_nodes = nodes.read(NODES_CSV_FILE, site=selected_site, apic_ip=apic)
        except FileNotFoundError as e:
            raise SystemExit(f"{NODES_CSV_FILE} is not found! Check typos") from e
        else:
            # Register nodes to ACI Fabric
            i, eet = 0, 0.0
            for node in fab_nodes:
                print(f"Registering {node.get('name')}...", end="\r")
                try:
                    reg = nodes.register(apic=apic, headers=headers, node=node)
                except (HTTPError, ConnectTimeout) as e:
                    print(
                        f"{node.get('name')}: {e.response.json().get('imdata')[0].get('error').get('attributes').get('text')}"
                    )
                else:
                    eet += reg.elapsed.total_seconds()
                    i += 1
                    print(
                        f"Registered {node.get('name')} with ID {node.get('node_id')} and S/N {node.get('serial')}"
                    )

            # Output
            print(
                f"Registered {i}/{len(fab_nodes)} nodes in {eet:.2f} seconds",
                end="\n\n",
            )

        out_res = auth.logout(apic=apic, headers=headers, usr=usr)
        if out_res.ok and "deleted" in out_res.headers.get("set-cookie"):
            print(f"Closed {apic} session")
        else:
            print("Registered nodes but might have not been logged out! Clear the session from the UI")



if __name__ == "__main__":
    main()
