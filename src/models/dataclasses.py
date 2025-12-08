from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

FORMAT_DATE = '%d.%m.%Y'

class LetterType(Enum):
    NEW = 'new'
    UPDATE = 'update'
    CANCELATION = 'cancelation'

@dataclass
class EmailData:
    message_id: str
    subject: str
    sender: str
    body: str
    recieved_date: datetime
    msg_class: int
    
@dataclass
class CommandTrip:
    email_data: EmailData
    start_date: datetime
    end_date: datetime
    order_date: datetime
    order_number: str
    location: str
    purpose: str
    letter_type: LetterType
    
    def _get_date(self, date: datetime):
        return datetime.strftime(date, FORMAT_DATE)
    
    def get_subject(self) -> str:
        return f'[командировка] {self.order_number} {self._get_date(self.order_date)} '\
            f'{self._get_date(self.start_date)} - {self._get_date(self.end_date)}'
    
    def get_text(self) -> str:
        return f'{self.purpose}\n{self.location}\n'\
                f'{self._get_date(self.start_date)} - {self._get_date(self.end_date)}\n'\
                f'/ {self.order_number} от {self._get_date(self.order_date)}'

@dataclass
class Reminder:
    reminder_date: datetime
    subject: str
    text: str
    reminder_id: Optional[str] = None