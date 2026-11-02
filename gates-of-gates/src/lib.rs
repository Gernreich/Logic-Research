//! Lambda terms for the gates-of-gates tools.
//!
//! The tools were JavaScript until 2026-11-02. The pages and gates-data.json were
//! written by Node, and the Rust port writes them byte for byte: `jsfmt` writes
//! numbers by JavaScript's rules and `json` lays JSON out as JSON.stringify did.
//!
//! * `reference` -- the plain normal-order reducer (no ids); allreduce prints its steps
//!   and `core` checks itself against it
//! * `core` -- terms with stable ids, the reducer the cells are computed with, the Tromp
//!   layout and its SVG
//! * `shortform` -- the conventional short form, its parser, and de Bruijn form

pub mod core;
pub mod jsfmt;
pub mod json;
pub mod reference;
pub mod shortform;

use std::path::PathBuf;

/// The gates-of-gates folder: found from the running program (target/release/...),
/// falling back to where it was built.
pub fn root() -> PathBuf {
    if let Ok(exe) = std::env::current_exe() {
        if let Some(r) = exe.parent().and_then(|p| p.parent()).and_then(|p| p.parent()) {
            if r.join("tools").is_dir() && r.join("Cargo.toml").exists() {
                return r.to_path_buf();
            }
        }
    }
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

/// lambda16.txt: $LAMBDA16, or the top of the repository.
pub fn lambda16() -> PathBuf {
    std::env::var("LAMBDA16").map(PathBuf::from).unwrap_or_else(|_| root().join("..").join("lambda16.txt"))
}

pub struct Gate {
    pub idx: usize,
    pub bits: String,
    pub name: String,
    pub term: String,
}

/// The sixteen gates, by index, from lambda16.txt's table.
pub fn read_gates() -> Result<Vec<Gate>, String> {
    let text = std::fs::read_to_string(lambda16()).map_err(|e| format!("lambda16.txt: {e}"))?;
    let re = regex::Regex::new(r"^\s*(\d+)\s+([01])\s+([01])\s+([01])\s+([01])\s+(.*?)\s+(λ\S.*)$").unwrap();
    let mut rows: Vec<Option<Gate>> = (0..16).map(|_| None).collect();
    let mut count = 0;
    for l in text.split('\n') {
        if let Some(m) = re.captures(l) {
            let idx: usize = m[1].parse().unwrap();
            if idx >= rows.len() {
                rows.resize_with(idx + 1, || None);
            }
            if rows[idx].is_none() {
                count += 1;
            }
            rows[idx] = Some(Gate {
                idx,
                bits: format!("{}{}{}{}", &m[2], &m[3], &m[4], &m[5]),
                name: m[6].trim().to_string(),
                term: m[7].to_string(),
            });
        }
    }
    if rows.len() != 16 || count != 16 {
        return Err("expected 16 gates from lambda16.txt".into());
    }
    Ok(rows.into_iter().map(Option::unwrap).collect())
}
