from src.command_trip_processor import CommandTripProcessor
from src.email_parser import EmailParser
from src.email_reader import EmailReader


class Application:
    def __init__(self) -> None:
        self.mail_reader = EmailReader()
        self.mail_parser = EmailParser()
        self.command_trip_processor = CommandTripProcessor()
    
    def run(self):
        messages = self.mail_reader.run()
        parsed_messages = self.mail_parser.run(messages)
        processed_messages = self.command_trip_processor.run(parsed_messages)
        for msg in processed_messages:
            print(msg.start_date, msg.end_date)