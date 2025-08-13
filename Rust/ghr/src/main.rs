// Copyright (C) 2025 iDigitalFlame
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

#![no_implicit_prelude]

extern crate core;
extern crate libc;
extern crate std;

use core::iter::{ExactSizeIterator, Iterator};
use core::ptr::{null, null_mut};
use core::result::Result::{self, Err, Ok};
use std::env::{Args, args};
use std::eprintln;
use std::ffi::CString;
use std::path::Path;
use std::process::exit;
use std::string::String;
use std::vec::Vec;

use libc::{execv, geteuid, getgrnam_r, getuid, group, setgid, setuid};

enum Error {
    NoArgs,
    NoFullpath,
    FileInvalid,
    FileNotExist(String),
    GroupInvalid,
    GroupOSError(i32),
    GroupNotFound(CString),
}

impl Error {
    #[inline]
    fn exit(&self) -> ! {
        match self {
            Error::NoArgs => {
                eprintln!("ghr <group> <command> [args..]");
                exit(2)
            },
            Error::NoFullpath => {
                eprintln!("error: fullpath must be used!");
                exit(1)
            },
            Error::FileInvalid => {
                eprintln!("error: filepath is invalid!");
                exit(1)
            },
            Error::GroupInvalid => {
                eprintln!("error: group name is invalid!");
                exit(1)
            },
            Error::GroupOSError(e) => {
                eprintln!("error: group cannot be found (error {e})!");
                exit(*e)
            },
            Error::FileNotExist(v) => {
                eprintln!("error: file \"{v}\" does not exist!");
                exit(1)
            },
            Error::GroupNotFound(v) => {
                eprintln!("error: group {v:?} was not found!");
                exit(1)
            },
        }
    }
}

fn main() {
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

    let mut a = args();
    let g = match find_gid(&mut a) {
        Err(e) => e.exit(),
        Ok(v) => v,
    };
    let p = match find_file(&mut a) {
        Err(e) => e.exit(),
        Ok(v) => v,
    };

    if unsafe { setgid(g) } != 0 {
        eprintln!("error: setgid failed!");
        exit(1);
    }
    if unsafe { setuid(u) } != 0 {
        eprintln!("error: setgid failed!");
        exit(1);
    }

    let (mut b, mut x) = (Vec::new(), Vec::new());
    x.push(p.as_ptr());

    for i in a {
        let v = match CString::new(i) {
            Ok(v) => v,
            Err(_) => {
                eprintln!("error: filepath is invalid!");
                exit(1)
            },
        };
        x.push(v.as_ptr());
        b.push(v);
    }
    x.push(null());

    if unsafe { execv(p.as_ptr(), x.as_ptr()) } != 0 {
        eprintln!("error: execv failed!");
        exit(1)
    }
}
fn find_gid(a: &mut Args) -> Result<u32, Error> {
    if a.len() <= 2 {
        return Err(Error::NoArgs);
    }
    // Check if first arg (arg[0]) starts with '/'
    //
    // SAFETY: Cannot be None as the 'len' check passed.
    if unsafe { a.next().unwrap_unchecked() }
        .as_bytes()
        .first()
        .is_none_or(|v| *v != b'/')
    {
        return Err(Error::NoFullpath);
    }
    // SAFETY: Cannot be None as the 'len' check passed.
    let n = CString::new(unsafe { a.next().unwrap_unchecked() }).map_err(|_| Error::GroupInvalid)?;
    let mut g = group {
        gr_gid:    0u32,
        gr_mem:    null_mut(),
        gr_name:   null_mut(),
        gr_passwd: null_mut(),
    };
    let (mut b, mut i) = (Vec::with_capacity(256usize), 256usize);
    loop {
        b.resize(i, 0u8);
        let mut o = null_mut();
        let r = unsafe {
            getgrnam_r(
                n.as_ptr() as *const i8,
                &mut g,
                b.as_mut_ptr() as *mut i8,
                i,
                &mut o,
            )
        };
        match r {
            0x22 => i *= 2,
            0x0 if o.is_null() => break Err(Error::GroupNotFound(n)),
            0 => break Ok(g.gr_gid),
            e => break Err(Error::GroupOSError(e)),
        }
    }
}
#[inline]
fn find_file(a: &mut Args) -> Result<CString, Error> {
    // SAFETY: Cannot be None as the 'len' check passed.
    let v = unsafe { a.next().unwrap_unchecked() };
    if !Path::new(&v).is_file() {
        return Err(Error::FileNotExist(v));
    }
    CString::new(v).map_err(|_| Error::FileInvalid)
}
