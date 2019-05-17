// linker.go
// URL Shortner with MySQL database.
// iDigitalFlame

package main

import (
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"os"
	"strings"
)
import _ "github.com/go-sql-driver/mysql"

const (
	linkerInvalid          = "!@#$%^&*()-_+=|\\][{}\"':;/?><,.~` "
	linkerDefaultConfig    = "/etc/linker.conf"
	linkerGetAllQuery      = "SELECT LinkName, LinkURL FROM Links"
	linkerDeleteLinkQuery  = "DELETE FROM Links WHERE LinkName = ?"
	linkerGetByNameQuery   = "SELECT LinkURL FROM Links WHERE LinkName = ?"
	linkerAddLinkQuery     = "INSERT INTO Links(LinkName, LinkURL) VALUES(?, ?)"
	linkerCreateTableQuery = "CREATE TABLE IF NOT EXISTS Links (LinkID INT(32) NOT NULL PRIMARY KEY AUTO_INCREMENT, " +
		"LinkName VARCHAR(64) NOT NULL UNIQUE, LinkURL VARCHAR(1024) NOT NULL)"
)

var (
	linkerError       error
	linkerConfig      linkerConfigFile
	linkerGetAll      *sql.Stmt
	linkerAddLink     *sql.Stmt
	linkerDatabase    *sql.DB
	linkerGetByName   *sql.Stmt
	linkerDeleteLink  *sql.Stmt
	linkerCreateTable *sql.Stmt
)

type linkerConfigFile struct {
	Port     int    `json:"http_port"`
	Server   string `json:"db_server"`
	Default  string `json:"default_url,omitempty"`
	Address  string `json:"http_listen,omitempty"`
	Database string `json:"db_name"`
	Username string `json:"db_username"`
	Password string `json:"db_password"`
}

func main() {
	linkerFlagURL := flag.String("url", "", "URL to add.")
	linkerFlagAdd := flag.String("add", "", "Add a new URL with Name.")
	linkerFlagDelete := flag.String("del", "", "Delete a URL by Name.")
	linkerFlagList := flag.Bool("list", false, "List all current URLs.")
	linkerFlagConfig := flag.String("config", "", "Linker configuration file path.")
	linkerFlagNoHTTP := flag.Bool("nohttp", false, "Will not correct URLS without \"http://\".")
	flag.Parse()
	if *linkerFlagAdd != "" && *linkerFlagURL == "" {
		flag.PrintDefaults()
		os.Exit(1)
	}
	if *linkerFlagAdd != "" && *linkerFlagDelete != "" {
		flag.PrintDefaults()
		os.Exit(1)
	}
	err := loadConfig(*linkerFlagConfig)
	if err != nil {
		panic(fmt.Errorf("error loading configuration! (%s)", err.Error()))
	}
	defer closeAll()
	if *linkerFlagList {
		listLinks()
		return
	}
	if *linkerFlagDelete != "" {
		if removeLink(*linkerFlagDelete) {
			fmt.Printf("The URL with name \"%s\" was removed.\n", *linkerFlagDelete)
		} else {
			fmt.Printf("The URL with name \"%s\" could not be removed!\n", *linkerFlagDelete)
			os.Exit(1)
		}
		return
	}
	if *linkerFlagAdd != "" {
		linkerURL := *linkerFlagURL
		if !strings.HasPrefix(strings.ToLower(*linkerFlagURL), "http") && !(*linkerFlagNoHTTP) {
			linkerURL = fmt.Sprintf("http://%s", linkerURL)
		}
		if addLink(*linkerFlagAdd, linkerURL) {
			fmt.Printf("The URL with name \"%s\" was added.\n", *linkerFlagAdd)
		} else {
			fmt.Printf("The URL with name \"%s\" could not be added!\n", *linkerFlagAdd)
			os.Exit(1)
		}
		return
	}
	http.HandleFunc("/", getLinkRequest)
	log.Fatal(http.ListenAndServe(fmt.Sprintf("%s:%d", linkerConfig.Address, linkerConfig.Port), nil))
}

func tryFail() {
	if linkerError != nil {
		closeAll()
		panic(fmt.Errorf("errors have occured in operation: \"%s\"", linkerError.Error()))
	}
}

func closeAll() {
	if linkerGetAll != nil {
		linkerGetAll.Close()
	}
	if linkerAddLink != nil {
		linkerAddLink.Close()
	}
	if linkerGetByName != nil {
		linkerGetByName.Close()
	}
	if linkerDeleteLink != nil {
		linkerDeleteLink.Close()
	}
	if linkerCreateTable != nil {
		linkerCreateTable.Close()
	}
	if linkerDatabase != nil {
		linkerDatabase.Close()
	}
}

func listLinks() {
	defer tryFail()
	fmt.Printf("Name\t->\tURL\n")
	var linkerRows *sql.Rows
	if linkerRows, linkerError = linkerGetAll.Query(); linkerError != nil {
		return
	}
	var linkName, linkURL string
	for linkerRows.Next() {
		if linkerError = linkerRows.Err(); linkerError != nil {
			return
		}
		linkerError = linkerRows.Scan(&linkName, &linkURL)
		fmt.Printf("%s\t->\t%s\n", linkName, linkURL)
	}
	if linkerError = linkerRows.Err(); linkerError != nil {
		return
	}
	linkerRows.Close()
}

func removeLink(s string) bool {
	if strings.ContainsAny(s, linkerInvalid) {
		return false
	}
	defer tryFail()
	var linkerResult sql.Result
	if linkerResult, linkerError = linkerDeleteLink.Exec(s); linkerError != nil {
		return false
	}
	var linkerRows int64
	if linkerRows, linkerError = linkerResult.RowsAffected(); linkerError != nil {
		return false
	}
	return linkerRows > 0
}

func loadConfig(s string) error {
	var linkerConfigBytes []byte
	if s == "" {
		if _, err := os.Stat(linkerDefaultConfig); err != nil {
			linkerConfig.Port = 8080
			linkerConfig.Address = "127.0.0.1"
			linkerConfig.Database = "linker_db"
			linkerConfig.Password = "Password69"
			linkerConfig.Username = "linker_user"
			linkerConfig.Server = "tcp(localhost:3306)"
			linkerConfig.Default = "https://duckduckgo.com"
			linkerConfigBytes, err = json.Marshal(linkerConfig)
			err = ioutil.WriteFile(linkerDefaultConfig, linkerConfigBytes, 0440)
			if err != nil {
				return err
			}
			fmt.Printf("Created a default config at \"%s\", please edit it!\nBye!\n", linkerDefaultConfig)
			os.Exit(1)
		} else {
			linkerConfigBytes, linkerError = ioutil.ReadFile(linkerDefaultConfig)
		}
	} else {
		linkerConfigBytes, linkerError = ioutil.ReadFile(s)
	}
	if linkerError != nil {
		return linkerError
	}
	if linkerError = json.Unmarshal(linkerConfigBytes, &linkerConfig); linkerError != nil {
		return linkerError
	}
	defer tryFail()
	linkerDatabase, linkerError = sql.Open("mysql", fmt.Sprintf("%s:%s@%s/%s", linkerConfig.Username, linkerConfig.Password, linkerConfig.Server, linkerConfig.Database))
	if linkerError != nil {
		return linkerError
	}
	if linkerError = linkerDatabase.Ping(); linkerError != nil {
		return linkerError
	}
	if linkerCreateTable, linkerError = linkerDatabase.Prepare(linkerCreateTableQuery); linkerError != nil {
		return linkerError
	}
	if _, linkerError = linkerCreateTable.Exec(); linkerError != nil {
		return linkerError
	}
	if linkerGetAll, linkerError = linkerDatabase.Prepare(linkerGetAllQuery); linkerError != nil {
		return linkerError
	}
	if linkerAddLink, linkerError = linkerDatabase.Prepare(linkerAddLinkQuery); linkerError != nil {
		return linkerError
	}
	if linkerGetByName, linkerError = linkerDatabase.Prepare(linkerGetByNameQuery); linkerError != nil {
		return linkerError
	}
	if linkerDeleteLink, linkerError = linkerDatabase.Prepare(linkerDeleteLinkQuery); linkerError != nil {
		return linkerError
	}
	return nil
}

func addLink(s string, u string) bool {
	defer tryFail()
	if strings.ContainsAny(s, linkerInvalid) {
		return false
	}
	defer tryFail()
	var linkerNewURL *url.URL
	if linkerNewURL, linkerError = url.Parse(u); linkerError != nil {
		return false
	}
	var linkerResult sql.Result
	if linkerResult, linkerError = linkerAddLink.Exec(s, linkerNewURL.String()); linkerError != nil {
		return false
	}
	var linkerRows int64
	if linkerRows, linkerError = linkerResult.RowsAffected(); linkerError != nil {
		return false
	}
	return linkerRows > 0
}

func getLinkRequest(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		if len(r.RequestURI) == 1 {
			if linkerConfig.Default != "" {
				http.Redirect(w, r, linkerConfig.Default, http.StatusTemporaryRedirect)
				return
			}
			return
		}
		linkerURLRow, err := linkerGetByName.Query(r.RequestURI[1:])
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, http.StatusText(http.StatusInternalServerError))
			fmt.Printf("Error occured when attempting to get URL \"%s\"! (%s)\n", r.RequestURI, err.Error())
			return
		}
		for linkerURLRow.Next() {
			if linkerURLRow.Err() != nil {
				linkerURLRow.Close()
				w.WriteHeader(http.StatusInternalServerError)
				fmt.Fprintf(w, http.StatusText(http.StatusInternalServerError))
				fmt.Printf("Error occured when attempting to get URL \"%s\"! (%s)\n", r.RequestURI, err.Error())
				return
			}
			var linkerURL string
			err := linkerURLRow.Scan(&linkerURL)
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				fmt.Fprintf(w, http.StatusText(http.StatusInternalServerError))
				fmt.Printf("Error occured when attempting to get URL \"%s\"! (%s)\n", r.RequestURI, err.Error())
				return
			}
			linkerURLRow.Close()
			http.Redirect(w, r, linkerURL, http.StatusTemporaryRedirect)
			return
		}
		if linkerConfig.Default != "" {
			http.Redirect(w, r, linkerConfig.Default, http.StatusTemporaryRedirect)
			return
		}
		return
	}
	w.WriteHeader(http.StatusMethodNotAllowed)
	fmt.Fprintf(w, http.StatusText(http.StatusMethodNotAllowed))
}
