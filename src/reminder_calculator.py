import configparser
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.models import Reminder
from src.models.models import CommandTrip

class ReminderCalculator:
    SCRIPT_PATH = Path(__file__).parent.parent / 'config_mails.ini'
    
    CONFIG_BLOCK = 'mails'

    config = configparser.ConfigParser()
    config.read(SCRIPT_PATH, encoding='utf-8')
    WORKING_PERIOD =  (
        int(config.get(CONFIG_BLOCK, 'START_LOCK')), 
        int(config.get(CONFIG_BLOCK, 'END_LOCK'))
    )
    START_NOTIFICATION = list(
        [int(i) for i in config.get(CONFIG_BLOCK, 'START_NOTIFICATION').split(', ')]
    )
    END_NOTIFICATION = list(
        [int(i) for i in config.get(CONFIG_BLOCK, 'END_NOTIFICATION').split(', ')]
    )
    WORKING_RANGE = tuple(
        [int(i) for i in config.get(CONFIG_BLOCK, 'WORKING_RANGE').split(', ')]
    )
    
    def run(self, messages: List[CommandTrip]) -> List[Reminder]:
        reminders: List[Reminder] = []
        for msg in messages:
            for date in self._dates_for_remind(msg):
                reminders.append(
                    Reminder(
                        date,
                        msg.get_subject(),
                        msg.get_text(),
                    )
                )
        return reminders
    

    
    def _dates_for_remind(self, msg: CommandTrip) -> List[datetime]:
        result = []
        for date, reminder_days in zip(
            (msg.start_date, msg.end_date), 
            (self.START_NOTIFICATION, self.END_NOTIFICATION)
        ):
            for reminder_day in reminder_days:
                reminder_date = date + timedelta(reminder_day)
                while reminder_date.day not in range(*self.WORKING_PERIOD)\
                        and reminder_date.weekday in (6, 7):
                    reminder_date -= timedelta(days=1)
                result.append(reminder_date)
        return result