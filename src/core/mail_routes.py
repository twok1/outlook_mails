from dataclasses import dataclass
from typing import List
from exchangelib import Q

from .interfaces import BaseMailProcessor, BaseMailParser
from src.parsers import TripEmailParser
from src.processors import CommandTripProcessor
from src.services import ReminderCalculator
from src.integrations.outlook import ReminderManager, OutlookConnector
from src.integrations.filesystem import TripDirectoryManager
from src.utils import Config

@dataclass
class MailRoute:
    """Структура, связывающая запрос с парсером"""
    query: Q
    parser: BaseMailParser
    processor: BaseMailProcessor
    
trip_query = Q(
        Q(sender='iasup_notify@greenatom.ru') &
        (
            Q(subject__contains='Информирование о направлении в командировку') |
            Q(subject__contains='Информирование об изменении данных командировки')
        )
    )

def get_routes(outlook_connector: OutlookConnector, settings: Config) -> List[MailRoute]:
    return [
        MailRoute(
            query=trip_query,
            parser=TripEmailParser(),
            processor=CommandTripProcessor(
                dir_manager=TripDirectoryManager(settings=settings),
                reminder_calculator=ReminderCalculator(settings=settings),
                reminder_manager=ReminderManager(outlook=outlook_connector),
            )
        ),
    ]