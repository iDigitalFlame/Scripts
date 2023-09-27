# File Pruner

__Linux Only__

Automatically prunes files based on their timestamps. Can be configured with a "filter"
string that will only consider files that contain the provied string.

Usage

```text
fileprune -d <dir> -f [filter] -t [days]

  -d <dir>    Directory to scan.
  -f [filter] Filter scan to files that contain this string.
  -t [days]   Day limit for when file is deleted, defaults to 10.
```

# Building

Any standard building procedures will work.

Basic example

```shell
go build -o webscan -trimpath -ldflags '-w -s' main.go
```
