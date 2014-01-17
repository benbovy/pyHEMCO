# -*- coding: utf-8 -*-

# parts of pygchem (Python interface for GEOS-Chem Chemistry Transport Model)
#
# Copyright (C) 2012-2013 Gerrit Kuhlmann, Benoît Bovy
# see license.txt for more details
# 

"""
Miscellaneous routine(s) for time calculations and conversions
"""

import itertools
from datetime import datetime
from dateutil import rrule
from dateutil import relativedelta


#-----------------------------------------------------------------------------
# Utils classes
#-----------------------------------------------------------------------------

class DatetimeSlicer(object):
    """
    A sequence of time slices with custom recurrence rules.
    
    Each slice consists of a fixed time span defined by a 2-length tuple of
    :class:`datetime.datetime` objects (start time, end time).
    The recurrence pattern of time slices is determined by the set of
    parameters below.
    
    Parameters
    ----------
    years : [int, int...]
        The years to apply the recurrence to.
    months : [int, int...]
        The months to apply the recurrence to.
    days : [int, int...]
        The month days of to apply the recurrence to.
    hours : [int, int...]
        The day hours to apply the recurrence to.
    
    Notes
    -----
    By default, all slices are time spans of 1 hour. If an empty list is
    given for `hours` (resp. `days`, `months`, `years`), slices will have
    a duration of 1 day (resp. 1 month, 1 year, max duration allowed by the
    Python's built-in `datetime` module).
    
    See Also
    --------
    :func:`strptimeslices`
        Create a sequence of time slices from a formatted string (time stamp).
    
    Examples
    --------
    TODO: 
    
    """
    
    # separators and special characters for string formatting
    _str_dt_sep = '/'
    _str_value_sep = ','
    _str_range_sep = '-'
    _str_wildcard_char = '*'
    
    def __init__(self, years, months, days, hours):
        self.years = list(years)
        self.months = list(months)
        self.days = list(days)
        self.hours = list(hours)
        
        # ensure that an empty list will be followed by other empty list too
        # and set the fixed duration of time slice.
        self._interval = relativedelta(hours=+1)  
        self._freq = rrule.HOURLY
        self._has_emptylist = False
        if not self.hours:
            self._change_timespan(rrule.DAILY, relativedelta(days=+1))
        if not self.days:
            self._change_timespan(rrule.MONTHLY, relativedelta(months=+1))
        if not self.months:
            self._change_timespan(rrule.YEARLY, relativedelta(years=+1))
        if not self.years:
            self._change_timespan(None, None)
    
    def _change_timespan(self, freq, interval):
        """Change duration of each time slice."""
        if not self._has_emptylist:
            raise ValueError("found empty list with non empty "
                             "list(s) for shorter time spans")
        self._interval = interval
        self._freq = freq
        self._has_emptylist = True
    
    @classmethod
    def _parse_fmt(self, fmt):
        """Parse Formatted string to class init arguments."""
        args = []
        str_list = fmt.split(self._str_dt_sep)
        for str_elem in str_list:
            dt_elem = []
            if str_elem == self._str_wildcard_char:
                continue
            for val in str_elem.split(self._str_value_sep):
                try:
                    dt_elem.append(int(val))
                except ValueError:
                    min_max = [int(v) for v in val.split(self._str_range_sep)]
                    min_max[1] += 1
                    dt_elem.extend(range(*min_max))
            args.append(dt_elem)
        return args
    
    @classmethod
    def from_string(cls, fmt):
        """
        Create a sequence of time slices from a formatted string `fmt`
        (time stamp).
        
        See Also
        --------
        :func:`strp_datetimeslicer`
        """
        try:
            args = cls._parse_fmt(fmt)
        except (ValueError, TypeError):
            raise ValueError("Invalid string '{}'".format(fmt))
        return cls(*args)
    
    def to_string(self):
        """
        Get the string representation (time stamp) of the :class:`TimeSlicer`
        object.
        
        See Also
        --------
        :func:`strp_datetimeslicer`
        """
        str_list = []
        for dt_elem in (self.years, self.months, self.days, self.hours):
            if not dt_elem:
                str_list.append(self._str_wildcard_char)
            else:
                if dt_elem == list(range(min(dt_elem), max(dt_elem) + 1)):
                    str_list.append("{0}{1}{2}".format(min(dt_elem),
                                                       self._str_range_sep,
                                                       max(dt_elem)))
                else:
                    str_list.append(self._str_value_sep.join(dt_elem))
        return self._str_dt_sep.join(str_list)
    
    def __iter__(self):
        if not self.years:
            yield (datetime.min, datetime.max)
        else:
            for year in self.years:
                months = self.months or (1,)
                days = self.days or (1,)
                hours = self.hours or (0,)
                from_dt = datetime(year, min(months), min(days), min(hours))
                to_dt = datetime(year, max(months), max(days), max(hours))
                dt_slices = rrule.rrule(self._freq,
                                        dstart=from_dt, until=to_dt,
                                        bymonth=months, bymonthday=days,
                                        byhour=hours)
                for dt in dt_slices:
                    yield (dt, dt + self._interval)
    
    def __str__(self):
        return self.to_string()
    
    def __repr__(self):
        return "<{0}: {1}>".format(self.__class__.__name__, self.to_string())


#-----------------------------------------------------------------------------
# Utils functions
#-----------------------------------------------------------------------------

def strp_datetimeslicer(fmt):
    """
    Create a sequence of time slices from a formatted string (time stamp).
    
    Parameters
    ----------
    fmt : string
        A timestamp with YYYY/MM/DD/HH format. Multiple values or ranges
        can be given (see examples).
    
    Returns
    -------
    A :class:`DatetimeSlicer` object.
    
    Notes
    -----
    The wildcard character (*) can be used to extend the duration of each slice
    to 1 day, 1 month, 1 year or max. duration allowed by Python's built-in
    :mod:`datetime` (default duration is 1 hour). 
    
    Examples
    --------
    >>> list(strp_datetimeslicer('2010,2012/1-3/1/0'))
    [(datetime.datetime(2010, 1, 1, 0, 0), datetime.datetime(2010, 1, 1, 1, 0)),
     (datetime.datetime(2010, 2, 1, 0, 0), datetime.datetime(2010, 2, 1, 1, 0)),
     (datetime.datetime(2010, 3, 1, 0, 0), datetime.datetime(2010, 3, 1, 1, 0)),
     (datetime.datetime(2012, 1, 1, 0, 0), datetime.datetime(2012, 1, 1, 1, 0)),
     (datetime.datetime(2012, 2, 1, 0, 0), datetime.datetime(2012, 2, 1, 1, 0)),
     (datetime.datetime(2012, 3, 1, 0, 0), datetime.datetime(2012, 3, 1, 1, 0))]
    >>> list(strp_datetimeslicer('2013/6/1,5/*'))
    [(datetime.datetime(2013, 6, 1, 0, 0), datetime.datetime(2010, 6, 2, 0, 0)),
     (datetime.datetime(2010, 6, 5, 0, 0), datetime.datetime(2010, 6, 6, 0, 0))]
    >>> list(strp_datetimeslicer('2013/*/*/*'))
    [(datetime.datetime(2013, 1, 1, 0, 0), datetime.datetime(2014, 1, 1, 0, 0))]
    """
    return DatetimeSlicer.from_string(fmt)
