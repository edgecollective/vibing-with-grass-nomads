# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ IMPORTANT: Start Here

**Before working on this repository, ALWAYS read the development logs first:**
1. Read `ai_agents/CLAUDE_LOG.md` to understand the complete development history
2. Review recent entries to understand current state and recent changes
3. Check for any pending issues or ongoing development activities

## Project Overview

**Vibing with Grass Nomads** is a production-ready CircuitPython IoT system for remote water depth monitoring with satellite communication capabilities.

### System Description
- **Primary Purpose**: Autonomous water depth monitoring in remote locations
- **Hardware Platform**: ItsyBitsy M4 Express with multiple sensors and communication modules
- **Communication**: Iridium satellite network via RockBlock 9602 modem
- **Power Management**: Ultra-low power operation with TPL5110 timer-controlled wake cycles
- **Data Persistence**: SD card logging with state management across power cycles

### Key Features
- **Scheduled Transmissions**: Twice daily (5AM & 1PM PST/PDT) satellite data uplinks
- **10-Minute Wake Cycles**: TPL5110-controlled power cycling for battery conservation  
- **Robust Error Handling**: Automatic retry logic with exponential backoff
- **Timezone Intelligence**: Automatic PST/PDT handling with DST transitions
- **State Persistence**: JSON state files and CSV logging survive power cycles
- **Interactive Setup**: Calibration tools and comprehensive diagnostics

### Hardware Components
- ItsyBitsy M4 Express (main controller)
- RockBlock 9602 (Iridium satellite modem)
- Adafruit DS3231 (precision RTC with temperature compensation)  
- TPL5110 (low-power timer for wake cycles)
- Analog pressure sensor (hydrostatic water depth measurement)
- MicroSD card (data logging and state persistence)
- LiPo battery with voltage monitoring

## Development Logging

**IMPORTANT**: All significant development activities must be logged to `ai_agents/CLAUDE_LOG.md`. This includes:
- New features or components added
- Bug fixes and their solutions
- Refactoring activities
- Architecture changes
- Build/deployment modifications
- Test additions or changes

Each log entry should include timestamp, activity type, description, files modified, and any important context.

## Repository Structure

- `.claude/` - Claude Code configuration directory
- `ai_agents/` - AI agent tooling and development logs
  - `CLAUDE_LOG.md` - Running log of all significant development activities
- `circuitpython/` - Main CircuitPython application code
  - `main.py` - Primary application orchestrating wake cycles and transmissions
  - `config.py` - Hardware configuration and system parameters
  - `sensor.py` - Pressure sensor reading and water depth calculation
  - `time_manager.py` - RTC management with PST/PDT timezone handling
  - `satellite.py` - RockBlock satellite communication with retry logic
  - `storage_manager.py` - SD card state persistence and data logging
  - `power_manager.py` - TPL5110 power management and battery monitoring
  - `setup_calibration.py` - Interactive setup and calibration tools
  - `libraries_needed.txt` - Required CircuitPython libraries
  - `README.md` - Comprehensive project documentation

## Development Commands

This is a CircuitPython project - no traditional build process required:

1. **Deploy to Hardware**: Copy `.py` files to CIRCUITPY drive root
2. **Initial Setup**: Upload `setup_calibration.py` as `main.py` for first-time configuration
3. **Production Deploy**: Replace with actual `main.py` after setup completion
4. **Library Installation**: Download libraries from circuitpython.org/libraries to `/lib` folder

## Architecture Notes

### Modular Design
The system uses a modular architecture with specialized classes for each hardware component:
- **Separation of Concerns**: Each module handles one aspect (sensor, communication, storage, etc.)
- **Error Isolation**: Component failures don't cascade to entire system
- **Easy Testing**: Individual modules can be tested independently

### Power Management Strategy
- **Wake Cycle**: 10-minute intervals controlled by TPL5110 hardware timer
- **Transmission Windows**: Only at scheduled times (5AM/1PM) to conserve satellite airtime
- **Battery Protection**: Automatic transmission skipping when battery is critically low
- **Sleep Mode**: All components put into low-power states between cycles

### State Persistence
- **JSON State Files**: System state survives power cycles via SD card storage
- **Retry Logic**: Failed transmissions automatically retried on subsequent wake cycles
- **Data Logging**: All sensor readings logged regardless of transmission success
- **Error Recovery**: System designed to recover from component failures gracefully

## Conventions and Best Practices

- Use the linux command `date` after completing any TODO list item
- When adding entries to the log, use `date` and ensure accurate timestamps for EDT timezone for each entry

## AI Workflow Instructions

### Session Wrapping
- When the phrase "wrap the session" is used, perform the following steps:
  - Reread the development logs in `ai_agents/CLAUDE_LOG.md`
  - Make microcommits for every outstanding git change and new project files
  - Update the development logs with a session summary
  - Make a final commit of the updated logs