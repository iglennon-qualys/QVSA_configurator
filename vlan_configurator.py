import QualysAPI
import QualysVLAN
import QualysRoute

import xml.etree.ElementTree as ET
import csv
import configparser
import argparse
from getpass import getpass
import sys


def response_handler(response: ET.ElementTree):
    if response.find('RESPONSE/CODE') is None:
        return True

    print('ERROR: API Call FAILED (CODE=%s : TEXT=%s' % (response.find('RESPONSE/CODE').text,
                                                         response.find('RESPONSE/TEXT').text))
    return False


def read_config(file='config.ini'):
    config = configparser.ConfigParser()
    config.read(file)
    return config


def update_appliance(url, appliance_id, api: QualysAPI.QualysAPI, virtual=True, debug=False):
    if virtual:
        api_url = "%s/api/2.0/fo/appliance/?action=update&id=%s&%s" % (api.server, appliance_id, url)
    else:
        api_url = "%s/api/2.0/fo/appliance/physical/?action=update&id=%s&%s" % (api.server, appliance_id, url)
    if debug:
        print("API URL : %s" % api_url)
    api.makeCall(api_url)


def get_appliances(api: QualysAPI.QualysAPI):
    resp: ET.ElementTree
    full_url = "%s/api/2.0/fo/appliance/?action=list" % api.server
    ret_val = {}

    resp = api.makeCall(full_url)
    if not response_handler(resp):
        return None
    for appliance in resp.findall('.//APPLIANCE'):
        ret_val[appliance.find('NAME').text] = appliance.find('ID').text

    return ret_val


if __name__ == '__main__':
    # Script entry point
    parser = argparse.ArgumentParser()

    parser.add_argument('username', help='API Username')
    parser.add_argument('password', help='API Password (use - to prompt for password')
    parser.add_argument('api_url', help='The base URL of the API service (e.g. https://qualysapi.qualys.com')
    parser.add_argument('-v', '--vlans', help='CSV File containing VLAN configurations')
    parser.add_argument('-r', '--routes', help='CSV File containing Static Route configurations')
    parser.add_argument('-p', '--enable_proxy', help='Enable HTTPS Proxy (required -u or --proxy_url)')
    parser.add_argument('-u', '--proxy_url', help='URL of HTTPS Proxy')
    parser.add_argument('-d', '--debug', help='Enable debug output', action='store_true')

    args = parser.parse_args()
    print("Starting application configuration")

    if args.password == '-':
        password = getpass('Enter password: ')
    else:
        password = args.password

    api_url: str = args.api_url
    api_url = api_url.rstrip('/')

    if (not args.vlans) and (not args.routes):
        print('ERROR: Must specify -v|--vlans and/or -r|--routes')
        sys.exit(-1)

    if args.proxy_url:
        proxy_url = args.proxy_url
    else:
        proxy_url = ''

    # Create our Qualys API object to handle interactions with the Qualys platform
    api = QualysAPI.QualysAPI(svr=api_url, usr=args.username, passwd=password, proxy=args.proxy_url,
                              enableProxy=args.enable_proxy, debug=args.debug)

    # We need a list of appliances from the subscription to both sanity check the input and translate
    # appliance names to appliance IDs
    print("Getting appliances from subscription and building vlan/route tables")
    appliances = get_appliances(api)
    if appliances is None:
        print('ERROR: Could not get list of scanner appliances')
        sys.exit(-1)

    if args.vlans:
        # vlans is a dictionary type variable which will contain appliances and their proposed vlan configurations
        # { appliance_id: [vlan1, vlan2, ...] }
        # each configuration is a QualysVLAN object
        vlans = {}

        # Process the vlan CSV file to build the vlans dictionary, as described above
        with open(args.vlans, newline='') as csv_file:
            vlan_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            for row in vlan_reader:
                # Get the appliance name from the CSV
                appliance_name = row[0]

                # Sanity check to make sure the appliance exists in the subscription
                if appliance_name not in appliances.keys():
                    print("Fatal Error: Appliance %s does not exist in subscription" % appliance_name)
                    sys.exit(1)

                # Create a QualysVLAN object with the vlan configuration contents from the CSV file
                v = QualysVLAN.QualysVLAN(row[1], row[2], row[3], row[4])

                # Check if the appliance already exists in the dictionary
                # If so, append the new one.  If not, create it
                if appliance_name in vlans.keys():
                    vlan = vlans[appliance_name]
                    vlan.append(v)
                    vlans[appliance_name] = vlan
                else:
                    vlans[appliance_name] = [v]

                print("Starting VLAN Setup")
                full_url = ''

                for app in vlans.keys():
                    appid = appliances[app]
                    for vlan in vlans[app]:
                        url = vlan.create_url()
                        if full_url != "":
                            full_url = "%s," % full_url
                        full_url = "%s%s" % (full_url, url)

                    # We need to add to the beginning of this URL the type of update we're making
                    full_url = "set_vlans=%s" % full_url

                    # Now that we have the action part of the URL we can make the API call
                    print("VLAN Setup: Updating appliance %s (ID: %s)" % (app, appid))
                    update_appliance(full_url, appid, api, debug=args.debug)

                print("VLAN Setup Complete")

    if args.routes:
        # routes is a dictionary type variable which will contain appliances and their proposed static routes
        # { appliance_id: [route1, route2, ...]
        # each route is itself a QualysRoute object
        routes = {}

        # Process the routes CSV file to build the routes dictionary, as described above
        with open(args.routes, newline='') as csv_file:
            route_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            for row in route_reader:
                # Get the appliance name from the CSV
                appliance_name = row[0]

                # Sanity check to make sure the appliance exists in the subscription
                if appliance_name not in appliances.keys():
                    print("Fatal Error: Appliance %s does not exist in subscription" % appliance_name)
                    sys.exit(1)

                # Create an array with the static contents from the CSV file
                r = QualysRoute.QualysRoute(row[1], row[2], row[3], row[4])

                # Check if the appliance already has a route configuration
                # If so, append the new one.  If not, create it
                if appliance_name in routes.keys():
                    route = routes[appliance_name]
                    route.append(r)
                    routes[appliance_name] = route
                else:
                    routes[appliance_name] = [r]

        print("Starting Static Routes Setup")
        full_url = ""
        for app in routes.keys():
            appid = appliances[app]
            for route in routes[app]:
                url = route.create_url()
                if full_url != "":
                    full_url = "%s," % full_url
                full_url = "%s%s" % (full_url, url)

            full_url = "set_routes=%s" % full_url
            print("Static Routes Setup: Updating appliance %s (ID: %s)" % (app, appid))
            update_appliance(full_url, appid, api, debug=args.debug)
        print("Static Routes Setup Complete")

    sys.exit(0)
