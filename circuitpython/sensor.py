"""
Pressure sensor handling for water depth measurement
Converts analog pressure reading to water depth in feet
"""

import analogio
import time
from config import *

class PressureSensor:
    def __init__(self):
        """Initialize pressure sensor on analog pin"""
        self.analog_pin = analogio.AnalogIn(PRESSURE_SENSOR_PIN)
        self.calibration_offset = 0.0  # Can be adjusted for sensor calibration
        
    def read_raw_value(self):
        """Read raw ADC value (0-4095 for 12-bit)"""
        return self.analog_pin.value
        
    def read_voltage(self):
        """Convert raw ADC to voltage"""
        raw_value = self.read_raw_value()
        voltage = (raw_value / PRESSURE_SENSOR_RESOLUTION) * PRESSURE_SENSOR_VREF
        return voltage
        
    def read_pressure_psi(self):
        """Convert voltage to pressure in PSI"""
        voltage = self.read_voltage()
        
        # Linear conversion from voltage to pressure
        # Assumes sensor outputs 0.5V to 4.5V for 0 to max pressure
        # Adjust these values based on your specific pressure sensor datasheet
        voltage_min = 0.5
        voltage_max = 4.5
        
        if voltage < voltage_min:
            voltage = voltage_min
        elif voltage > voltage_max:
            voltage = voltage_max
            
        # Linear interpolation
        pressure_range = PRESSURE_SENSOR_MAX_PRESSURE - PRESSURE_SENSOR_MIN_PRESSURE
        voltage_range = voltage_max - voltage_min
        
        pressure = PRESSURE_SENSOR_MIN_PRESSURE + (
            (voltage - voltage_min) / voltage_range
        ) * pressure_range
        
        return pressure + self.calibration_offset
        
    def read_water_depth_feet(self):
        """Convert pressure to water depth in feet"""
        pressure_psi = self.read_pressure_psi()
        
        # Subtract atmospheric pressure to get gauge pressure
        gauge_pressure = pressure_psi - ATMOSPHERIC_PRESSURE
        
        # Convert to water depth (feet)
        # 1 foot of water = 0.433 psi
        if gauge_pressure <= 0:
            return 0.0
            
        depth_feet = gauge_pressure / WATER_DENSITY_FACTOR
        return max(0.0, depth_feet)  # Ensure non-negative depth
        
    def take_averaged_reading(self, num_samples=10, delay_ms=100):
        """Take multiple readings and return average for better accuracy"""
        readings = []
        
        for _ in range(num_samples):
            readings.append(self.read_water_depth_feet())
            time.sleep(delay_ms / 1000.0)
            
        # Remove outliers (simple method: remove highest and lowest)
        if len(readings) > 2:
            readings.sort()
            readings = readings[1:-1]  # Remove first and last
            
        return sum(readings) / len(readings) if readings else 0.0
        
    def calibrate_zero(self, num_samples=50):
        """Calibrate sensor to zero depth (call when sensor is at atmospheric pressure)"""
        print("Calibrating pressure sensor to zero depth...")
        pressure_readings = []
        
        for i in range(num_samples):
            pressure_readings.append(self.read_pressure_psi())
            time.sleep(0.1)
            if (i + 1) % 10 == 0:
                print(f"Calibration progress: {i + 1}/{num_samples}")
                
        avg_pressure = sum(pressure_readings) / len(pressure_readings)
        self.calibration_offset = ATMOSPHERIC_PRESSURE - avg_pressure
        
        print(f"Calibration complete. Offset: {self.calibration_offset:.3f} psi")
        return self.calibration_offset
        
    def get_sensor_diagnostics(self):
        """Return diagnostic information about sensor readings"""
        raw = self.read_raw_value()
        voltage = self.read_voltage()
        pressure = self.read_pressure_psi()
        depth = self.read_water_depth_feet()
        
        return {
            "raw_adc": raw,
            "voltage": round(voltage, 3),
            "pressure_psi": round(pressure, 2),
            "depth_feet": round(depth, 2),
            "calibration_offset": round(self.calibration_offset, 3)
        }
        
    def deinit(self):
        """Clean up resources"""
        self.analog_pin.deinit()