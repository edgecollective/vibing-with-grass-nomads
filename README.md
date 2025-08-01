# Vibing with Grass Nomads

A production-ready CircuitPython IoT system for remote water depth monitoring with satellite communication capabilities.

## 🌊 Overview

**Vibing with Grass Nomads** is an autonomous water depth monitoring system designed for remote locations without cellular coverage. The system uses Iridium satellite communication to transmit water depth readings twice daily, making it ideal for environmental monitoring, water management, and research applications.

### Key Features

- **🛰️ Satellite Communication**: Iridium network via RockBlock 9602 modem
- **⚡ Ultra-Low Power**: TPL5110 timer-controlled 10-minute wake cycles
- **🕐 Scheduled Transmissions**: Twice daily at 5AM & 1PM PST/PDT
- **💾 Data Persistence**: SD card logging with state management across power cycles
- **🔋 Battery Protection**: Automatic power management and low-battery protection
- **⏰ Timezone Intelligence**: Automatic PST/PDT handling with DST transitions
- **🔧 Interactive Setup**: Comprehensive calibration and diagnostic tools
- **🛡️ Robust Error Handling**: Automatic retry logic with exponential backoff

## 🔧 Hardware Components

| Component | Purpose | Connection |
|-----------|---------|------------|
| **ItsyBitsy M4 Express** | Main microcontroller | - |
| **RockBlock 9602** | Iridium satellite modem | UART (D0/D1) + Sleep (D6) |
| **Adafruit DS3231** | Precision RTC with temperature compensation | I2C (SDA/SCL) |
| **TPL5110** | Low-power timer for wake cycles | Done signal (D5) |
| **Analog Pressure Sensor** | Hydrostatic water depth measurement | Analog input (A0) |
| **MicroSD Card** | Data logging and state persistence | SPI (D10 CS) |
| **LiPo Battery** | Power source with voltage monitoring | - |

## 🚀 Quick Start

### 1. Hardware Setup

1. **Assemble Hardware**: Connect components according to pin assignments in `circuitpython/config.py`
2. **Install CircuitPython**: Flash CircuitPython 8.x or later to ItsyBitsy M4
3. **Install Libraries**: Copy required libraries from `circuitpython/libraries_needed.txt` to `/lib` folder

### 2. Initial Configuration

1. **Upload Setup Tool**: Copy `setup_calibration.py` as `main.py` to CIRCUITPY drive
2. **Connect Serial**: Use serial console to access interactive setup menu
3. **Run Calibration**: Follow prompts to calibrate sensors and test components
4. **Deploy System**: Replace with actual `main.py` after setup completion

### 3. System Operation

The system automatically:
- Wakes every 10 minutes via TPL5110 timer
- Checks current time and transmission schedule  
- Reads water depth from pressure sensor
- Transmits data during scheduled windows (5AM/1PM PST/PDT)
- Logs all data to SD card
- Powers down until next wake cycle

## 📊 Data Format

Satellite transmissions use this format:
```
WD:YYYYMMDD_HHMMSS,depth_ft,pressure_raw,battery_v
```

Example: `WD:20250801_050015,2.45,3891,4.15`

## 🗂️ Project Structure

```
/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── CLAUDE.md                    # AI development guidelines
├── circuitpython/              # CircuitPython source code
│   ├── main.py                 # Main application orchestrator
│   ├── config.py               # Hardware configuration
│   ├── sensor.py               # Pressure sensor interface
│   ├── time_manager.py         # RTC and timezone management
│   ├── satellite.py            # RockBlock communication
│   ├── storage_manager.py      # SD card data persistence
│   ├── power_manager.py        # TPL5110 power management
│   ├── setup_calibration.py    # Interactive setup tools
│   ├── libraries_needed.txt    # Required CircuitPython libraries
│   └── README.md               # Detailed technical documentation
├── ai_agents/                  # AI development tools
│   └── CLAUDE_LOG.md           # Development activity log
├── data/                       # Data storage directory
└── lib/                        # CircuitPython libraries
```

## 🔧 Configuration

### Transmission Schedule

Modify scheduled transmission times in `circuitpython/config.py`:

```python
TRANSMISSION_TIMES = [
    (5, 0),   # 5:00 AM PST/PDT
    (13, 0),  # 1:00 PM PST/PDT
]
```

### Power Management

```python
LOW_BATTERY_THRESHOLD = 3.2  # Volts
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_MINUTES = [5, 15, 30]
```

### Sensor Calibration

```python
PRESSURE_SENSOR_VREF = 3.3          # Reference voltage
ATMOSPHERIC_PRESSURE = 14.7         # psi at sea level
WATER_DENSITY_FACTOR = 0.433        # psi per foot of water
```

## 📈 System Architecture

### Modular Design

The system uses a modular architecture with specialized classes:

- **`PowerManager`**: TPL5110 interface and battery monitoring
- **`TimeManager`**: DS3231 RTC with PST/PDT timezone support
- **`PressureSensor`**: Analog pressure sensor with depth calculation
- **`SatelliteModem`**: RockBlock 9602 communication with retry logic
- **`StorageManager`**: SD card state persistence and CSV logging

### Power Management Strategy

- **Wake Cycles**: 10-minute intervals controlled by TPL5110 hardware timer
- **Transmission Windows**: Only during scheduled times to conserve satellite airtime
- **Battery Protection**: Automatic transmission skipping when voltage is critically low
- **Sleep Mode**: All components enter low-power states between cycles

### State Persistence

- **JSON State Files**: System state survives power cycles via SD card
- **Retry Logic**: Failed transmissions automatically retried on subsequent cycles
- **Data Logging**: All sensor readings logged regardless of transmission success
- **Error Recovery**: System designed to gracefully recover from component failures

## 🛠️ Development

### Requirements

- CircuitPython 8.x or later
- Required libraries (see `circuitpython/libraries_needed.txt`)
- Hardware components listed above

### Development Commands

```bash
# No build process required for CircuitPython
# Simply copy .py files to CIRCUITPY drive

# For development logging
date  # Use after completing tasks (EDT timezone)
```

### Testing

1. **Component Testing**: Use `setup_calibration.py` for individual component tests
2. **System Integration**: Deploy full system and monitor via serial console
3. **Field Testing**: Validate satellite communication and power management

## 🔍 Troubleshooting

### Common Issues

**No satellite communication:**
- Verify clear sky view for satellite signal
- Check RockBlock connections (TX/RX, power, sleep pin)
- Test with setup script first

**Incorrect timing:**
- Recalibrate RTC using setup script
- Verify timezone configuration (PST/PDT)
- Check RTC backup battery if applicable

**Sensor reading errors:**
- Recalibrate at atmospheric pressure
- Verify analog pin connections and power supply

**Power issues:**
- Check TPL5110 connections and timing configuration
- Verify battery voltage monitoring circuit
- Test "done" signal pin operation

### LED Status Indicators

- **3 quick blinks**: System startup
- **5 quick blinks**: Successful transmission
- **1 long blink**: Transmission failure
- **10 rapid blinks**: System error
- **2 slow blinks**: Normal shutdown

### Debug Mode

Enable detailed logging by setting `DEBUG_MODE = True` in `config.py`.

## 📚 Documentation

- **`circuitpython/README.md`**: Comprehensive technical documentation
- **`CLAUDE.md`**: AI development guidelines and project context
- **`ai_agents/CLAUDE_LOG.md`**: Complete development history and notes

## 🛡️ Security & Safety

- **No secrets in code**: All sensitive data handled via external configuration
- **Battery protection**: Automatic shutdown prevents over-discharge
- **Error isolation**: Component failures don't cascade to entire system
- **Data integrity**: State persistence ensures no data loss during power cycles

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Read the development guidelines in `CLAUDE.md`
3. Check the development log in `ai_agents/CLAUDE_LOG.md` for context
4. Make your changes following existing code conventions
5. Test thoroughly with hardware setup
6. Submit a pull request with clear description

## 🌟 Use Cases

- **Environmental Monitoring**: Stream gauging and flood detection
- **Water Management**: Reservoir and tank level monitoring
- **Research Applications**: Long-term hydrological studies
- **Agricultural**: Irrigation system monitoring
- **Infrastructure**: Storm water management systems

## 📞 Support

For technical support:
1. Check troubleshooting section in `circuitpython/README.md`
2. Review development logs in `ai_agents/CLAUDE_LOG.md`
3. Open an issue with detailed description and hardware setup

---

**Built with ❤️ for environmental monitoring and water resource management**