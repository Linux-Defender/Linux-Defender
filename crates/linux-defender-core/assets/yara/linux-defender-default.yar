// Linux Defender default YARA rule (MIT). Active only with standalone clamscan.
// It matches the standard EICAR test string, which already appears in the host
// signature database; it cannot match legitimate user content.
rule LinuxDefender_Default_EICAR_Test {
    strings:
        $eicar = "EICAR-STANDARD-ANTIVIRUS-TEST-FILE"
    condition:
        $eicar
}
