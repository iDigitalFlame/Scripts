# Group Helper

__Linux Only__

__May need to be configured before compiling__

*Deprecated in favor of [Ghr](https://github.com/iDigitalFlame/Scripts/tree/main/Rust/ghr)*

The Group Helper binary is one component that is commonly used in [spaceport](https://github.com/iDigitalFlame/Spaceport)
to switch to a group to help "containerize" applications or give them separate permissions.

While `sg` usually works for most commands, Group Helper allows for var args for
commands and will take anything after the Group Name as the command line.

Currently the source contains the default Group mappings (name => group ID)

```go
var groups = map[string]int{
   "db":    9905,
   "web":   9901,
   "ssh":   9902,
   "ftp":   9904,
   "ctl":   9906,
   "all":   9907,
   "mail":  9003,
   "icmp":  9900,
   "voice": 9908,
}
```

These may need to be changed based on your configuration and can take more groups
if needed.

This binary needs the ability to switch groups, which may require the SUID bit
for some deployments.

## Building

Any standard building procedures will work.

Basic example

```shell
go build -o gh -trimpath -ldflags '-w -s' main.go
```
