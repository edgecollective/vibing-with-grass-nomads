"""
RockBlock 9602 satellite modem communication
Handles message transmission with retry logic and error recovery
"""

import time
import busio
import digitalio
import adafruit_rockblock
from config import *

class SatelliteModem:
    def __init__(self):
        """Initialize RockBlock 9602 modem"""
        # Setup UART for RockBlock communication
        self.uart = busio.UART(
            ROCKBLOCK_TX_PIN, 
            ROCKBLOCK_RX_PIN, 
            baudrate=ROCKBLOCK_BAUD_RATE,
            timeout=10
        )
        
        # Setup sleep control pin
        self.sleep_pin = digitalio.DigitalInOut(ROCKBLOCK_SLEEP_PIN)
        self.sleep_pin.direction = digitalio.Direction.OUTPUT
        self.sleep_pin.value = False  # Wake up RockBlock
        
        # Initialize RockBlock library
        self.rockblock = None
        self.is_initialized = False
        
    def initialize(self):
        """Initialize and test RockBlock modem"""
        try:
            # Wake up RockBlock
            self.wake_up()
            time.sleep(2)  # Give it time to wake up
            
            # Initialize RockBlock
            self.rockblock = adafruit_rockblock.RockBlock(self.uart)
            
            # Test communication
            if self.test_communication():
                self.is_initialized = True
                if DEBUG_MODE:
                    print("RockBlock initialized successfully")
                return True
            else:
                if DEBUG_MODE:
                    print("RockBlock communication test failed")
                return False
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"RockBlock initialization error: {e}")
            return False
            
    def wake_up(self):
        """Wake up RockBlock from sleep mode"""
        self.sleep_pin.value = False  # Active low
        time.sleep(1)
        
    def sleep(self):
        """Put RockBlock into sleep mode to save power"""
        if self.rockblock:
            try:
                self.rockblock.sleep()
            except:
                pass  # Ignore errors when putting to sleep
        self.sleep_pin.value = True  # Put into sleep mode
        
    def test_communication(self):
        """Test basic communication with RockBlock"""
        try:
            if not self.rockblock:
                return False
                
            # Try to get signal quality
            signal_quality = self.rockblock.signal_quality
            if DEBUG_MODE:
                print(f"Signal quality: {signal_quality}")
                
            # Check if we got a valid response
            return signal_quality is not None
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Communication test error: {e}")
            return False
            
    def get_signal_quality(self):
        """Get current satellite signal quality (0-5)"""
        try:
            if not self.is_initialized:
                if not self.initialize():
                    return -1
                    
            return self.rockblock.signal_quality
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error getting signal quality: {e}")
            return -1
            
    def send_message(self, message, max_attempts=MAX_RETRY_ATTEMPTS):
        """
        Send message via satellite with retry logic
        Returns: (success, attempt_count, error_message)
        """
        if not message:
            return False, 0, "Empty message"
            
        # Ensure message isn't too long (RockBlock has ~340 byte limit)
        if len(message.encode()) > 340:
            message = message[:337] + "..."
            
        last_error = ""
        
        for attempt in range(max_attempts):
            try:
                if DEBUG_MODE:
                    print(f"Transmission attempt {attempt + 1}/{max_attempts}")
                    print(f"Message: {message}")
                
                # Initialize if needed
                if not self.is_initialized:
                    if not self.initialize():
                        last_error = "Failed to initialize RockBlock"
                        continue
                
                # Check signal quality first
                signal_quality = self.get_signal_quality()
                if signal_quality < 1:
                    last_error = f"Poor signal quality: {signal_quality}"
                    if DEBUG_MODE:
                        print(last_error)
                    time.sleep(30)  # Wait for better signal
                    continue
                
                if DEBUG_MODE:
                    print(f"Signal quality: {signal_quality}/5")
                
                # Send message
                success = self.rockblock.text_message(message)
                
                if success:
                    if DEBUG_MODE:
                        print("Message sent successfully!")
                    return True, attempt + 1, ""
                else:
                    last_error = "RockBlock reported send failure"
                    
            except Exception as e:
                last_error = f"Exception during send: {str(e)}"
                if DEBUG_MODE:
                    print(last_error)
            
            # Progressive backoff between attempts
            if attempt < max_attempts - 1:
                backoff_minutes = RETRY_BACKOFF_MINUTES[min(attempt, len(RETRY_BACKOFF_MINUTES) - 1)]
                if DEBUG_MODE:
                    print(f"Waiting {backoff_minutes} minutes before retry...")
                time.sleep(backoff_minutes * 60)
        
        # All attempts failed
        return False, max_attempts, last_error
        
    def format_data_message(self, timestamp, depth_feet, pressure_raw, battery_voltage):
        """Format sensor data into transmission message"""
        return MESSAGE_FORMAT.format(
            timestamp=timestamp,
            depth_ft=depth_feet,
            pressure_raw=pressure_raw,
            battery_v=battery_voltage
        )
        
    def send_data_reading(self, sensor_data, time_manager):
        """Send a sensor data reading via satellite"""
        try:
            # Get timestamp
            timestamp = time_manager.get_timestamp_string()
            
            # Format message
            message = self.format_data_message(
                timestamp=timestamp,
                depth_feet=sensor_data["depth_feet"],
                pressure_raw=sensor_data["raw_adc"],
                battery_voltage=sensor_data.get("battery_voltage", 0.0)
            )
            
            # Send with retries
            success, attempts, error = self.send_message(message)
            
            return {
                "success": success,
                "attempts": attempts,
                "error": error,
                "message": message,
                "timestamp": timestamp,
                "signal_quality": self.get_signal_quality()
            }
            
        except Exception as e:
            return {
                "success": False,
                "attempts": 0,
                "error": f"Exception formatting/sending data: {str(e)}",
                "message": "",
                "timestamp": "",
                "signal_quality": -1
            }
            
    def get_diagnostics(self):
        """Get modem diagnostic information"""
        try:
            diagnostics = {
                "initialized": self.is_initialized,
                "signal_quality": self.get_signal_quality(),
                "sleep_pin_state": self.sleep_pin.value
            }
            
            if self.rockblock and self.is_initialized:
                try:
                    # Try to get additional info from RockBlock
                    diagnostics["model"] = "RockBlock 9602"
                    diagnostics["uart_ready"] = True
                except:
                    diagnostics["uart_ready"] = False
            else:
                diagnostics["uart_ready"] = False
                
            return diagnostics
            
        except Exception as e:
            return {
                "initialized": False,
                "signal_quality": -1,
                "error": str(e)
            }
            
    def deinit(self):
        """Clean up resources and put modem to sleep"""
        try:
            self.sleep()
            if self.uart:
                self.uart.deinit()
        except:
            pass  # Ignore cleanup errors