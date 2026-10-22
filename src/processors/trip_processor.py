from typing import List

from src.models import CommandTrip, LetterType
from src.core.interfaces import BaseMailProcessor
from src.integrations.outlook import ReminderManager
from src.integrations.filesystem import TripDirectoryManager
from src.services import ReminderCalculator


class CommandTripProcessor(BaseMailProcessor):
    def __init__(
        self, 
        dir_manager: TripDirectoryManager, 
        reminder_calculator: ReminderCalculator, 
        reminder_manager: ReminderManager
    ) -> None:
        self.dir_manager = dir_manager
        self.reminder_calculator = reminder_calculator
        self.reminder_manager = reminder_manager
    
    def process(self, messages: List[CommandTrip]) -> None:
        if not messages:
            return
        
        processed_messages: List[CommandTrip] = []
        messages = sorted(messages, key = lambda x: x.email_data.received_date)
        for message in messages:
            if message.letter_type == LetterType.NEW:
                processed_messages.append(message)
            else:
                for processed_message in processed_messages:
                    if self._is_one_trip(message=message, processed_message=processed_message):
                        processed_message.start_date = message.start_date
                        processed_message.end_date = message.end_date
                        processed_message.purpose = message.purpose
        
        self.dir_manager.run(processed_messages)
        
        reminders = self.reminder_calculator.run(processed_messages)
        self.reminder_manager.run(reminders=reminders)
    
    def _is_one_trip(self, message: CommandTrip, processed_message: CommandTrip) -> bool:
        if message.location != processed_message.location:
            return False
        if any((
            processed_message.start_date <= message.start_date <= processed_message.end_date,
            processed_message.start_date <= message.end_date <= processed_message.end_date,
        )):
            return True
        return False