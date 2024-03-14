# Group Helper (Rust)

__Linux Only__

The Group Helper binary is one component that is commonly used in [spaceport](https://github.com/iDigitalFlame/Spaceport)
to switch to a group to help "containerize" applications or give them separate permissions.

While `sg` usually works for most commands, Group Helper allows for var args for
commands and will take anything after the Group Name as the command line.

This binary needs the ability to switch groups, which may require the SUID bit
for some deployments.
