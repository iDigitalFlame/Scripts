// +build windows

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
//
// Build Options Example:
//  env GOOS=windows go build -o prune.exe -ldflags '-w -s -H=windowsgui' -trimpath appxprune.go

package main

import (
	"io/ioutil"
	"os"
	"os/exec"
	"strings"
	"syscall"
)

func main() {
	s := "packages.txt"
	if len(os.Args) == 2 {
		s = os.Args[1]
	}

	if i, err := os.Stat(s); err != nil {
		os.Stderr.WriteString(`Could not open package list "` + s + `": ` + err.Error() + "!\n")
		os.Exit(1)
	} else if i.IsDir() {
		os.Stderr.WriteString(`Package list "` + s + `" is not a file!` + "\n")
		os.Exit(1)
	}

	d, err := ioutil.ReadFile(s)
	if err != nil {
		os.Stderr.WriteString(`Could not open package list "` + s + `": ` + err.Error() + `!` + "\n")
		os.Exit(1)
	}

	for _, o := range strings.Split(string(d), "\n") {
		if len(o) == 0 {
			continue
		}
		n := strings.Replace(strings.Replace(o, "\n", "", -1), "\r", "", -1)
		if len(n) == 0 {
			continue
		}
		e := exec.Command("powershell.exe", "-Command", `Get-AppxPackage "`+n+`" | Remove-AppxPackage`)
		e.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
		if err := e.Run(); err != nil {
			os.Stderr.WriteString(`Removing package "` + n + `" raised an error: ` + err.Error() + `!` + "\n")
			continue
		}
	}
}
