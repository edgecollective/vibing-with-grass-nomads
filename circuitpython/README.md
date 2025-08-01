# Water Depth Monitor - CircuitPython Implementation

A robust IoT water depth monitoring system using satellite communication for remote deployment.

## Hardware Components

- **ItsyBitsy M4 Express** - Main microcontroller (CircuitPython compatible)
- **RockBlock 9602** - Iridium satellite modem for data transmission
- **Adafruit DS3231** - Precision real-time clock with temperature compensation
- **TPL5110** - Low power timer for automated wake cycles
- **Pressure Sensor** - Analog output (0.5-4.5V) for hydrostatic pressure measurement
- **MicroSD Card** - Data logging and state persistence
- **LiPo Battery** - Power source with voltage monitoring

## System Overview

The system operates on a 10-minute wake cycle controlled by the TPL5110:

1. **Wake Up** - TPL5110 powers on the system every 10 minutes
2. **Time Check** - DS3231 RTC provides accurate Pacific Time (PST/PDT)
3. **Transmission Window** - Sends data at 5:00 AM and 1:00 PM
4. **Sensor Reading** - Measures water depth via pressure sensor
5. **Satellite Communication** - Transmits data via RockBlock 9602
6. **Data Logging** - Records all readings and transmission status to SD card
7. **Power Down** - Signals TPL5110 to cut power until next cycle

## Pin Connections

| Component | Pin | ItsyBitsy M4 |
|-----------|-----|--------------|
| Pressure Sensor | Analog Out | A0 |
| TPL5110 | Done Signal | D5 |
| RockBlock | TX | D1 |
| RockBlock | RX | D0 |
| RockBlock | Sleep | D6 |
| SD Card | CS | D10 |
| DS3231 | SDA | SDA |
| DS3231 | SCL | SCL |
| SD Card | MOSI | MOSI |
| SD Card | MISO | MISO |
| SD Card | SCK | SCK |
| Status LED | Built-in | D13 |

## Installation

### 1. CircuitPython Setup

1. Install CircuitPython 8.x or later on ItsyBitsy M4
2. Download required libraries from [circuitpython.org/libraries](https://circuitpython.org/libraries)
3. Copy libraries to `/lib` folder on CIRCUITPY drive

### 2. Required Libraries

See `libraries_needed.txt` for complete list:

- `adafruit_ds3231.mpy`
- `adafruit_rockblock.mpy`
- `adafruit_sdcard.mpy`
- `adafruit_bus_device/` (folder)

### 3. Code Deployment

1. Copy all `.py` files to root of CIRCUITPY drive
2. Rename `setup_calibration.py` to `main.py` for initial setup
3. After setup, rename actual `main.py` to replace setup file

## Initial Setup & Calibration

### 1. Hardware Assembly

Connect all components according to pin diagram above. Ensure:
- Pressure sensor is properly sealed for underwater use
- SD card is formatted as FAT32
- Battery voltage divider provides 0-3.3V range to analog pin

### 2. System Configuration

1. Upload `setup_calibration.py` as `main.py`
2. Connect to serial console
3. Run through setup menu:
   - Test hardware components
   - Set RTC time (Pacific timezone)
   - Calibrate pressure sensor at zero depth
   - Initialize SD card storage
   - Test satellite communication (optional - uses airtime)

### 3. Sensor Calibration

**Critical**: Calibrate pressure sensor at atmospheric pressure (zero depth):

1. Remove sensor from water
2. Run calibration routine
3. System calculates offset for accurate depth readings

## Configuration

### Timing Settings (`config.py`)

```python
TRANSMISSION_TIMES = [
    (5, 0),   # 5:00 AM PST/PDT
    (13, 0),  # 1:00 PM PST/PDT
]
```

### Sensor Configuration

```python
PRESSURE_SENSOR_VREF = 3.3          # Reference voltage
PRESSURE_SENSOR_RESOLUTION = 4096   # 12-bit ADC
ATMOSPHERIC_PRESSURE = 14.7         # psi at sea level
WATER_DENSITY_FACTOR = 0.433        # psi per foot of water
```

### Power Management

```python
LOW_BATTERY_THRESHOLD = 3.2  # Volts
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_MINUTES = [5, 15, 30]
```

## Operation

### Normal Operation Cycle

1. **System powers on** via TPL5110 every 10 minutes
2. **Battery check** - Emergency shutdown if critically low
3. **Time evaluation** - Check if transmission window is active
4. **Sensor reading** - Always log current depth
5. **Transmission logic**:
   - Send if scheduled transmission time (±5 minutes)
   - Retry failed transmissions from previous cycles
   - Skip if battery too low
6. **Data logging** - All readings and transmission results to SD card
7. **Power down** - Signal TPL5110 to cut power

### Data Transmission

Messages sent via satellite contain:
```
WD:YYYYMMDD_HHMMSS,depth_ft,pressure_raw,battery_v
```

Example: `WD:20231201_050015,2.45,3891,4.15`

### Error Handling

- **Communication failures**: Automatic retry with exponential backoff
- **Low battery**: Skip transmissions to preserve power
- **Sensor errors**: Log error and continue with system operation
- **SD card issues**: Continue operation without logging
- **RTC drift**: System still functional, may affect transmission timing

## Data Storage

### SD Card Structure

```
/sd/
├── state.json              # System state persistence
├── water_log.csv           # Sensor readings and transmission log
├── errors.log              # Error messages with timestamps
├── logs/                   # Additional log files
├── data/                   # Raw data exports
└── backup/                 # State file backups
```

### State Persistence

System maintains state across power cycles including:
- Last successful transmission times
- Failed transmission attempts for retry
- Sensor calibration values
- Battery status history
- Wake cycle counters

## Troubleshooting

### Common Issues

**No satellite communication:**
- Check RockBlock connections (TX/RX, power, sleep pin)
- Verify clear sky view for satellite signal
- Test with setup script first

**Incorrect time:**
- Re-calibrate RTC using setup script
- Check timezone configuration (PST/PDT)
- Verify RTC battery if using DS3231 with backup battery

**Sensor reading errors:**
- Recalibrate at atmospheric pressure
- Check analog pin connections
- Verify sensor power supply voltage

**SD card issues:**
- Reformat as FAT32
- Check SPI connections
- Verify chip select pin configuration

**Power issues:**
- Check TPL5110 connections and timing
- Verify battery voltage monitoring circuit
- Test "done" signal pin

### Debug Mode

Enable debug output by setting `DEBUG_MODE = True` in `config.py`. This provides:
- Detailed console output
- Step-by-step operation logging
- Error details and stack traces
- Timing information

### LED Status Indicators

- **3 quick blinks**: System startup
- **5 quick blinks**: Successful transmission
- **1 long blink**: Transmission failure
- **10 rapid blinks**: System error
- **2 slow blinks**: Normal shutdown

## Advanced Configuration

### Custom Transmission Schedule

Modify `TRANSMISSION_TIMES` in `config.py`:
```python
TRANSMISSION_TIMES = [
    (6, 0),    # 6:00 AM
    (12, 0),   # 12:00 PM  
    (18, 0),   # 6:00 PM
]
```

### Sensor Calibration

For different pressure sensors, adjust:
```python
# Voltage range from sensor datasheet
voltage_min = 0.5  # Minimum output voltage
voltage_max = 4.5  # Maximum output voltage

# Pressure range
PRESSURE_SENSOR_MIN_PRESSURE = 0.0   # Min pressure (psi)
PRESSURE_SENSOR_MAX_PRESSURE = 30.0  # Max pressure (psi)
```

### Power Optimization

- Reduce `max_wake_duration` for shorter operation cycles
- Adjust `LOW_BATTERY_THRESHOLD` based on battery characteristics
- Modify retry backoff timing for power conservation

## Monitoring & Maintenance

### Remote Monitoring

Satellite messages provide:
- Current water depth
- Battery voltage
- System timestamp
- Raw sensor values

### Maintenance Schedule

- **Monthly**: Check battery voltage logs
- **Quarterly**: Download SD card data, check for errors
- **Annually**: Recalibrate pressure sensor, replace backup battery

### Data Analysis

CSV log format allows easy analysis:
```python
import pandas as pd
data = pd.read_csv('water_log.csv')
print(data.describe())
```

## License

This project is designed for environmental monitoring and research applications. Please ensure compliance with local regulations for satellite communication devices.