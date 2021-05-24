from dataclasses import dataclass, field
import QualysRoute
import QualysVLAN
from xml.etree import ElementTree as ET


@dataclass(eq=True, frozen=False, unsafe_hash=True)
class QualysVirtualScannerAppliance:
    id: str = field()
    name: str = field(default=None, hash=False)
    routes: set = field(default_factory=set, hash=False)
    vlans: set = field(default_factory=set, hash=False)
    update_url: str = field(default=None, hash=False)
    dirty: bool = field(default=False, hash=False)

    def add_route(self, route: QualysRoute.QualysRoute):
        if not self.routes.__contains__(route):
            self.routes.add(route)
            self.dirty = True

    def remove_route(self, route: QualysRoute.QualysRoute):
        if self.routes.__contains__(route):
            self.routes.remove(route)
            self.dirty = True

    def add_vlan(self, vlan: QualysVLAN.QualysVLAN):
        if not self.vlans.__contains__(vlan):
            self.vlans.add(vlan)
            self.dirty = True

    def remove_vlan(self, vlan: QualysVLAN.QualysVLAN):
        if self.vlans.__contains__(vlan):
            self.vlans.remove(vlan)
            self.dirty = True

    def get_from_xml(self, appliance_xml: ET.Element):
        self.id = appliance_xml.find('ID').text
        self.name = appliance_xml.find('NAME').text
        if appliance_xml.find('VLANS/SETTING').text == 'Enabled':
            # Get the VLANs here
            vlan: QualysVLAN.QualysVLAN
            for xml_vlan in appliance_xml.find('VLANS').findall('VLAN'):
                vlan_id = xml_vlan.find('ID').text
                vlan_name = xml_vlan.find('NAME').text
                vlan_addr = xml_vlan.find('IP_ADDRESS').text
                vlan_netmask = xml_vlan.find('NETMASK').text
                vlan = QualysVLAN.QualysVLAN(vlan_id=vlan_id, vlan_name=vlan_name, ipv4_address=vlan_addr,
                                             netmask=vlan_netmask)
                self.vlans.add(vlan)

        if appliance_xml.find('STATIC_ROUTES/ROUTE') is not None:
            # Get static routes
            route: QualysRoute.QualysRoute
            for xml_route in appliance_xml.find('STATIC_ROUTES').findall('ROUTE'):
                route_name = xml_route.find('NAME').text
                route_addr = xml_route.find('IP_ADDRESS').text
                route_netmask = xml_route.find('NETMASK').text
                route_gateway = xml_route.find('GATEWAY').text
                route = QualysRoute.QualysRoute(route_name=route_name, ipv4_address=route_addr, netmask=route_netmask,
                                                ipv4_gateway=route_gateway)
                self.routes.add(route)

    def build_update_request(self, routes: bool = True, vlans: bool = True):
        url = '/api/2.0/fo/appliance/?action=update&id=%s' % self.id
        if routes:
            url = url + '&set_routes='
            if len(self.routes) > 0:
                route: QualysRoute.QualysRoute
                for index, route in enumerate(self.routes):
                    if index == 0:
                        url = url + "%s|%s|%s|%s" % (route.ipv4_address, route.netmask, route.ipv4_gateway,
                                                     route.route_name)
                    else:
                        url = url + ",%s|%s|%s|%s" % (route.ipv4_address, route.netmask, route.ipv4_gateway,
                                                      route.route_name)
        if vlans:
            url = url + '&set_vlans='
            if len(self.vlans) > 0:
                vlan: QualysVLAN.QualysVLAN

                for index, vlan in enumerate(self.vlans):
                    if index == 0:
                        url = url + "%s|%s|%s|%s" % (vlan.vlan_id, vlan.ipv4_address, vlan.netmask, vlan.vlan_name)
                    else:
                        url = url + ",%s|%s|%s|%s" % (vlan.vlan_id, vlan.ipv4_address, vlan.netmask, vlan.vlan_name)

        self.update_url = url
