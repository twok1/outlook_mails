from src.command_trip_processor import CommandTripProcessor
from src.email_parser import EmailParser
from src.email_reader import EmailReader
from src.reminder_calculator import ReminderCalculator
from src.reminder_manager import ReminderManager


class Application:
    def __init__(self) -> None:
        self.mail_reader = EmailReader()
        self.mail_parser = EmailParser()
        self.command_trip_processor = CommandTripProcessor()
        self.remind_calculator = ReminderCalculator()
        self.remind_manager = ReminderManager()
    
    def run(self):
        messages = self.mail_reader.run()
        parsed_messages = self.mail_parser.run(messages)
        processed_messages = self.command_trip_processor.run(parsed_messages)
        reminds = self.remind_calculator.run(processed_messages)
        self.remind_manager.run(reminds=reminds)