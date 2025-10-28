import configparser
from pathlib import Path
from typing import List
from workalendar.europe import Russia
from datetime import datetime, timedelta

from src.models.dataclasses import CommandTrip


class RussianCalendar:
    SCRIPT_PATH = Path(__file__).parent.parent / 'config_mails.ini'
    
    CONFIG_BLOCK = 'mails'

    config = configparser.ConfigParser()
    config.read(SCRIPT_PATH, encoding='utf-8')
    
    WORKING_PERIOD =  (
        int(config.get(CONFIG_BLOCK, 'END_LOCK')), 
        int(config.get(CONFIG_BLOCK, 'START_LOCK'))
    )
    
    START_NOTIFICATION = list(
        [int(i) for i in config.get(CONFIG_BLOCK, 'START_NOTIFICATION').split(', ')]
    )
    END_NOTIFICATION = list(
        [int(i) for i in config.get(CONFIG_BLOCK, 'END_NOTIFICATION').split(', ')]
    )
    
    def __init__(self) -> None:
        self.calendar = Russia()
        
    def dates_for_remind(self, msg: CommandTrip) -> List[datetime]:
        result = []
        for date, reminder_days in zip(
            (msg.start_date, msg.end_date), 
            (self.START_NOTIFICATION, self.END_NOTIFICATION)
        ):
            for reminder_day in reminder_days:
                reminder_date = date + timedelta(reminder_day)
                remidner_date_source = date + timedelta(reminder_day)
                while reminder_date.day not in range(*self.WORKING_PERIOD)\
                        or not self.calendar.is_working_day(reminder_date):
                    reminder_date -= timedelta(days=1)
                result.append(reminder_date)
                if remidner_date_source != reminder_date:
                    result.append(remidner_date_source)
        return result