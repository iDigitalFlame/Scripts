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
import glob


def _get_files(dir_path, name):
    if not os.path.isdir(dir_path):
        print('[!] "%s" does not exist or is not a directory!' % dir_path)
        sys.exit(1)
    _files_path = os.path.join(os.path.abspath(dir_path), "**")
    _file_no = 0
    for _file in glob.glob(_files_path):
        if os.path.isfile(_file):
            _fn = os.path.basename(_file)
            _fn = _fn[: _fn.find(".")]
            _fnn = _file.replace(_fn, "%s-%d" % (name, _file_no))
            _file_no = _file_no + 1
            print('Moving "%s" to "%s"..' % (_file, _fnn))
            os.rename(_file, _fnn)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        _get_files(sys.argv[1], sys.argv[2])
