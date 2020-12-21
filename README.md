# OS-defaults_research
Information pertaining to OS install defaults to baseline normal for a given OS.

Will not be including metadata such as file hashes as they change too much to track.

This information is meant for:
 - hunting the OS by understanding defaults
 - triaging a host by having non-defaults stand out more

Example; attacker creates a DLL file in C:\Windows\SysWOW64 that does not exist there by default but does exist in C:\Windows\System32. A good attacker evasion technique as the file will be a legit default OS file name but not in the correct directory.