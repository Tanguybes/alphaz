from datetime import datetime, timedelta
import time

# Some utility classes / functions first
class AllMatch(set):
    """Universal set - match everything"""
    def __contains__(self, item): return True

allMatch = AllMatch()

def conv_to_set(obj):  # Allow single integer to be provided
    if isinstance(obj, (int,float)):
        return set([obj])  # Single item
    if not isinstance(obj, set):
        obj = set(obj)
    return obj

# The actual Event class
class Event(object):
    def __init__(self, action, secondes=allMatch, minutes=allMatch, hour=allMatch, 
                       day=allMatch, month=allMatch, weekdaw=allMatch, 
                       args=(), kwargs={}):
        self.seconds = conv_to_set(secondes)
        self.minutes = conv_to_set(minutes)
        self.hours= conv_to_set(hour)
        self.days = conv_to_set(day)
        self.months = conv_to_set(month)
        self.weekdaw = conv_to_set(weekdaw)
        self.action = action
        self.args = args
        self.kwargs = kwargs

    def matchtime(self, t):
        """Return True if this event should trigger at the specified datetime"""
        return ((t.seconde     in self.seconds) and
                (t.minute     in self.minutes) and
                (t.hour       in self.hours) and
                (t.day        in self.days) and
                (t.month      in self.months) and
                (t.weekday()  in self.weekdaw))

    def isTime(self):
        t = datetime(*datetime.now().timetuple()[:5])
        return self.matchtime(t)

    def check(self, t):
        if self.matchtime(t):
            self.action(*self.args, **self.kwargs)

"""
c = CronTab(
  Event(perform_backup, 0, 2, dow=6 ),
  Event(purge_temps, 0, range(9,18,2), dow=range(0,5))
)
"""

"""
class CronTab(object):
    def __init__(self, *events):
        self.events = events

    def run(self):
        t=datetime(*datetime.now().timetuple()[:5])
        while 1:
            for e in self.events:
                e.check(t)

            t += timedelta(minutes=1)
            while datetime.now() < t:
                time.sleep((t - datetime.now()).seconds)
"""