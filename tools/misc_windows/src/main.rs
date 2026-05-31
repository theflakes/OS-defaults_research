use encoding_rs;
use quick_xml::events::Event;
use quick_xml::reader::Reader;
use serde_json::{Map, Value};
use std::fs;
use std::path::Path;
use std::process::Command;
use walkdir;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let pretty_mode = args.iter().any(|arg| arg == "--pretty" || arg == "-p");

    let run = |res: Result<(), Box<dyn std::error::Error>>, name: &str| {
        if let Err(e) = res {
            eprintln!("[!] CRITICAL ERROR in {}: {}", name, e);
        }
    };

    println!("--- Starting Harvest ---");

    run(harvest_scheduled_tasks(pretty_mode), "Scheduled Tasks");

    run(
        harvest_via_ps(
            "Get-CimInstance Win32_Service | Select-Object Name, DisplayName, PathName, State | ConvertTo-Json -Compress",
            "wmi_service",
            pretty_mode,
        ),
        "WMI Service",
    );

    run(
        harvest_via_ps(
            "Get-NetTCPConnection | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess | ConvertTo-Json -Compress",
            "network_connection",
            pretty_mode,
        ),
        "Network Connection",
    );

    run(
        harvest_via_ps(
            "Get-DnsClientCache | Select-Object EntryName, Data, Type, Status | ConvertTo-Json -Compress",
            "dns_cache",
            pretty_mode,
        ),
        "DNS Cache",
    );

    run(
        harvest_via_ps(
            "Get-NetNeighbor -AddressFamily IPv4 | Select-Object IPAddress, LinkLayerAddress, State | ConvertTo-Json -Compress",
            "arp_entry",
            pretty_mode,
        ),
        "ARP Entry",
    );

    run(harvest_processes_enriched(pretty_mode), "Process");

    run(harvest_minifilters(pretty_mode), "Minifilters");

    run(harvest_named_pipes_native(pretty_mode), "Named Pipes");

    run(harvest_bitsadmin(pretty_mode), "BITS Jobs");

    println!("--- Harvest Complete ---");
    Ok(())
}

fn harvest_processes_enriched(pretty: bool) -> Result<(), Box<dyn std::error::Error>> {
    let script = r#"
        $all = Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, CommandLine, ExecutablePath
        $all | ForEach-Object {
            $p = $_
            $parent = $all | Where-Object { $_.ProcessId -eq $p.ParentProcessId }
            [PSCustomObject]@{
                process_id          = [int]$p.ProcessId
                name                = $p.Name
                command_line        = $p.CommandLine
                path                = $p.ExecutablePath
                ppid                = [int]$p.ParentProcessId
                parent_path         = $parent.ExecutablePath
                parent_command_line = $parent.CommandLine
            }
        } | ConvertTo-Json -Compress
    "#;
    harvest_via_ps(script, "process", pretty)
}

fn harvest_minifilters(pretty: bool) -> Result<(), Box<dyn std::error::Error>> {
    let script = r#"
        $raw = fltmc instances | Where-Object { $_ -match '\S' }
        if ($raw.Count -lt 3) { return "[]" }

        # 1. Identify the separator line (the one with the dashes)
        $separatorLine = $raw | Where-Object { $_ -match '^[- ]+$' }
        if (-not $separatorLine) { return "[]" }

        # 2. Map the start index of every dash block
        $matches = [regex]::Matches($separatorLine, '-+')
        $offsets = $matches | ForEach-Object { $_.Index }

        # 3. Get the header names using these same offsets
        $headerLine = $raw[0]
        $colNames = for($i=0; $i -lt $offsets.Count; $i++) {
            $len = if ($i -lt $offsets.Count - 1) { $offsets[$i+1] - $offsets[$i] } else { $headerLine.Length - $offsets[$i] }
            $headerLine.Substring($offsets[$i], [math]::Min($len, $headerLine.Length - $offsets[$i])).Trim().Replace(" ", "_").ToLower()
        }

        # 4. Parse rows using the mapped offsets
        $data = $raw | Where-Object { $_ -notmatch "Filter Name" -and $_ -notmatch '^[- ]+$' } | ForEach-Object {
            $line = $_
            $obj = @{}
            for($i=0; $i -lt $offsets.Count; $i++) {
                $start = $offsets[$i]
                if ($start -lt $line.Length) {
                    $len = if ($i -lt $offsets.Count - 1) { $offsets[$i+1] - $start } else { $line.Length - $start }
                    $val = $line.Substring($start, [math]::Min($len, $line.Length - $start)).Trim()
                    $obj[$colNames[$i]] = $val
                }
            }
            [PSCustomObject]$obj
        }
        $data | ConvertTo-Json -Compress
    "#;
    harvest_via_ps(script, "minifilter_instance", pretty)
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
    let trimmed = json_str.trim();

    if trimmed.is_empty() || trimmed == "[]" {
        return Ok(());
    }

    if let Ok(parsed) = serde_json::from_str::<Value>(trimmed) {
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

                if let Ok(raw_bytes) = fs::read(entry.path()) {
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
                                        task_data.insert(
                                            to_smart_snake_case(&current_tag),
                                            Value::String(val_trimmed),
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
                    print_ordered_sanitized(Value::Object(task_data), "scheduled_task", pretty)?;
                }
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
        if (-not ([System.Management.Automation.PSTypeName]'FileNative').Type) { Add-Type -TypeDefinition $Definition }
        [System.IO.Directory]::GetFiles('\\.\pipe\') | ForEach-Object {
            $pipePath = $_
            $serverPid = 0
            $hPipe = [FileNative]::CreateFile($pipePath, 0, 0, [IntPtr]::Zero, 3, 0, [IntPtr]::Zero)
            if ($hPipe.ToInt64() -ne -1) {
                $outPid = 0
                if ([FileNative]::GetNamedPipeServerProcessId($hPipe, [ref]$outPid)) { $serverPid = $outPid }
                [void][FileNative]::CloseHandle($hPipe)
            }
            $procName = "Unknown"
            if ($serverPid -gt 0) {
                $proc = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
                if ($proc) { $procName = $proc.Name }
            }
            [PSCustomObject]@{ name = $pipePath; process = $procName; pid = [int]$serverPid }
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
    ];

    for job_block in text.split("GUID:") {
        if !job_block.contains("DISPLAY:") {
            continue;
        }
        let mut map = Map::new();
        for &kw in keywords.iter() {
            if let Some(start) = job_block.find(kw) {
                let val_start = start + kw.len();
                let end = job_block[val_start..]
                    .find("\r\n")
                    .unwrap_or(job_block.len() - val_start);
                let value = job_block[val_start..val_start + end].trim();
                map.insert(to_smart_snake_case(kw.trim_matches(':')), value.into());
            }
        }
        print_ordered_sanitized(Value::Object(map), "bits_job", pretty)?;
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
            let snake_key = to_smart_snake_case(&k);
            if v.is_null()
                || (v.is_string() && v.as_str().unwrap().is_empty())
                || snake_key == "data_type"
            {
                continue;
            }
            clean_map.insert(snake_key, v);
        }
    }

    let mut final_map = Map::new();
    final_map.insert("data_type".into(), Value::String(data_type.to_string()));
    for (k, v) in clean_map {
        final_map.insert(k, v);
    }

    let final_val = Value::Object(final_map);
    println!(
        "{}",
        if pretty {
            serde_json::to_string_pretty(&final_val)?
        } else {
            serde_json::to_string(&final_val)?
        }
    );
    Ok(())
}

fn decode_bytes(bytes: &[u8]) -> String {
    let (res, _, _) = encoding_rs::UTF_8.decode(bytes);
    if res.contains('\u{0000}') {
        let (res_u16, _, _) = encoding_rs::UTF_16LE.decode(bytes);
        return res_u16.trim_matches(char::from(0)).to_string();
    }
    res.into_owned()
}

fn to_smart_snake_case(s: &str) -> String {
    let mut res = String::new();
    let chars: Vec<char> = s.chars().collect();
    for i in 0..chars.len() {
        let c = chars[i];
        if c.is_uppercase() {
            if i > 0 && !res.ends_with('_') {
                let prev = chars[i - 1];
                let next = if i + 1 < chars.len() {
                    Some(chars[i + 1])
                } else {
                    None
                };
                if prev.is_lowercase() || (next.is_some() && next.unwrap().is_lowercase()) {
                    res.push('_');
                }
            }
            res.push(c.to_ascii_lowercase());
        } else if c.is_whitespace() || c == '-' || c == '.' {
            if !res.ends_with('_') {
                res.push('_');
            }
        } else {
            res.push(c);
        }
    }
    res.replace("__", "_").trim_matches('_').to_string()
}
