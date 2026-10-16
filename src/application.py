from .outlook_connector import OutlookConnector
from .command_trip_processor import CommandTripProcessor
from .email_parser import EmailParser
from .email_reader import EmailReader
from .reminder_calculator import ReminderCalculator
from .reminder_manager_outlook import ReminderManager
from .trip_directory_manager import TripDirectoryManager


class Application:
    def __init__(self) -> None:
        outlook = OutlookConnector()
        self.mail_reader = EmailReader(outlook=outlook)
        self.mail_parser = EmailParser()
        self.command_trip_processor = CommandTripProcessor()
        self.remind_calculator = ReminderCalculator()
        self.remind_manager = ReminderManager(outlook=outlook)
        # путь берётся из config_mails.ini автоматически
        self.trip_directory_manager = TripDirectoryManager()

    def run(self):
        messages = self.mail_reader.run()
        parsed_messages = self.mail_parser.run(messages)
        processed_messages = self.command_trip_processor.run(parsed_messages)

        # создание каталогов командировок
        self.trip_directory_manager.run(processed_messages)

        reminds = self.remind_calculator.run(processed_messages)
        self.remind_manager.run(reminds=reminds)