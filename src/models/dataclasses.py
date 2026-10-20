from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

FORMAT_DATE = '%d.%m.%Y'

class LetterType(Enum):
    NEW = 'new'
    UPDATE = 'update'
    CANCELLATION = 'cancellation'

@dataclass
class EmailData:
    message_id: str
    subject: str
    sender: str
    body: str
    received_date: datetime
    msg_type: int
    
@dataclass
class CommandTrip:
    """
    Представляет информацию о командировке, сформированную на основе приказа.
    """
    email_data: EmailData
    start_date: datetime
    end_date: datetime
    order_date: datetime
    order_number: str
    location: str
    purpose: str
    letter_type: LetterType
    sequence_number: Optional[int] = None
    
    def _fmt_date(self, date: datetime) -> str:
        """форматирует дату в нужный формат

        Args:
            date (datetime): форматирвуемая дата

        Returns:
            str: строка даты нужного формата
        """
        return datetime.strftime(date, FORMAT_DATE)
    
    def get_subject(self) -> str:
        """возвращает тему для напоминания

        Returns:
            str: тема напоминания
        """
        return f'[командировка] {self.order_number} {self._fmt_date(self.order_date)} '\
            f'{self._fmt_date(self.start_date)} - {self._fmt_date(self.end_date)}'
    
    def get_text(self) -> str:
        """возвращает текст напоминания

        Returns:
            str: текст напоминания
        """
        return f'{self.purpose}\n{self.location}\n'\
                f'{self._fmt_date(self.start_date)} - {self._fmt_date(self.end_date)}\n'\
                f'/ {self.order_number} от {self._fmt_date(self.order_date)}'

@dataclass
class Reminder:
    """датакласс напоминания
    """
    reminder_date: datetime
    subject: str
    text: str
    reminder_id: Optional[str] = None  # Опциональное поле для хранения ID в Exchange