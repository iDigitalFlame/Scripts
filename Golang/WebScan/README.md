# WebScan

__Linux Only__

WebScan uses the `scanimage` binary to allow for scanning over the network using
a network device. This service runs a webserver that holds a very simple webapp that
scans documents into images for saving and review.

Usage

```text
webscan -a [args] -l [address] -b [url] -d [dir] -e [binary]
  -a [args]    Scan binary arguments.
  -l [address] Address to listen on.
  -b [url]     URL to use as the base web URL path.
  -d [dir]     Directory to save scans to.
  -e [binary]  Binary to use for scanning.
```

The `-e` argument defaults to `/usr/bin/scanimage` if not supplied or empty.

# Building

Any standard building procedures will work.

Basic example

```shell
go build -o motivate -trimpath -ldflags '-w -s' main.go
```
