use encoding_rs;
use quick_xml::events::Event;
use quick_xml::reader::Reader;
use serde_json::{Map, Value};
use std::fs;
use std::path::Path;
use std::process::Command;
use walkdir; // Added missing walkdir dependency

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let pretty_mode = args.iter().any(|arg| arg == "--pretty" || arg == "-p");

    // 1. Scheduled Tasks
    let _ = harvest_scheduled_tasks(pretty_mode);

    // 2. PowerShell Harvesters
    let _ = harvest_via_ps(
        "Get-CimInstance Win32_Service | Select-Object Name, DisplayName, PathName, State",
        "wmi_service",
        pretty_mode,
    );
    let _ = harvest_via_ps(
        "Get-NetTCPConnection | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess",
        "network_connection",
        pretty_mode,
    );
    let _ = harvest_via_ps(
        "Get-DnsClientCache | Select-Object EntryName, Data, Type, Status",
        "dns_cache",
        pretty_mode,
    );
    let _ = harvest_via_ps(
        "Get-NetNeighbor -AddressFamily IPv4 | Select-Object IPAddress, LinkLayerAddress, State",
        "arp_entry",
        pretty_mode,
    );
    let _ = harvest_via_ps(
        "Get-CimInstance Win32_Process | Select-Object ProcessId, Name, CommandLine",
        "process",
        pretty_mode,
    );

    // 3. Native Named Pipe Harvester (No external tools)
    let _ = harvest_named_pipes_native(pretty_mode);

    // 4. BITS Jobs
    let _ = harvest_bitsadmin(pretty_mode);

    Ok(())
}

fn decode_bytes(bytes: &[u8]) -> String {
    let (res, _encoding_used, _had_errors) = encoding_rs::UTF_8.decode(bytes);
    if res.contains('\u{0000}') {
        let (res_u16, _, _) = encoding_rs::UTF_16LE.decode(bytes);
        return res_u16.trim_matches(char::from(0)).to_string();
    }
    res.into_owned()
}

fn harvest_scheduled_tasks(pretty: bool) -> Result<(), Box<dyn std::error::Error>> {
    let task_loc = "C:\\Windows\\System32\\Tasks";
    if Path::new(task_loc).exists() {
        for entry in walkdir::WalkDir::new(task_loc).into_iter().flatten() {
            if entry.path().is_file() {
                let mut task_data = Map::new();
                task_data.insert(
                    "task_file_path".into(),
                    Value::String(entry.path().to_string_lossy().into()),
                );

                let raw_bytes = fs::read(entry.path())?;
                let xml_string = decode_bytes(&raw_bytes);

                let mut reader = Reader::from_str(&xml_string);
                reader.config_mut().trim_text(true);

                let mut buf = Vec::new();
                let mut current_tag = String::new();

                loop {
                    match reader.read_event_into(&mut buf) {
                        Ok(Event::Start(e)) => {
                            current_tag =
                                String::from_utf8_lossy(e.local_name().as_ref()).to_string();
                        }
                        Ok(Event::Text(e)) => {
                            if let Ok(val_str) = reader.decoder().decode(&e) {
                                let val_trimmed = val_str.trim().to_string();
                                if !val_trimmed.is_empty() && !current_tag.is_empty() {
                                    let clean_key =
                                        to_smart_snake_case(&current_tag.replace('\u{0000}', ""));
                                    task_data.insert(
                                        clean_key,
                                        Value::String(val_trimmed.replace('\u{0000}', "")),
                                    );
                                }
                            }
                        }
                        Ok(Event::End(_)) => current_tag = String::new(),
                        Ok(Event::Eof) => break,
                        _ => (),
                    }
                    buf.clear();
                }

                let exe_path = task_data
                    .get("command")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string());
                let args = task_data
                    .get("arguments")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string())
                    .unwrap_or_default();

                if let Some(path_val) = exe_path {
                    task_data.insert("path".into(), Value::String(path_val.clone()));
                    let command_line = format!("{} {}", path_val, args).trim().to_string();
                    task_data.insert("command_line".into(), Value::String(command_line));
                }

                print_ordered_sanitized(Value::Object(task_data), "scheduled_task", pretty)?;
            }
        }
    }
    Ok(())
}

fn harvest_named_pipes_native(pretty: bool) -> Result<(), Box<dyn std::error::Error>> {
    let script = r#"
        $Definition = @"
        using System;
        using System.Runtime.InteropServices;
        public class FileNative {
            [DllImport("kernel32.dll", SetLastError = true)]
            public static extern IntPtr CreateFile(string lpFileName, uint dwDesiredAccess, uint dwShareMode, IntPtr lpSecurityAttributes, uint dwCreationDisposition, uint dwFlagsAndAttributes, IntPtr hTemplateFile);
            [DllImport("kernel32.dll", SetLastError = true)]
            public static extern bool GetNamedPipeServerProcessId(IntPtr hPipe, out uint ServerProcessId);
            [DllImport("kernel32.dll", SetLastError = true)]
            public static extern bool CloseHandle(IntPtr hObject);
        }
"@
        if (-not ([System.Management.Automation.PSTypeName]'FileNative').Type) {
            Add-Type -TypeDefinition $Definition
        }

        [System.IO.Directory]::GetFiles('\\.\pipe\') | ForEach-Object {
            $pipePath = $_
            $serverPid = 0

            # Method 1: Win32 API
            $hPipe = [FileNative]::CreateFile($pipePath, 0, 0, [IntPtr]::Zero, 3, 0, [IntPtr]::Zero)
            if ($hPipe.ToInt64() -ne -1) {
                $outPid = 0
                if ([FileNative]::GetNamedPipeServerProcessId($hPipe, [ref]$outPid)) {
                    $serverPid = $outPid
                }
                [void][FileNative]::CloseHandle($hPipe)
            }

            # Method 2: Fallback - Parse PID from common pipe name patterns
            if ($serverPid -eq 0) {
                if ($pipePath -match '\.(\d+)\.') { $serverPid = $matches[1] }
                elseif ($pipePath -match '_(\d+)_') { $serverPid = $matches[1] }
            }

            $procName = "Unknown"
            if ($serverPid -gt 0) {
                $proc = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
                if ($proc) { $procName = $proc.Name }
            }

            [PSCustomObject]@{
                pipe_name = $pipePath
                process = $procName
                pid = [int]$serverPid
            }
        } | ConvertTo-Json -Compress
    "#;

    harvest_via_ps(script, "named_pipe", pretty)
}

fn harvest_bitsadmin(pretty: bool) -> Result<(), Box<dyn std::error::Error>> {
    let output = Command::new("bitsadmin.exe")
        .args(&["/list", "/allusers", "/verbose"])
        .output()?;
    let text = String::from_utf8_lossy(&output.stdout);

    let keywords = [
        "TYPE:",
        "STATE:",
        "OWNER:",
        "PRIORITY:",
        "FILES:",
        "BYTES:",
        "CREATION TIME:",
        "MODIFICATION TIME:",
        "COMPLETION TIME:",
        "DESCRIPTION:",
        "RETRY DELAY:",
        "ACL FLAGS:",
        "ERROR COUNT:",
        "NO PROGRESS TIMEOUT:",
        "PROXY USAGE:",
    ];

    for job_block in text.split("GUID:") {
        if !job_block.contains("DISPLAY:") {
            continue;
        }
        let mut map = Map::new();

        // 1. Extract Job ID and Display Name
        if let Some(first_line) = job_block.lines().next() {
            let parts: Vec<&str> = first_line.split("DISPLAY:").collect();
            map.insert("job_id".into(), parts[0].trim().into());
            if parts.len() > 1 {
                map.insert(
                    "display_name".into(),
                    parts[1].trim().trim_matches('\'').into(),
                );
            }
        }

        // 2. Procedural Keyword Scanning (Fixed unused 'i')
        for &kw in keywords.iter() {
            if let Some(start_pos) = job_block.find(kw) {
                let val_start = start_pos + kw.len();

                // Find the nearest next keyword to terminate this value
                let mut end_pos = job_block.len();
                for next_kw in keywords.iter() {
                    if let Some(next_pos) = job_block[val_start..].find(next_kw) {
                        let absolute_next_pos = val_start + next_pos;
                        if absolute_next_pos < end_pos {
                            end_pos = absolute_next_pos;
                        }
                    }
                }

                let value = job_block[val_start..end_pos].trim();
                if !value.is_empty() {
                    let clean_key = to_smart_snake_case(kw.trim_matches(':'));
                    map.insert(clean_key, value.into());
                }
            }
        }

        // 3. File Transfer Parsing
        for line in job_block.lines() {
            let l = line.trim();
            if l.contains("http") && l.contains("->") {
                let file_parts: Vec<&str> = l.split("->").collect();
                if file_parts.len() == 2 {
                    let url_part = file_parts[0].split_whitespace().last().unwrap_or("").trim();
                    map.insert("remote_url".into(), url_part.into());
                    map.insert("local_path".into(), file_parts[1].trim().into());
                }
            }
        }

        print_ordered_sanitized(Value::Object(map), "bits_job", pretty)?;
    }
    Ok(())
}

fn harvest_via_ps(
    script: &str,
    data_type: &str,
    pretty: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let output = Command::new("powershell")
        .args(&["-NoProfile", "-Command", script])
        .output()?;

    let json_str = String::from_utf8_lossy(&output.stdout);
    if json_str.trim().is_empty() || json_str == "[]" {
        return Ok(());
    }

    if let Ok(parsed) = serde_json::from_str::<Value>(&json_str) {
        if let Some(arr) = parsed.as_array() {
            for item in arr {
                print_ordered_sanitized(item.clone(), data_type, pretty)?;
            }
        } else {
            print_ordered_sanitized(parsed, data_type, pretty)?;
        }
    }
    Ok(())
}

fn print_ordered_sanitized(
    item: Value,
    data_type: &str,
    pretty: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut clean_map = Map::new();
    if let Value::Object(m) = item {
        for (k, v) in m {
            if v.is_null() || (v.is_string() && v.as_str().unwrap().is_empty()) || k == "data_type"
            {
                continue;
            }
            clean_map.insert(k, v);
        }
    }
    let body_json = serde_json::to_string(&Value::Object(clean_map))?;
    let mut final_raw = format!("{{\"data_type\":\"{}\",{}", data_type, &body_json[1..]);
    if pretty {
        if let Ok(val) = serde_json::from_str::<Value>(&final_raw) {
            final_raw = serde_json::to_string_pretty(&val)?;
        }
    }
    println!("{}", final_raw);
    Ok(())
}

fn to_smart_snake_case(s: &str) -> String {
    if s.chars()
        .all(|c| c.is_uppercase() || c.is_whitespace() || c == '_')
    {
        return s.to_lowercase().replace(' ', "_").replace("__", "_");
    }

    let mut res = String::new();
    let chars: Vec<char> = s.chars().collect();
    for i in 0..chars.len() {
        let c = chars[i];
        if c.is_uppercase() {
            if i > 0 && !res.ends_with('_') && chars[i - 1].is_lowercase() {
                res.push('_');
            }
            res.push(c.to_ascii_lowercase());
        } else if c.is_whitespace() {
            res.push('_');
        } else {
            res.push(c);
        }
    }
    res.replace("i_p", "ip")
        .replace("u_r_i", "uri")
        .replace("__", "_")
        .trim_matches('_')
        .to_string()
}
