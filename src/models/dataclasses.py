from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import List, Optional

FORMAT_DATE = '%d.%m.%Y'

class LetterType(Enum):
    NEW = 'new'
    UPDATE = 'update'
    CANCELLATION = 'cancellation'

class EmailData(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    message_id: str
    subject: str
    sender: str
    body: str
    received_date: datetime
    msg_type: str
    
class CommandTrip(BaseModel):
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
    
    @field_validator('order_number')
    @classmethod
    def order_number_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Номер приказа не может быть пустым')
        return v
    
    @model_validator(mode='after')
    def check_dates_order(self) -> 'CommandTrip':
        if self.start_date > self.end_date:
            raise ValueError('Дата начала не может быть позже окончания')
        return self
    
    @property
    def duration_days(self) -> int:
        return  (self.end_date - self.start_date).days
        
    
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
    
    
class VacationSubstitute(BaseModel):
    """Модель заместителя на время отпуска"""
    person: str
    dates: List[str]

class VacationData(BaseModel):
    """Модель информации об отпуске"""
    email_id: str
    main_person: str
    main_position: str
    main_dates: List[str]
    substitutes: List[VacationSubstitute] = []
    
    
class AbsencePeriod(BaseModel):
    start_date: datetime
    end_date: datetime

class AbsenceSubstitute(BaseModel):
    person: str
    dates: List[AbsencePeriod]

class AbsenceData(BaseModel):
    email_id: str
    main_person: str
    main_position: str
    main_dates: List[AbsencePeriod]
    substitutes: List[AbsenceSubstitute] = []