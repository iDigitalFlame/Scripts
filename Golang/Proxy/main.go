// Copyright (C) 2026iDigitalFlame
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
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/signal"
	"syscall"
	"time"
)

const usage = `Simple Reverse Proxy

Usage:
    proxy <backend_url> <listen_address>

Copyright (C) 2026 iDigitalFlame

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

func main() {
	if len(os.Args) < 3 {
		os.Stderr.WriteString(usage)
		os.Exit(2)
	}

	u, err := url.Parse(os.Args[1])
	if err != nil {
		os.Stderr.WriteString(`Invalid backend URL "` + os.Args[1] + `": ` + err.Error() + "\n")
		os.Exit(1)
	}

	var (
		b = os.Args[2]
		l net.Listener
	)
	if (b[0] == 'u' || b[0] == 'U') && (b[3] == 'x' || b[3] == 'X') {
		if l, err = net.Listen("unix", b[5:]); err != nil {
			os.Stderr.WriteString(`Failed to bind to UNIX socket "` + b[5:] + `": ` + err.Error() + "\n")
			os.Exit(1)
		}
	} else {
		if l, err = net.Listen("tcp", b); err != nil {
			os.Stderr.WriteString(`Failed to bind to "` + b + `": ` + err.Error() + "\n")
			os.Exit(1)
		}
	}

	s := &http.Server{Handler: httputil.NewSingleHostReverseProxy(u)}
	go wait(s)

	err = s.Serve(l)
	if l.Close(); err != nil && err != http.ErrServerClosed {
		os.Stderr.WriteString(`Server runtime failure: ` + err.Error() + "\n")
		os.Exit(1)
	}
}
func wait(s *http.Server) {
	v := make(chan os.Signal, 1)
	signal.Notify(v, syscall.SIGINT, syscall.SIGTERM, syscall.SIGQUIT)
	<-v
	close(v)
	x, f := context.WithTimeout(context.Background(), time.Second*5)
	s.Shutdown(x)
	f()
}
