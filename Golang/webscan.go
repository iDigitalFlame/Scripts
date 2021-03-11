// webscan.go
// A web based scanning program that uses the "imgscan" linux binary to scan remotely.
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
	"errors"
	"flag"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"sync/atomic"
	"syscall"
	"time"
)

const (
	usage = `Web Scanner and File Host

Usage:
  -a [args]    Scan binary arguments.
  -l [address] Address to listen on.
  -b [url]     URL to use as the base web URL path.
  -d [dir]     Directory to save scans to.
  -e [binary]  Binary to use for scanning.

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
	footer = `</div></html>`
	script = `
<script type="text/javascript">setTimeout(function(){document.location=document.location},3000);</script>
<div id="wait">Please wait while your document is scanned..</div><div>`
	header = `
<html><head><title>Web Scanner</title></head>
<style type="text/css">h3{margin:0}#wait{text-align:center}
a,a:visited,a:hover{color:#000}a:hover{text-decoration:underline}
#newscan{font-size:16pt;margin:0 0 10px 0;text-align:center}
body{padding:10px 0 0 0;font-size:12pt;font-family:Arial;background:#9b9b9b;margin: 0 10% 0 10%}
#list{width:90%%;padding:8px;color:#000;text-align:center;border-radius:8px;background:#FFF;margin:0 auto}
#newscan a{width:75%%;padding:5px;display:block;border-radius:5px;background:#eb4504;margin:0 auto 0 auto;text-decoration:none;border:1px solid #eb4504}
</style><body>`
	format  = `150401022006`
	timeout = time.Duration(60) * time.Second
)

type job struct {
	ctx     context.Context
	File    *os.File
	Process *exec.Cmd
	cancel  context.CancelFunc
	Path    string
	Done    uint32
}

// Scanner is a struct that represents a Web Scanner instance. This struct takes the place of a http.Server.
type Scanner struct {
	URL  string
	Dir  string
	Jobs map[string]*job
	Args []string

	ctx    context.Context
	dir    http.Handler
	cancel context.CancelFunc
	http.Server
}

func main() {
	var (
		u, d, b, l, a string
		args          = flag.NewFlagSet("Files Pruner", flag.ExitOnError)
	)

	args.Usage = func() {
		os.Stdout.WriteString(usage)
		os.Exit(2)
	}
	args.StringVar(&a, "a", "", "Scan binary arguments.")
	args.StringVar(&l, "l", "0.0.0.0:80", "Address to listen on.")
	args.StringVar(&u, "b", "", "URL to use as the base web URL path.")
	args.StringVar(&d, "d", "/tmp/scans/", "Directory to save scans to.")
	args.StringVar(&b, "e", "/usr/bin/scanimage", "Binary to use for scanning.")

	if err := args.Parse(os.Args[1:]); err != nil {
		os.Stderr.WriteString("Error: " + err.Error() + "\n")
		os.Exit(1)
	}

	s, err := NewScanner(d, u, l, b, strings.Split(a, " ")...)
	if err != nil {
		os.Stderr.WriteString("Error: " + err.Error() + "\n")
		os.Exit(1)
	}

	if err := s.Listen(); err != nil {
		os.Stderr.WriteString("Error: " + err.Error() + "\n")
		os.Exit(1)
	}
}
func (j *job) process() {
	err := j.Process.Run()
	j.File.Close()
	j.cancel()
	if err != nil {
		os.Stderr.WriteString("Error occurred when running scan: " + err.Error() + "!\n")
		atomic.StoreUint32(&j.Done, 2)
		return
	}
	atomic.StoreUint32(&j.Done, 1)
}

// Listen starts the WebScanner and will block until a OS signal is received. This function will also close
// the server when it completes and will return any errors that occur during closing or starting the listening thread.
func (s *Scanner) Listen() error {
	var (
		l   = make(chan os.Signal, 1)
		err error
	)
	signal.Notify(l, syscall.SIGINT, syscall.SIGTERM, syscall.SIGQUIT)
	go func(e *error, x context.CancelFunc) {
		*e = s.Server.ListenAndServe()
		x()
	}(&err, s.cancel)
	select {
	case <-l:
	case <-s.ctx.Done():
	}
	signal.Stop(l)
	close(l)
	s.Server.Shutdown(s.ctx)
	s.Server.Close()
	s.cancel()
	return err
}
func (s *Scanner) context(_ net.Listener) context.Context {
	return s.ctx
}
func (s *Scanner) serve(w http.ResponseWriter, r *http.Request) {
	var (
		i, n  = r.URL.Query().Get("job"), r.URL.Query().Get("scan")
		j, ok = s.Jobs[i]
	)
	if len(i) > 0 && ok {
		if atomic.LoadUint32(&j.Done) == 0 {
			w.Write([]byte(header))
			w.Write([]byte(script))
			w.Write([]byte(footer))
			return
		}
		delete(s.Jobs, i)
		if atomic.LoadUint32(&j.Done) == 2 {
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			return
		}
		http.Redirect(w, r, s.URL+"/"+j.Path, http.StatusTemporaryRedirect)
		return
	}
	if len(n) > 0 {
		var (
			j   = &job{Path: "scan-" + time.Now().Format(format) + ".jpg"}
			err error
		)
		if j.File, err = os.Create(filepath.Join(s.Dir, j.Path)); err != nil {
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
			os.Stderr.WriteString("Error occurred when attempting to scan: " + err.Error() + "!\n")
			return
		}
		j.ctx, j.cancel = context.WithTimeout(s.ctx, timeout)
		j.Process = exec.CommandContext(j.ctx, s.Args[0])
		j.Process.Args, j.Process.Stdout = s.Args, j.File
		s.Jobs[n] = j
		go j.process()
		http.Redirect(w, r, s.URL+"/?job="+n, http.StatusTemporaryRedirect)
		return
	}
	if len(r.URL.Path) <= 1 {
		w.Write([]byte(header))
		w.Write([]byte(
			`<div id="newscan"><a href="` + s.URL + `/?scan=do" target="_blank">Start a new Scan</a></div><div id="list"><h3>Previous Scans</h3>`,
		))
		s.dir.ServeHTTP(w, r)
		w.Write([]byte(footer))
		return
	}
	s.dir.ServeHTTP(w, r)
}

// NewScanner creates a new WebScanner instance using the specified parameters.
func NewScanner(dir, url, bind, bin string, args ...string) (*Scanner, error) {
	x, err := exec.LookPath(bin)
	if err != nil {
		return nil, errors.New(`scan binary "` + bin + `" does not exist: ` + err.Error())
	}
	i, err := os.Stat(dir)
	if err == nil && !i.IsDir() {
		return nil, errors.New(`path "` + dir + `" is not a directory`)
	}
	if err != nil {
		if err := os.Mkdir(dir, 0750); err != nil {
			return nil, errors.New(`could not create directory "` + dir + `": ` + err.Error())
		}
	}
	s := &Scanner{
		dir:  http.FileServer(http.Dir(dir)),
		Dir:  dir,
		URL:  url,
		Jobs: make(map[string]*job),
		Args: []string{x},
		Server: http.Server{
			Addr:    bind,
			Handler: new(http.ServeMux),
		},
	}
	if len(args) > 0 {
		s.Args = append(s.Args, args...)
	}
	s.Server.BaseContext = s.context
	s.ctx, s.cancel = context.WithCancel(context.Background())
	s.Server.ReadTimeout, s.Server.IdleTimeout = timeout, timeout
	s.Server.WriteTimeout, s.Server.ReadHeaderTimeout = s.Server.ReadTimeout, s.Server.ReadTimeout
	s.Server.Handler.(*http.ServeMux).HandleFunc("/", s.serve)
	return s, nil
}
