// Copyright (C) 2025 - 2026 iDigitalFlame
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
#![cfg(target_os = "linux")]

extern crate core;
extern crate libc;
extern crate std;

use core::ffi::CStr;
use core::mem::{drop, transmute};
use core::option::Option::{self, None, Some};
use core::ptr::{copy_nonoverlapping, null_mut};
use core::result::Result::{self, Err, Ok};
use core::sync::atomic::{AtomicPtr, AtomicU32, Ordering};
use std::eprintln;
use std::ffi::OsStr;
use std::path::Path;
use std::process::exit;
use std::vec::Vec;

use libc::{O_CREAT, O_WRONLY, close, dup2, execv, geteuid, getgrnam_r, getuid, group, open, setgid, setgroups, setuid};

const GID_MIN: u32 = 9_900u32;
const GID_MAX: u32 = 9_910u32;

const NULL: &str = "/dev/null\0";

static ARGC: AtomicU32 = AtomicU32::new(0u32);
static ARGV: AtomicPtr<*const i8> = AtomicPtr::new(null_mut());

#[used]
#[unsafe(link_section = ".init_array.00099")]
static ARGV_INIT_ARRAY: extern "C" fn(u32, *const *const u8, *const *const u8) = {
    extern "C" fn wrapper(c: u32, v: *const *const u8, _e: *const *const u8) {
        ARGC.store(c, Ordering::Relaxed);
        ARGV.store(v as _, Ordering::Relaxed);
    }
    wrapper
};

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
            return Err(Error::Lib($n));
        }
    };
}

enum Error<'a> {
    NoArgs,
    NoRoot,
    NoGroups,
    NoSetUID,
    NoFullpath,
    Group(i32),
    GroupNotFound(&'a str),
    GroupNotAllowed(&'a str),
    FileNotExist(&'a CStr),
    Lib(&'a str),
}

impl Error<'_> {
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
            Error::Group(e) => {
                eprintln!("error: group cannot be found (error {e})!");
                exit(*e)
            },
            Error::GroupNotFound(v) => {
                eprintln!("error: group {v:?} was not found!");
                exit(1)
            },
            Error::GroupNotAllowed(v) => {
                eprintln!("error: group {v:?} access denied!");
                exit(1)
            },
            Error::FileNotExist(v) => {
                eprintln!("error: file {v:?} does not exist!");
                exit(1)
            },
            Error::Lib(v) => {
                eprintln!("error: {} failed! ({})", v, unsafe {
                    &*libc::__errno_location()
                });
                exit(1);
            },
        }
    }
}

fn main() {
    let (a, f, n) = check!(setup());
    // Contain most of the allocating calls in 'setup' so they'll be free'd
    // regardless of the outcome of the exec call.
    exec(&f, a, n);
}

#[inline]
fn exec(v: &CStr, a: *const *const i8, n: bool) -> ! {
    // If 'n' is true, we connect stdout/stderr to /dev/null.
    if n {
        // We don't error on this as it really doesn't matter if it fails.
        let f = unsafe { open(NULL.as_ptr() as _, O_CREAT | O_WRONLY, 0o0666) };
        if f != -1 {
            unsafe {
                dup2(f, 1);
                dup2(f, 2);
                close(f);
            }
        }
    }
    let _ = unsafe { execv(v.as_ptr(), a) };
    // The code below never will run unless an error occurs.
    eprintln!("error: execv failed! ({})", unsafe {
        &*libc::__errno_location()
    });
    exit(2);
}
fn groups<'a>(v: &'a CStr) -> Result<Vec<u32>, Error<'a>> {
    // 'b' stores the backing buffer that will be free'd once we're done.
    // 's' stores a copy of our name buffer for reading, so we don't modify
    //     the initial args block.
    let (mut g, mut b) = (Vec::new(), Vec::new());
    let mut s = Vec::with_capacity(v.to_bytes().len() + 1);
    s.resize(s.capacity(), 0); // Resize it to the max size of 'v' + NULL.
    for i in v.to_bytes().split(|v| *v == b':') {
        if i.is_empty() {
            continue; // Ignore empty names
        }
        unsafe {
            copy_nonoverlapping(i.as_ptr(), s.as_mut_ptr(), i.len());
            *s.get_unchecked_mut(i.len()) = 0u8; // NULL
        };
        match gid(&mut b, &s)? {
            Some(0..GID_MIN | GID_MAX..) => return Err(Error::GroupNotAllowed(unsafe { transmute(i) })),
            Some(r) if g.contains(&r) => (),
            Some(r) => g.push(r),
            None => return Err(Error::GroupNotFound(unsafe { transmute(i) })),
        }
    }
    if g.is_empty() { Err(Error::NoGroups) } else { Ok(g) }
}
fn gid<'a>(b: &mut Vec<u8>, n: &[u8]) -> Result<Option<u32>, Error<'a>> {
    let mut g = group {
        gr_gid:    0u32,
        gr_mem:    null_mut(),
        gr_name:   null_mut(),
        gr_passwd: null_mut(),
    };
    let mut i = 256usize;
    loop {
        b.resize(i, 0);
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
            e => break Err(Error::Group(e)),
        }
    }
}
fn setup<'a>() -> Result<(*const *const i8, &'a CStr, bool), Error<'a>> {
    let n = ARGC.load(Ordering::Relaxed);
    if n < 3 {
        return Err(Error::NoArgs);
    }
    let u = unsafe { getuid() };
    match (u == 0, unsafe { geteuid() != 0 }) {
        (true, _) => return Err(Error::NoRoot),
        (_, true) => return Err(Error::NoSetUID),
        _ => (),
    }
    let s = ARGV.load(Ordering::Relaxed);
    // Check if first arg (arg[0]) starts with '/'. We don't need to read
    // the full string, just the first char.
    if unsafe { *s.read() as u8 } != b'/' {
        return Err(Error::NoFullpath);
    }
    let f = unsafe { CStr::from_ptr(s.add(2).read()) };
    if !Path::new(unsafe { OsStr::from_encoded_bytes_unchecked(f.to_bytes()) }).is_file() {
        return Err(Error::FileNotExist(f));
    }
    let g = groups(unsafe { CStr::from_ptr(s.add(1).read()) })?;
    // SAFETY: We return an error if the list is empty, 'g' will always be
    //         at least size of 1 here.
    check!("setgid", setgid(*g.first().unwrap_unchecked()));
    if g.len() > 1 {
        // Set Supplimentry Groups (if supplied)
        check!("setgroups", setgroups(g.len(), g.as_ptr()));
    }
    check!("setuid", setuid(u));
    drop(g); // 'g' should be dropped here
    Ok(unsafe {
        (
            s.add(2),
            f,
            CStr::from_ptr(s.read()).to_bytes().last().map_or(false, |&v| v == b'n'),
        )
    })
}
