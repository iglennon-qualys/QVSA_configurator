from dataclasses import dataclass, field


@dataclass(eq=True, frozen=False, unsafe_hash=True)
class QualysVLAN:
    vlan_id: str = field()
    vlan_name: str = field(hash=False)
    ipv4_address: str = field(hash=False)
    netmask: str = field(hash=False)

    def __init__(self, vlan_id, ipv4_address, netmask, vlan_name):
        self.vlan_id = vlan_id
        self.vlan_name = vlan_name
        self.ipv4_address = ipv4_address
        self.netmask = netmask

    def create_url(self):
        return "%s|%s|%s|%s" % (self.vlan_id, self.ipv4_address, self.netmask, self.vlan_name)

