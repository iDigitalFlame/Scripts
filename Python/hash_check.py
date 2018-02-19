#!/usr/bin/python

import os
import sys
import glob
import hashlib

def _get_files(dir_path):
    if not os.path.isdir(dir_path):
        print('[!] "%s" does not exist or is not a directory!' % dir_path)
        sys.exit(1)
    _files_path = os.path.join(os.path.abspath(dir_path), '**')
    _files = dict()
    for _file in glob.glob(_files_path):
        if os.path.isfile(_file):
            _file_hash = hashlib.md5(open(_file, 'rb').read()).hexdigest()
            if _file_hash not in _files:
                _files[_file_hash] = list()
            _files[_file_hash].append(_file)
    _matches = dict()
    for _hash, _list in _files.items():
        if len(_list) > 1:
            _matches[_hash] = _list
    return _matches
    

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        for h,f in _get_files(sys.argv[1]).items():
            print('# Hash: %s' % h)
            for x in range(0, len(f)):
                if x == 0:
                  print('# ', end='')
                print('rm "%s"' % f[x])
