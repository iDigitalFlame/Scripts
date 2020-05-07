// motivate.go
// Outputs great quotes and messages.
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
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"strings"
	"time"
)

const (
	api    = "http://www.forismatic.com/api/1.0/"
	body   = "method=getQuote&lang=en&format=json"
	config = "$HOME/.config/quotes.db"

	usage = `Motivate

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
along with this program.  If not, see <https://www.gnu.org/licenses/>.`
)

var random = rand.New(rand.NewSource(time.Now().Unix() ^ 2))

type quotes []string

func main() {
	var (
		d    bool
		q    quotes
		f, a string
		args = flag.NewFlagSet("Motivate", flag.ExitOnError)
	)

	args.Usage = func() {
		fmt.Fprintln(os.Stderr, usage)
		os.Exit(2)
	}
	args.StringVar(&f, "f", config, "Quotes file path.")
	args.StringVar(&a, "a", "", "Add a quote to the quotes file.")
	args.BoolVar(&d, "n", false, "Download a quote from the Internet.")

	if err := args.Parse(os.Args[1:]); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %s\n", err.Error())
		os.Exit(1)
	}

	if err := q.load(f); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %s\n", err.Error())
		os.Exit(1)
	}

	if len(a) > 0 {
		if err := q.add(a, f); err != nil {
			fmt.Fprintf(os.Stderr, "Error during save: %s\n", err.Error())
			os.Exit(1)
		}
		os.Exit(0)
	}

	if d {
		if err := q.download(api, f); err != nil {
			fmt.Fprintf(os.Stderr, "Error during download: %s\n", err.Error())
			os.Exit(1)
		}
		os.Exit(0)
	}

	fmt.Fprintln(os.Stdout, q.String())
}
func (q quotes) String() string {
	return q[random.Intn(len(q))]
}
func (q quotes) save(s string) error {
	var (
		f      = os.ExpandEnv(s)
		w      *os.File
		i, err = os.Stat(f)
	)
	if err != nil || i.IsDir() {
		return fmt.Errorf("file path %q is not valid", f)
	}
	if w, err = os.OpenFile(f, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0640); err != nil {
		return fmt.Errorf("could not open file %q: %w", f, err)
	}
	defer w.Close()
	for x := range q {
		n := strings.TrimSpace(q[x])
		if len(n) == 0 {
			continue
		}
		if _, err := fmt.Fprintln(w, n); err != nil {
			return fmt.Errorf("could not save file %q: %w", f, err)
		}
	}
	return nil
}
func (q *quotes) load(s string) error {
	var (
		b      []byte
		f      = os.ExpandEnv(s)
		i, err = os.Stat(f)
	)
	if err != nil || i.IsDir() {
		return fmt.Errorf("file path %q is not valid", f)
	}
	if b, err = ioutil.ReadFile(f); err != nil {
		return fmt.Errorf("could not read file %q: %s", f, err)
	}
	*q = strings.Split(string(b), "\n")
	return nil
}
func (q *quotes) add(s, f string) error {
	c := strings.TrimSpace(strings.ToLower(s))
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
		x, c   = context.WithTimeout(context.Background(), time.Duration(5*time.Second))
		r, err = http.NewRequestWithContext(x, http.MethodPost, api, strings.NewReader(body))
	)
	defer c()
	if err != nil {
		return fmt.Errorf("could not download quote from %q: %w", s, err)
	}
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	o, err := http.DefaultClient.Do(r)
	if err != nil {
		return fmt.Errorf("could not download quote from %q: %w", s, err)
	}
	if o.Body == nil {
		return fmt.Errorf("could not download quote from %q: empty response", s)
	}
	defer o.Body.Close()
	if o.StatusCode != http.StatusOK {
		return fmt.Errorf("could not download quote from %q: status %d received", s, o.StatusCode)
	}
	b, err := ioutil.ReadAll(o.Body)
	if err != nil {
		return fmt.Errorf("could not read quote from %q: %w", s, err)
	}
	m := make(map[string]string)
	if err := json.Unmarshal(b, &m); err != nil {
		return fmt.Errorf("could not read quote from %q: %w", s, err)
	}
	v, ok := m["quoteText"]
	if !ok {
		return fmt.Errorf(`could not find json key "quoteText"`)
	}
	if err := q.add(v, f); err != nil {
		return err
	}
	if a, ok := m["quoteAuthor"]; ok {
		fmt.Fprintf(os.Stdout, "%s\n  - %s\n", v, a)
	} else {
		fmt.Fprintln(os.Stdout, v)
	}
	return nil
}
