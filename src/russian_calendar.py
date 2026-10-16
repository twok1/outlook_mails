import configparser
import json
import os
import sys
from pathlib import Path
from typing import List
from datetime import datetime, timedelta
import requests

from .models.dataclasses import CommandTrip


def get_app_root() -> Path:
    """
    Возвращает корневую папку приложения.
    - для exe: папка рядом с исполняемым файлом
    - для скрипта: корень проекта (на уровень выше src/)
    """
    if getattr(sys, 'frozen', False):
        return Path(os.path.dirname(sys.executable))
    # __file__ = .../src/russian_calendar.py -> parent = src -> parent.parent = корень
    return Path(__file__).resolve().parent.parent


class RussianCalendar:
    CALENDAR_URLS = (
        'https://raw.githubusercontent.com/iposho/holidays-calendar-ru/refs/heads/main/src/data/holidays.json',
        'https://raw.githubusercontent.com/iposho/holidays-calendar-ru/refs/heads/main/src/data/shortDays.json',
        'https://raw.githubusercontent.com/iposho/holidays-calendar-ru/refs/heads/main/src/data/workingHolidays.json',
    )

    # Путь к config_mails.ini — рядом с exe или в корне проекта
    SCRIPT_PATH = get_app_root() / 'config_mails.ini'

    CONFIG_BLOCK = 'mails'

    config = configparser.ConfigParser()
    # Читаем по абсолютному пути — не зависит от cwd
    if not config.read(str(SCRIPT_PATH), encoding='utf-8'):
        raise FileNotFoundError(
            f"Не найден конфиг: {SCRIPT_PATH}"
        )

    WORKING_PERIOD = (
        int(config.get(CONFIG_BLOCK, 'END_LOCK')),
        int(config.get(CONFIG_BLOCK, 'START_LOCK')),
    )

    START_NOTIFICATION = list(
        [int(i) for i in config.get(CONFIG_BLOCK, 'START_NOTIFICATION').split(', ')]
    )
    END_NOTIFICATION = list(
        [int(i) for i in config.get(CONFIG_BLOCK, 'END_NOTIFICATION').split(', ')]
    )

    def __init__(self) -> None:
        # Папка для кэша JSON-календарей — рядом с exe или в корне проекта
        self.cache_dir = get_app_root() / 'data'
        self.cache_dir.mkdir(exist_ok=True)
        self.holidays, self.short_days, self.working_holidays = self._download_calendars()

    def _download_calendars(self):
        result = []
        for calendar, url in zip(('holidays', 'short_days', 'working_holidays'), self.CALENDAR_URLS):
            result.append(self._load_calendar(calendar, url))
        return result

    def _load_calendar(self, calendar: str, url: str):
        file_path = self.cache_dir / f'{calendar}.json'
        if not file_path.exists():
            response = requests.get(url=url)
            response.raise_for_status()
            data = response.json()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=True)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        return data
    
    def _date_eq_line(self, date: datetime, line: dict) -> bool:
        if date.day == line['day'] and date.month == line['month'] + 1:
            return True
        return False
    
    def is_working_day(self, date: datetime) -> bool:
        str_year = str(date.year)
        if not self.holidays.get(str_year, ''):
            return True
        for line in self.holidays[str_year]:
            if self._date_eq_line(date, line):
                return False
        for line in self.short_days[str_year]:
            if self._date_eq_line(date, line):
                return True
        for line in self.working_holidays[str_year]:
            if self._date_eq_line(date, line):
                return True
        if date.weekday() >= 5:
            return False
        return True
        
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
                        or not self.is_working_day(reminder_date):
                    reminder_date -= timedelta(days=1)
                result.append(reminder_date)
                if remidner_date_source != reminder_date:
                    result.append(remidner_date_source)
        return result