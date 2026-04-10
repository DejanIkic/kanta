# Pico Firmware Commands

## Copy Pico Firmware

### Basic Copy Command
```bash
# Copy firmware to destination directory
cp -r /path/to/picofirmware/* /destination/directory/
```

### Copy with Preservation
```bash
# Copy preserving permissions and timestamps
cp -rp /path/to/picofirmware/* /destination/directory/
```

### Copy with Verbose Output
```bash
# Copy with detailed output
cp -rpv /path/to/picofirmware/* /destination/directory/
```

## Additional Pico Commands

### Flash Firmware to Pico
```bash
# Flash firmware using picotool
picotool load -f firmware.uf2

# Flash with verification
picotool load -f firmware.uf2 -v
```

### Check Pico Status
```bash
# Check connected Pico devices
picotool info

# List all connected devices
picotool info -a
```

### Build Firmware
```bash
# Build Pico project
cmake --build build

# Build with specific configuration
cmake --build build --config Release
```

### Clean Build
```bash
# Clean build directory
rm -rf build/
mkdir build
cd build
cmake ..
```

### Monitor Serial Output
```bash
# Monitor serial output from Pico
sudo screen /dev/ttyACM0 115200

# Or using minicom
sudo minicom -D /dev/ttyACM0 -b 115200
```

### Backup Current Firmware
```bash
# Backup existing firmware
picotool save backup.uf2

# Backup specific memory regions
picotool save backup.uf2 -a 0x10000000 -s 0x2000
```

### Reset Pico
```bash
# Reset connected Pico
picotool reboot

# Reboot into bootloader mode
picotool reboot -b
```

## Useful Aliases

Add these to your `.bashrc` or `.zshrc`:

```bash
# Pico firmware management aliases
alias pico-copy='cp -rpv /path/to/picofirmware/* /destination/directory/'
alias pico-flash='picotool load -f firmware.uf2 -v'
alias pico-info='picotool info'
alias pico-reset='picotool reboot'
alias pico-monitor='sudo screen /dev/ttyACM0 115200'
```

## Notes

- Replace `/path/to/picofirmware/` with your actual firmware source path
- Replace `/destination/directory/` with your target destination
- Ensure `picotool` is installed and configured properly
- Adjust serial device (`/dev/ttyACM0`) and baud rate (`115200`) as needed
- Use `sudo` only when necessary for device access
