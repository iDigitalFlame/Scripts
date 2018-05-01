package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"strings"
	"time"
)

type webQuote struct {
	URL    string `json:"quoteLink"`
	Text   string `json:"quoteText"`
	Name   string `json:"senderName"`
	Link   string `json:"senderLink"`
	Author string `json:"quoteAuthor"`
}

func main() {
	quotesFile := os.ExpandEnv("$HOME/.config/quotes.db")
	check(quotesFile)
	if len(os.Args) > 1 {
		if os.Args[1] == "-get" {
			download(quotesFile)
		} else {
			add(quotesFile, os.Args[1])
		}
	} else {
		get(quotesFile)
	}
	os.Exit(0)
}

func get(QuotesFile string) {
	quotesRaw, err := ioutil.ReadFile(QuotesFile)
	if err != nil {
		fmt.Printf("Could not read quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
		os.Exit(1)
	}
	qoutesList := strings.Split(string(quotesRaw), "\n")
	quotesRand := rand.New(rand.NewSource(time.Now().Unix()))
	quotesIndex := quotesRand.Intn(len(qoutesList))
	fmt.Printf("%s\n", strings.Replace(qoutesList[quotesIndex], "\n", "", 0))
}

func check(QuotesFile string) {
	quotesStat, err := os.Stat(QuotesFile)
	if err != nil {
		err = ioutil.WriteFile(QuotesFile, []byte("\n"), 0660)
		if err != nil {
			fmt.Printf("Error creating quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
			os.Exit(1)
		}
	} else {
		if quotesStat.IsDir() {
			fmt.Printf("Quotes file \"%s\" is not a file!\n", QuotesFile)
			os.Exit(1)
		}
	}
}

func download(QuotesFile string) {
	quoteOnline, err := ioutil.ReadFile(os.ExpandEnv("$HOME/.xonline"))
	if err != nil {
		fmt.Printf("Could not access online status file! (%s)\n", err.Error())
		os.Exit(1)
	}
	if string(quoteOnline[0]) == "0" {
		fmt.Printf("Online operations are disabled, please enable with \"online on\"!\n")
		os.Exit(1)
	}
	quoteReader := strings.NewReader("method=getQuote&lang=en&format=json")
	quoteResponse, err := http.Post("http://www.forismatic.com/api/1.0/", "application/x-www-form-urlencoded", quoteReader)
	if err != nil {
		fmt.Printf("Could not download a new quote! (%s)\n", err.Error())
		os.Exit(1)
	}
	quoteData, err := ioutil.ReadAll(quoteResponse.Body)
	if err != nil {
		fmt.Printf("Could not download a new quote! (%s)\n", err.Error())
		os.Exit(1)
	}
	quoteResponse.Body.Close()
	if quoteResponse.StatusCode == 200 {
		var newQuote webQuote
		err = json.Unmarshal(quoteData, &newQuote)
		if err != nil {
			fmt.Printf("Could not decode quote JSON! (%s)\n", err.Error())
			os.Exit(1)
		}
		fmt.Printf("%s\n- %s\n", newQuote.Text, newQuote.Author)
		add(QuotesFile, newQuote.Text)
	} else {
		fmt.Printf("Received (%d) status code from the server! (%s)\n", quoteResponse.StatusCode, string(quoteData))
		os.Exit(1)
	}
}

func add(QuotesFile string, NewQuote string) {
	qoutesRaw, err := ioutil.ReadFile(QuotesFile)
	if err != nil {
		fmt.Printf("Could not read quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
		os.Exit(1)
	}
	quoteText := strings.Trim(NewQuote, " ")
	quotesList := strings.Split(string(qoutesRaw), "\n")
	quoteLower := strings.ToLower(quoteText)
	for _, quoteString := range quotesList {
		if strings.ToLower(quoteString) == quoteLower {
			os.Exit(0)
		}
	}
	quotesList = append(quotesList, quoteText)
	qoutesHandle, err := os.Create(QuotesFile)
	if err != nil {
		fmt.Printf("Error getting quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
		os.Exit(1)
	}
	for quotesIndex, quoteString := range quotesList {
		if len(quoteString) > 0 {
			if quotesIndex > 0 {
				fmt.Fprintf(qoutesHandle, "\n")
			}
			fmt.Fprintf(qoutesHandle, "%s", strings.Replace(strings.Trim(quoteString, " "), "\n", "", 0))
		}
	}
	err = qoutesHandle.Close()
	if err != nil {
		fmt.Printf("Error writing to quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
		os.Exit(1)
	}
}

//# EOF