"""
Setup and Calibration Script for Water Depth Monitor
Run this script initially to configure the system and calibrate sensors

Usage: Upload this as main.py temporarily to run setup, then replace with actual main.py
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

def setup_menu():
    """Interactive setup menu"""
    print("\n" + "="*50)
    print("WATER DEPTH MONITOR - SETUP & CALIBRATION")
    print("="*50)
    print("1. Test all hardware components")
    print("2. Set RTC time")
    print("3. Calibrate pressure sensor")
    print("4. Test satellite communication")
    print("5. Initialize SD card and create files")
    print("6. Run full system test")
    print("7. View current diagnostics")
    print("8. Exit setup")
    print("="*50)
    
    while True:
        try:
            choice = input("Enter choice (1-8): ").strip()
            if choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
                return choice
            print("Invalid choice. Please enter 1-8.")
        except:
            print("Please enter a number 1-8")
            
def test_hardware():
    """Test all hardware components"""
    print("\nTesting Hardware Components...")
    print("-" * 40)
    
    results = {}
    
    # Test I2C and RTC
    try:
        i2c = busio.I2C(I2C_SCL, I2C_SDA)
        time_mgr = TimeManager(i2c)
        time_info = time_mgr.get_system_info()
        print(f"✓ RTC: {time_info['pacific_time']}")
        results['rtc'] = True
    except Exception as e:
        print(f"✗ RTC Error: {e}")
        results['rtc'] = False
        
    # Test pressure sensor
    try:
        sensor = PressureSensor()
        sensor_data = sensor.get_sensor_diagnostics()
        print(f"✓ Pressure Sensor: {sensor_data['depth_feet']:.2f}ft, {sensor_data['voltage']:.3f}V")
        results['sensor'] = True
    except Exception as e:
        print(f"✗ Pressure Sensor Error: {e}")
        results['sensor'] = False
        
    # Test SD card
    try:
        storage_mgr = StorageManager()
        if storage_mgr.initialize():
            storage_info = storage_mgr.get_storage_info()
            print(f"✓ SD Card: {storage_info['total_mb']}MB total, {storage_info['free_mb']}MB free")
            results['storage'] = True
        else:
            print("✗ SD Card: Mount failed")
            results['storage'] = False
    except Exception as e:
        print(f"✗ SD Card Error: {e}")
        results['storage'] = False
        
    # Test power management
    try:
        power_mgr = PowerManager()
        power_info = power_mgr.get_power_diagnostics()
        print(f"✓ Power: {power_info['battery_voltage']:.2f}V ({power_info['battery_percentage']}%)")
        results['power'] = True
    except Exception as e:
        print(f"✗ Power Management Error: {e}")
        results['power'] = False
        
    # Test satellite modem (basic init only)
    try:
        satellite = SatelliteModem()
        if satellite.initialize():
            signal = satellite.get_signal_quality()
            print(f"✓ Satellite Modem: Signal {signal}/5")
            satellite.sleep()  # Put back to sleep
            results['satellite'] = True
        else:
            print("✗ Satellite Modem: Initialization failed")
            results['satellite'] = False
    except Exception as e:
        print(f"✗ Satellite Modem Error: {e}")
        results['satellite'] = False
        
    print("-" * 40)
    working_count = sum(results.values())
    total_count = len(results)
    print(f"Hardware Test Results: {working_count}/{total_count} components working")
    
    return results

def set_rtc_time():
    """Set RTC time interactively"""
    print("\nSetting RTC Time...")
    print("Enter current Pacific Time (PST/PDT)")
    
    try:
        year = int(input("Year (YYYY): "))
        month = int(input("Month (1-12): "))
        day = int(input("Day (1-31): "))
        hour = int(input("Hour (0-23): "))
        minute = int(input("Minute (0-59): "))
        second = int(input("Second (0-59): "))
        
        i2c = busio.I2C(I2C_SCL, I2C_SDA)
        time_mgr = TimeManager(i2c)
        
        # Convert Pacific time to UTC for storage
        # This is a simplified conversion - doesn't account for DST transitions
        is_dst = input("Is this Daylight Saving Time (PDT)? (y/n): ").lower().startswith('y')
        utc_offset = TIMEZONE_OFFSET_PDT if is_dst else TIMEZONE_OFFSET_PST
        
        # Convert to UTC
        utc_hour = hour - utc_offset
        if utc_hour >= 24:
            utc_hour -= 24
            day += 1  # Simplified - doesn't handle month/year rollover
        elif utc_hour < 0:
            utc_hour += 24
            day -= 1  # Simplified
            
        time_mgr.set_rtc_time(year, month, day, utc_hour, minute, second)
        print("✓ RTC time set successfully")
        
    except Exception as e:
        print(f"✗ Error setting RTC time: {e}")

def calibrate_pressure_sensor():
    """Calibrate pressure sensor for zero depth"""
    print("\nPressure Sensor Calibration...")
    print("IMPORTANT: Ensure sensor is at atmospheric pressure (zero depth)")
    input("Press Enter when ready to calibrate...")
    
    try:
        sensor = PressureSensor()
        offset = sensor.calibrate_zero()
        print(f"✓ Calibration complete. Offset: {offset:.3f} psi")
        
        # Save calibration to config or state file
        storage_mgr = StorageManager()
        if storage_mgr.initialize():
            state = storage_mgr.load_state()
            state['sensor_calibration_offset'] = offset
            storage_mgr.save_state(state)
            print("✓ Calibration saved to storage")
        else:
            print("⚠ Could not save calibration - SD card not available")
            
    except Exception as e:
        print(f"✗ Calibration error: {e}")

def test_satellite_communication():
    """Test satellite communication with actual message"""
    print("\nTesting Satellite Communication...")
    print("WARNING: This will use satellite airtime credits!")
    
    proceed = input("Continue with satellite test? (y/n): ").lower().startswith('y')
    if not proceed:
        print("Satellite test cancelled")
        return
        
    try:
        # Initialize components
        satellite = SatelliteModem()
        if not satellite.initialize():
            print("✗ Could not initialize satellite modem")
            return
            
        i2c = busio.I2C(I2C_SCL, I2C_SDA)
        time_mgr = TimeManager(i2c)
        sensor = PressureSensor()
        
        print("Sending test message...")
        
        # Send test message
        sensor_data = sensor.get_sensor_diagnostics()
        result = satellite.send_data_reading(sensor_data, time_mgr)
        
        if result["success"]:
            print(f"✓ Test message sent successfully!")
            print(f"  Message: {result['message']}")
            print(f"  Attempts: {result['attempts']}")
            print(f"  Signal Quality: {result['signal_quality']}/5")
        else:
            print(f"✗ Test message failed")
            print(f"  Error: {result['error']}")
            print(f"  Attempts: {result['attempts']}")
            
        satellite.sleep()
        
    except Exception as e:
        print(f"✗ Satellite test error: {e}")

def initialize_storage():
    """Initialize SD card and create necessary files"""
    print("\nInitializing Storage...")
    
    try:
        storage_mgr = StorageManager()
        if not storage_mgr.initialize():
            print("✗ Could not initialize SD card")
            return
            
        # Create initial state file
        initial_state = storage_mgr.default_state.copy()
        initial_state['setup_completed'] = True
        initial_state['setup_time'] = time.monotonic()
        
        if storage_mgr.save_state(initial_state):
            print("✓ Initial state file created")
        else:
            print("⚠ Could not create state file")
            
        # Test logging
        test_data = {
            "depth_feet": 0.0,
            "raw_adc": 2048,
            "voltage": 1.65,
            "battery_voltage": 4.1
        }
        
        if storage_mgr.log_sensor_reading("SETUP_TEST", test_data):
            print("✓ Test log entry created")
        else:
            print("⚠ Could not create log entry")
            
        storage_info = storage_mgr.get_storage_info()
        print(f"✓ Storage initialized: {storage_info['free_mb']}MB free")
        
    except Exception as e:
        print(f"✗ Storage initialization error: {e}")

def run_full_system_test():
    """Run complete system test simulating normal operation"""
    print("\nRunning Full System Test...")
    print("This simulates a complete wake-up cycle")
    
    try:
        # Initialize all components
        print("Initializing components...")
        power_mgr = PowerManager()
        storage_mgr = StorageManager()
        storage_mgr.initialize()
        
        i2c = busio.I2C(I2C_SCL, I2C_SDA)
        time_mgr = TimeManager(i2c)
        sensor = PressureSensor()
        
        # Load state
        state = storage_mgr.load_state()
        state['total_wake_cycles'] = state.get('total_wake_cycles', 0) + 1
        
        # Check time and transmission requirements
        is_tx_time, tx_slot = time_mgr.is_transmission_time(tolerance_minutes=60)  # Wider window for testing
        print(f"Transmission time check: {is_tx_time} (slot: {tx_slot})")
        
        # Take sensor readings
        sensor_data = sensor.get_sensor_diagnostics()
        battery_status = power_mgr.check_battery_status()
        sensor_data['battery_voltage'] = battery_status['voltage']
        
        print(f"Sensor reading: {sensor_data['depth_feet']:.2f}ft")
        print(f"Battery: {battery_status['voltage']:.2f}V")
        
        # Log the reading
        timestamp = time_mgr.get_timestamp_string()
        storage_mgr.log_sensor_reading(timestamp, sensor_data)
        
        # Save state
        storage_mgr.save_state(state)
        
        print("✓ Full system test completed successfully")
        
        # Don't signal TPL5110 done during testing
        print("⚠ TPL5110 done signal NOT sent (test mode)")
        
    except Exception as e:
        print(f"✗ System test error: {e}")

def view_diagnostics():
    """View current system diagnostics"""
    print("\nSystem Diagnostics...")
    print("-" * 40)
    
    try:
        # Power diagnostics
        power_mgr = PowerManager()
        power_info = power_mgr.get_power_diagnostics()
        print(f"Battery: {power_info['battery_voltage']:.2f}V ({power_info['battery_percentage']}%)")
        
        # Time diagnostics
        i2c = busio.I2C(I2C_SCL, I2C_SDA)
        time_mgr = TimeManager(i2c)
        time_info = time_mgr.get_system_info()
        print(f"Time: {time_info['pacific_time']}")
        print(f"Next transmission: {time_info['minutes_until_next']} minutes")
        
        # Sensor diagnostics
        sensor = PressureSensor()
        sensor_data = sensor.get_sensor_diagnostics()
        print(f"Depth: {sensor_data['depth_feet']:.2f}ft")
        print(f"Pressure: {sensor_data['pressure_psi']:.2f}psi")
        print(f"Sensor voltage: {sensor_data['voltage']:.3f}V")
        
        # Storage diagnostics
        storage_mgr = StorageManager()
        if storage_mgr.initialize():
            storage_info = storage_mgr.get_storage_info()
            print(f"Storage: {storage_info['used_mb']}MB used / {storage_info['total_mb']}MB total")
            
            # Load and display state
            state = storage_mgr.load_state()
            print(f"Wake cycles: {state.get('total_wake_cycles', 0)}")
            print(f"Failed attempts: {len(state.get('failed_attempts', []))}")
        else:
            print("Storage: Not available")
            
    except Exception as e:
        print(f"Error getting diagnostics: {e}")

def main():
    """Main setup program"""
    while True:
        choice = setup_menu()
        
        if choice == '1':
            test_hardware()
        elif choice == '2':
            set_rtc_time()
        elif choice == '3':
            calibrate_pressure_sensor()
        elif choice == '4':
            test_satellite_communication()
        elif choice == '5':
            initialize_storage()
        elif choice == '6':
            run_full_system_test()
        elif choice == '7':
            view_diagnostics()
        elif choice == '8':
            print("\nSetup complete! Replace this file with main.py to run normal operation.")
            break
            
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()