//go:build linux
// +build linux

// ghelper.go
// Group Helper: Escape and quote/tick mark friendly 'sg' replacement.
//
// Copyright (C) 2021 - 2022 iDigitalFlame
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
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"syscall"
)

// default groups in the 'Spaceport' project.
var groups = map[string]int{
	"db":    9905,
	"web":   9901,
	"ssh":   9902,
	"ftp":   9904,
	"ctl":   9906,
	"all":   9907,
	"mail":  9003,
	"icmp":  9900,
	"voice": 9908,
}

func main() {
	if !filepath.IsAbs(os.Args[0]) {
		os.Stderr.WriteString("You must use the fullpath of this binary!\n")
		os.Exit(1)
	}

	switch {
	case os.Getuid() == 0:
		os.Stderr.WriteString("Refusing to run as root!\n")
		os.Exit(1)
	case os.Geteuid() != 0:
		os.Stderr.WriteString("Binary is lacking the SUID permissions bit!\n")
		os.Exit(1)
	case len(os.Args) <= 2:
		os.Stderr.WriteString(os.Args[0] + " <group> <command...>\n")
		os.Exit(2)
	}

	g, ok := groups[os.Args[1]]
	if !ok {
		os.Stderr.WriteString(`Invalid Group "` + os.Args[1] + `"!` + "\n")
		os.Exit(1)
	}

	if err := syscall.Setgid(g); err != nil {
		os.Stderr.WriteString(`Could not set Group "` + strconv.Itoa(g) + `": ` + err.Error() + "!\n")
		os.Exit(1)
	}

	r := os.Getuid()
	if err := syscall.Setuid(r); err != nil {
		os.Stderr.WriteString(`Could not set User "` + strconv.Itoa(r) + `": ` + err.Error() + "!\n")
		os.Exit(1)
	}
	if err := syscall.Seteuid(r); err != nil {
		os.Stderr.WriteString(`Could not set Effective User "` + strconv.Itoa(r) + `": ` + err.Error() + "!\n")
		os.Exit(1)
	}

	e := exec.Command(os.Args[2])
	if len(os.Args) > 2 {
		e.Args = append(e.Args, os.Args[3:]...)
	}
	e.Stdin = os.Stdin
	e.Stdout = os.Stdout
	e.Stderr = os.Stderr

	err := e.Run()
	if err == nil {
		os.Exit(0)
	}
	if x, ok := err.(*exec.ExitError); ok {
		os.Exit(x.ExitCode())
	}

	os.Stderr.WriteString(err.Error() + "!\n")
	os.Exit(1)
}
