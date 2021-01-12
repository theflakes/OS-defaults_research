[CmdletBinding()]
param (
    [switch] $recurse = $false,
    [switch] $pretty = $false
)

Function Get-MetaData {
    [CmdletBinding()]
    param (
        $item
    )

    $md = New-Object psobject

    if ($is_x64) {
        $md | Add-Member -type NoteProperty -name arch -value 64
    } else {
        $md | Add-Member -type NoteProperty -name arch -value 32
    }
    $md | Add-Member -type NoteProperty -name version -value $version
    $md | Add-Member -type NoteProperty -name os -value $productName
    
    # Get File/Directory metadata
    $md | Add-Member -type NoteProperty -name ParentPath -value ($item.PSParentPath -split "::")[1]
    $md | Add-Member -type NoteProperty -name Name -value $item.Name
    $md | Add-Member -type NoteProperty -name BaseName -value $item.BaseName
    $md | Add-Member -type NoteProperty -name Extension -value $(if ($item.Extension) {$item.Extension} else {$null})
    $md | Add-Member -type NoteProperty -name Mode -value $item.Mode
    $md | Add-Member -type NoteProperty -name Size -value $item.Length
    $md | Add-Member -type NoteProperty -name LinkType -value $item.LinkType
    if ($item.LinkType) {
        $md | Add-Member -type NoteProperty -name Links -value $item.Target
    } else {
        $md | Add-Member -type NoteProperty -name Links -value $null
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
    if ($streams_array.Count -eq 0) { $streams_array = $null }
    $md | Add-Member -type NoteProperty -name Streams -value $streams_array

    if ($pretty) {
        $md | ConvertTo-Json
    } else {
        $md | ConvertTo-Json -Compress
    }
}


<#
    MAIN
#>
$is_x64 = [System.Environment]::Is64BitOperatingSystem
$version = [Environment]::OSVersion.Version.ToString()
$productName = Get-ComputerInfo | select WindowsProductName.WindowsProductName

if ($recurse) {
    Get-ChildItem -Force -Recurse | ForEach-Object {
        Get-MetaData $_
    }
} else {
    Get-ChildItem -Force | ForEach-Object {
        Get-MetaData $_
    }
}
