class QualysRoute:
    routename: str
    ipv4addr: str
    netmask: str
    ipv4gateway: str

    def __init__(self, routename, ipv4addr, netmask, ipv4gateway):
        self.routename = routename
        self.ipv4addr = ipv4addr
        self.netmask = netmask
        self.ipv4gateway = ipv4gateway

    def createurl(self):
        return "%s|%s|%s|%s" % (self.ipv4addr, self.netmask, self.ipv4gateway, self.routename)
