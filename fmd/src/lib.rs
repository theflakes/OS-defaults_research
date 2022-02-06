extern crate libc;
extern crate tree_magic;
extern crate fuzzyhash;

use libc::{c_char};
use std::ffi::CString;
use std::str;
use std::path::Path;
use std::{io};
use std::io::Read;
use std::process;
use fuzzyhash::FuzzyHash;

#[repr(C)]
pub struct MetaData {
    pub mime_type: *mut c_char,
    pub fuzzy_hash: *mut c_char
}

fn convert_to_path(target_file: &str) -> io::Result<&Path> {
    let file_path = Path::new(target_file);
    if file_path.exists() && file_path.is_file() { 
        return Ok(file_path)
    }

    println!("\nFile not found!\n");
    process::exit(1)
}

fn get_mimetype(target_file: &Path) -> io::Result<String> {
    let mtype = tree_magic::from_filepath(target_file);

    Ok(mtype)
}

/* 
    See:    https://github.com/rustysec/fuzzyhash-rs
            https://docs.rs/fuzzyhash/latest/fuzzyhash/
*/
fn get_fuzzy_hash(target_file: &Path) -> io::Result<FuzzyHash> {
    let mut file = std::fs::File::open(target_file).unwrap();
    let mut fuzzy_hash = FuzzyHash::default();

    loop {
        let mut buffer = vec![0; 1024];
        let count = file.read(&mut buffer).unwrap();
    
        fuzzy_hash.update(buffer);
    
        if count < 1024 {
            break;
        }
    }
    
    fuzzy_hash.finalize();
    
    Ok(fuzzy_hash)
}

#[no_mangle]
pub extern fn GetMetadata(target_file: &str) -> MetaData {
    println!("HI");
    let path = convert_to_path(target_file).unwrap();
    let mime_type = CString::new(get_mimetype(path).unwrap()).unwrap();
    let fuzzy_hash = CString::new(get_fuzzy_hash(path).unwrap().to_string()).unwrap();
    println!("{:?}", fuzzy_hash);
    MetaData {
        mime_type: mime_type.into_raw(),
        fuzzy_hash: fuzzy_hash.into_raw()
    }
}