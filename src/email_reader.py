from typing import List

from exchangelib import Q

from .outlook_connector import OutlookConnector
from .models import EmailData


class EmailReader:
    def __init__(self, outlook: OutlookConnector) -> None:
        self.outlook = outlook.outlook
    
    def run(self):
        query = (
            Q(sender='iasup_notify@greenatom.ru') &
                (
                    Q(subject__contains='Информирование о направлении в командировку') |
                    Q(subject__contains='Информирование об изменении данных командировки')
                )
            )
        messages = self.outlook.inbox.filter(query)
        return self._process_to_emaildata(messages=messages)
    
    def _process_to_emaildata(self, messages: list) -> List[EmailData]:
        new_messages = []
        for msg in messages:
            new_messages.append(
                EmailData(
                    msg.id, 
                    msg.subject,
                    msg.sender,
                    msg.text_body,
                    msg.datetime_received,
                    msg.item_class
                )
            )
        return new_messages