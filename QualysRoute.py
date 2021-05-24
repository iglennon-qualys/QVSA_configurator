from dataclasses import dataclass, field


@dataclass()
class QualysRoute:
    route_name: str = field(default=None)
    ipv4_address: str = field(default=None)
    netmask: str = field(default=None)
    ipv4_gateway: str = field(default=None)

    def __init__(self, route_name, ipv4_address, netmask, ipv4_gateway):
        self.route_name = route_name
        self.ipv4_address = ipv4_address
        self.netmask = netmask
        self.ipv4_gateway = ipv4_gateway

    def create_url(self):
        return "%s|%s|%s|%s" % (self.ipv4_address, self.netmask, self.ipv4_gateway, self.route_name)
