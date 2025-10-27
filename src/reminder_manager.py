from datetime import timedelta
from pathlib import Path
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import win32com.client

from src.models import Reminder
from src.models import CommandTripDB, ReminderDB, Base

class ReminderManager:
    def __init__(self, db_path: Optional[Path] = None, folder: int=9) -> None:
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / 'data' / 'reminders.db'
            
        db_path.parent.mkdir(exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
        self.folder = folder
        self.outlook_tasks = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        self.create_tasks = win32com.client.Dispatch("Outlook.Application")
        
        
    def _get_session(self) -> sessionmaker[Session]:
        return self.Session
    
    def _get_all_reminds(self):
        appointments = self.outlook_tasks.GetDefaultFolder(self.folder).Items
        appointments.Sort("[Start]")
        appointments.IncludeRecurrences = "True"
        com_tasks = []
        for a in appointments:
            if a.Subject.startswith('[командировка] '):
                com_tasks.append(a)
        return com_tasks
    
    def _make_reminds(self, reminds: List[Reminder]):
        for remind in reminds:
            mess = self.create_tasks.CreateItem(1)
            mess.Start = timedelta(hours=3) + remind.reminder_date
            mess.ReminderMinutesBeforeStart = 15
            mess.Duration = 90
            mess.AllDayEvent = True
            mess.Subject = remind.subject
            mess.Body = remind.text
            mess.Save()
            
    def _analize_reminds(self, exists_tasks: List[win32com.client.CDispatch], reminds: List[Reminder]) -> List[Reminder]:
        result: List[Reminder] = []
        for remind in reminds:
            need_add = True
            for task in exists_tasks:
                if all((
                    remind.subject == task.Subject,
                    remind.reminder_date.date() == task.Start.date()
                )):
                    need_add = False
                    break
            if need_add:
                result.append(remind)
        return result
    
    def run(self, reminds: List[Reminder]):
        exists_tasks = self._get_all_reminds()
        need_reminds = self._analize_reminds(exists_tasks, reminds)
        self._make_reminds(need_reminds)
        