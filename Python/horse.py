#!/usr/bin/python

import csv, sys, random


S_SPEC = {
		'WindowsDC': 0, 
		'Linux': 0,
		'NetDevice': 0,
		'Printer?': 0,
		}	
S_DESC = {
		'80': 'Web Server',
		'443': 'Web Server',
		'445': 'Windows Host/Samba',
		'1434': 'MSSQL',
		'1433': 'MSSQL',
		'137': 'Windows Client',
		'3389': 'Windows TS',
		'143': 'Mail Server',
		'25': 'Mail Server',
		'110': 'Mail Server',
		'587': 'Mail Server',
		'993': 'Mail Server',
		'995': 'Mail Server',
		'22': 'SSH',
		'23': 'Telnet',
		'21': 'FTP',
		'3306': 'MySQL',
		'161': 'SNMP',
		'69': 'TFTP',
		'53': 'DNS',
		'67': 'DHCP',
		'7': 'Pingable',
		}


class HostData:
	def __init__(self):
		self.ip = None
		self.desc = []
		self.ports = []


def _help():
	print("Useage:")
	print("\t ./horse.py <csvinput>")
	print("\nOutput file will be named <csvinput>.output.txt")

def _splash():
	print("""
	
                                                  `T",.`-, 
                                                     '8, :. 
                                              `""`oooob."T,. 
                                            ,-`".)O;8:doob.'-. 
                                     ,..`'.'' -dP()d8O8Yo8:,..`, 
                                   -o8b-     ,..)doOO8:':o; `Y8.`,    
                                  ,..bo.,.....)OOO888o' :oO.  ".  `-.   /---------\ 
                                , "`"d....88OOOOO8O88o  :O8o;.    ;;,b  |  HORSE  |
                               ,dOOOOO"'"'"'"'O88888o:  :O88Oo.;:o888d <    DERP  |
                               ""888Ob...,-- :o88O88o:. :o'""'"'"'Y8OP  |   PY    |
                               d8888.....,.. :o8OO888:: ::              \---------/
                              "" .dOO8bo`'',,;O88O:O8o: ::, 
                                 ,dd8".  ,-)do8O8o:""'; ::: 
                                 ,db(.  T)8P:8o:::::    ::: 
                                 -"",`(;O"KdOo::        ::: 
                                   ,K,'".doo:::'        :o: 
                                    .doo:::""'::  :.    'o: 
        ,..            .;ooooooo..o:""'""     ::;. ::;.  'o. 
   ,, "'    ` ..   .d;o:"'"'                  ::o:;::o::  :; 
   d,         , ..ooo::;                      ::oo:;::o"'.:o 
  ,d'.       :OOOOO8Oo::" '.. .               ::o8Ooo:;  ;o: 
  'P"   ;  ;.OPd8888O8::;. 'oOoo:.;..         ;:O88Ooo:' O"' 
  ,8:   o::oO` 88888OOo:::  o8O8Oo:::;;     ,;:oO88OOo;  ' 
 ,YP  ,::;:O:  888888o::::  :8888Ooo::::::::::oo888888o;. , 
 ',d: :;;O;:   :888888::o;  :8888888Ooooooooooo88888888Oo; , 
 dPY:  :o8O     YO8888O:O:;  O8888888888OOOO888"" Y8o:O88o; , 
,' O:  'ob`      "8888888Oo;;o8888888888888'"'     `8OO:.`OOb . 
'  Y:  ,:o:       `8O88888OOoo"'"'"'""'""'           `OOob`Y8b` 
   ::  ';o:        `8O88o:oOoP                        `8Oo `YO. 
   `:   Oo:         `888O::oP                          88O  :OY 
    :o; 8oP         :888o::P                           do:  8O: 
   ,ooO:8O'       ,d8888o:O'                          dOo   ;:. 
   ;O8odo'        88888O:o'                          do::  oo.: 
  d"`)8O'         "YO88Oo'                          "8O:   o8b' 
 ''-'`"            d:O8oK                          dOOo'  :o": 
                   O:8o:b.                        :88o:   `8:, 
                   `8O:;7b,.                       `"8'     Y: 
                    `YO;`8b' 
                     `Oo; 8:. 
                      `OP"8.` 
                       :  Y8P 
                       `o  `, 
                        Y8bod. 
                        `""''' .py
    		""")
	print("-idf 2015")
	print("horse.py - Nessus CSV output to OS search/detection")
	
def _dohorse(tfile):
	fil = open(tfile,'r')
	csvd = csv.DictReader(fil)
	desct = dict()
	host = dict()
	print("Reading file"),
	for row in csvd:
		if random.randrange(0, 50) == 0:
			print('.'),
		if row["Port"] == '0':
			continue
		if not row["Host"] in host and row["Port"] != 0:
		  	host[row["Host"]] = HostData()
		  	host[row["Host"]].ip = row["Host"]
		if not ("%s:%s" % (row["Port"], row["Protocol"])) in host[row["Host"]].ports and (
			row["Port"] != 0):
			host[row["Host"]].ports.append("%s:%s" % (row["Port"], row["Protocol"]))
			if row["Port"] in S_DESC:
				if not S_DESC[row["Port"]] in host[row["Host"]].desc:
					host[row["Host"]].desc.append(S_DESC[row["Port"]])
					if S_DESC[row["Port"]] in desct:
						desct[S_DESC[row["Port"]]] += 1
					else:
						desct[S_DESC[row["Port"]]] = 1
	wo = open("%s.output.txt" % tfile, 'w+')
	print("\nBuilding report"),
	for k,v in host.iteritems():
		if random.randrange(0, 50) == 0:
			print('.'),
		wo.write("=========================================\n")
		wo.write("%s\n" % v.ip)
		for por in v.ports:
			wo.write("%s > %s\t\topen\n" % (v.ip, por))
		wo.write("OS ident (%s): %s\n" % (v.ip, ', '.join(v.desc)))
		if "445:tcp" in v.ports and "53:udp" in v.ports:
			wo.write("Windows DC!\n")
			S_SPEC['WindowsDC'] += 1
		if "22:tcp" in v.ports and not "445:tcp" in v.ports:
			wo.write("Linux Box!\n");
			S_SPEC['Linux'] += 1
		if "23:tcp" in v.ports and "22:tcp" in v.ports:
			wo.write("Network Device!\n");
			S_SPEC['NetDevice'] += 1
		if "23:tcp" in v.ports and "161:udp" in v.ports and not "22:tcp" in v.ports:
			wo.write("Network Device!\n");
			S_SPEC['NetDevice'] += 1
		if "22:tcp" in v.ports and "161:udp" in v.ports and not "23:tcp" in v.ports:
			wo.write("Network Device!\n");
			S_SPEC['NetDevice'] += 1
		if "21:tcp" in v.ports and "23:tcp" in v.ports and not "445:tcp" in v.ports:
			wo.write("Printer??\n");
			S_SPEC['Printer?'] +=1 
		wo.write("=========================================\n")
	wo.write("============---------------------===========\n\n\n")
	for k,v in desct.iteritems():
		wo.write("%s: %s times\n" % (k, v))
	for k,v in S_SPEC.iteritems():
		wo.write("%s: %s times\n" % (k, v))
	wo.write("\n%s Hosts\n" % len(host))
	wo.close()
	print("\nDone.")
	print("File saved at '%s.output.txt'." % tfile)
	print("Results:")
	for k,v in desct.iteritems():
		print("Detected %s: %s times" % (k, v))
	for k,v in S_SPEC.iteritems():
		print("Detected %s: %s times" % (k, v))


if __name__ == "__main__":
	_splash()
	if len(sys.argv) <= 1:
		_help()
		sys.exit(-1)
	ff = sys.argv[1]
	print("Using file %s" % ff)
	_dohorse(ff)
