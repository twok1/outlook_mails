import os
from typing import List
import sertifi

from exchangelib import Credentials, Configuration, Account, DELEGATE, Q
from .models import EmailData
from .filters import ClassFilter, SubjectFilter, SenderEmailFilter

class EmailReader:
    def __init__(self):
        self.outlook = self.connect_to_exchange()
    
    def run(self):
        messages = self.outlook.inbox.filter(
            sender__email_adress_exact='iasup_notify@greenatom.ru'
        ).filter(
            Q(subject__contains='Информирование о направлении в командировку') |
            Q(subject__contains='Информирование об изменении данных командировки')
        )
        return self._process_to_emaildata(messages=messages)
    
    def connect_to_exchange(self):
        """Подключение к Exchange."""
        EMAIL = os.getenv('EMAIL')
        PASSWORD = os.getenv('PASS')
        SERVER = os.getenv('SERV')
        
        credentials = Credentials(username=EMAIL, password=PASSWORD)

        # print("Подключение без SSL проверки")
        # BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
        
        config = Configuration(
            server=SERVER,
            credentials=credentials,
            verify_ssl=sertifi.where(),
        )
        
        account = Account(
            primary_smtp_address=EMAIL,
            config=config,
            autodiscover=False,
            access_type=DELEGATE
        )
        
        return account
    
    def _process_to_emaildata(self, messages: list) -> List[EmailData]:
        new_messages = []
        for msg in messages:
            new_messages.append(
                EmailData(
                    msg.EntryID, 
                    msg.Subject,
                    msg.SenderName,
                    msg.Body,
                    msg.ReceivedTime,
                    msg.Class
                )
            )
        return new_messages