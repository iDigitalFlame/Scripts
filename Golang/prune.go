// prune.go
// Files prune script, deletes files older than the specified amount of days.
//
// Copyright (C) 2020 iDigitalFlame
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
	"flag"
	"fmt"
	"io/ioutil"
	"math"
	"os"
	"path"
	"strings"
	"syscall"
	"time"
)

const usage = `Files Pruner

Usage:
  -d <dir>    Directory to scan.
  -f [filter] Filter scan to files that contain this string.
  -t [days]   Day limit for when file is deleted, defaults to 10.

Copyright (C) 2020 iDigitalFlame

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.`

func main() {
	var (
		t    int
		d, f string
		args = flag.NewFlagSet("Files Pruner", flag.ExitOnError)
	)
	args.StringVar(&d, "d", "", "Directory to scan.")
	args.StringVar(&f, "f", "", "Filter scan to files that contain this string.")
	args.IntVar(&t, "t", 10, "Day limit for when file is deleted, defaults to 10.")
	args.Usage = func() {
		fmt.Fprintln(os.Stderr, usage)
		os.Exit(2)
	}
	if err := args.Parse(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %s\n", err.Error())
		os.Exit(1)
	}

	if len(d) == 0 {
		fmt.Fprintf(os.Stderr, "Directory must be specified!\n")
		os.Exit(1)
	}

	if err := check(d, f, uint16(t)); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %s", err.Error())
		os.Exit(1)
	}
}
func getDays(f os.FileInfo) uint16 {
	i := f.Sys().(*syscall.Stat_t)
	t := time.Unix(int64(i.Ctim.Sec), int64(i.Ctim.Nsec))
	return uint16(math.Floor(time.Since(t).Hours()/24) + 1)
}
func check(s, f string, d uint16) error {
	l, err := ioutil.ReadDir(s)
	if err != nil {
		return fmt.Errorf("could not read directory listing for %q: %s", s, err.Error())
	}
	var r, p, k int
	for _, b := range l {
		if b.IsDir() {
			continue
		}
		if len(f) > 0 && !strings.Contains(b.Name(), f) {
			continue
		}
		p++
		if o := getDays(b); o > d {
			fmt.Printf("File %q is %d days old, limit is %d, removing!\n", b.Name(), o, d)
			if err := os.Remove(path.Join(s, b.Name())); err != nil {
				return fmt.Errorf("could not remove file %q: %s", b.Name(), err.Error())
			}
			r++
		} else {
			k++
		}
	}
	fmt.Printf("Done. %d Scanned, %d Kept, %d Removed.\n", p, k, r)
	return nil
}
