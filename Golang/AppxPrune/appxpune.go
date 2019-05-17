// appxprune.go
// Removes Windows 10 Appx Packages
// iDigitalFlame

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
	packageList      = "packages.txt"
	packageUninstall = "Get-AppxPackage | Where-Object { $_.Name -eq '%s' } | Remove-AppxPackage"
)

func main() {
	if s, err := os.Stat(packageList); err != nil {
		fmt.Printf("Could not open package list \"%s\": %s\n", packageList, err.Error())
		os.Exit(1)
	} else {
		if s.IsDir() {
			fmt.Printf("Package list \"%s\" is not a file!\n", packageList)
			os.Exit(1)
		}
	}
	d, err := ioutil.ReadFile(packageList)
	if err != nil {
		fmt.Printf("Could not open package list \"%s\": %s\n", packageList, err.Error())
		os.Exit(1)
	}
	p := strings.Split(string(d), "\n")
	for _, o := range p {
		if len(o) > 0 {
			o = strings.Replace(strings.Replace(o, "\n", "", -1), "\r", "", -1)
			c := exec.Command("powershell.exe", "-Command", fmt.Sprintf(packageUninstall, o))
			c.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
			if err := c.Run(); err != nil {
				fmt.Printf("Removing pacakge \"%s\" raised the error: %s\n", o, err.Error())
			}
		}
	}
	os.Exit(0)
}
