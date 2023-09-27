#!/usr/bin/dash
# Relinks files to their respective directories.
#
# Copyright (C) 2016 - 2023 iDigitalFlame
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

DEBUG=0

if [ $# -ne 2 ]; then
    echo "relink <config source> <config target> [debug]"
    exit 1
fi

if [ $# -eq 3 ]; then
    DEBUG=1
fi

list() {
    if [ $# -ne 2 ]; then
        return 1
    fi
    files_src=${2%/}
    files_target=${1%/}
    find "$files_target" -type f -print | while IFS= read -r file; do
        file_name=$(printf "%s" "$file" | awk "{gsub(\"${files_target}\", \"\"); print \$1}")
        if ! echo "$file_name" | grep -qE '.(nlk|nolink)$|^/.git(|ignore$|config$)|^/(LICENSE|license|.vscode)$|^/[a-zA-Z0-9_.-]+.(md|vscode|MD|code-workspace)$'; then
            check "${files_src}${file_name}" "${files_target}${file_name}"
        fi
    done
    return 0
}

link() {
    if [ $# -ne 2 ]; then
        return 1
    fi
    rm -f "$1" 2> /dev/null
    file_dir=$(dirname "$1")
    if ! [ -d "$file_dir" ]; then
        printf "Making \"%s\"..\n" "$file_dir"
        if ! mkdir -p "$file_dir" 2> /dev/null; then
            panic "Cannot create directory \"${file_dir}\"!"
        fi
        if [ "$USER" = "root" ]; then
            chmod 0555 "$file_dir"
        else
            chmod 0755 "$file_dir"
        fi
    fi
    if ! ln -s "$2" "$1"; then
        panic "Could not link \"${1}\" to \"${2}\"!"
    fi
    printf "[+] Relinked \"%s\" to \"%s\".\n" "$1" "$2"
    return 0
}

check() {
    if [ $# -ne 2 ]; then
        return 1
    fi
    if [ $DEBUG -eq 1 ]; then
        printf "[+] Checking \"%s\"..\n" "$1"
    fi
    if ! [ -L "$1" ]; then
        printf "File \"%s\" is invalid, updating!\n" "$1"
        link "$1" "$2"
    else
        if ! [ "$(readlink "$1")" = "$2" ]; then
            printf "File \"%s\" is invalid, updating!\n" "$1"
            link "$1" "$2"
        else
            if [ $DEBUG -eq 1 ]; then
                printf "File \"%s\" is valid!\n" "$1"
            fi
        fi
    fi
    return 0
}

panic() {
    echo "[!] $1"
    exit 1
}

if ! [ -d "$1" ]; then
    panic "Config source directory \"${1}\" does not exist!"
fi
if ! [ -d "$2" ]; then
    if ! mkdir -p "$2" 2> /dev/null; then
        panic "Could not create target directory \"${2}\"!"
    fi
fi

list "$1" "$2"
exit 0
