"""
SD card storage management for state persistence and data logging
Handles JSON state files, CSV data logs, and error logging
"""

import os
import json
import time
import busio
import digitalio
import adafruit_sdcard
import storage
from config import *

class StorageManager:
    def __init__(self):
        """Initialize SD card storage"""
        self.spi = None
        self.sdcard = None
        self.vfs = None
        self.is_mounted = False
        self.mount_point = "/sd"
        
        # Default state structure
        self.default_state = {
            "last_successful_transmissions": {},  # {"05:00": "timestamp", "13:00": "timestamp"}
            "failed_attempts": [],  # List of failed transmission attempts
            "last_wake_time": "",
            "total_wake_cycles": 0,
            "sensor_calibration_offset": 0.0,
            "battery_low_count": 0,
            "system_errors": []
        }
        
    def initialize(self):
        """Initialize and mount SD card"""
        try:
            # Setup SPI for SD card
            self.spi = busio.SPI(SPI_SCK, SPI_MOSI, SPI_MISO)
            
            # Setup SD card chip select
            cs_pin = digitalio.DigitalInOut(SD_CS_PIN)
            
            # Initialize SD card
            self.sdcard = adafruit_sdcard.SDCard(self.spi, cs_pin)
            self.vfs = storage.VfsFat(self.sdcard)
            
            # Mount SD card
            storage.mount(self.vfs, self.mount_point)
            self.is_mounted = True
            
            # Create necessary directories
            self._ensure_directory_structure()
            
            if DEBUG_MODE:
                print("SD card mounted successfully")
            return True
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"SD card initialization failed: {e}")
            self.is_mounted = False
            return False
            
    def _ensure_directory_structure(self):
        """Create necessary directories on SD card"""
        try:
            directories = ["/sd/logs", "/sd/data", "/sd/backup"]
            for directory in directories:
                try:
                    os.mkdir(directory)
                except OSError:
                    pass  # Directory already exists
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error creating directories: {e}")
                
    def load_state(self):
        """Load system state from JSON file"""
        if not self.is_mounted:
            if not self.initialize():
                return self.default_state.copy()
                
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                
            # Merge with default state to handle new fields
            merged_state = self.default_state.copy()
            merged_state.update(state)
            
            if DEBUG_MODE:
                print("State loaded from SD card")
            return merged_state
            
        except (OSError, ValueError, KeyError) as e:
            if DEBUG_MODE:
                print(f"Error loading state (using defaults): {e}")
            return self.default_state.copy()
            
    def save_state(self, state):
        """Save system state to JSON file"""
        if not self.is_mounted:
            if not self.initialize():
                return False
                
        try:
            # Create backup first
            try:
                with open(STATE_FILE, 'r') as f:
                    backup_data = f.read()
                with open("/sd/backup/state_backup.json", 'w') as f:
                    f.write(backup_data)
            except:
                pass  # Ignore backup errors
                
            # Save new state
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f)
                
            if DEBUG_MODE:
                print("State saved to SD card")
            return True
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error saving state: {e}")
            return False
            
    def log_sensor_reading(self, timestamp, sensor_data, transmission_result=None):
        """Log sensor reading to CSV file"""
        if not self.is_mounted:
            if not self.initialize():
                return False
                
        try:
            # Check if log file exists, create header if not
            file_exists = True
            try:
                with open(LOG_FILE, 'r'):
                    pass
            except OSError:
                file_exists = False
                
            with open(LOG_FILE, 'a') as f:
                if not file_exists:
                    # Write CSV header
                    f.write("timestamp,depth_feet,pressure_raw,battery_voltage,")
                    f.write("transmission_success,transmission_attempts,signal_quality,error\n")
                
                # Write data row
                tx_success = transmission_result.get("success", False) if transmission_result else False
                tx_attempts = transmission_result.get("attempts", 0) if transmission_result else 0
                signal_quality = transmission_result.get("signal_quality", -1) if transmission_result else -1
                error = transmission_result.get("error", "") if transmission_result else ""
                
                f.write(f"{timestamp},{sensor_data['depth_feet']:.2f},{sensor_data['raw_adc']},")
                f.write(f"{sensor_data.get('battery_voltage', 0.0):.2f},{tx_success},{tx_attempts},")
                f.write(f"{signal_quality},\"{error}\"\n")
                
            return True
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error logging sensor reading: {e}")
            return False
            
    def log_error(self, error_message, error_type="GENERAL"):
        """Log error message with timestamp"""
        if not self.is_mounted:
            if not self.initialize():
                return False
                
        try:
            timestamp = time.monotonic()  # Use monotonic time for error logging
            
            with open(ERROR_LOG, 'a') as f:
                f.write(f"{timestamp},{error_type},\"{error_message}\"\n")
                
            if DEBUG_MODE:
                print(f"Error logged: {error_type} - {error_message}")
            return True
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Failed to log error: {e}")
            return False
            
    def record_transmission_attempt(self, state, time_slot, success, error_message=""):
        """Record transmission attempt in state"""
        timestamp = time.monotonic()
        
        attempt_record = {
            "time_slot": time_slot,
            "timestamp": timestamp,
            "success": success,
            "error": error_message
        }
        
        if success:
            # Record successful transmission
            state["last_successful_transmissions"][time_slot] = timestamp
            
            # Remove any failed attempts for this time slot
            state["failed_attempts"] = [
                attempt for attempt in state["failed_attempts"]
                if attempt.get("time_slot") != time_slot
            ]
        else:
            # Record failed attempt
            state["failed_attempts"].append(attempt_record)
            
            # Limit failed attempts list size
            if len(state["failed_attempts"]) > 10:
                state["failed_attempts"] = state["failed_attempts"][-10:]
                
        return state
        
    def get_pending_transmissions(self, state, current_time_manager):
        """Get list of transmissions that need to be sent"""
        pending = []
        current_time = time.monotonic()
        
        # Check each scheduled transmission time
        for hour, minute in TRANSMISSION_TIMES:
            time_slot = f"{hour:02d}:{minute:02d}"
            
            # Check if we have a recent successful transmission for this slot
            last_success = state["last_successful_transmissions"].get(time_slot, 0)
            
            # Consider successful if transmitted within last 12 hours
            if current_time - last_success < 12 * 3600:
                continue
                
            # Check if we have recent failed attempts
            recent_failures = [
                attempt for attempt in state["failed_attempts"]
                if (attempt.get("time_slot") == time_slot and 
                    current_time - attempt.get("timestamp", 0) < 6 * 3600)
            ]
            
            if recent_failures:
                pending.append({
                    "time_slot": time_slot,
                    "retry_count": len(recent_failures),
                    "last_attempt": recent_failures[-1]
                })
            else:
                # New transmission needed
                is_time, _ = current_time_manager.is_transmission_time()
                if is_time:
                    pending.append({
                        "time_slot": time_slot,
                        "retry_count": 0,
                        "last_attempt": None
                    })
                    
        return pending
        
    def cleanup_old_data(self, days_to_keep=30):
        """Clean up old log files to save space"""
        if not self.is_mounted:
            return False
            
        try:
            current_time = time.monotonic()
            cutoff_time = current_time - (days_to_keep * 24 * 3600)
            
            # This is a simplified cleanup - in a real implementation,
            # you'd want to parse the CSV and remove old entries
            # For now, just rotate the log file if it gets too big
            
            try:
                stat = os.stat(LOG_FILE)
                if stat[6] > 1000000:  # If larger than 1MB
                    # Rotate log file
                    os.rename(LOG_FILE, f"{LOG_FILE}.old")
                    if DEBUG_MODE:
                        print("Log file rotated")
            except OSError:
                pass  # File doesn't exist or can't be rotated
                
            return True
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error during cleanup: {e}")
            return False
            
    def get_storage_info(self):
        """Get storage diagnostic information"""
        info = {
            "mounted": self.is_mounted,
            "mount_point": self.mount_point
        }
        
        if self.is_mounted:
            try:
                # Get storage usage info
                statvfs = os.statvfs(self.mount_point)
                total_bytes = statvfs[0] * statvfs[2]
                free_bytes = statvfs[0] * statvfs[3]
                used_bytes = total_bytes - free_bytes
                
                info.update({
                    "total_mb": total_bytes // (1024 * 1024),
                    "used_mb": used_bytes // (1024 * 1024),
                    "free_mb": free_bytes // (1024 * 1024),
                    "usage_percent": (used_bytes * 100) // total_bytes
                })
                
                # Check if critical files exist
                info["state_file_exists"] = self._file_exists(STATE_FILE)
                info["log_file_exists"] = self._file_exists(LOG_FILE)
                
            except Exception as e:
                info["error"] = str(e)
                
        return info
        
    def _file_exists(self, filepath):
        """Check if file exists"""
        try:
            os.stat(filepath)
            return True
        except OSError:
            return False
            
    def deinit(self):
        """Clean up resources"""
        try:
            if self.is_mounted:
                storage.umount(self.mount_point)
            if self.spi:
                self.spi.deinit()
        except:
            pass  # Ignore cleanup errors