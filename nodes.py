# CREDIT
# The original code is licensed under the BSD 3-Clause License.
# The original code is copyright (c) 2022, Osama Abbas
# The original code is available here:
# https://github.com/Tes3awy/register-fabric-nodes

# -*- coding: utf-8 -*-
import csv
from typing import Dict, List

import requests


def read(__nodes_file: str, /) -> List[Dict[str, str]]:
    """
    Read Fabric nodes from CSV file

    Parameters
    ----------
    __nodes_file : str
        Fabric nodes CSV file name. e.g. "Fabric-Nodes.csv"

    Returns
    -------
    List[Dict[str, str]]
        List of dictionaries of Fabric nodes
    """
    # Column mapping from CSV headers to internal keys
    column_mapping = {
        "Node Type": "node_type",
        "Node Role": "role",
        "POD ID": "pod_id",
        "Serial Number": "serial",
        "Node Name": "name",
        "Node ID": "node_id",
    }
    
    nodes = []
    seen_serials = set()
    
    with open(__nodes_file, mode='r', encoding='utf-8', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            # Skip duplicates based on Serial Number
            serial = row.get("Serial Number", "").strip()
            if serial in seen_serials:
                continue
            seen_serials.add(serial)
            
            # Rename columns and handle empty values
            node = {}
            for csv_col, internal_key in column_mapping.items():
                value = row.get(csv_col, "")
                # Convert None or empty strings to empty string
                node[internal_key] = "" if value is None or str(value).strip() == "" else str(value).strip()
            
            nodes.append(node)
    
    return nodes


def register(
    apic: str, headers: Dict[str, str], node: Dict[str, str]
) -> requests.Response:
    """
    Register Fabric node to ACI Fabric

    Parameters
    ----------
    apic : str
        APIC IP Address. e.g. "sandboxapicdc.cisco.com"

    headers : Dict[str, str]
        Headers from APIC login

    node : Dict[str, str]
        Fabric node

    Returns
    -------
    requests.Response
        Response from APIC register node API
    """
    url = f"https://{apic}/api/mo/uni/controller/nodeidentpol.json"
    payload = {
        "fabricNodeIdentP": {
            "attributes": {
                "nodeId": str(node.get("node_id")),
                "nodeType": node.get("node_type"),
                "role": node.get("role"),
                "name": node.get("name").strip(),
                "serial": node.get("serial").strip(),
            }
        },
        "fabricNodePEp": {
            "attributes": {
                "tDn": f"topology/pod-{node.get('pod_id', 1)}/{node.get('name')}",
            }
        },
    }
    r = requests.post(url=url, headers=headers, json=payload, verify=False)
    r.raise_for_status()
    return r
