import re

from datetime import datetime
from typing import List, Optional, Tuple
from src.models import EmailData, CommandTrip
from src.models.dataclasses import LetterType

class EmailParser:
    DATES_LINE_PHRASE = 'Вы направлены в командировку с '
    DATES_PATTERN = '%d.%m.%Y'
    LOCATION_LINE_PHRASE = 'В: '
    PURPOSE_LINE_PHRASE = 'С целью - '
    CHANGED_COMMAND_PHRASE = 'Условия указанной командировки изменены. Ознакомьтесь, пожалуйста, с новыми условиями.'
    
    def run(self, messages: List[EmailData]):
        parsed_messages = []
        for message in messages:
            parsed_messages.append(self.parse(message))
        return parsed_messages
        
    def parse(self, msg: EmailData) -> Optional[CommandTrip]:
        
        start_date, end_date, order_date, order_number, location, purpose, letter_type = self._parse_and_check_for_errors(msg)
        
        return CommandTrip(
            msg,
            start_date,
            end_date,
            order_date,
            order_number,
            location,
            purpose,
            letter_type
        )
    
    def _parse_and_check_for_errors(self, msg: EmailData) -> Tuple[datetime, datetime, datetime, str, str, str, LetterType]:
        souce_line, start_date, end_date, order_date, letter_type = self._parse_dates(msg.body)
        order_number = self._parse_order_number(souce_line)
        location = self._parse_location(msg.body)
        purpose = self._parse_purpose(msg.body)
        for val, descr in (
            (start_date, 'дата начала'),
            (end_date, 'дата окончания'),
            (order_date, 'дата приказа'), 
            (order_number, 'номер приказа'),
            (location, 'место командирования'),
            (purpose, 'цель командирования')
        ):
            if not val:
                raise ValueError(f'Ошибка парсинга {msg.body}, не найден {descr}')
        return start_date, end_date, order_date, order_number, location, purpose, letter_type
    
    def _parse_dates(self, body: str) -> Optional[Tuple[str, datetime, datetime, datetime, LetterType]]:
        letter_type = LetterType.NEW
        for source_line in body.splitlines():
            if source_line == self.CHANGED_COMMAND_PHRASE:
                letter_type = LetterType.UPDATE
            if source_line.startswith(self.DATES_LINE_PHRASE):
                line = re.findall(r'\d\d\.\d\d\.\d{4}', source_line)
                if len(line) == 3:
                    start, end, order = tuple(map(lambda d: datetime.strptime(d, self.DATES_PATTERN), line))
                    return source_line, start, end, order, letter_type
                
    def _parse_order_number(self, line) -> Optional[str]:
        order_num = re.search(r'№ ([^.]+)\.', line)
        if order_num:
            return order_num.group(1)
    
    def _parse_location(self, body: str) -> Optional[str]:
        for line in body.splitlines():
            if line.startswith(self.LOCATION_LINE_PHRASE):
                location = re.search(rf'{self.LOCATION_LINE_PHRASE}([^\n]+)\.', line)
                if location:
                    return location.group(1)
                
    def _parse_purpose(self, body: str) -> Optional[str]:
        for line in body.splitlines():
            if line.startswith(self.PURPOSE_LINE_PHRASE):
                purpose = re.search(rf'{self.PURPOSE_LINE_PHRASE}([^\n]+)', line)
                if purpose:
                    return purpose.group(1)