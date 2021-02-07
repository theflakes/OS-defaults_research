[CmdletBinding()]
param (
    [switch] $recurse = $false,
    [switch] $pretty = $false,
    [switch] $hashFiles = $false,
    [string] $directory = "$env:SYSTEMDRIVE\"
)

Function Init-Log {
    $log = New-Object psobject -Property @{
        DataType = "FileSystem"
        Arch = 64
        Version = $null
        OS = $null
        
        ParentPath = $null
        Name = $null
        BaseName = $null
        Extension = $null
        Mode = $null
        Size = $null
        Hidden = 0
        Link = 0
        Links = $null
        Streams = $null

        md5 = $null
        sha1 = $null
        sha256 = $null

        Comments = $null
        CompanyName = $null
        FileBuildPart = $null
        FileDescription = $null
        FileMajorPart = $null
        FileMinorPart = $null
        FileName = $null
        FilePrivatePart = $null
        FileVersion = $null
        InternalName = $null
        IsDebug = $null
        IsPatched = $null
        IsPrivateBuild = $null
        IsPreRelease = $null
        IsSpecialBuild = $null
        Language = $null
        LegalCopyright = $null
        LegalTrademarks = $null
        OriginalFilename = $null
        PrivateBuild = $null
        ProductBuildPart = $null
        ProductMajorPart = $null
        ProductMinorPart = $null
        ProductName = $null
        ProductPrivatePart = $null
        ProductVersion = $null

        Group = $null
        User = $null
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

Function ConvertTo-BinaryBool($bool) {
    if ($bool) {
        if ($bool -eq $true) {
            return 1
        } else {
            return 0
        }
    } else {
        return $null
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
    $group_user = (Get-Acl $item.FullName)
    $log.Group = $group_user.Group.Split('\')[1]
    $log.User = $group_user.Owner.Split('\')[1]
    if ($item.Name.StartsWith(".") -or $item.Attributes -contains "Hidden") {
        $log.Hidden = 1
    }
    if ($item.LinkType) {
        $log.Link = 1
        $log.Links = $item.Target
    } elseif (-not $item.PSIsContainer) {
        if ($hashFiles) {
            $log.md5 = (Get-FileHash $item.FullName -Algorithm md5 -ErrorAction SilentlyContinue).Hash
            $log.sha1 = (Get-FileHash $item.FullName -Algorithm sha1 -ErrorAction SilentlyContinue).Hash
            $log.sha256 = (Get-FileHash $item.FullName -Algorithm sha256 -ErrorAction SilentlyContinue).Hash
        }
        $log.Comments = $item.VersionInfo.Comments
        $log.CompanyName = $item.VersionInfo.CompanyName
        $log.FileBuildPart = $item.VersionInfo.FileBuildPart
        $log.FileDescription = $item.VersionInfo.FileDescription
        $log.FileMajorPart = $item.VersionInfo.FileMajorPart
        $log.FileMinorPart = $item.VersionInfo.FileMinorPart
        $log.FileName = $item.VersionInfo.FileName
        $log.FilePrivatePart = $item.VersionInfo.FilePrivatePart
        $log.FileVersion = $item.VersionInfo.FileVersion
        $log.InternalName = $item.VersionInfo.InternalName
        $log.IsDebug = ConvertTo-BinaryBool $item.VersionInfo.IsDebug
        $log.IsPatched = ConvertTo-BinaryBool $item.VersionInfo.IsPatched
        $log.IsPrivateBuild = ConvertTo-BinaryBool $item.VersionInfo.IsPrivateBuild
        $log.IsPreRelease = ConvertTo-BinaryBool $item.VersionInfo.IsPreRelease
        $log.IsSpecialBuild = ConvertTo-BinaryBool $item.VersionInfo.IsSpecialBuild
        $log.Language = $item.VersionInfo.Language
        $log.LegalCopyright = $item.VersionInfo.LegalCopyright
        $log.LegalTrademarks = $item.VersionInfo.LegalTrademarks
        $log.OriginalFilename = $item.VersionInfo.OriginalFilename
        $log.PrivateBuild = $item.VersionInfo.PrivateBuild
        $log.ProductBuildPart = $item.VersionInfo.ProductBuildPart
        $log.ProductMajorPart = $item.VersionInfo.ProductMajorPart
        $log.ProductMinorPart = $item.VersionInfo.ProductMinorPart
        $log.ProductName = $item.VersionInfo.ProductName
        $log.ProductPrivatePart = $item.VersionInfo.ProductPrivatePart
        $log.ProductVersion = $item.VersionInfo.ProductVersion
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
