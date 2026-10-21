from typing import List

from exchangelib import Q

from .outlook_connector import OutlookConnector
from src.models import EmailData


class EmailReader:
    def __init__(self, outlook: OutlookConnector) -> None:
        self.outlook = outlook.outlook
    
    def run(self, query: Q):
        messages = self.outlook.inbox.filter(query)
        return self._process_to_emaildata(messages=messages)
    
    def _process_to_emaildata(self, messages: list) -> List[EmailData]:
        new_messages = []
        for msg in messages:
            new_messages.append(
                EmailData(
                    message_id=msg.id, 
                    subject=msg.subject,
                    sender=msg.sender.email_address,
                    body=msg.text_body,
                    received_date=msg.datetime_received,
                    msg_type=msg.item_class
                )
            )
        return new_messages