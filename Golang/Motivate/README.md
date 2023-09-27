# Motivate

Displays quotes and stuff. Can also be used to acquire more (via Interwebs).

Usage

```text
motivate -f <db> -a <quote> -n

  -f <db>    Quotes file path.
  -a <quote> Add a quote to the quotes file.
  -n         Download a quote from the Internet.
```

The db file defaults to `$HOME/.config/quotes.db` if not supplied.

## Building

Any standard building procedures will work.

Basic example

```shell
go build -o motivate -trimpath -ldflags '-w -s' main.go
```
