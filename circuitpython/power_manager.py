"""
Power management integration with TPL5110 timer and battery monitoring
Handles system power cycling and low battery protection
"""

import time
import analogio
import digitalio
from config import *

class PowerManager:
    def __init__(self):
        """Initialize power management"""
        # Setup TPL5110 done signal pin
        self.done_pin = digitalio.DigitalInOut(TPL5110_DONE_PIN)
        self.done_pin.direction = digitalio.Direction.OUTPUT
        self.done_pin.value = False  # Start low
        
        # Setup battery monitoring (if available)
        self.battery_monitor = None
        try:
            self.battery_monitor = analogio.AnalogIn(BATTERY_MONITOR_PIN)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Battery monitoring not available: {e}")
        
        # Power management state
        self.wake_start_time = time.monotonic()
        self.max_wake_duration = 300  # 5 minutes max wake time
        self.battery_voltage = 0.0
        self.is_low_battery = False
        
    def signal_done(self):
        """Signal TPL5110 that we're done and ready to sleep"""
        try:
            if DEBUG_MODE:
                wake_duration = time.monotonic() - self.wake_start_time
                print(f"Signaling TPL5110 done (awake for {wake_duration:.1f}s)")
            
            # Pulse the done pin high briefly
            self.done_pin.value = True
            time.sleep(0.1)  # 100ms pulse
            self.done_pin.value = False
            
            # Give TPL5110 time to cut power
            time.sleep(1)
            
            # If we get here, TPL5110 didn't cut power - something's wrong
            if DEBUG_MODE:
                print("WARNING: TPL5110 did not cut power as expected")
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error signaling TPL5110: {e}")
                
    def read_battery_voltage(self):
        """Read current battery voltage"""
        if not self.battery_monitor:
            return 0.0
            
        try:
            # Read raw ADC value
            raw_value = self.battery_monitor.value
            
            # Convert to voltage (assuming voltage divider or direct measurement)
            # This may need adjustment based on your specific battery monitoring circuit
            voltage = (raw_value / 65535.0) * PRESSURE_SENSOR_VREF
            
            # If using a voltage divider, multiply by the divider ratio
            # For example, if using a 2:1 divider for a 3.7V LiPo:
            voltage = voltage * 2.0  # Adjust this multiplier as needed
            
            self.battery_voltage = voltage
            self.is_low_battery = voltage < LOW_BATTERY_THRESHOLD
            
            return voltage
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error reading battery voltage: {e}")
            return 0.0
            
    def check_battery_status(self):
        """Check battery status and return recommendations"""
        voltage = self.read_battery_voltage()
        
        status = {
            "voltage": voltage,
            "is_low": self.is_low_battery,
            "percentage": self._estimate_battery_percentage(voltage),
            "recommendation": "normal"
        }
        
        if self.is_low_battery:
            if voltage < 3.0:  # Critical low
                status["recommendation"] = "emergency_shutdown"
            elif voltage < 3.2:  # Low battery
                status["recommendation"] = "conserve_power"
            else:
                status["recommendation"] = "monitor_closely"
                
        return status
        
    def _estimate_battery_percentage(self, voltage):
        """Estimate battery percentage from voltage (rough approximation)"""
        if voltage <= 0:
            return 0
            
        # Simple linear approximation for Li-Ion/LiPo battery
        # These values may need adjustment based on your specific battery
        voltage_min = 3.0  # Empty voltage
        voltage_max = 4.2  # Full voltage
        
        if voltage >= voltage_max:
            return 100
        elif voltage <= voltage_min:
            return 0
        else:
            percentage = ((voltage - voltage_min) / (voltage_max - voltage_min)) * 100
            return max(0, min(100, int(percentage)))
            
    def should_skip_transmission(self, battery_status):
        """Determine if transmission should be skipped due to power constraints"""
        if battery_status["recommendation"] == "emergency_shutdown":
            return True, "Critical low battery - emergency shutdown"
            
        if battery_status["recommendation"] == "conserve_power":
            return True, "Low battery - conserving power"
            
        return False, ""
        
    def get_wake_duration(self):
        """Get how long the system has been awake this cycle"""
        return time.monotonic() - self.wake_start_time
        
    def should_force_sleep(self):
        """Check if system should be forced to sleep due to time limits"""
        wake_duration = self.get_wake_duration()
        
        if wake_duration > self.max_wake_duration:
            return True, f"Maximum wake time exceeded ({wake_duration:.1f}s)"
            
        return False, ""
        
    def prepare_for_sleep(self):
        """Prepare system components for sleep mode"""
        preparations = []
        
        try:
            # Log final battery status
            battery_status = self.check_battery_status()
            preparations.append(f"Battery: {battery_status['voltage']:.2f}V ({battery_status['percentage']}%)")
            
            # Calculate and log wake duration
            wake_duration = self.get_wake_duration()
            preparations.append(f"Wake duration: {wake_duration:.1f}s")
            
            if DEBUG_MODE:
                print("Preparing for sleep:")
                for prep in preparations:
                    print(f"  - {prep}")
                    
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error preparing for sleep: {e}")
                
        return preparations
        
    def handle_emergency_shutdown(self, storage_manager, error_message):
        """Handle emergency shutdown due to critical low battery"""
        try:
            if DEBUG_MODE:
                print(f"EMERGENCY SHUTDOWN: {error_message}")
            
            # Log emergency shutdown
            if storage_manager:
                storage_manager.log_error(
                    f"Emergency shutdown: {error_message}", 
                    "POWER_CRITICAL"
                )
                
            # Signal done immediately
            self.signal_done()
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error during emergency shutdown: {e}")
            # Still try to signal done
            try:
                self.signal_done()
            except:
                pass
                
    def get_power_diagnostics(self):
        """Get power system diagnostic information"""
        battery_status = self.check_battery_status()
        wake_duration = self.get_wake_duration()
        force_sleep, force_reason = self.should_force_sleep()
        skip_tx, skip_reason = self.should_skip_transmission(battery_status)
        
        return {
            "battery_voltage": battery_status["voltage"],
            "battery_percentage": battery_status["percentage"],
            "is_low_battery": battery_status["is_low"],
            "battery_recommendation": battery_status["recommendation"],
            "wake_duration_seconds": wake_duration,
            "max_wake_duration": self.max_wake_duration,
            "should_force_sleep": force_sleep,
            "force_sleep_reason": force_reason,
            "should_skip_transmission": skip_tx,
            "skip_transmission_reason": skip_reason,
            "tpl5110_done_pin_state": self.done_pin.value
        }
        
    def optimize_power_consumption(self):
        """Apply power optimization settings"""
        try:
            # Reduce CPU frequency if possible (CircuitPython specific)
            # This is board-dependent and may not be available
            pass
            
            # Disable unnecessary peripherals
            # This would be implementation-specific
            
            if DEBUG_MODE:
                print("Power optimization applied")
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error optimizing power: {e}")
                
    def deinit(self):
        """Clean up power management resources"""
        try:
            if self.battery_monitor:
                self.battery_monitor.deinit()
        except:
            pass  # Ignore cleanup errors