import os
import sys
import uuid
import json

from xml.dom.minidom import parseString, NodeList


class Os:
    os_accuracy = 0
    os_name = 'Unknown'
    os_supported = True
    os_vendor = 'Unknown'
    os_family = 'Unknown'
    os_version = 'Unknown'

    def __init__(self, name):
        self.os_name = name

    def __str__(self):
        return '%s (%s)' % (self.os_name, self.os_version)

    def __eq__(self, other):
        if isinstance(other, Os):
            return other.os_name == self.os_name and other.os_version == self.os_version
        return False


class Host:
    host_mfg = ''
    host_addr = ''
    host_up_time = 0
    host_distance = 0
    host_status = 'down'
    host_mac = '00:00:00:00:00:00'
    host_required_smb_sign = False

    def __init__(self, ip):
        self.host_os = []
        self.host_addr = ip
        self.host_ports = []
        self.host_scripts = []
        self.host_hostname = []

    def print(self):
        buffer = [Host.fill_line_with(None, '=', 300), '\n']
        buffer.append('%s =' % Host.fill_line_with('= Host: %s/%s\tOS: %s' % (self.host_addr.address_ip,
                                                                                   self.host_addr.address_type,
                                                                                   self.__get_os()), ' ', 298))
        buffer.append('\n')
        buffer.append('%s = ' % Host.fill_line_with('= Port\tStatus == Port\tStatus == Port\tStatus == Port\tStatus',
                                                    '', 298))
        port_count = 0
        port_buffer = []
        """for port in self.host_ports:
            if port_count >= 3:
                port_count = 0
                buffer.append('%s =\n' % Host.fill_line_with('= %s' % ' == '.join(port_buffer), ' ', 298))
                port_buffer = []
            else:
                port_count += 1
            port_buffer.append('%s/%s\t%a' % (port.port_id, port.port_protocol, port.port_status))"""
        return ''.join(buffer)

    def __str__(self):
        return '%s (%s) %s [%s]' % (self.host_addr.address_ip, self.host_mac, self.__get_os(), self.host_status)

    def __get_os(self):
        if len(self.host_os) > 0:
            return '%s (%s)' % (self.host_os[0].os_name, self.host_os[0].os_version)
        return 'Unknown'

    def __bool__(self):
        return self.status != 'down'

    def host_is_dc(self):
        for port in self.host_ports:
            if (port.port_id == 389 or port.port_id == 636) and port.port_protocol == 'tcp':
                return True
        return False

    def __nonzero__(self):
        return self.__bool__()

    def host_is_mssql(self):
        for script in self.host_scripts:
            if script.script_name == 'ms-sql-info':
                return True
        for port in self.host_ports:
            if port.port_id == 1433 and port.port_protocol == 'tcp':
                return True
        return False

    def host_send_mail(self):
        for port in self.host_ports:
            if port.port_id == 25 and port.port_protocol == 'tcp':
                return True
        return False

    def host_os_supported(self):
        for os in self.host_os:
            if not os.os_supported:
                return False
        return True

    def host_open_port(self, port):
        for ports in self.host_ports:
            if port.port_id == port and port.port_status == 'open':
                return True
        return False

    @staticmethod
    def fill_line_with(line, char, max):
        if not line:
            return ''.join([char for x in range(0, max)])
        if len(line) < max:
            return '%s%s' % (line, ''.join([char for x in range(len(line), max)]))
        return line


class Port:
    port_id = 0
    port_protocol = 'tcp'
    port_status = 'closed'

    def __init__(self, id, status, protocol):
        self.port_id = id
        self.port_scripts = []
        self.port_services = []
        self.port_status = status
        self.port_protocol = protocol

    def __str__(self):
        return "%s/%s (%s)" % (self.port_id, self.port_protocol, self.port_status)

    def __eq__(self, other):
        if isinstance(other, Port):
            return other.port_id == self.port_id and other.port_protocol == other.port_protocol
        return False


class Script:
    script_name = ''
    script_output = ''

    def __init__(self, name):
        self.script_name = name
        self.script_details = dict()

    def __str__(self):
        return self.script_name

    def __eq__(self, other):
        if isinstance(other, Script):
            return other.script_name == self.script_name
        return False

    def get_certificate(self):
        if self.script_name == 'ssl-cert' and self.script_output:
            return self.script_output
        return None


class Address:
    address_ip = ''
    address_type = 'ipv4'

    def __init__(self, ip, type):
        self.address_ip = ip
        self.address_type = type

    def is_ipv6(self):
        return self.type == 'ipv6'

    def __str__(self):
        return '%s/%s' % (self.address_ip, self.address_type)

    def __eq__(self, other):
        if isinstance(other, Address):
            return other.address_ip == self.address_ip and other.address_type == self.address_type
        return False


class Service:
    service_name = ''
    service_cpe = 'Unknown'
    service_extra_info = ''
    service_product = 'Unknown'

    def __init__(self, name):
        self.service_name = name
        self.service_scripts = []

    def __str__(self):
        return '%s::%s' % (self.service_name, self.service_product)

    def __eq__(self, other):
        if isinstance(other, Service):
            return other.service_name == self.service_name and other.service_cpe == self.service_cpe
        return False


class NMapScan:

    def inp(self, xmlfile):
        fil = open(xmlfile)
        fil_d = fil.read()
        fil.close()
        self.__input(fil_d)

    def __log(self, level, data):
        if level >= 1:
            pass #print('[*] %s' % data)

    def __input(self, xml):
        xml_data = parseString(xml)

        start = int(NMapScan.getSingleXML(xml_data, 'nmaprun', 'start'))

        xml_hosts = xml_data.getElementsByTagName('host')
        self.__log(0, 'Enumerating %d hosts' % len(xml_hosts))
        if xml_hosts:
            for hostd in xml_hosts:
                inst_data = Host(Address(NMapScan.getSingleXML(hostd, 'address', 'addr'),
                                         NMapScan.getSingleXML(hostd, 'address', 'addrtype')))
                inst_data.host_status = NMapScan.getSingleXML(hostd, 'status', 'state')
                self.__log(0, 'Added host %s/%s' % (inst_data.host_addr.address_ip, inst_data.host_addr.address_type))
                if inst_data.host_status == 'up':
                    self.__log(0, 'Host %s/%s is up, adding scan data' % (inst_data.host_addr.address_ip,
                                                                          inst_data.host_addr.address_type))
                    self.__scanhost(hostd, inst_data, xml_data)
                #print(inst_data)

    def __scanhost(self, hostd, instance, xml_data):
        host_hnames = hostd.getElementsByTagName('hostname')
        if host_hnames:
            for host_name in host_hnames:
                instance.host_hostname.append(host_name.getAttribute('name'))
                self.__log(0, 'Found hostname: %s' % host_name.getAttribute('name'))
        host_ports = hostd.getElementsByTagName('port')
        self.__log(0, 'Found %d ports scanned' % len(host_ports))
        for host_port in host_ports:
            port_ins = Port(int(host_port.getAttribute('portid')),
                            NMapScan.getSingleXML(host_port, 'state', 'state'), host_port.getAttribute('protocol'))
            if (port_ins.port_id == 80 or port_ins.port_id == 443 or port_ins.port_id == 8000 or port_ins.port_id == 8080) and port_ins.port_status == 'open':
            	print('//%s:%d' % (instance.host_addr.address_ip, port_ins.port_id))
            self.__log(0, 'Found port %d/%s, is %s' % (port_ins.port_id, port_ins.port_protocol, port_ins.port_status))
            port_svc = host_port.getElementsByTagName('service')
            self.__log(0, 'Port %d/%s has %d services' % (port_ins.port_id, port_ins.port_protocol, len(port_svc)))
            for srvc in port_svc:
                srv_ins = Service(srvc.getAttribute('name'))
                srv_ins.service_product = srvc.getAttribute('product')
                srvc_cpe = srvc.getElementsByTagName('cpe')
                if srvc_cpe:
                    srv_ins.service_cpe = srvc_cpe[0].firstChild.nodeValue
                srv_ins.service_extra_info = srvc.getAttribute('extrainfo')
                self.__log(0, 'Added service %s/%s to port %d/%s' % (srv_ins.service_product, srv_ins.service_name,
                                                                     port_ins.port_id, port_ins.port_protocol))
                port_ins.port_services.append(srv_ins)
            port_script = host_port.getElementsByTagName('script')
            self.__log(0, 'Port %d/%s has %d scripts' % (port_ins.port_id, port_ins.port_protocol, len(port_script)))
            for script in port_script:
                script_ins = Script(script.getAttribute('id'))
                script_ins.script_output = script.getAttribute('output')
                for c_node in script.childNodes:
                    self.__scan_nodes(c_node, script_ins.script_details, 'default')
                port_ins.port_scripts.append(script_ins)
                self.__log(0, 'Added script %s to port %d/%s' % (script_ins.script_name, port_ins.port_id,
                                                                 port_ins.port_protocol))
            instance.host_ports.append(port_ins)
        host_os = hostd.getElementsByTagName('os')
        self.__log(0, 'Adding host OS info')
        for host_os_sus in host_os:
            host_os_match = host_os_sus.getElementsByTagName('osmatch')
            for host_match in host_os_match:
                host_match_ins = Os(host_match.getAttribute('name'))
                host_match_ins.os_accuracy = host_match.getAttribute('accuracy')
                host_match_class = host_match.getElementsByTagName('osmatch')
                if host_match_class:
                    host_match_ins.os_vendor = host_match_class[0].getAttribute('vendor')
                    host_match_ins.os_family = host_match_class[0].getAttribute('osfamily')
                    host_match_ins.os_version = host_match_class[0].getAttribute('osgen')
                    if host_match_ins.os_version == 'Xp' or host_match_ins.os_version == '2003':
                        host_match_ins.os_supported = False
                self.__log(0, 'Added OS %s (%s%%) fam %s, gen %s, ven %s' % (host_match_ins.os_name,
                                                                             host_match_ins.os_accuracy,
                                                                             host_match_ins.os_family,
                                                                             host_match_ins.os_version,
                                                                             host_match_ins.os_vendor))
                instance.host_os.append(host_match_ins)
        host_up = hostd.getElementsByTagName('uptime')
        if host_up:
            instance.host_up_time = int(host_up[0].getAttribute('seconds'))
            self.__log(0, 'Added uptime for %d seconds' % instance.host_up_time)
        host_scripts = hostd.getElementsByTagName('hostscript')
        self.__log(0, 'Found %d host scripts' % len(host_scripts))
        if host_scripts:
            for script in host_scripts[0].getElementsByTagName('script'):
                script_ins = Script(script.getAttribute('id'))
                for c_node in script.childNodes:
                    self.__scan_nodes(c_node, script_ins.script_details, 'default')
                if script_ins.script_name == 'nbstat':
                    instance.host_mfg = script_ins.script_details['mac']['manuf']
                    instance.host_mac = script_ins.script_details['mac']['address']
                if script_ins.script_name == 'smb-security-mode':
                    if script_ins.script_details['message_signing'] == 'disabled':
                        instance.host_required_smb_sign = False
                self.__log(0, 'Adding host script %s' % script_ins.script_name)
                instance.host_scripts.append(script_ins)
        host_dist = hostd.getElementsByTagName('distance')
        if host_dist:
            instance.host_distance = int(host_dist[0].getAttribute('value'))

    def __scan_nodes(self, c_node, c_dict, c_name):
        self.__log(0, 'Scanning nodes, on name %s' % c_name)
        if c_node.nodeType == 3 and c_name:
            if c_node.nodeValue != '\n':
                c_dict[c_name] = c_node.nodeValue
                self.__log(0, 'Adding text node on name %s' % c_name)
            return
        if c_node.nodeType == 1:
            ch_name = c_node.getAttribute('key')
            #if ch_name == '' or not ch_name:
            #    ch_name = uuid.uuid4().hex
            ch_dict = c_dict
            if c_node.tagName == 'table':
                ch_dict = dict()
                c_dict[ch_name] = ch_dict
            self.__log(0, 'Scanning nodes, on name %s to name %s' % (c_name, ch_name))
            for ch_node in c_node.childNodes:
                self.__scan_nodes(ch_node, ch_dict, ch_name)

    @staticmethod
    def getSingleXML(xml_node, string, attrib=None):
        if xml_node:
            xml_st = xml_node.getElementsByTagName(string)
            if isinstance(xml_st, NodeList):
                if attrib:
                    return xml_st[0].getAttribute(attrib)
                return xml_st[0]
            return xml_st
        return None


if __name__ == '__main__':
    a = NMapScan()
    for z in os.listdir('.'):
    	if '.xml' in z:
	    	a.inp(z)
