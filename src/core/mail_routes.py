from dataclasses import dataclass
from exchangelib import Q
from typing import List

from .interfaces import BaseMailProcessor, BaseMailParser
from src.integrations.filesystem import (
    TripDirectoryManager, 
    VacationStorage,
)
from src.integrations.outlook import ReminderManager, OutlookConnector
from src.services import ReminderCalculator
from src.utils import Config
from src.parsers import (
    TripEmailParser, 
    VacationMailParser,
    AbsenceMailParser,
)
from src.processors import (
    CommandTripProcessor,
    VacationProcessor,
)

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

vacation_query = Q(
    Q(sender='orp@cate.ru') &
    Q(subject__contains='Отсутствие ')
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
        MailRoute(
            query=vacation_query,
            parser=AbsenceMailParser(),
            processor=VacationProcessor(vacation_storage=VacationStorage(settings=settings)),
        )
    ]