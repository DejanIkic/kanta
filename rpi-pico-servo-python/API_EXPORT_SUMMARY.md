# RPi Pico Servo Control API - Export Summary

## Overview
Complete dual servo waste sorting system with material-based positioning, comprehensive API, and testing suite.

## API Endpoints Export

### Base URL: `http://localhost:8000`

### 1. System Endpoints
- **GET /** - Root endpoint with API info
- **GET /health** - System health check (database, Pico connection)

### 2. Material Positioning (NEW)
- **POST /api/servo/material/{material_type}**
  - Materials: `plastic`, `glass`, `pet`, `organic`
  - Sequence: Vertical (0.5s) + Horizontal (1.5s) + Base return (0.5s) = 2.5s total
  - Positions:
    - plastic: vertical -90°, horizontal -20°
    - glass: vertical -90°, horizontal 20°
    - pet: vertical 90°, horizontal -20°
    - organic: vertical 90°, horizontal 20°

### 3. Legacy Endpoints (Backward Compatibility)
- **POST /api/servo/{side}**
  - Sides: `left` (-20°), `right` (20°)
  - Maintains existing single servo functionality

### 4. Status & History
- **GET /api/servo/status** - Connection status and statistics
- **GET /api/servo/history** - Movement history (last 100)
- **GET /api/servo/history/{limit}** - Movement history with custom limit (1-1000)

## Hardware Configuration

### Servo Setup
- **Vertical Servo**: GP2, range -90° to 90°, wire: Yellow/Orange
- **Horizontal Servo**: GP3, range -20° to 20°, wire: Blue/White
- **Power**: VBUS (3.3V), GND
- **Communication**: USB Serial, 115200 baud

### Pico Firmware Commands
- `MATERIAL:{type}` - Full material sequence
- `VERTICAL:{angle}` - Direct vertical control (-90 to 90)
- `HORIZONTAL:{angle}` - Direct horizontal control (-20 to 20)
- `BASE:0` - Return to base position (0°, 0°)
- `ANGLE:{angle}` - Legacy single servo control

## Files Created

### 1. API Documentation
- **api_documentation.json** - Complete API specification with examples
- **api_endpoints.json** - OpenAPI specification from FastAPI

### 2. Test Collections
- **test_collection.json** - Postman collection with comprehensive tests
- **run_api_tests.py** - Python test runner with detailed reporting
- **api_test_results.json** - Latest test results

### 3. Enhanced System Files
- **pico_firmware/main.py** - Dual servo control with sequential movement
- **pico_firmware/servo_driver.py** - Multi-servo instance support
- **pico_firmware/pin_config.py** - Dual servo pin configuration
- **rpi_api/servo_service.py** - Dual servo API methods
- **rpi_api/main.py** - New material endpoint
- **rpi_api/config.py** - Material positions and delays
- **rpi_api/models.py** - Enhanced database models

## Testing Results

### Current Status (No Hardware Connected)
- **API Structure**: 100% Working
- **Validation**: 100% Working  
- **Error Handling**: 100% Working
- **Hardware Operations**: Expected failures (no Pico connected)

### Test Categories
1. **System Health**: PASS
2. **Material Validation**: PASS
3. **Invalid Input Rejection**: PASS
4. **Hardware Operations**: FAIL (expected - no hardware)

### Expected Behavior with Hardware
- All material positioning endpoints should return 200 OK
- Response time ~2500ms (2.5s sequence)
- Database logging of all movements
- Real-time servo control

## Usage Examples

### Material Positioning
```bash
# Position for plastic waste
curl -X POST "http://localhost:8000/api/servo/material/plastic"

# Position for glass waste  
curl -X POST "http://localhost:8000/api/servo/material/glass"
```

### Legacy Control
```bash
# Move servo left
curl -X POST "http://localhost:8000/api/servo/left"

# Move servo right
curl -X POST "http://localhost:8000/api/servo/right"
```

### System Status
```bash
# Check system health
curl -X GET "http://localhost:8000/health"

# Get servo status
curl -X GET "http://localhost:8000/api/servo/status"
```

## Sequence Timing
1. **Vertical Movement**: Instant + 0.5s delay
2. **Horizontal Movement**: Instant + 1.5s delay (trash drop)
3. **Base Return**: Instant + 0.5s delay
4. **Total Sequence**: ~2.5 seconds
5. **API Response**: After sequence completion

## Database Schema
- **ServoMovement** table enhanced with:
  - `vertical_angle` (-90 to 90)
  - `horizontal_angle` (-20 to 20)
  - `material_type` (plastic, glass, pet, organic)
  - `command_type` (material, vertical, horizontal, base, legacy)

## Error Codes
- **200** - Success
- **400** - Bad Request
- **422** - Validation Error (invalid material/side)
- **500** - Internal Server Error (hardware/connection issues)

## Deployment Notes
1. Flash updated firmware to Pico
2. Connect servos to GP2 (vertical) and GP3 (horizontal)
3. Update serial port in config if needed
4. Run API server: `python -m uvicorn rpi_api.main:app --host 0.0.0.0 --port 8000`
5. Test with provided test collection

## Future Enhancements
- Hardware abstraction layer for RPi GPIO control
- Additional material types
- Custom sequence timing
- Real-time servo position feedback
- Mobile app integration
