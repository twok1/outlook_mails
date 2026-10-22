import logging

from src.integrations.outlook import EmailReader, OutlookConnector
from src.core import get_routes
from src.utils import settings, setup_logging


class Application:
    def __init__(self) -> None:
        setup_logging(app_root=settings.app_root)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Запуск приложения...')
        
        self.outlook = OutlookConnector()
        self.logger.info('OutlookConnector загружен')
        self.mail_reader = EmailReader(outlook=self.outlook)

    def run(self):
        for route in get_routes(outlook_connector=self.outlook, settings=settings):
            try:
                messages = self.mail_reader.run(query=route.query)
            except Exception as e:
                self.logger.error(f'Ошибка при чтении почты', exc_info=True)
                return
            parsed_messages = route.parser.run(messages)
            if parsed_messages:
                route.processor.process(parsed_messages)
