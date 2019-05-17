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
)

const (
	quotesDBFile      = "$HOME/.config/quotes.db"
	quotesDownloadURL = "http://www.forismatic.com/api/1.0/"
)

type quoteDictonary []string

func main() {
	d := flag.Bool("get", false, "Download a quote from the Internet.")
	flag.Parse()
	q, err := newQuoteDictonary(quotesDBFile)
	if err != nil {
		fmt.Printf("Exception occured: %s\n", err.Error())
		os.Exit(1)
	}
	if *d {
		s, err := q.downloadQuote(quotesDownloadURL)
		if err != nil {
			fmt.Printf("Exception occured: %s\n", err.Error())
			os.Exit(1)
		}
		fmt.Printf("%s\n", s)
		if err := q.saveDictonary(quotesDBFile); err != nil {
			fmt.Printf("Exception occured: %s\n", err.Error())
			os.Exit(1)
		}
	} else {
		fmt.Printf("%s\n", q.getQuote())
	}
	os.Exit(0)
}

func (q *quoteDictonary) getQuote() string {
	r := rand.New(rand.NewSource(time.Now().Unix()))
	return (*q)[r.Intn(len(*q))]
}

func (q *quoteDictonary) saveDictonary(s string) error {
	p := os.ExpandEnv(s)
	f, err := os.Stat(p)
	if err == nil && f.IsDir() {
		return fmt.Errorf("quotes db path \"%s\" is a directory", p)
	}
	if err != nil {
		if err := ioutil.WriteFile(p, []byte("\n"), 0640); err != nil {
			return fmt.Errorf("could not create quotes db \"%s\", %s", p, err.Error())
		}
	}
	w, err := os.OpenFile(p, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0640)
	if err != nil {
		return fmt.Errorf("could not open quotes db \"%s\", %s", p, err.Error())
	}
	defer w.Close()
	for _, l := range *q {
		if len(l) > 0 {
			if _, err := fmt.Fprintf(w, "%s\n", l); err != nil {
				return fmt.Errorf("could not save quotes db \"%s\", %s", p, err.Error())
			}
		}
	}
	return nil
}

func newQuoteDictonary(s string) (*quoteDictonary, error) {
	p := os.ExpandEnv(s)
	f, err := os.Stat(p)
	if err == nil && f.IsDir() {
		return nil, fmt.Errorf("quotes db path \"%s\" is a directory", p)
	}
	if err != nil {
		if err := ioutil.WriteFile(p, []byte("\n"), 0640); err != nil {
			return nil, fmt.Errorf("could not create quotes db \"%s\", %s", p, err.Error())
		}
	}
	l, err := ioutil.ReadFile(p)
	if err != nil {
		return nil, fmt.Errorf("could not read quotes db \"%s\", %s", p, err.Error())
	}
	q := quoteDictonary(strings.Split(string(l), "\n"))
	return &q, nil
}

func (q *quoteDictonary) downloadQuote(s string) (string, error) {
	r, err := http.NewRequest("POST", s, strings.NewReader("method=getQuote&lang=en&format=json"))
	if err != nil {
		panic(fmt.Sprintf("could not download a new quote from \"%s\", %s.", s, err.Error()))
	}
	x, cn := context.WithTimeout(context.Background(), time.Duration(5*time.Second))
	defer cn()
	r = r.WithContext(x)
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	b, err := http.DefaultClient.Do(r)
	if err != nil {
		return "", err
	}
	defer b.Body.Close()
	if b.StatusCode != 200 {
		return "", fmt.Errorf("server returned a non ok status code \"%d\"", b.StatusCode)
	}
	d, err := ioutil.ReadAll(b.Body)
	if err != nil {
		return "", nil
	}
	n := make(map[string]interface{})
	err = json.Unmarshal(d, &n)
	if err != nil {
		return "", nil
	}
	v, ok := n["quoteText"]
	if !ok {
		return "", fmt.Errorf("could not find json key \"quoteText\"")
	}
	t, ok := v.(string)
	if !ok {
		return "", fmt.Errorf("json key \"quoteText\" is not a string")
	}
	c := true
	for _, l := range *q {
		if strings.ToLower(l) == strings.ToLower(t) {
			c = false
		}
	}
	if c {
		*q = append(*q, t)
	}
	if i, ok := n["quoteAuthor"]; ok {
		if a, ok := i.(string); ok {
			t = fmt.Sprintf("%s\n\t- %s", t, a)
		}
	}
	return t, nil
}
