#!/usr/bin/python

import sys
import json
import requests

if len(sys.argv) != 3:
	print('%s <category> <address>' % sys.argv[0])
	sys.exit(1)

SKYCTL_KEY = ''
SKYCTL_SERVER = 'http://skyctl.com/post/'

report = {'event': { 'address': str(sys.argv[2]), 'category': str(sys.argv[1])}}
session = requests.session()
session.headers['SKYCTL-AUTH'] = SKYCTL_KEY
result = session.post(SKYCTL_SERVER, data=json.dumps(report))
if result.status_code == 200:
	print('Success!')
	sys.exit(0)
print(result.content)
sys.exit(1)
