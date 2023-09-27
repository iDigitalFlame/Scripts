//go:build linux
// +build linux

// prune.go
// Files prune script, deletes files older than the specified amount of days.
//
// Copyright (C) 2021 - 2023 iDigitalFlame
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//

package main

import (
	"errors"
	"flag"
	"math"
	"os"
	"path"
	"strconv"
	"strings"
	"syscall"
	"time"
)

const usage = `Files Pruner

Usage:
  -d <dir>    Directory to scan.
  -f [filter] Filter scan to files that contain this string.
  -t [days]   Day limit for when file is deleted, defaults to 10.

Copyright (C) 2021 - 2023 iDigitalFlame

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
`

func main() {
	var (
		t    int
		d, f string
		args = flag.NewFlagSet("Files Pruner", flag.ExitOnError)
	)

	args.Usage = func() {
		os.Stderr.WriteString(usage)
		os.Exit(2)
	}
	args.StringVar(&d, "d", "", "Directory to scan.")
	args.StringVar(&f, "f", "", "Filter scan to files that contain this string.")
	args.IntVar(&t, "t", 10, "Day limit for when file is deleted, defaults to 10.")

	if err := args.Parse(os.Args[1:]); err != nil {
		os.Stderr.WriteString("Error: " + err.Error() + "\n")
		os.Exit(1)
	}

	if len(d) == 0 {
		os.Stderr.WriteString("Invalid directory path specified!\n")
		os.Exit(1)
	}

	if err := check(d, strings.ToLower(f), uint16(t)); err != nil {
		os.Stderr.WriteString("Error: " + err.Error() + "\n")
		os.Exit(1)
	}
}
func days(f os.FileInfo) uint16 {
	i, ok := f.Sys().(*syscall.Stat_t)
	if !ok {
		return 0
	}
	return uint16(math.Floor(time.Since(time.Unix(int64(i.Mtim.Sec), int64(i.Mtim.Nsec))).Hours()/24) + 1)
}
func check(s, f string, d uint16) error {
	l, err := os.ReadDir(s)
	if err != nil {
		return errors.New(`could not read directory listing for "` + s + `": ` + err.Error())
	}
	var r, p, k int
	for _, b := range l {
		if b.IsDir() || (len(f) > 0 && !strings.Contains(strings.ToLower(b.Name()), f)) {
			continue
		}
		p++
		i, err := b.Info()
		if err != nil {
			return errors.New(`could not read file "` + b.Name() + `": ` + err.Error())
		}
		if o := days(i); o > d {
			if len(f) > 0 {
				os.Stdout.WriteString("Filter [" + f + "] ")
			}
			os.Stdout.WriteString(`File "` + b.Name() + `" is ` + strconv.Itoa(int(o)) + " days old, limit is " + strconv.Itoa(int(d)) + ", removing!\n")
			if err := os.Remove(path.Join(s, b.Name())); err != nil {
				return errors.New(`could not remove file "` + b.Name() + `": ` + err.Error())
			}
			r++
			continue
		}
		k++
	}
	if len(f) > 0 {
		os.Stdout.WriteString("Filter [" + f + "] ")
	}
	os.Stdout.WriteString("Scan complete: " + strconv.Itoa(p) + " Scanned, " + strconv.Itoa(k) + " Kept, " + strconv.Itoa(r) + " Removed.\n")
	return nil
}
