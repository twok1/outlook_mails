from typing import List

from src.models.models import CommandTrip, LetterType


class CommandTripProcessor:
    def run(self, messages: List[CommandTrip]) -> List[CommandTrip]:
        processed_messages: List[CommandTrip] = []
        messages = sorted(messages, key = lambda x: x.email_data.recieved_date)
        for message in messages:
            if message.letter_type == LetterType.NEW:
                processed_messages.append(message)
            else:
                for processed_message in processed_messages:
                    if self._is_one_trip(message=message, processed_message=processed_message):
                        processed_message.start_date = message.start_date
                        processed_message.end_date = message.end_date
                        processed_message.purpose = message.purpose
        return processed_messages
    
    def _is_one_trip(self, message: CommandTrip, processed_message: CommandTrip) -> bool:
        if message.location != processed_message.location:
            return False
        if any((
            processed_message.start_date <= message.start_date <= processed_message.end_date,
            processed_message.start_date <= message.end_date <= processed_message.end_date,
        )):
            return True
        return False