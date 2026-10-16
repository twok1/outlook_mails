import os
import warnings
import sys

from exchangelib import (
    BaseProtocol, Credentials, Configuration, Account, DELEGATE,
    NoVerifyHTTPAdapter,
)
from dotenv import load_dotenv


def _get_app_root() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# .env ищем рядом с exe / в корне проекта — по абсолютному пути
_APP_ROOT = _get_app_root()
load_dotenv(dotenv_path=os.path.join(_APP_ROOT, '.env'))

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
                f"Не заданы EMAIL/PASS/SERV. Проверьте .env в {_APP_ROOT}"
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