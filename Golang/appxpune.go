// appxprune.go
// Removes Windows 10 Appx Packages
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
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"strings"
	"syscall"
)

const (
	list    = `packages.txt`
	command = `Get-AppxPackage "%s" | Remove-AppxPackage`
)

func main() {
	s := list
	if len(os.Args) == 2 {
		s = os.Args[1]
	}

	i, err := os.Stat(s)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Could not open package list %q: %s\n", s, err.Error())
		os.Exit(1)
	}
	if i.IsDir() {
		fmt.Fprintf(os.Stderr, "Package list %q is not a file!\n", s)
		os.Exit(1)
	}

	d, err := ioutil.ReadFile(s)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Could not open package list %q: %s\n", s, err.Error())
		os.Exit(1)
	}

	for _, o := range strings.Split(string(d), "\n") {
		if len(o) == 0 {
			continue
		}
		var (
			n = strings.Replace(strings.Replace(o, "\n", "", -1), "\r", "", -1)
			e = exec.Command("powershell.exe", "-Command", fmt.Sprintf(command, n))
		)
		e.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
		if err := e.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "Removing package %q raised the error: %s\n", n, err.Error())
			continue
		}
		fmt.Printf("Removed package %q.\n", n)
	}
}
