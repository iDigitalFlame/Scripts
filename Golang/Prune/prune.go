// prune.go
// Files prune script, deeletes files older than the specified amount of days.
// iDigitalflame

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

func main() {
	d := flag.String("d", "", "Directory to scan.")
	f := flag.String("f", "", "Filter scan to files that contain this string.")
	t := flag.Int("t", 10, "Day limit for when file is deleted, defaaults to 10.")
	flag.Parse()
	if len(*d) == 0 {
		fmt.Printf("Directory \"-d\" must be specified!\n")
		os.Exit(1)
	}
	if err := checkDirectory(*d, *f, uint16(*t)); err != nil {
		fmt.Printf("Error occured during processing! %s", err.Error())
		os.Exit(1)
	}
	os.Exit(0)
}
func getCreateDays(f os.FileInfo) uint16 {
	i := f.Sys().(*syscall.Stat_t)
	t := time.Unix(int64(i.Ctim.Sec), int64(i.Ctim.Nsec))
	return uint16(math.Floor(time.Since(t).Hours()/24) + 1)
}
func checkDirectory(s, f string, d uint16) error {
	l, err := ioutil.ReadDir(s)
	if err != nil {
		return fmt.Errorf("could not read directory listing for \"%s\": %s", s, err.Error())
	}
	r, p, k := 0, 0, 0
	for _, b := range l {
		if b.IsDir() {
			continue
		}
		if len(f) > 0 && !strings.Contains(b.Name(), f) {
			continue
		}
		p++
		o := getCreateDays(b)
		if o > d {
			fmt.Printf("File \"%s\" is \"%d\" days old, limit is \"%d\", removing!\n", b.Name(), o, d)
			if err := os.Remove(path.Join(s, b.Name())); err != nil {
				return fmt.Errorf("could not remove file \"%s\": %s", b.Name(), err.Error())
			}
			r++
		} else {
			k++
		}
	}
	fmt.Printf("Done. %d Scanned, %d Kept, %d Removed.\n", p, k, r)
	return nil
}
