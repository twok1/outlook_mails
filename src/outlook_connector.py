import os
import warnings
import sys

from exchangelib import BaseProtocol, Credentials, Configuration, Account, DELEGATE, NoVerifyHTTPAdapter
from dotenv import load_dotenv

# Получаем путь к директории, где находится исполняемый файл
if getattr(sys, 'frozen', False):
    # Если запускается как exe-файл
    app_path = os.path.dirname(sys.executable)
else:
    # Если запускается как Python-скрипт
    app_path = os.path.dirname(os.path.abspath(__file__))

# Устанавливаем рабочую директорию
os.chdir(app_path)

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
    