from dataclasses import dataclass
from datetime import datetime

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

@dataclass
class Reminder:
    reminder_id: str
    reminder_date: datetime
    subject: str
    text: str