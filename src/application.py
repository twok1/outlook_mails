import logging

from src.integrations.outlook import EmailReader, OutlookConnector
from src.core import get_routes
from src.utils import settings, setup_logging
from src.integrations.filesystem import ProcessedMessagesStorage


class Application:
    def __init__(self) -> None:
        setup_logging(app_root=settings.app_root)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Запуск приложения...')
        
        self.outlook = OutlookConnector()
        self.logger.info('OutlookConnector загружен')
        self.mail_reader = EmailReader(outlook=self.outlook)
        
        self.processed_storage = ProcessedMessagesStorage(settings=settings)
        self.logger.info('ProcessedMessagesStorage загружен')

    def run(self):
        for route in get_routes(outlook_connector=self.outlook, settings=settings):
            try:
                messages = self.mail_reader.run(query=route.query)
            except Exception as e:
                self.logger.error(f'Ошибка при чтении почты', exc_info=True)
                continue
            
            parser_name = type(route.parser).__name__

            # Отсеиваем дубликаты персонально для этого парсера
            new_messages = self.processed_storage.filter_new(messages, parser_name)
            if not new_messages:
                continue

            parsed_items = route.parser.run(new_messages)
            if parsed_items:
                route.processor.process(parsed_items)

            # Отмечаем письма как обработанные именно этим парсером
            self.processed_storage.mark_as_processed(new_messages, parser_name)
    
