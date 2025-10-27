import win32com.client
import datetime

from src.models import EmailData
from src.filters import ClassFilter, SubjectFilter, SenderEmailFilter

class EmailReader:
    FILTERS = (
        ClassFilter(52),
        SubjectFilter(
            'Информирование о направлении в командировку', 
            'Информирование об изменении данных командировки'
        ),
        SenderEmailFilter('iasup_notify@greenatom.ru')
    )
    OUTLOOK_INBOX = 6
    
    def __init__(self, folder: int=OUTLOOK_INBOX) -> None: # 6- папка Входящие Outlook
        self.folder = folder
        self.outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        
    def run(self):
        messages = self.outlook.GetDefaultFolder(self.folder).Items
        for filter in self.FILTERS:
            messages = [msg for msg in messages if filter.apply(msg)]
        return self._process_to_emaildata(messages=messages)
    
    def _process_to_emaildata(self, messages: list) -> list:
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