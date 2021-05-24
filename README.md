# vlan_configurator

## Usage
```text
python vlan_configurator.py [-h] [-v VLANS] [-r ROUTES] [-p ENABLE_PROXY] [-u PROXY_URL] [-d] username password api_url

positional arguments:
  username              API Username
  password              API Password (use - to prompt for password
  api_url               The base URL of the API service (e.g. https://qualysapi.qualys.com

optional arguments:
  -h, --help            show this help message and exit
  -v VLANS, --vlans VLANS
                        CSV File containing VLAN configurations
  -r ROUTES, --routes ROUTES
                        CSV File containing Static Route configurations
  -p ENABLE_PROXY, --enable_proxy ENABLE_PROXY
                        Enable HTTPS Proxy (required -u or --proxy_url)
  -u PROXY_URL, --proxy_url PROXY_URL
                        URL of HTTPS Proxy
  -d, --debug           Enable debug output
```

## Description

This script will add and/or remove VLANs and/or Static Routes on Qualys Virtual Scanner Appliances.

The script will first download a list of the existing scanner appliances and their configurations from your subscription.
It will then build an in-memory picture of the scanner appliances to which it will add and/or remove VLAN and/or
Static Route data as specified in the specified CSV files.

Columns in the CSV files must strictly adhere to the formats specified below.


## VLANs CSV Format

The CSV file does not use a header row.  The columns should be populated as follows.  An example file is provided.
```text
Appliance Name, VLAN ID, IPv4 Address, Subnet Mask, VLAN Name, Action
```

The column **Action** must contain 'add' or 'remove' to specify the action to take for the vlan 

## Routes CSV Format

The CSV file does not use a header row.  The columns should be populated as follows.  An example file is provided

```text
Appliance Name, Route Name, IPv4 Address, Subnet Mask, Gateway IPv4 Address, Action
```

The column **Action** must contain 'add' or 'remove' to specify the action to take for the route