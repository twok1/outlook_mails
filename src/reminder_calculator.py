from typing import List

from .models import Reminder
from .models.dataclasses import CommandTrip
from .russian_calendar import RussianCalendar
from .config import settings, Config

class ReminderCalculator:
    def __init__(self, settings: Config) -> None:
        self.calendar = RussianCalendar(settings=settings)
    
    def run(self, messages: List[CommandTrip]) -> List[Reminder]:
        reminders: List[Reminder] = []
        for msg in messages:
            was_dates = set()
            for date in self.calendar.dates_for_remind(msg):
                if date not in was_dates:
                    reminders.append(
                        Reminder(
                            date,
                            msg.get_subject(),
                            msg.get_text(),
                        )
                    )
                    was_dates.add(date)
        return reminders