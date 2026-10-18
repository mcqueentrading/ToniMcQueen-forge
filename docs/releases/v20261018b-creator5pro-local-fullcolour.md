# ToniMcQueen Forge Creator 5 Pro 20261018b

This release fixes the ImageMap full-colour toolchange transition. The
Creator 5 firmware now restores the purge-tower XY position after a successful
tool grab, so the first purge extrusion starts at the tower instead of
travelling from the dock while extruding. Z is intentionally not restored;
the existing calibrated tool-frame and print-Z logic remains unchanged.

It also adds a regression check and documents the slicer/firmware contract
behind the fix. This is a userspace/configuration update and does not reflash
the stock kernel or MCU firmware in the default slim installer.
