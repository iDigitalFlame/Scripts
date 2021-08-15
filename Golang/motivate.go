// motivate.go
// Outputs great quotes and messages.
//
// Copyright (C) 2021 iDigitalFlame
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
	"context"
	"encoding/json"
	"errors"
	"flag"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"strings"
	"time"
)

type quotes []string

const (
	api    = "http://www.forismatic.com/api/1.0/"
	body   = "method=getQuote&lang=en&format=json"
	config = "$HOME/.config/quotes.db"
)

const usage = `Motivate

Usage:
  -f <db>    Quotes file path.
  -a <quote> Add a quote to the quotes file.
  -n         Download a quote from the Internet.

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
along with this program.  If not, see <https://www.gnu.org/licenses/>.
`

var random = rand.New(rand.NewSource(time.Now().Unix() ^ 2))

func main() {
	var (
		d    bool
		q    quotes
		f, a string
		args = flag.NewFlagSet("Motivate", flag.ExitOnError)
	)

	args.Usage = func() {
		os.Stdout.WriteString(usage)
		os.Exit(2)
	}
	args.StringVar(&f, "f", config, "Quotes file path.")
	args.StringVar(&a, "a", "", "Add a quote to the quotes file.")
	args.BoolVar(&d, "n", false, "Download a quote from the Internet.")

	if err := args.Parse(os.Args[1:]); err != nil {
		os.Stderr.WriteString("Error: " + err.Error() + "\n")
		os.Exit(1)
	}

	if err := q.load(f); err != nil {
		os.Stderr.WriteString(`Error loading "` + f + `": ` + err.Error() + "\n")
		os.Exit(1)
	}

	switch {
	case len(a) > 0:
		if err := q.add(a, f); err != nil {
			os.Stderr.WriteString("Error during save: " + err.Error() + "\n")
			os.Exit(1)
		}
	case d:
		if err := q.download(api, f); err != nil {
			os.Stderr.WriteString("Error during download: " + err.Error() + "\n")
			os.Exit(1)
		}
	default:
		os.Stdout.WriteString(q.String() + "\n")
	}
}
func (q quotes) String() string {
	for {
		s := q[random.Intn(len(q))]
		if len(s) > 0 {
			return s
		}
	}
}
func (q quotes) save(s string) error {
	var (
		f = os.ExpandEnv(s)
		w *os.File
	)
	if i, err := os.Stat(f); err != nil {
		return errors.New(`could not open file "` + f + `": ` + err.Error())
	} else if i.IsDir() {
		return errors.New(`path "` + f + `" is not a file`)
	}
	var err error
	if w, err = os.OpenFile(f, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0640); err != nil {
		return errors.New(`could not open file "` + f + `": ` + err.Error())
	}
	for x := range q {
		n := strings.TrimSpace(q[x])
		if len(n) == 0 {
			continue
		}
		if _, err = w.WriteString(n + "\n"); err != nil {
			break
		}
	}
	if w.Close(); err != nil {
		return errors.New(`could not save file "` + f + `": ` + err.Error())
	}
	return nil
}
func (q *quotes) load(s string) error {
	f := os.ExpandEnv(s)
	if i, err := os.Stat(f); err != nil {
		return errors.New(`could not open file "` + f + `": ` + err.Error())
	} else if i.IsDir() {
		return errors.New(`path "` + f + `" is not a file`)
	}
	b, err := ioutil.ReadFile(f)
	if err != nil {
		return errors.New(`could not read file "` + f + `": ` + err.Error())
	}
	*q = strings.Split(string(b), "\n")
	return nil
}
func (q *quotes) add(s, f string) error {
	c := strings.TrimSpace(strings.ToLower(s))
	if len(c) == 0 {
		return nil
	}
	for i := range *q {
		if strings.ToLower((*q)[i]) == c {
			return nil
		}
	}
	*q = append(*q, c)
	return q.save(f)
}
func (q *quotes) download(s, f string) error {
	var (
		x, c = context.WithTimeout(context.Background(), time.Duration(2*time.Second))
		r, _ = http.NewRequestWithContext(x, http.MethodPost, api, strings.NewReader(body))
	)
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	o, err := http.DefaultClient.Do(r)
	switch c(); {
	case err != nil:
		return errors.New(`could not download quote from "` + s + `": ` + err.Error())
	case o.Body == nil:
		return errors.New(`could not download quote from "` + s + `": empty response`)
	case o.StatusCode != http.StatusOK:
		return errors.New(`could not download quote from "` + s + `": status "` + o.Status + `" received`)
	}
	b, err := ioutil.ReadAll(o.Body)
	if o.Body.Close(); err != nil {
		return errors.New(`could not read quote from "` + s + `": ` + err.Error())
	}
	m := make(map[string]string)
	if err = json.Unmarshal(b, &m); err != nil {
		return errors.New(`could not read quote from "` + s + `": ` + err.Error())
	}
	v, ok := m["quoteText"]
	if !ok {
		return errors.New(`could not find JSON key "quoteText"`)
	}
	if err = q.add(v, f); err != nil {
		return err
	}
	os.Stdout.WriteString(v + "\n")
	if a, ok := m["quoteAuthor"]; ok {
		os.Stdout.WriteString(" - " + a + "\n")
	}
	return nil
}
