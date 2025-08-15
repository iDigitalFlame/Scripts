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
#![feature(never_type)]

extern crate core;
extern crate libc;
extern crate std;

use core::ffi::CStr;
use core::iter::{ExactSizeIterator, Iterator};
use core::option::Option::{self, None, Some};
use core::ptr::{null, null_mut};
use core::result::Result::{self, Err, Ok};
use std::env::{ArgsOs, args_os};
use std::eprintln;
use std::ffi::{CString, OsString};
use std::path::Path;
use std::process::exit;
use std::vec::Vec;

use libc::{execv, geteuid, getgrnam_r, getuid, group, setgid, setgroups, setuid};

const GID_MIN: u32 = 1_000u32;
const GID_MAX: u32 = 9_999u32;

macro_rules! check {
    ($x:expr) => {
        match $x {
            Ok(v) => v,
            Err(e) => e.exit(),
        }
    };
    ($n:expr, $x:expr) => {
        let _e = unsafe { $x };
        if _e != 0 {
            eprintln!("error: {} failed! ({})", $n, unsafe { &*libc::__errno_location() });
            exit(1);
        }
    };
}

enum Error {
    NoArgs,
    NoRoot,
    NoAccess(CString),
    NoGroups,
    NoSetUID,
    NoFullpath,
    FileInvalid,
    FileArgInvalid,
    FileNotExist(OsString),
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
            Error::NoRoot => {
                eprintln!("error: cannot be ran as root!");
                exit(1)
            },
            Error::NoGroups => {
                eprintln!("error: no valid groups!");
                exit(1)
            },
            Error::NoSetUID => {
                eprintln!("error: binary lacks SUID!");
                exit(1)
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
                eprintln!("error: group string is invalid!");
                exit(1)
            },
            Error::FileArgInvalid => {
                eprintln!("error: exec argument is invalid!");
                exit(1)
            },
            Error::GroupOSError(e) => {
                eprintln!("error: group cannot be found (error {e})!");
                exit(*e)
            },
            Error::NoAccess(v) => {
                eprintln!("error: group {v:?} access denied!");
                exit(1)
            },
            Error::FileNotExist(v) => {
                eprintln!("error: file {v:?} does not exist!");
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
    let (mut a, u) = check!(setup());
    let (g, e) = (check!(groups(&mut a)), check!(file(&mut a)));
    check!("setgid", setgid(g[0]));
    if g.len() > 1 {
        // Supplimentry Groups
        check!("setgroups", setgroups(g.len(), g.as_ptr()));
    }
    check!("setuid", setuid(u));
    check!(exec(e, a));
}
fn setup() -> Result<(ArgsOs, u32), Error> {
    let mut a = args_os();
    if a.len() <= 2 {
        return Err(Error::NoArgs);
    }
    let u = unsafe { getuid() };
    match (u == 0, unsafe { geteuid() != 0 }) {
        (true, _) => return Err(Error::NoRoot),
        (_, true) => return Err(Error::NoSetUID),
        _ => (),
    }
    // Check if first arg (arg[0]) starts with '/'
    //
    // SAFETY: Cannot be None as the 'len' check passed.
    if unsafe { a.next().unwrap_unchecked() }
        .as_encoded_bytes()
        .first()
        .is_none_or(|v| *v != b'/')
    {
        return Err(Error::NoFullpath);
    }
    Ok((a, u))
}
#[inline]
fn file(a: &mut ArgsOs) -> Result<CString, Error> {
    // SAFETY: Cannot be None as the 'len' check passed.
    let v = unsafe { a.next().unwrap_unchecked() };
    if !Path::new(&v).is_file() {
        return Err(Error::FileNotExist(v));
    }
    CString::new(v.as_encoded_bytes()).map_err(|_| Error::FileInvalid)
}
fn exec(e: CString, a: ArgsOs) -> Result<!, Error> {
    let (mut b, mut c) = (
        Vec::with_capacity(a.len() + 1),
        Vec::with_capacity(a.len() + 1),
    );
    c.push(e.as_ptr());
    for i in a {
        let v = CString::new(i.as_encoded_bytes()).map_err(|_| Error::FileArgInvalid)?;
        c.push(v.as_ptr());
        b.push(v);
    }
    // Add Null ending.
    c.push(null());
    check!("execv", execv(e.as_ptr(), c.as_ptr()));
    // Never will run
    exit(0)
}
fn groups(a: &mut ArgsOs) -> Result<Vec<u32>, Error> {
    // SAFETY: Cannot be None as the 'len' check passed.
    let n = unsafe { a.next().unwrap_unchecked() };
    let (mut g, mut b) = (Vec::new(), Vec::new());
    for i in n.as_encoded_bytes().split(|v| *v == b':') {
        let v = CString::new(i).map_err(|_| Error::GroupInvalid)?;
        match gid(&mut b, &v)? {
            Some(0..GID_MIN | GID_MAX..) => return Err(Error::NoAccess(v)),
            Some(r) if g.contains(&r) => (),
            Some(r) => g.push(r),
            None => return Err(Error::GroupNotFound(v)),
        }
    }
    if g.is_empty() { Err(Error::NoGroups) } else { Ok(g) }
}
fn gid(b: &mut Vec<u8>, n: &CStr) -> Result<Option<u32>, Error> {
    let mut g = group {
        gr_gid:    0u32,
        gr_mem:    null_mut(),
        gr_name:   null_mut(),
        gr_passwd: null_mut(),
    };
    let mut i = 256usize;
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
            0x0 => break Ok(unsafe { o.as_ref() }.map(|v| v.gr_gid)),
            e => break Err(Error::GroupOSError(e)),
        }
    }
}
