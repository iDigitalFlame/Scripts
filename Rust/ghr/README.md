# Group Helper (Rust) (GHR)

__Linux Only__

The Group Helper binary is one component that is commonly used in [spaceport](https://github.com/iDigitalFlame/Spaceport)
to switch to a group to help "containerize" applications or give them separate permissions.

This is mostly used for firewall seperation using the GID meta in `nftables` to
allow/deny network access. This provides a switch-able method over outright denying
using a LSM like AppArmor.

## What is GHR?

Similar to how the `sg` command works, the Group Helper takes a group name, _(or names_,
_see the multi-group section)_, and a command line _(doesn't need to be escaped)_
and will `execv` the command __AFTER__ switching the GID to the supplied group(s).

This can be used to change the group that runs a command before executing.

In order to prevent any misuse, the GHR binary __MUST__ be executed using it's
__absolute/full path value__ and it will __NOT__ search `PATH` for the binary it's asked
to execute, it must also be supplied using it's __absolute/full path value__.

Example of running GHR:

```shell
/usr/bin/ghr firewall-web /usr/bin/firefox
```

This example executes `/usr/bin/firefox` under the context of the calling user, but
uses the `firewall-web` group as the primary group used.

## How does it work?

First, the binary must be installed with the SETUID bit enabled _(chmod 4755)_
as it will launch as root, parse the group information given and then set the
UID to the caller, then setup the GID _(and any supplementary GIDs)_.

Once complete the command will be executed as it's given, no parsing done.
 _(It literally just moves the args pointer along after it consumes it's arguments)._

## Security

GHR does __NOT__ check if the user belongs or has access to these groups. However
GHR will not assign a group unless it's GID tis between the compiled-in configuration
values `GID_MIN` and`GID_MAX` values. _(It's `[GID_MIN..GID_MAX)`, inclusive of_
_`GID_MIN` and exclusive of `GID_MAX`.)_ Any groups outside this range will cause
GHR to exit with an error message.

To change these values, you must edit the values in `main.rs` and recompile.

## Multi-Groups

Users in Linux have a primary group assigned but can also have a list of supplementary
groups in addition to their primary. Multiple groups may be specified by following
the first group with a colon (`:`) and then supplying the additional groups,
each additional name split with a colon (`:`).

An example of a multi-group GHR command:

```shell
/usr/bin/ghr firewall-web:firewall-voice:firewall-rdp /usr/bin/nmap
```

This example executes `/usr/bin/nmap` under the context of the calling user, but
uses the `firewall-web` group as the primary group and adds the `firewall-voice`
and `firewall-rdp` groups as the supplementary groups.

Using the command:

```shell
/usr/bin/ghr firewall-web:firewall-voice:firewall-rdp /usr/bin/id
```

Would print something similar to:

```shell
uid=5000(dij) gid=9005(firewall-web) groups=9005(firewall-web),9006(firewall-voice),9007(firewall-rdp)
```

The max amount of groups that can supplied is configured using `GROUPS_MAX` compiled-in
configuration value, which is `64` by default. To change this value, you must edit
the value in `main.rs` and recompile.

## GHN

`GHR` can be symlinked as `GHN` to add an additional way to execute GHR.

```shell
ln -s /usr/bin/ghr /usr/bin/ghn
```

If GHR detects it's called as GHN, it will set it's STDOUT/STDERR FDs to the `/dev/null`
device before calling `execv`. This can be used to silence the output of the
executed program automatically.
