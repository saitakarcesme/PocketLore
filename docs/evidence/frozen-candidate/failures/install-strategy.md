The initial streamed installation failed with device offline. Before boot ID was
75d5e110-b22d-431e-af27-b0bb96f6c109; after spontaneous device recovery it was
c33368d3-4fc4-4eac-ab2d-ed0a70b7fedb, boot reason reboot, old APK9c71a32d remained.
No reboot or service command was issued. No primary journey was measured.
The next bounded attempt stages a run-owned APK, checks its exact device hash,
then invokes local package installation rather than repeating streamed install.
If it fails, preserve it and leave the modern candidate gate open; no wipe or
service repair is authorized. This is a transport change, not a proven crash fix.
