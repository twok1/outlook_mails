import os
from typing import List
from dotenv import load_dotenv
import warnings

from exchangelib import BaseProtocol, Credentials, Configuration, Account, DELEGATE, Q, NoVerifyHTTPAdapter
from .models import EmailData

warnings.filterwarnings('ignore')
load_dotenv()

class EmailReader:
    def __init__(self):
        self.outlook = self.connect_to_exchange()
    
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
    
    def connect_to_exchange(self):
        """Подключение к Exchange."""
        EMAIL = os.getenv('EMAIL')
        PASSWORD = os.getenv('PASS')
        SERVER = os.getenv('SERV')
        
        credentials = Credentials(username=EMAIL, password=PASSWORD)

        # print("Подключение без SSL проверки")
        BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter
        
        config = Configuration(
            server=SERVER,
            credentials=credentials,
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
                    msg.id, 
                    msg.subject,
                    msg.sender,
                    msg.text_body,
                    msg.datetime_received,
                    msg.item_class
                )
            )
        return new_messages