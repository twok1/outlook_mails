from .integrations.outlook.outlook_connector import OutlookConnector
from .core.command_trip_processor import CommandTripProcessor
from .parsers.email_parser import EmailParser
from .integrations.outlook.email_reader import EmailReader
from .core.reminder_calculator import ReminderCalculator
from .integrations.outlook.reminder_manager_outlook import ReminderManager
from .integrations.filesystem.trip_directory_manager import TripDirectoryManager
from .utils.config import settings
from .utils.logger_config import setup_logging
import logging


class Application:
    def __init__(self) -> None:
        setup_logging(app_root=settings.app_root)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Запуск приложения...')
        
        outlook = OutlookConnector()
        self.mail_reader = EmailReader(outlook=outlook)
        self.mail_parser = EmailParser()
        self.command_trip_processor = CommandTripProcessor()
        self.remind_calculator = ReminderCalculator(settings=settings)
        self.remind_manager = ReminderManager(outlook=outlook)
        self.trip_directory_manager = TripDirectoryManager(settings=settings)  

    def run(self):
        messages = self.mail_reader.run()
        parsed_messages = self.mail_parser.run(messages)
        processed_messages = self.command_trip_processor.run(parsed_messages)

        # создание каталогов командировок
        self.trip_directory_manager.run(processed_messages)

        reminds = self.remind_calculator.run(processed_messages)
        self.remind_manager.run(reminds=reminds)