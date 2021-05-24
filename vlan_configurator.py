import QualysAPI
import QualysVLAN
import QualysRoute

import xml.etree.ElementTree as ET
import csv
import configparser
import argparse
from getpass import getpass
import sys

import QualysVirtualScannerAppliance


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


def get_full_appliances(api: QualysAPI.QualysAPI):
    resp: ET.ElementTree
    full_url = "%s/api/2.0/fo/appliance/?action=list&output_mode=full" % api.server
    ret_val = {}

    resp = api.makeCall(full_url)
    if not response_handler(resp):
        return None
    return resp


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

    # First we need a list of appliances from the subscription to build our internal picture
    print("Getting appliances from subscription and building vlan/route tables")
    # appliances = get_appliances(api)
    full_appliances = get_full_appliances(api)

    # The qvsas dict will contain all of the appliances in the subscription as QualysVirtualScannerAppliance objects
    # as values and the Appliance Name as its key
    qvsas = {}

    if full_appliances is None:
        # If we cannot get a list of appliances, there is nothing more to do so we quit
        print('ERROR: Could not get list of scanner appliances')
        sys.exit(-1)

    # For each appliance in the full_appliances XML output, create a QualysVirtualScannerAppliance object and add it
    # to the qvsas dict
    for xml_appliance in full_appliances.findall('.//APPLIANCE'):
        appliance_id = xml_appliance.find('ID').text
        appliance = QualysVirtualScannerAppliance.QualysVirtualScannerAppliance(id=appliance_id)
        appliance.get_from_xml(xml_appliance)
        qvsas[appliance.name] = appliance

    # If we have specified '-v' or '--vlans'
    if args.vlans:
        # Process the vlan CSV file to build new QualysVLAN objects
        with open(args.vlans, newline='') as csv_file:
            vlan_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            for row in vlan_reader:
                # Get the appliance name from the CSV and with it grab the QualysVirtualScannerAppliance object
                appliance_name = row[0]
                if appliance_name in qvsas.keys():
                    appliance = qvsas[appliance_name]
                else:
                    print("Fatal Error: Appliance %s does not exist in subscription" % appliance_name)
                    sys.exit(1)

                # Create a QualysVLAN object with the vlan configuration contents from the CSV file
                v = QualysVLAN.QualysVLAN(row[1], row[2], row[3], row[4])
                if row[5] == 'add':
                    appliance.add_vlan(v)
                elif row[5] == 'remove':
                    appliance.remove_vlan(v)
                else:
                    print('ERROR: Row %s does not contain an add/remove instruction' % row)
                    sys.exit(1)

    if args.routes:
        # Process the routes CSV file to build the routes dictionary, as described above
        with open(args.routes, newline='') as csv_file:
            route_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            for row in route_reader:
                # Get the appliance name from the CSV
                appliance_name = row[0]
                if appliance_name in qvsas.keys():
                    appliance = qvsas[appliance_name]
                else:
                    print("Fatal Error: Appliance %s does not exist in subscription" % appliance_name)
                    sys.exit(1)

                # Create an array with the static contents from the CSV file
                r = QualysRoute.QualysRoute(row[1], row[2], row[3], row[4])
                if row[5] == 'add':
                    appliance.add_route(r)
                elif row[5] == 'remove':
                    appliance.remove_route(r)
                else:
                    print('ERROR: Row %s does not contain an add/remove instruction' % row)
                    sys.exit(1)

    bRoutes = False
    if args.routes:
        bRoutes = True
    bVLANs = False
    if args.vlans:
        bVLANs = True
    for app_name in qvsas.keys():
        if qvsas[app_name].dirty:
            print('Updating Appliance %s' % app_name)
            qvsas[app_name].build_update_request(routes=bRoutes, vlans=bVLANs)
            full_url = api.server + qvsas[app_name].update_url
            resp = api.makeCall(url=full_url, method='POST')
            if not response_handler(resp):
                print('ERROR: Error updating appliance %s' % app_name)
                sys.exit(1)
            else:
                print('Appliance %s updated' % app_name)
        else:
            print('Skipping Appliance %s : No updates' % app_name)

    sys.exit(0)
