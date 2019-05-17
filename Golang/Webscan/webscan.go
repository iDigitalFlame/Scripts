// webscan.go
// A web based scannng program that uses the "imgscan" linux binary to scan remotly.
// iDigitalFlame

package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path"
	"strings"
	"time"
)

const (
	scanHTMLPre = `
<html>
<head>
<title>WebScanner</title>
</head>
<style type="text/css">
body {
	padding: 10px 0 0 0;
	font-size: 12pt;
	font-family: Arial;
	background: #9b9b9b;
	margin: 0 10% 0 10%;
}
h3 {
	margin: 0;
}
#wait {
	text-align: center;
}
#list {
	width: 90%%;
	padding: 8px;
	color: #000000;
	text-align: center;
	border-radius: 8px;
	background: #FFFFFF;
	margin: 0 auto 0 auto;
}
a:hover {
	text-decoration: underline;
}
#newscan {
	font-size: 16pt;
	margin: 0 0 10px 0;
	text-align: center;
}
#newscan a {
	width: 75%%;
	padding: 5px;
	display: block;
	border-radius: 5px;
	background: #eb4504;
	margin: 0 auto 0 auto;
	text-decoration: none;
	border: 1px solid #eb4504;
}
a, a:visited, a:hover {
	color: #000000;
}
</style>
<body>`
	scanHTMLScan = `
<div id="newscan">
<a href="%s/?scan=do">Start a new Scan</a>
</div>
<div id="list"><h3>Previous Scans</h3>`
	scanHTMLPost = `</div></html>`
	scanHTMLWait = `<script type="text/javascript">
setTimeout(function(){document.location=document.location},3000);</script>
<div id="wait">Please wait while your document is scanned..</div><div>`
)

type webScanner struct {
	scanURL       string
	scanJobs      map[string]*webScanJob
	scanCommand   []string
	scanHandler   http.Handler
	scanDirectory string
}
type webScanJob struct {
	jobTime    time.Time
	jobFile    string
	jobDone    bool
	jobError   error
	jobCommand *exec.Cmd
}

func main() {
	scanParameters := flag.String("args", "", "Scan binary arguments.")
	scanURL := flag.String("url", "", "URL to use as the base URL.")
	scanListen := flag.String("listen", "0.0.0.0:80", "Address to listen on.")
	scanDirectory := flag.String("dir", "/tmp/scans/", "Directory to scan to.")
	scanBinary := flag.String("bin", "/usr/bin/scanimage", "Binary to use for scanning.")
	flag.Parse()
	c := []string{*scanBinary}
	if len(*scanParameters) > 0 {
		c = append(c, strings.Split(*scanParameters, " ")...)
	}
	http.Handle("/", NewWebScanner(*scanURL, *scanDirectory, c))
	log.Fatal(http.ListenAndServe(*scanListen, nil))
}

// NewWebScanner creates a new WebScanner handler instance to be using with
// Golang's http.Handle function.
func NewWebScanner(u, d string, c []string) http.Handler {
	if s, err := os.Stat(d); err != nil || !s.IsDir() {
		if err := os.Mkdir(d, 0750); err != nil {
			panic(fmt.Sprintf("Could not create temp directory \"%s\"! %s", d, err.Error()))
		}
	}
	return &webScanner{
		scanURL:       u,
		scanJobs:      make(map[string]*webScanJob),
		scanCommand:   c,
		scanHandler:   http.FileServer(http.Dir(d)),
		scanDirectory: d,
	}
}

// ServeHTTP is the exported function for the http.Handler interface.
func (s *webScanner) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	defer r.Body.Close()
	if q := r.URL.Query().Get("job"); len(q) > 0 {
		if j, ok := s.scanJobs[q]; ok {
			if j.jobDone {
				delete(s.scanJobs, q)
				if j.jobError != nil {
					w.WriteHeader(http.StatusInternalServerError)
					fmt.Fprintf(w, http.StatusText(http.StatusInternalServerError))
					fmt.Printf("Error occured when attempting to scan! (%s)", j.jobError.Error())
					return
				}
				http.Redirect(w, r, fmt.Sprintf("%s/%s", s.scanURL, j.jobFile), http.StatusTemporaryRedirect)
				return
			}
			fmt.Fprintf(w, scanHTMLPre)
			fmt.Fprintf(w, scanHTMLWait)
			fmt.Fprintf(w, scanHTMLPost)
			return
		}
	}
	if q := r.URL.Query().Get("scan"); len(q) > 0 {
		t := time.Now()
		n := fmt.Sprintf(
			"%d-%d-%d-%d-%d-%d", t.Month(), t.Day(), t.Year(), t.Hour(), t.Minute(), t.Second(),
		)
		j := &webScanJob{
			jobTime:    t,
			jobFile:    fmt.Sprintf("scan-%s.jpg", n),
			jobDone:    false,
			jobCommand: nil,
		}
		f, err := os.Create(path.Join(s.scanDirectory, j.jobFile))
		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			fmt.Fprintf(w, http.StatusText(http.StatusInternalServerError))
			fmt.Printf("Error occured when attempting to scan! (%s)", err.Error())
			return
		}
		if len(s.scanCommand) > 1 {
			j.jobCommand = exec.Command(s.scanCommand[0], s.scanCommand[1:]...)
		} else {
			j.jobCommand = exec.Command(s.scanCommand[0])
		}
		j.jobCommand.Stdout = f
		go func(k *webScanJob, o *os.File) {
			defer o.Close()
			if err := k.jobCommand.Run(); err != nil {
				k.jobError = err
			}
			k.jobDone = true
		}(j, f)
		s.scanJobs[n] = j
		http.Redirect(w, r, fmt.Sprintf("%s/?job=%s", s.scanURL, n), http.StatusTemporaryRedirect)
		return
	}
	l := r.URL.Path
	if !strings.HasPrefix(l, "/") {
		l = "/" + l
		r.URL.Path = l
	}
	if x, err := os.Stat(path.Join(s.scanDirectory, path.Clean(l))); err != nil || x.IsDir() {
		fmt.Fprintf(w, scanHTMLPre)
		fmt.Fprintf(w, scanHTMLScan, s.scanURL)
		s.scanHandler.ServeHTTP(w, r)
		fmt.Fprintf(w, scanHTMLPost)
	} else {
		s.scanHandler.ServeHTTP(w, r)
	}
}
