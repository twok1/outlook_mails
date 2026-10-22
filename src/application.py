import logging

from src.integrations.outlook import EmailReader, OutlookConnector, ReminderManager
from src.integrations.filesystem import TripDirectoryManager
from src.core import CommandTripProcessor, ReminderCalculator, get_trip_query
from src.parsers import TripEmailParser
from src.utils import settings, setup_logging


class Application:
    def __init__(self) -> None:
        setup_logging(app_root=settings.app_root)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Запуск приложения...')
        
        outlook = OutlookConnector()
        self.logger.info('OutlookConnector загружен')
        self.mail_reader = EmailReader(outlook=outlook)
        self.logger.info('EmailReader загружен')
        self.trip_mail_parser = TripEmailParser()
        self.logger.info('EmailParser загружен')
        self.command_trip_processor = CommandTripProcessor()
        self.logger.info('CommandTripProcessor загружен')
        self.remind_calculator = ReminderCalculator(settings=settings)
        self.logger.info('ReminderCalculator загружен')
        self.remind_manager = ReminderManager(outlook=outlook)
        self.logger.info('ReminderManager загружен')
        self.trip_directory_manager = TripDirectoryManager(settings=settings)  
        self.logger.info('TripDirectoryManager загружен')

    def run(self):
        try:
            trip_messages = self.mail_reader.run(query=get_trip_query())
        except Exception as e:
            self.logger.error(f'Ошибка при чтении почты', exc_info=True)
            return
        parsed_messages = self.trip_mail_parser.run(trip_messages)
        processed_messages = self.command_trip_processor.run(parsed_messages)

        try:
            self.trip_directory_manager.run(processed_messages)
        except Exception:
            self.logger.error(f'Ошибка при создании каталога командировки', exc_info=True)

        reminds = self.remind_calculator.run(processed_messages)
        try:
            self.remind_manager.run(reminds=reminds)
        except Exception:
            self.logger.error(f'Ошибка при создании напоминания', exc_info=True)