"""
Real-time clock management with PST/PDT timezone handling
Uses Adafruit DS3231 RTC for accurate timekeeping
"""

import time
import rtc
import busio
import adafruit_ds3231
from config import *

class TimeManager:
    def __init__(self, i2c=None):
        """Initialize DS3231 RTC"""
        if i2c is None:
            i2c = busio.I2C(I2C_SCL, I2C_SDA)
        
        self.ds3231 = adafruit_ds3231.DS3231(i2c)
        self.rtc = rtc.RTC()
        
        # Sync CircuitPython RTC with DS3231 on startup
        self.sync_system_rtc()
        
    def sync_system_rtc(self):
        """Sync CircuitPython's internal RTC with DS3231"""
        ds_time = self.ds3231.datetime
        self.rtc.datetime = ds_time
        if DEBUG_MODE:
            print(f"RTC synced: {self.format_datetime(ds_time)}")
            
    def get_utc_time(self):
        """Get current UTC time from DS3231"""
        return self.ds3231.datetime
        
    def is_daylight_saving_time(self, dt):
        """
        Check if given datetime is during Daylight Saving Time (PDT)
        DST in US: Second Sunday in March to First Sunday in November
        """
        year, month, day = dt.tm_year, dt.tm_mon, dt.tm_mday
        
        # DST starts second Sunday in March
        if month < 3 or month > 11:
            return False
        if month > 3 and month < 11:
            return True
            
        # Calculate second Sunday in March
        if month == 3:
            # Find first day of March
            first_day_weekday = (day - dt.tm_wday - 1) % 7
            if first_day_weekday == 0:  # First day is Sunday
                second_sunday = 8
            else:
                second_sunday = 15 - first_day_weekday
            return day >= second_sunday
            
        # Calculate first Sunday in November  
        if month == 11:
            first_day_weekday = (day - dt.tm_wday - 1) % 7
            if first_day_weekday == 0:  # First day is Sunday
                first_sunday = 1
            else:
                first_sunday = 8 - first_day_weekday
            return day < first_sunday
            
        return False
        
    def utc_to_pacific(self, utc_dt):
        """Convert UTC datetime to Pacific Time (PST/PDT)"""
        # Convert to timestamp, adjust for timezone, convert back
        timestamp = time.mktime(utc_dt)
        
        if self.is_daylight_saving_time(utc_dt):
            # PDT: UTC - 7 hours
            pacific_timestamp = timestamp + (TIMEZONE_OFFSET_PDT * 3600)
        else:
            # PST: UTC - 8 hours  
            pacific_timestamp = timestamp + (TIMEZONE_OFFSET_PST * 3600)
            
        return time.localtime(pacific_timestamp)
        
    def get_pacific_time(self):
        """Get current Pacific Time (PST/PDT)"""
        utc_time = self.get_utc_time()
        return self.utc_to_pacific(utc_time)
        
    def is_transmission_time(self, tolerance_minutes=5):
        """
        Check if current time is within transmission window
        tolerance_minutes: How many minutes before/after exact time to allow
        """
        pacific_time = self.get_pacific_time()
        current_hour = pacific_time.tm_hour
        current_minute = pacific_time.tm_min
        
        for target_hour, target_minute in TRANSMISSION_TIMES:
            # Calculate minutes difference
            current_total_minutes = current_hour * 60 + current_minute
            target_total_minutes = target_hour * 60 + target_minute
            
            minutes_diff = abs(current_total_minutes - target_total_minutes)
            
            # Handle day boundary (e.g., 23:58 vs 00:02)
            if minutes_diff > 12 * 60:  # More than 12 hours apart
                minutes_diff = 24 * 60 - minutes_diff
                
            if minutes_diff <= tolerance_minutes:
                return True, (target_hour, target_minute)
                
        return False, None
        
    def minutes_until_next_transmission(self):
        """Calculate minutes until next scheduled transmission"""
        pacific_time = self.get_pacific_time()
        current_hour = pacific_time.tm_hour
        current_minute = pacific_time.tm_min
        current_total_minutes = current_hour * 60 + current_minute
        
        next_minutes = float('inf')
        
        for target_hour, target_minute in TRANSMISSION_TIMES:
            target_total_minutes = target_hour * 60 + target_minute
            
            if target_total_minutes > current_total_minutes:
                # Same day
                minutes_until = target_total_minutes - current_total_minutes
            else:
                # Next day
                minutes_until = (24 * 60) - current_total_minutes + target_total_minutes
                
            next_minutes = min(next_minutes, minutes_until)
            
        return int(next_minutes) if next_minutes != float('inf') else 0
        
    def format_datetime(self, dt, include_timezone=True):
        """Format datetime for logging and display"""
        formatted = f"{dt.tm_year:04d}-{dt.tm_mon:02d}-{dt.tm_mday:02d} " \
                   f"{dt.tm_hour:02d}:{dt.tm_min:02d}:{dt.tm_sec:02d}"
        
        if include_timezone:
            if self.is_daylight_saving_time(dt):
                formatted += " PDT"
            else:
                formatted += " PST"
                
        return formatted
        
    def get_timestamp_string(self):
        """Get current timestamp as string for data logging"""
        pacific_time = self.get_pacific_time()
        return f"{pacific_time.tm_year:04d}{pacific_time.tm_mon:02d}{pacific_time.tm_mday:02d}" \
               f"_{pacific_time.tm_hour:02d}{pacific_time.tm_min:02d}{pacific_time.tm_sec:02d}"
               
    def set_rtc_time(self, year, month, day, hour, minute, second):
        """Set DS3231 RTC time (use for initial setup)"""
        new_time = time.struct_time((year, month, day, hour, minute, second, 0, 0, 0))
        self.ds3231.datetime = new_time
        self.sync_system_rtc()
        print(f"RTC time set to: {self.format_datetime(new_time)}")
        
    def get_system_info(self):
        """Get system time information for diagnostics"""
        utc_time = self.get_utc_time()
        pacific_time = self.get_pacific_time()
        is_dst = self.is_daylight_saving_time(utc_time)
        is_tx_time, next_tx = self.is_transmission_time()
        minutes_until = self.minutes_until_next_transmission()
        
        return {
            "utc_time": self.format_datetime(utc_time, False),
            "pacific_time": self.format_datetime(pacific_time),
            "is_daylight_saving": is_dst,
            "timezone": "PDT" if is_dst else "PST",
            "is_transmission_time": is_tx_time,
            "next_transmission": next_tx,
            "minutes_until_next": minutes_until
        }