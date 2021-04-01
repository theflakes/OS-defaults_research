# OS-defaults_research
Information pertaining to OS install defaults to baseline normal for a given OS.

This information is meant for:
 - hunting the OS by understanding defaults
 - triaging a host by having non-defaults stand out more

Information collected:
 - Directories
 - Child directories
 - Files and the directories they are located in
 - Windows alternate data streams
 - meta data on files (hashes, PE header stuff, ...)
 - *nix and Windows lnk information

An SQLite DB is used to store all the metadata and relationships of directories, sub directories, files, and links. Refer to the "build_db.sql" to understand tables and their relationships.

TO DO:
 - Further testing
 - Build default set of queries for more interesting relationships and information

Example; attacker creates a DLL file in C:\Windows\SysWOW64 that does not exist there by default but does exist in C:\Windows\System32. A good attacker evasion technique as the file will be a legit default OS file name but not in the correct directory.
