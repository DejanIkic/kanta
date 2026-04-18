# Pico Firmware Management Guide

## Overview
This guide explains how to manage and update firmware on the Raspberry Pi Pico for servo control.

## Scripts Available

### 1. Manual Update Script
**Command:** `make update-firmware`

**Purpose:** Manually upload all firmware files to Pico and restart it

**Features:**
- Checks Pico connection
- Uploads all firmware files (boot.py, main.py, servo_driver.py, pin_config.py)
- Restarts Pico automatically
- Tests connection after update
- Error handling and logging

**Usage:**
```bash
# Edit firmware files
vim pico_firmware/main.py

# Update Pico
make update-firmware

# Start API
make dev
```

### 2. Automatic Watcher Script
**Command:** `python scripts/watch_firmware.py`

**Purpose:** Automatically monitors firmware directory for changes and updates Pico

**Features:**
- Real-time file monitoring
- Automatic firmware updates on file save
- Debounce to prevent duplicate updates
- Error handling and status reporting

**Usage:**
```bash
# Start watcher in one terminal
python scripts/watch_firmware.py

# Edit firmware files in another terminal
vim pico_firmware/main.py  # Auto-updates when saved

# Start API in third terminal  
make dev
```

## Firmware Files Structure

```
pico_firmware/
    boot.py          # Auto-start script
    main.py          # Main servo controller
    servo_driver.py  # SG90 servo driver class
    pin_config.py    # Pin configuration
```

## Current Firmware Configuration

### Servo Movement Settings
- **Smooth movements enabled by default**
- **Speed:** 200% slower than original
- **Steps:** 30 (increased from 20)
- **Delay:** 0.1s per step (increased from 0.05s)
- **Material sequence delays:**
  - Vertical movement: 1.0s delay
  - Hold position: 6.0s (for dropping waste)
  - Return to base: 1.0s delay

### Pin Configuration
- **Vertical Servo:** GP2 (Pin 2) - Range: -90° to 90°
- **Horizontal Servo:** GP3 (Pin 3) - Range: -20° to 20°
- **Status LED:** GPIO25 (Internal LED)
- **UART:** GP0 (TX), GP1 (RX)

### Material Positions
```python
material_positions = {
    "plastic": {"vertical": -90, "horizontal": -20},
    "glass": {"vertical": -90, "horizontal": 20},
    "pet": {"vertical": 90, "horizontal": -20},
    "organic": {"vertical": 90, "horizontal": 20}
}
```

## API Integration

### Available Commands
- `ANGLE:90` - Legacy single servo control
- `VERTICAL:45` - Control vertical servo
- `HORIZONTAL:10` - Control horizontal servo
- `MATERIAL:plastic` - Execute material sequence
- `BASE` - Return both servos to center position

### API Endpoints
- **Health Check:** `GET /health`
- **Servo Status:** `GET /api/servo/status`
- **Set Angle:** `POST /api/servo/angle`
- **Material Control:** `POST /api/servo/material`

## Troubleshooting

### Common Issues

1. **Pico Not Connected**
   - Check `/dev/ttyACM0` exists
   - Verify USB connection
   - Restart Pico with BOOTSEL if needed

2. **Upload Failed**
   - Ensure Pico is in MicroPython mode (not BOOTSEL)
   - Check permissions: `sudo usermod -a -G dialout $USER`
   - Kill blocking processes: `pkill -f screen`

3. **No Response from Pico**
   - Check if main.py is running
   - Verify boot.py imports main.py
   - Test with mpremote: `mpremote connect /dev/ttyACM0 repl`

### Debug Commands
```bash
# Check Pico connection
ls -la /dev/ttyACM0

# Test serial communication
echo "ANGLE:90" > /dev/ttyACM0

# Connect to Pico REPL
mpremote connect /dev/ttyACM0 repl

# Check running processes
ps aux | grep uvicorn
```

## Development Workflow

### Recommended Setup
1. **Terminal 1:** `python scripts/watch_firmware.py`
2. **Terminal 2:** Edit firmware files
3. **Terminal 3:** `make dev` for API server

### Manual Workflow
1. Edit firmware files
2. Run `make update-firmware`
3. Start API with `make dev`
4. Test with curl or API client

## Performance Notes

### Current Settings
- **Movement Speed:** Much slower and gentler
- **Mechanical Stress:** Reduced due to smooth transitions
- **Response Time:** Increased for better precision
- **Power Consumption:** More stable due to gradual movements

### Fine-Tuning
Edit `servo_driver.py` to adjust:
- `steps` parameter for smoothness
- `delay` parameter for speed
- Movement ranges in `pin_config.py`

## Safety Considerations

- Servos now move gently to reduce mechanical stress
- Longer delays ensure proper material dropping
- Smooth transitions prevent sudden movements
- Status LED indicates operational state

---

*Last Updated: April 10, 2026*
*Author: AI Assistant*
