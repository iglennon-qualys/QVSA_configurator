# vlan_configurator

## Usage
```text
vlan_configurator.py [-h] [-v VLANS] [-r ROUTES] [-p ENABLE_PROXY] [-u PROXY_URL] [-d] username password api_url

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


## VLANs CSV Configuration

The CSV file does not use a header row.  The columns should be populated as follows.  An example file is provided.
```text
Appliance Name, VLAN ID, IPv4 Address, Subnet Mask, VLAN Name
```

## Routes CSV configuration

The CSV file does not use a header row.  The columns should be populated as follows.  An example file is provided

```text
Appliance Name, Route Name, IPv4 Address, Subnet Mask, Gateway IPv4 Address
```