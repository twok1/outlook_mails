import os
import warnings

from exchangelib import (
    BaseProtocol, Credentials, Configuration, Account, DELEGATE,
    NoVerifyHTTPAdapter,
)
from dotenv import load_dotenv

from src.utils import settings


load_dotenv(dotenv_path=settings.app_root / '.env')
warnings.filterwarnings('ignore')

class OutlookConnector:
    def __init__(self) -> None:
        self.outlook = self.connect_to_exchange()

    def connect_to_exchange(self):
        """Подключение к Exchange."""
        EMAIL = os.getenv('EMAIL')
        PASSWORD = os.getenv('PASS')
        SERVER = os.getenv('SERV')

        if not all((EMAIL, PASSWORD, SERVER)):
            raise RuntimeError(
                f"Не заданы EMAIL/PASS/SERV. Проверьте .env в {settings.app_root}"
            )

        credentials = Credentials(username=EMAIL, password=PASSWORD)

        BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter

        config = Configuration(
            server=SERVER,
            credentials=credentials,
        )

        account = Account(
            primary_smtp_address=EMAIL,
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )
        return account