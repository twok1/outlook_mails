from typing import List

from src.models import Reminder
from src.models.dataclasses import CommandTrip
from src.russian_calendar import RussianCalendar

class ReminderCalculator:
    def __init__(self) -> None:
        self.calendar = RussianCalendar()
    
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