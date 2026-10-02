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

// AppXPruner (but in Rust!)
//  Removes Windows 10/11 Appx Packages based on a list of entries.
//
// This is Windows specific application
//
// Usage
// ```shell
// appxprune.exe [package_targets_file]
// ```
//
// The argument `package_targets_file` is optional and will default to
// `packages.txt` in the same directory as the binary file. The file contents
// are just a newline-separated list of AppX Package names (or wildcards) to be
// removed.
//
// The application will use PowerShell to remove each in order. Each is removed
// in order but is not waited on, so many can be removed in a smaller timeframe.
//
// Building
//
// ```shell
// cargo build --target x86_64-pc-windows-gnu --release
//```

#![no_implicit_prelude]
#![cfg(target_os = "windows")]
#![windows_subsystem = "windows"]

extern crate alloc;
extern crate core;
extern crate std;

use alloc::string::{String, ToString};
use alloc::vec::Vec;
use core::convert::From;
use core::default::Default;
use core::iter::Iterator;
use core::marker::PhantomData;
use core::mem::size_of;
use core::option::Option::{self, None, Some};
use core::result::Result::{self, Err, Ok};
use core::slice::from_raw_parts;
use std::env::{args_os, current_dir, split_paths, var_os};
use std::eprintln;
use std::ffi::OsString;
use std::fs::{File, OpenOptions, metadata};
use std::io::{BufRead, BufReader};
use std::os::windows::ffi::OsStrExt;
use std::path::PathBuf;

#[repr(C)]
struct ProcInfo {
    proc:   usize,
    thread: usize,
    pid:    u32,
    tid:    u32,
}
struct Reader<'a> {
    r:    BufReader<File>,
    buf:  Vec<u16>,
    line: String,
    _p:   PhantomData<&'a ()>,
}
#[repr(C)]
struct ProcStartup {
    size:   u32,
    pad0:   [usize; 3],
    pad1:   [u32; 8],
    window: u16,
    pad2:   u16,
    pad3:   [usize; 4],
}

type Error = String;

const ERROR_NO_PWSH: &str = "no powershell found";

const DEFAULT_EXE: &str = "powershell.exe";
const DEFAULT_PATH: &str = r"System32\WindowsPowerShell\v1.0\powershell.exe";
const DEFAULT_CONFIG: &str = "packages.txt";
const DEFAULT_WINDIR: &str = r"C:\Windows";

static GET: [u16; 23] = [
    0x47, 0x65, 0x74, 0x2D, 0x41, 0x70, 0x70, 0x78, 0x50, 0x61, 0x63, 0x6B, 0x61, 0x67, 0x65, 0x20, 0x2D, 0x4E, 0x61, 0x6D, 0x65, 0x20, 0x27,
]; // `Get-AppPackage -Name '`
static PIPE: [u16; 4] = [0x27, 0x20, 0x7C, 0x20]; // `' | `
static REMOVE: [u16; 18] = [
    0x52, 0x65, 0x6D, 0x6F, 0x76, 0x65, 0x2D, 0x41, 0x70, 0x70, 0x78, 0x50, 0x61, 0x63, 0x6B, 0x61, 0x67, 0x65,
]; // `Remove-AppPackage`
static COMMAND: [u16; 46] = [
    0x20, 0x2D, 0x4E, 0x6F, 0x4C, 0x6F, 0x67, 0x6F, 0x20, 0x2D, 0x4E, 0x6F, 0x50, 0x72, 0x6F, 0x66, 0x69, 0x6C, 0x65, 0x20, 0x2D, 0x4E, 0x6F, 0x6E, 0x49, 0x6E, 0x74, 0x65, 0x72, 0x61, 0x63, 0x74, 0x69, 0x76, 0x65, 0x20, 0x2D, 0x43, 0x6F, 0x6D, 0x6D, 0x61,
    0x6E, 0x64, 0x20, 0x22,
]; // ` -NoLogo -NoProfile -NonInteractive -Command "`

impl Default for ProcInfo {
    #[inline]
    fn default() -> ProcInfo {
        ProcInfo {
            pid:    0u32,
            tid:    0u32,
            proc:   0usize,
            thread: 0usize,
        }
    }
}
impl Default for ProcStartup {
    #[inline]
    fn default() -> ProcStartup {
        ProcStartup {
            pad0:   [0usize; 3],
            pad1:   [0u32; 8],
            pad2:   0u16,
            pad3:   [0usize; 4],
            size:   size_of::<ProcStartup>() as u32,
            window: 0u16,
        }
    }
}

impl<'a> Iterator for Reader<'a> {
    type Item = &'a [u16];

    fn next(&mut self) -> Option<&'a [u16]> {
        self.buf.clear();
        self.line.clear();
        match self.r.read_line(&mut self.line) {
            Ok(0) | Err(_) => return None,
            _ => (),
        };
        // Ignore empty lines
        if self.line.is_empty() {
            return self.next();
        }
        // Skip comment lines (first char is '#' or '/').
        if self.line.as_bytes().first().is_some_and(|&v| v == b'#' || v == b'/') {
            return self.next();
        }
        // All of the Package IDs for AppX Packages seem to be "ASCII"-only
        // and contain [A-Za-z0-9-_.] which can just use the simple codepoints
        // < 128.
        for &i in self.line.as_bytes() {
            match i {
                b'\r' | b'\n' => continue, // Skip newlines.
                b'0'..=b'9' | b'A'..=b'Z' | b'a'..=b'z' | b'_' | b'-' | b'.' => (),
                _ => return self.next(), // Invalid line, continue.
            }
            self.buf.push(i as u16);
        }
        // If the buffer is empty, skip it to the next result.
        if self.buf.is_empty() {
            return self.next();
        }
        // Pointer fuckery so we can avoid the borrow-checker as it's not
        // smart enough to understand what we're doing.
        Some(unsafe { from_raw_parts(self.buf.as_ptr(), self.buf.len()) })
    }
}

fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
    }
}

#[cfg(feature = "debug")]
#[inline]
fn eprintln_u16(v: &[u16]) {
    for &i in v {
        if i == 0 {
            break;
        }
        std::eprint!("{}", i as u8 as char);
    }
    eprintln!();
}
fn run() -> Result<(), Error> {
    let mut p = powershell()?.encode_wide().collect::<Vec<u16>>();
    // We add the null here but remove it down the line as we want to
    // use it for the "app" section in "CreateProcess".
    p.push(0); // NULL
    #[cfg(feature = "debug")]
    {
        std::eprint!("powershell.exe path: ");
        eprintln_u16(&p);
    }
    let v = match OpenOptions::new().read(true).open(packages()?) {
        Err(e) => return Err(e.to_string()),
        Ok(v) => v,
    };
    let mut b = Vec::new();
    let mut r = Reader {
        r:    BufReader::new(v),
        buf:  Vec::new(),
        line: String::new(),
        _p:   PhantomData,
    };
    let c = unsafe { p.get_unchecked(0..p.len() - 1) }; // Remove NULL.
    for i in &mut r {
        #[cfg(feature = "debug")]
        {
            std::eprint!("next item: ");
            eprintln_u16(i);
        }
        b.clear();
        b.extend_from_slice(&c); // `powershell.exe`
        b.extend_from_slice(&COMMAND); // `powershell.exe -Command "`
        b.extend_from_slice(&GET); // `powershell.exe -Command "Get-AppxPackage -Name '`
        b.extend_from_slice(i); // `powershell.exe -Command "Get-AppxPackage -Name '%NAME%`
        b.extend_from_slice(&PIPE); // `powershell.exe -Command "Get-AppxPackage -Name '%NAME%' | `
        b.extend_from_slice(&REMOVE); // `powershell.exe -Command "Get-AppxPackage -Name '%NAME%' | Remove-AppxPackage`
        b.push(0x22); // `powershell.exe -Command "Get-AppxPackage -Name '%NAME%' | Remove-AppxPackage"`
        b.push(0); // NULL
        if let Err(e) = exec(&p, &b) {
            eprintln!("exec error {e:X}");
        }
    }
    Ok(())
}
#[inline]
fn packages() -> Result<OsString, Error> {
    let mut a = args_os();
    let _ = a.next(); // Skip first arg "self".
    if let Some(v) = a.next() {
        return Ok(v);
    }
    let mut d = match current_dir() {
        Err(e) => return Err(e.to_string()),
        Ok(v) => v,
    };
    d.push(DEFAULT_CONFIG);
    Ok(d.into_os_string())
}
fn powershell() -> Result<OsString, Error> {
    if let Some(v) = var_os("PATH") {
        for mut i in split_paths(&v) {
            i.push(DEFAULT_EXE);
            if metadata(&i).is_ok_and(|x| x.is_file()) {
                return Ok(i.into_os_string());
            }
        }
    }
    let mut v = match var_os("WINDIR") {
        Some(v) => PathBuf::from(v),
        None => PathBuf::from(DEFAULT_WINDIR),
    };
    v.push(DEFAULT_PATH);
    if metadata(&v).is_ok_and(|x| x.is_file()) {
        return Ok(v.into_os_string());
    }
    Err(String::from(ERROR_NO_PWSH))
}
#[inline]
fn exec(app: &[u16], cmd: &[u16]) -> Result<(), u32> {
    #[cfg(feature = "debug")]
    {
        std::eprint!("exec: ");
        eprintln_u16(cmd);
    }
    let (s, mut i) = (ProcStartup::default(), ProcInfo::default());
    let r = unsafe {
        CreateProcessW(
            app.as_ptr(),
            cmd.as_ptr(),
            0,
            0,
            0,
            0x8000000, // CREATE_NO_WINDOW
            0,
            0,
            &s,
            &mut i,
        )
    };
    #[cfg(feature = "debug")]
    {
        eprintln!("result was {r:X}.");
    }
    if r == 0 {
        return Err(unsafe { GetLastError() });
    }
    #[cfg(feature = "debug")]
    {
        eprintln!("exec: pid {}", i.pid);
    }
    unsafe {
        // Wait for the Process to complete.
        let _ = WaitForSingleObject(i.proc, -1);
        CloseHandle(i.proc);
        CloseHandle(i.thread);
    }
    Ok(())
}

#[link(name = "kernel32")]
unsafe extern "system" {
    unsafe fn GetLastError() -> u32;
    unsafe fn CloseHandle(h: usize) -> u32;
    unsafe fn WaitForSingleObject(h: usize, sec: i32) -> u32;
    unsafe fn CreateProcessW(app: *const u16, cmd: *const u16, _x: usize, _y: usize, inherit: u32, flags: u32, env: usize, dir: usize, s: *const ProcStartup, i: *mut ProcInfo) -> u32;
}
