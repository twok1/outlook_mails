import os
import warnings

from exchangelib import BaseProtocol, Credentials, Configuration, Account, DELEGATE, NoVerifyHTTPAdapter
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings('ignore')

class OutlookConnector:
    def __init__(self) -> None:
        self.outlook = self.connect_to_exchange()
        
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
    