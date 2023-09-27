# AppXPrune

__Windows Only__

Removes a list of defined AppX Packages.

Usage

```shell
appx_prune.exe [package_targets_file]
```

The argument `package_targets_file` is optional and will default to `packages.txt` in the
same directory as the binary file. The file contents are just a newline-separated list
of AppX Package names (or wildcards) to be removed.

The application will use PowerShell to remove each in order.

## Building

```shell
env GOOS=windows go build -o appx_prune.exe -ldflags '-w -s -H=windowsgui' -trimpath main.go
```
