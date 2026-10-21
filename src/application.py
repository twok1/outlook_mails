import logging

from src.integrations.outlook import EmailReader, OutlookConnector, ReminderManager
from src.integrations.filesystem import TripDirectoryManager
from src.core import CommandTripProcessor, ReminderCalculator
from src.parsers import EmailParser
from src.utils import settings, setup_logging


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
        try:
            messages = self.mail_reader.run()
        except Exception as e:
            self.logger.error(f'Ошибка при чтении почты', exc_info=True)
            return
        parsed_messages = self.mail_parser.run(messages)
        processed_messages = self.command_trip_processor.run(parsed_messages)

        # создание каталогов командировок
        try:
            self.trip_directory_manager.run(processed_messages)
        except Exception:
            self.logger.error(f'Ошибка при создании каталога командировки', exc_info=True)

        reminds = self.remind_calculator.run(processed_messages)
        try:
            self.remind_manager.run(reminds=reminds)
        except Exception:
            self.logger.error(f'Ошибка при создании напоминания', exc_info=True)