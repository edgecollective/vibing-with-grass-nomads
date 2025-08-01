"""
Configuration settings for Water Depth Monitor
ItsyBitsy M4 + RockBlock 9602 + DS3231 RTC + TPL5110
"""

import board

# Hardware Pin Assignments
PRESSURE_SENSOR_PIN = board.A0      # Analog pin for pressure sensor
TPL5110_DONE_PIN = board.D5         # Signal TPL5110 we're done
ROCKBLOCK_TX_PIN = board.D1         # UART TX to RockBlock
ROCKBLOCK_RX_PIN = board.D0         # UART RX from RockBlock
ROCKBLOCK_SLEEP_PIN = board.D6      # Sleep control for RockBlock
SD_CS_PIN = board.D10               # SD card chip select
STATUS_LED_PIN = board.D13          # Built-in LED for status

# I2C pins for DS3231 RTC (built-in I2C)
I2C_SDA = board.SDA
I2C_SCL = board.SCL

# SPI pins for SD card (built-in SPI)
SPI_MOSI = board.MOSI
SPI_MISO = board.MISO
SPI_SCK = board.SCK

# Timing Configuration
TRANSMISSION_TIMES = [
    (5, 0),   # 5:00 AM
    (13, 0),  # 1:00 PM (13:00 in 24h format)
]

# Timezone offset from UTC (will need to handle PST/PDT)
# PST = UTC-8, PDT = UTC-7
TIMEZONE_OFFSET_PST = -8
TIMEZONE_OFFSET_PDT = -7

# Sensor Configuration
PRESSURE_SENSOR_VREF = 3.3          # Reference voltage
PRESSURE_SENSOR_RESOLUTION = 4096   # 12-bit ADC (2^12)
PRESSURE_SENSOR_MIN_PRESSURE = 0.0  # Min pressure (psi or kPa)
PRESSURE_SENSOR_MAX_PRESSURE = 30.0 # Max pressure (adjust based on sensor)

# Water depth calculation (pressure to depth conversion)
# Depth (feet) = (Pressure - atmospheric) / (fluid_density * gravity)
ATMOSPHERIC_PRESSURE = 14.7  # psi at sea level
WATER_DENSITY_FACTOR = 0.433 # psi per foot of water

# Communication Configuration
ROCKBLOCK_BAUD_RATE = 19200
TRANSMISSION_TIMEOUT = 300   # 5 minutes max for transmission
MAX_RETRY_ATTEMPTS = 3
RETRY_BACKOFF_MINUTES = [5, 15, 30]  # Progressive backoff

# File paths on SD card
STATE_FILE = "/sd/state.json"
LOG_FILE = "/sd/water_log.csv"
ERROR_LOG = "/sd/errors.log"

# Message format for satellite transmission
MESSAGE_FORMAT = "WD:{timestamp},{depth_ft:.2f},{pressure_raw},{battery_v:.2f}"

# Power management
LOW_BATTERY_THRESHOLD = 3.2  # Volts
BATTERY_MONITOR_PIN = board.VOLTAGE_MONITOR  # Built-in battery monitoring

# Debug mode (set to False for production)
DEBUG_MODE = True