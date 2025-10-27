import win32com.client
import datetime

from src.models import EmailData
from src.filters import ClassFilter, SubjectFilter

class EmailReader:
    FILTERS = (
        ClassFilter,
        SubjectFilter,
    )
    
    def __init__(self, folder: int=6) -> None: # 6- папка Входящие Outlook
        self.messages = []
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        messages = outlook.GetDefaultFolder(folder).Items
        for filter in self.FILTERS:
            messages = [msg for msg in messages if filter(52).apply(msg)]
        self._process_to_emaildata(messages=messages)
    
    def _process_to_emaildata(self, messages: list):
        for msg in messages:
            self.messages.append(
                EmailData(
                    msg.EntryID, 
                    msg.Subject,
                    msg.SenderName,
                    msg.Body,
                    msg.ReceivedTime,
                    msg.Class
                )
            )