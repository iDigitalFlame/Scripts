package main

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"./gorover"
)

func main() {
	if len(os.Args) >= 2 {
		r := gorover.NewRover()
		defer r.Stop()
		switch os.Args[1] {
		case "f":
			r.Forward()
		case "b":
			r.Reverse()
		case "r":
			r.Right()
		case "l":
			r.Left()
		default:
			fmt.Printf("Option must be [f, b, r, l]!\n")
			os.Exit(1)
		}
		if len(os.Args) >= 3 {
			if i, err := strconv.ParseInt(os.Args[2], 10, 32); err == nil {
				time.Sleep(time.Duration(i) * time.Millisecond)
				r.Stop()
				os.Exit(0)
			}
			fmt.Printf("%s is not a valid number!\n", os.Args[2])
			os.Exit(1)
		}
	}
}
