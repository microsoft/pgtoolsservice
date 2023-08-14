from datetime import date, datetime
from datetime import time
# Subclass existing adapters so that the base case is handled normally.
from psycopg.types.datetime import DateLoader, DateDumper, TimestampLoader, TimeLoader


class InfDateDumper(DateDumper):
    def dump(self, obj):
        if obj == date.max:
            return b"infinity"
        elif obj == date.min:
            return b"-infinity"
        else:
            return super().dump(obj)


class InfTimeLoader(TimeLoader):
    def load(self, data):
        s = bytes(data).decode("utf8", "replace")
        if s == "24:00:00":
            return time(0, 0, 0)  # or whatever representation you prefer for 24:00
        else:
            return super().load(data)


class InfDateLoader(DateLoader):
    def load(self, data):
        s = bytes(data).decode("utf8", "replace")
        if s == "infinity" or (s and len(s.split()[0]) > 10):
            return date.max
        elif s == "-infinity" or "BC" in s:
            return date.min
        else:
            return super().load(data)


class InfTimestampLoader(TimestampLoader):
    def load(self, data):
        s = bytes(data).decode("utf8", "replace")

        # Check for the special 'infinity' values first
        if s.startswith("infinity"):
            return datetime.max
        elif s.startswith("-infinity") or "BC" in s:
            return datetime.min

        # Use _order attribute to determine the year's position
        parts = s.split('-')
        if self._order == self._ORDER_YMD:
            year = int(parts[0])
        elif self._order == self._ORDER_DMY:
            year = int(parts[2])
        elif self._order == self._ORDER_MDY:
            # MDY might look like MM-DD-YYYY
            # So you need to get the YYYY from the date-time split
            year = int(s.split(' ')[0].split('-')[2])
        else:
            # Raise an exception or handle unknown formats
            year = None

        if year and year > 9999:
            return datetime.max
        else:
            return super().load(data)


def addAdapters(conn):
    conn.adapters.register_dumper(date, InfDateDumper)
    conn.adapters.register_loader("date", InfDateLoader)
    conn.adapters.register_loader("timestamp", InfTimestampLoader)
    conn.adapters.register_loader("time", InfTimeLoader)
