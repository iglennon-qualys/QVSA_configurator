import QualysAPI
import QualysVLAN
import QualysRoute

import xml.etree.ElementTree as ET
import csv
import configparser
import sys

def readconfig(file='config.ini'):
    config = configparser.ConfigParser()
    config.read(file)
    return config


def updateappliance(url, applianceid, api: QualysAPI.QualysAPI, virtual=True, debug=False):
    if virtual:
        apiurl = "%s/api/2.0/fo/appliance/?action=update&id=%s&%s" % (api.server, applianceid, url)
    else:
        apiurl = "%s/api/2.0/fo/appliance/physical/?action=update&id=%s&%s" % (api.server, applianceid, url)
    if debug:
        print("API URL : %s" % apiurl)
    api.makeCall(apiurl)


def getappliances(api: QualysAPI.QualysAPI):
    resp: ET.ElementTree
    url = "%s/api/2.0/fo/appliance/?action=list" % api.server
    appliances = {}

    resp = api.makeCall(url)
    for appliance in resp.findall('.//APPLIANCE'):
        appliances[appliance.find('NAME').text] = appliance.find('ID').text

    return appliances


if __name__ == '__main__':
    # Script entry point
    print("Starting application configuration")

    # Define the filename of the configuration file and process that configuration
    configfile = "config.ini"
    config = readconfig(configfile)

    # Specify the configuration section to use
    activeconfig = config['DEFAULT']

    # Get the various configuration items and create variables from them
    vlaninputfile = activeconfig['VLANInputFile']
    routesinputfile = activeconfig['RoutesInputFile']

    apiserver = activeconfig['APIServer']
    apiuser = activeconfig['APIUser']
    apipassword = activeconfig['APIPassword']
    apiproxyaddr = activeconfig['APIProxyAddress']
    if activeconfig['APIEnableProxy'] == "True" or activeconfig['APIEnableProxy'] == "Yes":
        apienableproxy = True
    else:
        apienableproxy = False

    if activeconfig['DebugMode'] == "True" or activeconfig['DebugMode'] == "Yes":
        debugflag = True
    else:
        debugflag = False

    # Create our Qualys API object to handle interactions with the Qualys platform
    api = QualysAPI.QualysAPI(svr=apiserver, usr=apiuser, passwd=apipassword, proxy=apiproxyaddr,
                              enableProxy=apienableproxy, debug=debugflag)

    # We need a list of appliances from the subscription to both sanity check the input and translate
    # appliance names to appliance IDs
    print("Getting appliances from subscription")
    appliances = getappliances(api)

    # vlans is a dictionary type variable which will contain appliances and their proposed vlan configurations
    # { appliance_id: [vlan1, vlan2, ...] }
    # each configuration is a QualysVLAN object
    vlans = {}

    # Process the vlan CSV file to build the vlans dictionary, as described above
    with open(vlaninputfile, newline='') as csvfile:
        vlanreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in vlanreader:
            # Get the appliance name from the CSV
            appname = row[0]

            # Sanity check to make sure the appliance exists in the subscription
            if appname not in appliances.keys():
                print("Fatal Error: Appliance %s does not exist in subscription" % appname)
                sys.exit(1)

            # Create a QualysVLAN object with the vlan configuration contents from the CSV file
            v = QualysVLAN.QualysVLAN(row[1], row[2], row[3], row[4])

            # Check if the appliance already exists in the dictionary
            # If so, append the new one.  If not, create it
            if appname in vlans.keys():
                vlan = vlans[appname]
                vlan.append(v)
                vlans[appname] = vlan
            else:
                vlans[appname] = [v]

    # routes is a dictionary type variable which will contain appliances and their proposed static routes
    # { appliance_id: [route1, route2, ...]
    # each route is itself a QualysRoute object
    routes = {}

    # Process the routes CSV file to build the routes dictionary, as described above
    with open(routesinputfile, newline='') as csvfile:
        routereader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in routereader:
            # Get the appliance name from the CSV
            appname = row[0]

            # Sanity check to make sure the appliance exists in the subscription
            if appname not in appliances.keys():
                print("Fatal Error: Appliance %s does not exist in subscription" % appname)
                sys.exit(1)

            # Create an array with the static contents from the CSV file
            r = QualysRoute.QualysRoute(row[1], row[2], row[3], row[4])

            # Check if the appliance already has a route configuration
            # If so, append the new one.  If not, create it
            if appname in routes.keys():
                route = routes[appname]
                route.append(r)
                routes[appname] = route
            else:
                routes[appname] = [r]

    # We now have both the vlans and the static routes.  Time to process the dictionary objects to create the API call
    # We start with an empty api URL and build it up for each appliance, then make the API call to update that appliance
    print("Starting VLAN Setup")
    apiurl = ""

    for app in vlans.keys():
        appid = appliances[app]
        for vlan in vlans[app]:
            url = vlan.createurl()
            if apiurl != "":
                apiurl = "%s," % apiurl
            apiurl = "%s%s" % (apiurl, url)

        # We need to add to the beginning of this URL the type of update we're making
        apiurl = "set_vlans=%s" % apiurl

        # Now that we have the action part of the URL we can make the API call
        print("VLAN Setup: Updating appliance %s (ID: %s)" % (app, appid))
        updateappliance(apiurl, appid, api, debug=debugflag)

    print("VLAN Setup Complete")
    # Rinse and repeat for the routes
    print("Starting Static Routes Setup")
    apiurl = ""
    for app in routes.keys():
        appid = appliances[app]
        for route in routes[app]:
            url = route.createurl()
            if apiurl != "":
                apiurl = "%s," % apiurl
            apiurl = "%s%s" % (apiurl, url)

        apiurl = "set_routes=%s" % apiurl
        print("Static Routes Setup: Updating appliance %s (ID: %s)" % (app, appid))
        updateappliance(apiurl, appid, api, debug=debugflag)
    print("Static Routes Setup Complete")
