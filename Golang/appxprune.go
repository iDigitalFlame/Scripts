//go:build windows
// +build windows

// appxprune.go
// Removes Windows 10 Appx Packages
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
//
// Build Options Example:
//  env GOOS=windows go build -o appxprune.exe -ldflags '-w -s -H=windowsgui' -trimpath appxprune.go

package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
)

func main() {
	s := "packages.txt"
	if d, _ := os.Getwd(); len(d) > 0 {
		s = filepath.Join(d, "packages.txt")
	}

	switch {
	case len(os.Args) == 1:
	case len(os.Args) == 2:
		s = os.Args[1]
	default:
		os.Stderr.WriteString(os.Args[0] + " <packages_list>")
		os.Exit(2)
	}

	p, err := exec.LookPath("powershell.exe")
	if err != nil {
		os.Stderr.WriteString(`Could not locate "powershell.exe": ` + err.Error() + "!\n")
		os.Exit(3)
	}

	d, err := os.ReadFile(s)
	if err != nil {
		os.Stderr.WriteString(`Could not open package list "` + s + `": ` + err.Error() + "!\n")
		os.Exit(1)
	}

	for _, o := range strings.Split(string(d), "\n") {
		if len(o) == 0 {
			continue
		}
		n := stripInvalids(strings.Replace(strings.Replace(o, "\n", "", -1), "\r", "", -1))
		if len(n) == 0 {
			continue
		}
		e := &exec.Cmd{
			Path:        p,
			Args:        []string{"powershell.exe", "-Command", "Get-AppxPackage " + n + " | Remove-AppxPackage"},
			SysProcAttr: &syscall.SysProcAttr{HideWindow: true},
		}
		if err := e.Run(); err != nil {
			os.Stderr.WriteString(`Removing package "` + n + `" raised an error: ` + err.Error() + "!\n")
		}
		e = nil
	}
}
func stripInvalids(s string) string {
	if len(s) == 0 {
		return s
	}
	var b strings.Builder
	b.Grow(len(s))
	for i := range s {
		switch c := s[i]; {
		case c >= '0' && c <= '9':
			fallthrough
		case c >= 'a' && c <= 'z':
			fallthrough
		case c >= 'A' && c <= 'Z':
			fallthrough
		case c == '_' || c == '-' || c == '.' || c == '*':
			b.WriteByte(c)
		default:
		}
	}
	r := b.String()
	b.Reset()
	return r
}
