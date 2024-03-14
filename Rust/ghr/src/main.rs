// Copyright (C) 2024 iDigitalFlame
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

// Group Helper (but in Rust!)
//  Takes command line args and concats them directly, so we can avoid the
//  sg <group> "cmd" boilerplate.
//
//  Also fixes xdg-open calls (since it just appends to the end).

extern crate libc;

use core::iter::once;
use core::ptr;
use std::env::args;
use std::ffi::CString;
use std::io::{self, Error, ErrorKind};
use std::path;
use std::process::exit;

use libc::{execv, geteuid, getgrnam_r, getuid, group, setgid, setuid};

fn main() {
    let a = args().collect::<Vec<String>>();
    if !a[0].starts_with(|v| v == '/') {
        eprintln!("error: fullpath must be used!");
        exit(1)
    }
    if a.len() <= 2 {
        eprintln!("ghr <group> <command> [args..]");
        exit(2)
    }

    let u = unsafe { getuid() };
    match (u == 0, unsafe { geteuid() != 0 }) {
        (true, ..) => {
            eprintln!("error: cannot be ran as root!");
            exit(1)
        },
        (_, true) => {
            eprintln!("error: binary lacks SUID!");
            exit(1)
        },
        (..) => (),
    }

    if !path::Path::new(&a[2]).is_file() {
        eprintln!("error: file \"{}\" does not exist!", a[2]);
        exit(1)
    }

    let g = match group_gid(&a[1]) {
        Ok(i) => i,
        Err(_) => {
            eprintln!("error: group \"{}\" does not exist!", a[1]);
            exit(1)
        },
    };

    if unsafe { setgid(g) } != 0 {
        eprintln!("error: setgid failed!");
        exit(1);
    }
    if unsafe { setuid(u) } != 0 {
        eprintln!("error: setgid failed!");
        exit(1);
    }

    let mut b = Vec::new();
    b.push(match CString::new(a[2].as_bytes()) {
        Ok(r) => r,
        Err(_) => {
            eprintln!("error: cannot convert string \"{}\"!", a[2]);
            exit(1)
        },
    });
    if a.len() > 2 {
        b.extend(a[3..].iter().map(|i| match CString::new(i.as_bytes()) {
            Ok(r) => r,
            Err(_) => {
                eprintln!("error: cannot convert string \"{}\"!", i);
                exit(1)
            },
        }));
    }

    let x: Vec<*const i8> = b.iter().map(|i| i.as_ptr()).chain(once(ptr::null())).collect();
    if unsafe { execv(b[0].as_ptr(), x.as_ptr()) } != 0 {
        eprintln!("error: execv failed!");
        exit(1)
    }
}
fn group_gid(name: &str) -> io::Result<u32> {
    let mut b: Vec<u8> = Vec::with_capacity(256);
    let mut g = group {
        gr_gid:    0,
        gr_mem:    ptr::null_mut(),
        gr_name:   ptr::null_mut(),
        gr_passwd: ptr::null_mut(),
    };
    let (mut o, mut n) = (ptr::null_mut(), 256);
    loop {
        let r = unsafe {
            getgrnam_r(
                name.as_ptr() as *const i8,
                &mut g,
                b.as_mut_ptr() as *mut i8,
                n,
                &mut o,
            )
        };
        match r {
            0x22 => {
                n *= 2;
                b.resize(n, 0);
                continue;
            },
            0 => {
                return match unsafe { o.as_ref() } {
                    Some(z) => Ok(z.gr_gid),
                    None => Err(ErrorKind::NotFound.into()),
                }
            },
            _ => return Err(Error::last_os_error()),
        }
    }
}
