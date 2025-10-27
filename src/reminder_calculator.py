import configparser
import os
from typing import List

from src.models import Reminder
from src.models.models import CommandTrip

class ReminderCalculator:
    SCRIPT_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_mails.ini'))

    config = configparser.ConfigParser()
    config.read(SCRIPT_PATH, encoding='utf-8')
    FUCKING_OUT =  (int(config.get('mails', 'START_LOCK')), int(config.get('mails', 'END_LOCK')))
    START_NOTIFICATION = list([i for i in map(int, config.get('mails', 'START_NOTIFICATION').split(', '))])
    END_NOTIFICATION = list([i for i in map(int, config.get('mails', 'END_NOTIFICATION').split(', '))])
    WORKING_RANGE = tuple([i for i in map(int, config.get('mails', 'WORKING_RANGE').split(', '))])
    def __init__(self) -> None:
        pass
    
    def run(self, messages: List[CommandTrip]) -> List[Reminder]:
        reminders: List[Reminder] = []
        
        return reminders