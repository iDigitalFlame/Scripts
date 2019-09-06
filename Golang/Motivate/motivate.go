// motovate.go
// Outputs great quotes and messages.
// iDigitalFlame

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

	"golang.org/x/xerrors"
)

const (
	quotesURL  = "http://www.forismatic.com/api/1.0/"
	quotesFile = "$HOME/.config/quotes.db"
)

var (
	random = rand.New(rand.NewSource(time.Now().Unix() ^ 2))
)

type quotes []string

func main() {
	f := flag.String("file", quotesFile, "Quotes file path.")
	a := flag.String("add", "", "Add a quote to the quotes file.")
	d := flag.Bool("get", false, "Download a quote from the Internet.")
	flag.Parse()

	q := new(quotes)
	if err := q.load(*f); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %s\n", err.Error())
		os.Exit(1)
	}

	if len(*a) > 0 {
		q.add(*a)
		if err := q.save(*f); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %s\n", err.Error())
			os.Exit(1)
		}
		os.Exit(0)
	} else if *d {
		if err := q.download(quotesURL); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %s\n", err.Error())
			os.Exit(1)
		}
		if err := q.save(*f); err != nil {
			fmt.Fprintf(os.Stderr, "Error: %s\n", err.Error())
			os.Exit(1)
		}
		os.Exit(0)
	}
	fmt.Fprintf(os.Stdout, "%s\n", q.String())
	os.Exit(0)
}
func (q *quotes) add(s string) {
	c := strings.ToLower(s)
	for i := range *q {
		if strings.ToLower((*q)[i]) == c {
			return
		}
	}
	*q = append(*q, c)
}
func (q *quotes) String() string {
	return (*q)[random.Intn(len(*q))]
}
func (q *quotes) load(s string) error {
	f := os.ExpandEnv(s)
	if i, err := os.Stat(f); err != nil || i.IsDir() {
		return fmt.Errorf("file path \"%s\" is not valid", f)
	}
	b, err := ioutil.ReadFile(f)
	if err != nil {
		return xerrors.Errorf("could not read file \"%s\": %s", f, err)
	}
	*q = strings.Split(string(b), "\n")
	return nil
}
func (q *quotes) save(s string) error {
	f := os.ExpandEnv(s)
	if i, err := os.Stat(f); err != nil || i.IsDir() {
		return fmt.Errorf("file path \"%s\" is not valid", f)
	}
	w, err := os.OpenFile(f, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0640)
	if err != nil {
		return xerrors.Errorf("could not open file \"%s\": %w", f, err)
	}
	defer w.Close()
	for x := range *q {
		if len((*q)[x]) == 0 {
			continue
		}
		if _, err := fmt.Fprintf(w, "%s\n", (*q)[x]); err != nil {
			return xerrors.Errorf("could not save file \"%s\": %w", f, err)
		}
	}
	return nil
}
func (q *quotes) download(s string) error {
	r, err := http.NewRequest("POST", s, strings.NewReader("method=getQuote&lang=en&format=json"))
	if err != nil {
		return xerrors.Errorf("could not download quote from \"%s\": %w", s, err)
	}
	x, c := context.WithTimeout(context.Background(), time.Duration(5*time.Second))
	r = r.WithContext(x)
	defer c()
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	o, err := http.DefaultClient.Do(r)
	if err != nil || o.Body == nil {
		return xerrors.Errorf("could not download quote from \"%s\": %w", s, err)
	}
	defer o.Body.Close()
	if o.StatusCode != http.StatusOK {
		return fmt.Errorf("received a non 200 status code \"%d\"", o.StatusCode)
	}
	b, err := ioutil.ReadAll(o.Body)
	if err != nil {
		return xerrors.Errorf("could not read quote from \"%s\": %w", s, err)
	}
	m := make(map[string]string)
	if err := json.Unmarshal(b, &m); err != nil {
		return xerrors.Errorf("could not read quote from \"%s\": %w", s, err)
	}
	v, ok := m["quoteText"]
	if !ok {
		return fmt.Errorf("could not find json key \"quoteText\"")
	}
	q.add(v)
	if a, ok := m["quoteAuthor"]; ok {
		fmt.Fprintf(os.Stdout, "%s\n  - %s\n", v, a)
	}
	return nil
}
