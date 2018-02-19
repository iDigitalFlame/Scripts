import os
import tempfile
import traceback

from django.db import models
from django.utils import timezone
from rule.models import RuleGroup
from picklefield.fields import PickledObjectField


class Os(models.Model):
    class Meta:
        verbose_name = 'Operating System'
        verbose_name_plural = 'Operating Systems'

    os_accuracy = models.SmallIntegerField('Os Accuracy', default=0)
    os_name = models.CharField('Os Name', default='Unknown', max_length=200)
    os_vendor = models.CharField('Os Vendor', default='Unknown', max_length=100)
    os_family = models.CharField('Os Family', default='Unknown', max_length=100)
    os_version = models.CharField('Os Version', default='Unknown', max_length=50)

    def __str__(self):
        return 'OS %s (%s)' % (self.os_name, self.os_version)

    def __eq__(self, other):
        if isinstance(other, Os):
            return other.os_name == self.os_name and other.os_version == self.os_version
        return False

    @staticmethod
    def get_os(accuracy, name, vendor, family, version):
        try:
            sel_os = Os.objects.get(os_accuracy=accuracy, os_name__iexact=name, os_vendor__iexact=vendor,
                                    os_family__iexact=family, os_version__iexact=version)
        except Os.DoesNotExist:
            sel_os = Os()
            sel_os.os_accuracy = accuracy
            sel_os.os_name = name
            sel_os.os_vendor = vendor
            sel_os.os_family = family
            sel_os.os_version = version
            sel_os.save()
        return sel_os


class Tag(models.Model):
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    tag_name = models.CharField('Tag Name', max_length=100)

    def __str__(self):
        return self.tag_name

    def __eq__(self, other):
        return isinstance(other, Tag) and other.tag_name.lower() == self.tag_name.lower()

    @staticmethod
    def get_tag(tag_name):
        try:
            sel_tag = Tag.objects.get(tag_name__iexact=tag_name)
        except Tag.DoesNotExist:
            sel_tag = Tag()
            sel_tag.tag_name = tag_name.lower()
            sel_tag.save()
        return sel_tag


class Host(models.Model):
    class Meta:
        verbose_name = 'Host'
        verbose_name_plural = 'Hosts'

    host_os = models.ManyToManyField('scan.Os')
    host_tag = models.ManyToManyField('scan.Tag')
    host_port = models.ManyToManyField('scan.Port')
    host_address = models.ForeignKey('scan.Address')
    host_script = models.ManyToManyField('scan.Script')
    host_hostname = PickledObjectField('Host Hostnames')
    #host_rscripts = models.ManyToManyField(RunScriptResult)
    host_status = models.BooleanField('Host Status', default=False)
    host_up_time = models.BigIntegerField('Host Uptime', default=0)
    host_distance = models.SmallIntegerField('Host Distance', default=0)
    host_mfg = models.CharField('Host Manufacter', max_length=100, null=True, blank=True)
    host_required_smb_sign = models.BooleanField('Host Requires SMB Signing', default=True)
    host_mac = models.CharField('Host Mac Address', default='00:00:00:00:00:00', max_length=17)

    def __str__(self):
        return '%s (%s) %s [%s]' % (self.host_address.address_ip, self.host_mac, self.__get_os(),
                                    ('online' if self.host_status else 'offline'))

    def __get_os(self):
        if self.host_os.all().count() > 0:
            first_os = self.host_os.all().first()
            return '%s (%s)' % (first_os.os_name, first_os.os_version)
        return 'Unknown'

    def __bool__(self):
        return self.host_status

    def host_is_dc(self):
        for port in self.host_ports.all():
            if (port.port_id == 389 or port.port_id == 636) and port.port_protocol == 'tcp':
                return True
        return False

    def __nonzero__(self):
        return self.__bool__()

    def host_is_mssql(self):
        for script in self.host_scripts.all():
            if script.script_name == 'ms-sql-info':
                return True
        for port in self.host_ports.all():
            if port.port_id == 1433 and port.port_protocol == 'tcp':
                return True
        return False

    def host_send_mail(self):
        for port in self.host_ports.all():
            if port.port_id == 25 and port.port_protocol == 'tcp':
                return True
        return False

    def host_os_supported(self):
        for os in self.host_os.all():
            if not os.os_supported:
                return False
        return True

    def host_open_port(self, port):
        for ports in self.host_ports.all():
            if ports.port_id == port and ports.port_status == 'open':
                return True
        return False


class Scan(models.Model):
    class Meta:
        verbose_name = 'Scan'
        verbose_name_plural = 'Scans'

    scan_host = models.ManyToManyField('scan.Host')
    scan_client = models.ForeignKey('client.Client')
    scan_job = models.ManyToManyField('scan.ScanJob')
    scan_network = PickledObjectField('Scan Networks')
    scan_name = models.CharField('Scan Name', max_length=250)
    scan_start = models.DateTimeField('Scan Start', auto_now_add=True)
    scan_end = models.DateTimeField('Scan End', null=True, blank=True)
    scan_multi = models.BooleanField('Scan Multi Thread', default=True)

    def __str__(self):
        if self.scan_end:
            return 'Scan (%d nets) Finished on %s' % (len(self.scan_network), self.scan_end.strftime('%H:%m %b %d,%Y'))
        return 'Scan (%d nets) Running (%d Jobs running)%s' % (len(self.scan_network),
                                                               self.scan_job.filter(job_status=1).count(),
                                                               'MultiThread' if self.scan_multi else '')

    def is_done(self):
        for job in self.scan_job.all():
            if job.job_status <= 2:
                return False
        return True

    def has_jobs(self):
        return self.scan_job.filter(job_status=0).count() > 0

    def get_jobs(self):
        if self.scan_multi:
            return self.scan_job.filter(job_status=0)
        if self.scan_job.filter(job_status=1).count() == 0:
            return [self.scan_job.filter(job_status=0).first()]
        return None


class Port(models.Model):
    class Meta:
        verbose_name = 'Port'
        verbose_name_plural = 'Ports'

    port_id = models.SmallIntegerField('Port ID')
    port_script = models.ManyToManyField('scan.Script')
    port_service = models.ManyToManyField('scan.Service')
    port_protocol = models.CharField('Port Protocol', max_length=5)
    port_status = models.SmallIntegerField('Port Status', default=0)

    def __str__(self):
        return "%s/%s (%s)" % (self.port_id, self.port_protocol, self.port_status)

    def __eq__(self, other):
        if isinstance(other, Port):
            return other.port_id == self.port_id and other.port_protocol == other.port_protocol
        return False


class Script(models.Model):
    class Meta:
        verbose_name = 'Script'
        verbose_name_plural = 'Scripts'

    script_details = PickledObjectField('Script Details')
    script_name = models.CharField('Script Name', max_length=75)
    script_output = models.CharField('Script Output', max_length=850)

    def __str__(self):
        return 'Script %s' % self.script_name

    def __eq__(self, other):
        if isinstance(other, Script):
            return other.script_name == self.script_name
        return False

    def get_certificate(self):
        if self.script_name == 'ssl-cert' and self.script_output:
            return self.script_output
        return None


class Address(models.Model):
    class Meta:
        verbose_name = 'IP Address'
        verbose_name_plural = 'IP Addresses'

    address_ip = models.CharField('Address IP', max_length=140)
    address_type = models.CharField('Address Type', default='ipv4', max_length=5)

    def is_ipv6(self):
        return self.type == 'ipv6'

    def __str__(self):
        return 'Address %s/%s' % (self.address_ip, self.address_type)

    def __eq__(self, other):
        if isinstance(other, Address):
            return other.address_ip == self.address_ip and other.address_type == self.address_type
        return False

    @staticmethod
    def get_address(address, type):
        try:
            sel_addr = Address.objects.get(address_ip__iexact=address, address_type__iexact=type)
        except Address.DoesNotExist:
            sel_addr = Address()
            sel_addr.address_ip = address
            sel_addr.address_type = type
            sel_addr.save()
        return sel_addr


class Service(models.Model):
    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    service_script = models.ManyToManyField('scan.Script')
    service_cpe = models.CharField('Service CPE', max_length=75)
    service_name = models.CharField('Service Name', max_length=50)
    service_extra_info = models.CharField('Service Extra Info', max_length=850)
    service_product = models.CharField('Service Product', default='Unknown', max_length=100)

    def __str__(self):
        return '%s::%s' % (self.service_name, self.service_product)

    def __eq__(self, other):
        if isinstance(other, Service):
            return other.service_name == self.service_name and other.service_cpe == self.service_cpe
        return False


class ScanJob(models.Model):
    JOB_STATUS = {0:'Waiting',1:'Running',3:'Timed out',4:'Failure',5:' Internal Failure',6:'Finished Scan',
                  7:'Compiling XML',8:'Running Rules',9:'Finished'}
    JOB_COMMAND = 'nmap -sS{is_udp} -vvv{is_ping} -A -p T:21,T:22,T:23,T:25,{dns}T:80,T:110,T:135,T:143,T:389,T:443,' \
                  'T:445,T:514,T:587,T:636,T:1433,T:3306,T:3389,T:5432,T:5900,T:5938,T:8000,T:8008,T:8080{ex_ports}' \
                  ' -oX {file} {ex_args} {net}'

    ##([TUtu]\:\d{1,4})|(?:\d{1,4})|(?:\,)]+
    class Meta:
        verbose_name = 'Scan Job'
        verbose_name_plural = 'Scan Jobs'

    job_pid = models.IntegerField('Job PID', default=0)
    job_command = models.CharField('Job Command', max_length=350)
    job_status = models.IntegerField('Job Status Code', default=0)
    job_timeout = models.IntegerField('Job Timeout', default=1800)
    job_end = models.DateTimeField('Job End', null=True, blank=True)
    job_start = models.DateTimeField('Job Start', null=True, blank=True)
    job_message = models.CharField('Job Output', max_length=750, null=True, blank=True)
    job_file = models.CharField('Job Output File', max_length=100, null=True, blank=True)
    job_message_last = models.CharField('Job Output Last', max_length=250, null=True, blank=True)

    def __str__(self):
        if self.job_end:
            return 'Job Finished (%d seconds) on %s' % ((self.job_end - self.job_start).seconds,
                                                        self.job_end.strftime('%H:%m %b %d,%Y'))
        elif self.job_start:
            return 'Job PID: %d Started %s' % (self.job_pid, self.job_start.strftime('%H:%m %b %d,%Y'))
        else:
            return 'Job Waiting'

    def __len__(self):
        if self.job_end:
            return (self.job_end - self.job_start).seconds
        return (timezone.now() - self.job_start).seconds

    def kill_by(self):
        return self.job_file

    def on_start(self, pid):
        self.job_start = timezone.now()
        self.job_status = 1
        self.job_message_last = 'Job started on %s' % self.job_start.strftime('%H:%m %b %d,%Y')
        self.job_pid = pid
        self.save()

    def on_stop(self, reason):
        print('[*] Set-reason: %d' % reason)
        self.job_status = reason
        if reason == 3:
            self.job_message_last = 'Job Timed out'
            self.job_end = timezone.now()
            self.save()
            return
        if reason == 5:
            self.job_end = timezone.now()
            self.save()
        self.job_status = 7
        self.save()
        scan_output = open(self.job_file, 'r')
        try:
            import netscan.utils.reader
            scan_data = netscan.utils.reader.read_xml(scan_output.read())
        except Exception as ErrMessage:
            print(str(ErrMessage))
            traceback.print_tb(ErrMessage.__traceback__)
            self.job_status = 5
            self.job_end = timezone.now()
            self.job_message_last = 'XML reading failed!'
            self.save()
            return
        scan_output.close()
        os.remove(self.job_file)
        scan_instance = Scan.objects.get(scan_job__exact=self)
        self.job_status = 8
        self.save()
        scan_rules = RuleGroup.objects.all()
        for host in scan_data:
            scan_instance.scan_host.add(host)
            for rule in scan_rules:
                rule.process_rules(host)
        self.job_end = timezone.now()
        self.job_status = 9
        self.job_message_last = ''
        self.save()

    def update(self, message):
        self.job_message_last = message
        if self.job_message_last and '\n' in self.job_message_last:
            self.job_message_last = self.job_message_last.replace('\n', '')
        if self.job_message_last and '\r' in self.job_message_last:
            self.job_message_last = self.job_message_last.replace('\r', '')
        if self.job_message:
            if len(self.job_message) > 500:
                self.job_message = message
            else:
                self.job_message = '%s%s' % (self.job_message, message)
        else:
            self.job_message = message
        self.save()

    def init_job(self, extra_ports, extra_args, network, disable_udp=False, disable_ping=False):
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.job_file = temp_file.name
        temp_file.close()
        self.job_command = ScanJob.JOB_COMMAND.format(is_udp=('' if disable_udp else ' -sU'),
                                                      is_ping=(' -Pn' if disable_ping else ''),
                                                      dns=('' if disable_udp else 'U:53,'),
                                                      ex_ports=(',%s' % ','.join(extra_ports) if extra_ports else ''),
                                                      file=self.job_file, ex_args=(extra_args if extra_args else ''),
                                                      net=network)
        self.save()
