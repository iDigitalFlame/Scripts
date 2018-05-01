package main

import (
	"fmt"
	"io/ioutil"
	"math/rand"
	"os"
	"strings"
	"time"
)

func main() {
	quotesFile := os.ExpandEnv("$HOME/.config/quotes.db")
	checkQuotes(quotesFile)
	if len(os.Args) > 1 {
		addQuote(quotesFile, os.Args[1])
	} else {
		getQuote(quotesFile)
	}
	os.Exit(0)

}

func getQuote(QuotesFile string) {
	raw, err := ioutil.ReadFile(QuotesFile)
	if err != nil {
		fmt.Printf("Could not read quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
		os.Exit(1)
	}
	contents := strings.Split(string(raw), "\n")
	random := rand.New(rand.NewSource(time.Now().Unix()))
	index := random.Intn(len(contents))
	fmt.Printf("%s\n", strings.Replace(contents[index], "\n", "", 0))
}

func checkQuotes(QuotesFile string) {
	file, err := os.Stat(QuotesFile)
	if err != nil {
		err = ioutil.WriteFile(QuotesFile, []byte("\n"), 0660)
		if err != nil {
			fmt.Printf("Error creating quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
			os.Exit(1)
		}
	} else {
		if file.IsDir() {
			fmt.Printf("Quotes file \"%s\" is not a file!\n", QuotesFile)
			os.Exit(1)
		}
	}
}

func addQuote(QuotesFile string, NewQuote string) {
	raw, err := ioutil.ReadFile(QuotesFile)
	if err != nil {
		fmt.Printf("Could not read quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
		os.Exit(1)
	}
	contents := strings.Split(string(raw), "\n")
	quoteLower := strings.ToLower(NewQuote)
	for index := 0; index < len(contents); index++ {
		if strings.ToLower(contents[index]) == quoteLower {
			os.Exit(0)
		}
	}
	contents = append(contents, NewQuote)
	file, err := os.Create(QuotesFile)
	if err != nil {
		fmt.Printf("Error getting quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
		os.Exit(1)
	}
	for index := 0; index < len(contents); index++ {
		if len(contents[index]) > 0 {
			if index > 0 {
				fmt.Fprintf(file, "\n")
			}
			fmt.Fprintf(file, "%s", strings.Replace(contents[index], "\n", "", 0))
		}
	}
	err = file.Close()
	if err != nil {
		fmt.Printf("Error writing to quotes file \"%s\"! (%s)\n", QuotesFile, err.Error())
		os.Exit(1)
	}
}

//# EOF