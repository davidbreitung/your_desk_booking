> Historischer Entwicklungsbericht, Stand der jeweils genannten Version. Betriebsdetails wurden für die öffentliche Übernahme neutralisiert. Aktueller Stand: siehe README und Handbücher im Repository.

# Display flash expansion — completed

Device: Elecrow CrowPanel 2.1 inch rotary, DHE03921D. Manufacturer specifies
16 MB flash and 8 MB PSRAM. Existing ESPHome configuration defaults to 4 MB.

Backup on Home Assistant:
`/config/desk_display_backups/before-flash-expand-20261115_171001`
contains the configuration, original partition table, bootloader, OTA firmware
and factory firmware. This is a build/configuration backup, not a dump of live NVS.

The proposed layout in `display-partitions-expanded.csv` retains NVS at
0x390000 (size 0x70000), OTA metadata at 0x9000 and PHY at 0xB000.
Both app slots become 0x380000 bytes (3.5 MiB). App0 retains address 0x10000;
app1 moves to 0x400000. The remaining flash stays unallocated.

Migration preparation uses a separate configuration with the original partition
table, 16 MB flash and temporarily enabled partition-update support. The normal
configuration remains unchanged until migration succeeds.

Required order: verify transition build fits the old slot; install and verify;
ensure bootloader supports the full flash; apply verified expanded table while
retaining/copying the running image to app0; verify reboot and actual table;
install normal firmware using expanded layout and disable partition-update access;
verify both OTA functionality and retained display settings.

Transition firmware built and installed successfully, followed by the 16 MB
bootloader. Both rebooted and reconnected. The first partition-table attempt
triggered a device reset inside `esp_partition_copy`; the old partition table
remained active and the device recovered in app1 at 0x1D0000. Do not repeat the
copy route: first install the transition firmware normally into app0, verify its
running address is 0x10000, then apply the new table using the no-copy route.

After a normal OTA upload, running app0 at 0x10000 was verified. Updating the
partition table through this no-copy path then succeeded. The rebooted device
reported app0 at 0x10000 / size 0x380000 and app1 at 0x400000 / size 0x380000,
with the original NVS address and size. Its flash sensor reported 49.917% for
the transition firmware. Check-in, custom light names/icons, favorites 66/111 cm,
height setpoint 74 cm and display brightness 50% were retained in the readings.

Final normal firmware successfully built and uploaded into the newly located
second slot; reboot and API reconnection verified. Final image size 1,826,639
bytes, OTA file 1,826,752 bytes; each slot is 3,670,016 bytes. The live ESPHome
flash sensor reports 49.775%, versus 99.550% before expansion. No UI asset or
feature was removed. The active configuration does not enable partition access.

The original active configuration now explicitly sets `flash_size: 16MB` and
`partitions: display-partitions-expanded.csv`. Temporary migration configuration
and logs are archived under the backup's `migration` directory, along with the
final OTA and factory binaries. The temporary device configuration no longer
appears beside the normal ESPHome device configuration.

Status: completed and verified on 2026-11-15. Both enlarged slots were used
successfully: transition firmware in app0 and final normal firmware in app1.
The existing check-in and the recorded height/settings values remain intact.
