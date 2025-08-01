"""
Water Depth Monitor - Main Application
ItsyBitsy M4 + RockBlock 9602 + DS3231 RTC + TPL5110 Power Management

Wakes every 10 minutes via TPL5110 to check time and transmit data
at scheduled intervals (5AM and 1PM PST/PDT).
"""

import time
import busio
import digitalio
from config import *
from sensor import PressureSensor
from time_manager import TimeManager
from satellite import SatelliteModem
from storage_manager import StorageManager
from power_manager import PowerManager

# Global status LED for visual feedback
status_led = digitalio.DigitalInOut(STATUS_LED_PIN)
status_led.direction = digitalio.Direction.OUTPUT

def blink_status_led(count=1, duration=0.2):
    """Blink status LED for visual feedback"""
    for _ in range(count):
        status_led.value = True
        time.sleep(duration)
        status_led.value = False
        time.sleep(duration)

def main():
    """Main application logic"""
    print("\n" + "="*50)
    print("Water Depth Monitor Starting")
    print("="*50)
    
    # Initialize components
    power_mgr = None
    storage_mgr = None
    time_mgr = None
    sensor = None
    satellite = None
    
    try:
        # Blink LED to indicate startup
        blink_status_led(3, 0.1)
        
        # Initialize power management first
        power_mgr = PowerManager()
        print("Power management initialized")
        
        # Check battery status immediately
        battery_status = power_mgr.check_battery_status()
        print(f"Battery: {battery_status['voltage']:.2f}V ({battery_status['percentage']}%)")
        
        # Handle emergency low battery
        if battery_status["recommendation"] == "emergency_shutdown":
            print("CRITICAL LOW BATTERY - Emergency shutdown")
            power_mgr.handle_emergency_shutdown(None, "Critical low battery detected")
            return  # This line may never execute if TPL5110 cuts power
            
        # Initialize storage management
        storage_mgr = StorageManager()
        if not storage_mgr.initialize():
            print("WARNING: SD card not available - running without persistence")
        else:
            print("Storage initialized")
            
        # Load system state
        state = storage_mgr.load_state() if storage_mgr.is_mounted else {}
        state["total_wake_cycles"] = state.get("total_wake_cycles", 0) + 1
        state["last_wake_time"] = time.monotonic()
        
        print(f"Wake cycle #{state['total_wake_cycles']}")
        
        # Initialize time management
        i2c = busio.I2C(I2C_SCL, I2C_SDA)
        time_mgr = TimeManager(i2c)
        time_info = time_mgr.get_system_info()
        print(f"Current time: {time_info['pacific_time']}")
        
        # Initialize sensor
        sensor = PressureSensor()
        print("Pressure sensor initialized")
        
        # Check if it's transmission time or if we have pending retries
        is_tx_time, tx_slot = time_mgr.is_transmission_time(tolerance_minutes=5)
        pending_transmissions = storage_mgr.get_pending_transmissions(state, time_mgr) if storage_mgr.is_mounted else []
        
        should_transmit = is_tx_time or len(pending_transmissions) > 0
        
        if should_transmit:
            print(f"Transmission needed - Time slot: {tx_slot}, Pending: {len(pending_transmissions)}")
            
            # Check if we should skip transmission due to low battery
            skip_tx, skip_reason = power_mgr.should_skip_transmission(battery_status)
            if skip_tx:
                print(f"Skipping transmission: {skip_reason}")
                if storage_mgr.is_mounted:
                    storage_mgr.log_error(f"Transmission skipped: {skip_reason}", "POWER")
            else:
                # Perform transmission
                transmission_result = perform_transmission(sensor, time_mgr, satellite, state)
                
                # Log results
                if storage_mgr.is_mounted:
                    sensor_data = sensor.get_sensor_diagnostics()
                    sensor_data["battery_voltage"] = battery_status["voltage"]
                    storage_mgr.log_sensor_reading(
                        time_mgr.get_timestamp_string(),
                        sensor_data,
                        transmission_result
                    )
                    
                    # Update state with transmission result
                    if tx_slot:
                        time_slot_str = f"{tx_slot[0]:02d}:{tx_slot[1]:02d}"
                        storage_mgr.record_transmission_attempt(
                            state, 
                            time_slot_str, 
                            transmission_result["success"],
                            transmission_result.get("error", "")
                        )
                        
        else:
            print("No transmission needed")
            next_tx_minutes = time_mgr.minutes_until_next_transmission()
            print(f"Next transmission in {next_tx_minutes} minutes")
            
            # Still take a sensor reading for logging
            sensor_data = sensor.get_sensor_diagnostics()
            sensor_data["battery_voltage"] = battery_status["voltage"]
            print(f"Current depth: {sensor_data['depth_feet']:.2f} feet")
            
            if storage_mgr.is_mounted:
                storage_mgr.log_sensor_reading(
                    time_mgr.get_timestamp_string(),
                    sensor_data
                )
        
        # Save updated state
        if storage_mgr.is_mounted:
            storage_mgr.save_state(state)
            
        # Print system diagnostics
        print_system_diagnostics(power_mgr, storage_mgr, time_mgr, sensor, satellite)
        
    except Exception as e:
        print(f"SYSTEM ERROR: {e}")
        blink_status_led(10, 0.1)  # Rapid blinking for error
        
        # Log error if possible
        if storage_mgr and storage_mgr.is_mounted:
            storage_mgr.log_error(f"System error in main: {str(e)}", "SYSTEM")
            
    finally:
        # Clean up and prepare for sleep
        print("\nPreparing for sleep...")
        
        if power_mgr:
            preparations = power_mgr.prepare_for_sleep()
            
        # Clean up resources
        cleanup_resources(power_mgr, storage_mgr, time_mgr, sensor, satellite)
        
        # Final status blink
        blink_status_led(2, 0.5)
        
        # Signal TPL5110 that we're done
        if power_mgr:
            power_mgr.signal_done()
        
        print("System should power down now...")
        time.sleep(2)  # Give time for power down
        
        # If we reach here, TPL5110 didn't cut power
        print("WARNING: System did not power down as expected!")

def perform_transmission(sensor, time_mgr, satellite, state):
    """Perform satellite transmission with sensor data"""
    print("Starting satellite transmission...")
    
    try:
        # Initialize satellite modem if not already done
        if not satellite:
            satellite = SatelliteModem()
            
        if not satellite.initialize():
            return {
                "success": False,
                "attempts": 0,
                "error": "Failed to initialize satellite modem",
                "signal_quality": -1
            }
            
        # Take sensor reading
        print("Taking sensor reading...")
        sensor_data = sensor.get_sensor_diagnostics()
        print(f"Depth reading: {sensor_data['depth_feet']:.2f} feet")
        
        # Send data
        result = satellite.send_data_reading(sensor_data, time_mgr)
        
        if result["success"]:
            print(f"✓ Transmission successful (attempt {result['attempts']})")
            blink_status_led(5, 0.1)  # Success pattern
        else:
            print(f"✗ Transmission failed after {result['attempts']} attempts")
            print(f"  Error: {result['error']}")
            blink_status_led(1, 2)  # Long blink for failure
            
        return result
        
    except Exception as e:
        error_msg = f"Exception during transmission: {str(e)}"
        print(f"✗ {error_msg}")
        return {
            "success": False,
            "attempts": 0,
            "error": error_msg,
            "signal_quality": -1
        }
    finally:
        # Put satellite to sleep to save power
        if satellite:
            satellite.sleep()

def print_system_diagnostics(power_mgr, storage_mgr, time_mgr, sensor, satellite):
    """Print comprehensive system diagnostics"""
    print("\n" + "-"*30)
    print("SYSTEM DIAGNOSTICS")
    print("-"*30)
    
    try:
        if power_mgr:
            power_diag = power_mgr.get_power_diagnostics()
            print(f"Power: {power_diag['battery_voltage']:.2f}V ({power_diag['battery_percentage']}%)")
            print(f"Wake duration: {power_diag['wake_duration_seconds']:.1f}s")
            
        if storage_mgr:
            storage_diag = storage_mgr.get_storage_info()
            if storage_diag["mounted"]:
                print(f"Storage: {storage_diag['used_mb']}MB used / {storage_diag['total_mb']}MB total")
            else:
                print("Storage: Not available")
                
        if time_mgr:
            time_info = time_mgr.get_system_info()
            print(f"Time: {time_info['pacific_time']}")
            print(f"Next TX: {time_info['minutes_until_next']} minutes")
            
        if sensor:
            sensor_diag = sensor.get_sensor_diagnostics()
            print(f"Sensor: {sensor_diag['depth_feet']:.2f}ft, {sensor_diag['voltage']:.3f}V")
            
        if satellite:
            sat_diag = satellite.get_diagnostics()
            print(f"Satellite: Signal {sat_diag.get('signal_quality', 'N/A')}/5, Init: {sat_diag.get('initialized', False)}")
            
    except Exception as e:
        print(f"Error in diagnostics: {e}")
        
    print("-"*30)

def cleanup_resources(*managers):
    """Clean up all system resources"""
    for manager in managers:
        if manager and hasattr(manager, 'deinit'):
            try:
                manager.deinit()
            except:
                pass  # Ignore cleanup errors

if __name__ == "__main__":
    main()