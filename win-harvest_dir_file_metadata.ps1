[CmdletBinding()]
param (
    [switch] $recurse = $false,
    [switch] $pretty = $false,
    [switch] $hashfiles = $false,
    [string] $directory = "$env:SYSTEMDRIVE\"
)

Function Init-Log {
    $log = New-Object psobject -Property @{
        Arch = 64
        Version = $null
        OS = $null
        ParentPath = $null
        Name = $null
        BaseName = $null
        Extension = $null
        Mode = $null
        Size = $null
        Hidden = $false
        Link = $false
        Links = $null
        Streams = $null
        md5 = $null
        sha1 = $null
        sha256 = $null
    }

    return $log
}

Function Print-log($log) {
    if ($pretty) {
        $log | ConvertTo-Json
    } else {
        $log | ConvertTo-Json -Compress
    }
}

Function Get-MetaData($item) {
    $log = Init-Log

    if (-not $is_x64) {
        $log.Arch = 32
    }
    $log.Version = $version
    $log.OS = $productName
    
    # Get File/Directory metadata
    $log.ParentPath = ($item.PSParentPath -split "::")[1]
    $log.Name = $item.Name
    $log.BaseName = $item.BaseName
    $log.Extension = $(if ($item.Extension) {$item.Extension} else {$null})
    $log.Mode = $item.Mode
    $log.Size = $item.Length
    if ($item.Name.StartsWith(".") -or $item.Attributes -contains "Hidden") {
        $log.Hidden = $true
    }
    if ($item.LinkType) {
        $log.Link = $true
        $log.Links = $item.Target
    } elseif ($hashFiles -and -not $item.PSIsContainer) {
        $log.md5 = (Get-FileHash $item.FullName -Algorithm md5).Hash -ErrorAction SilentlyContinue
        $log.sha1 = (Get-FileHash $item.FullName -Algorithm sha1).Hash -ErrorAction SilentlyContinue
        $log.sha256 = (Get-FileHash $item.FullName -Algorithm sha256).Hash -ErrorAction SilentlyContinue
    }

    # Get Alternate Data Streams
    $streams_array = New-Object -TypeName System.Collections.ArrayList
    $streams = Get-Item $item -Stream * -ErrorAction SilentlyContinue
    foreach ($s in $streams) {
        if ($s.Stream.Equals(':$DATA')) { continue }    # ignore default ADS
        $smd = New-Object psobject
        $smd | Add-Member -type NoteProperty -name Name -value $s.Stream
        $smd | Add-Member -type NoteProperty -name Size -value $s.Length
        [void]$streams_array.Add($smd)
    }
    $log.Streams = $streams_array

    Print-log $log
}


<#
    MAIN
#>
$is_x64 = [System.Environment]::Is64BitOperatingSystem
$version = [Environment]::OSVersion.Version.ToString()
$productName = gwmi win32_operatingsystem | % caption

if ($recurse) {
    Get-ChildItem $directory -Force -Recurse | ForEach-Object {
        Get-MetaData $_
    }
} else {
    Get-ChildItem $directory -Force | ForEach-Object {
        Get-MetaData $_
    }
}
