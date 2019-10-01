class QualysVLAN:
    vlanid: str
    vlanname: str
    ipv4addr: str
    netmask: str

    def __init__(self, vlanid, ipv4addr, netmask, vlanname):
        self.vlanid = vlanid
        self.vlanname = vlanname
        self.ipv4addr = ipv4addr
        self.netmask = netmask

    def createurl(self):
        return "%s|%s|%s|%s" % (self.vlanid, self.ipv4addr, self.netmask, self.vlanname)

