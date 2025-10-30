from datetime import datetime, time, date, timezone, timedelta
from typing import Union, Optional
import re

from loguru import logger


class DateTimeHandler:
    """
    A class to parse date and time strings into appropriate Python date/time objects, with custom timezone handling.
    """

    def __init__(self):
        """
        Initialize the handler with Danish standard timezone and daylight savings logic.
        """
        self.cet = timezone(timedelta(hours=1))  # Standard time (CET: UTC+1)
        self.cest = timezone(timedelta(hours=2))  # Summer time (CEST: UTC+2)

    @staticmethod
    def convert_to_date(date_str: str) -> Union[date, None]:
        """
        Converts a string to a date or time object. Handles various xsd:date and xsd:time formats, including optional timezones.

        Parameters:
        date_str (str): The string to be converted. Example formats: '2024-04-25+02:00', '2024-04-25', '14:30:00', '14:30:00+02:00', '2002-09-24Z'

        Returns:
        Union[date, time]: A date or time object representing the input string, or None if the format is invalid.
        """
        try:
            if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                # Handle xsd:date without timezone
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            elif re.match(r"^\d{4}-\d{2}-\d{2}Z$", date_str):
                # Handle xsd:date with UTC timezone 'Z'
                return datetime.strptime(date_str, '%Y-%m-%dZ').date()
            elif re.match(r"^\d{4}-\d{2}-\d{2}(?:[+-]\d{2}:\d{2})?$", date_str):
                # Handle xsd:date with optional timezone
                dt = datetime.fromisoformat(date_str)
                return dt.date() if dt.tzinfo else dt.date()
            else:
                # logger.debug(f"Invalid date format: {date_str}")
                pass
        except ValueError as e:
            # logger.debug(f"Error parsing date: {e}")
            pass

    def convert_to_time(self, time_str: str, date_obj: Optional[date] = None) -> Union[time, None]:
        try:
            time_str = self.__clean_fractional_seconds(time_str)
            # Handle time without timezone(e.g., "01:01:01")
            if re.match(r"^\d{2}:\d{2}:\d{2}$", time_str):
                return self._apply_default_timezone(datetime.strptime(time_str, '%H:%M:%S').timetz(), date_obj)

            # Handle time with UTC timezone 'Z' (e.g., "01:01:01Z")
            elif re.match(r"^\d{2}:\d{2}:\d{2}Z$", time_str):
                time_obj = datetime.strptime(time_str, '%H:%M:%SZ').timetz()
                return time_obj.replace(tzinfo=timezone.utc)

            # Handle time with specific timezone offset (e.g., "01:01:01+01:00")
            elif re.match(r"^\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$", time_str):
                time_obj = datetime.fromisoformat(f"2000-01-01T{time_str}").timetz()  # Use dummy date
                return time_obj
            else:
                # logger.debug(f"Invalid time format: {time_str}")
                pass

        except ValueError as e:
            pass
            # logger.debug(f"Error parsing time: {e}")

    def convert_to_datetime(self, date_str: str, time_str: str) -> Union[datetime, None]:
        try:
            if date_str and time_str:
                date_obj = self.convert_to_date(date_str)
                time_obj = self.convert_to_time(time_str, date_obj)
                return self.combine_date_time(date_obj, time_obj)
        except:
            pass

    @staticmethod
    def __clean_fractional_seconds(time: str):
        """
        Cleans the fractional seconds (milliseconds, microseconds) from time strings.
        """
        # Regex to match and remove fractional seconds (e.g., .000000 or .0000000)
        return re.sub(r'\.\d+', '', time)

    @staticmethod
    def truncate_seconds(date_time_ojb: datetime):
        if isinstance(date_time_ojb, datetime):
            return date_time_ojb.replace(second=0).replace(microsecond=0)

    @staticmethod
    def combine_date_time(date_obj: date, time_obj: time) -> datetime:
        """
        Combines a date object and a time object into a datetime object.

        Parameters:
        date_obj (date): The date object.
        time_obj (time): The time object.

        Returns:
        datetime: A datetime object representing the combined date and time.
        """
        return datetime.combine(date_obj, time_obj)

    def _apply_default_timezone(self, time_obj: time, date_obj: Optional[date] = None) -> time:
        """
        Applies the Danish timezone (CET or CEST) to a time object based on the provided date.
        If the date is in the DST period, applies CEST (UTC+2). Otherwise, applies CET (UTC+1).

        Parameters:
        time_obj (time): The time object to apply the correct timezone to.
        date_obj (Optional[date]): The date object to determine if DST should apply.

        Returns:
        time: The time object with the appropriate timezone applied.
        """
        if time_obj.tzinfo is None:
            if date_obj and self._is_danish_dst(date_obj):
                return time_obj.replace(tzinfo=self.cest)  # Apply summer time (UTC+2)
            return time_obj.replace(tzinfo=self.cet)  # Apply standard time (UTC+1)
        return time_obj

    def _is_danish_dst(self, date_obj: date) -> bool:
        """
        Determines if the given date falls within the Danish daylight saving time (DST) period.
        DST starts on the last Sunday of March and ends on the last Sunday of October.

        Parameters:
        date_obj (date): The date object to check.

        Returns:
        bool: True if the date falls within the DST period, False otherwise.
        """
        year = date_obj.year

        # Calculate the last Sunday of March
        last_sunday_march = self._last_sunday_of_month(year, 3)

        # Calculate the last Sunday of October
        last_sunday_october = self._last_sunday_of_month(year, 10)

        # DST is between the last Sunday of March and the last Sunday of October
        return last_sunday_march <= date_obj <= last_sunday_october

    @staticmethod
    def _last_sunday_of_month(year: int, month: int) -> date:
        """
        Returns the last Sunday of a given month.

        Parameters:
        year (int): The year.
        month (int): The month.

        Returns:
        date: The date of the last Sunday of the month.
        """
        # Start from the last day of the month
        last_day = date(year, month, 1).replace(day=28) + timedelta(days=4)  # Guarantees it's in the next month
        last_day -= timedelta(days=last_day.weekday() + 1)  # Go back to the last Sunday
        return last_day


date_time_handler = DateTimeHandler()

if __name__ == '__main__':

    time_test = ["01:01:01",
                 "01:01:01Z",
                 "01:01:01+01:00",
                 "01:01:01.000000",
                 "01:01:01.000000Z",
                 "01:01:01.000000+01:00",
                 "01:01:01.0000000",
                 "01:01:01.0000000Z",
                 "01:01:01.0000000+01:00"]
    for time in time_test:
        res = date_time_handler.convert_to_time(time)
        print(f"before: {time} \t\t\t  after: {res}")
