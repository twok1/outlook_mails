import logging
import warnings
from datetime import datetime, timedelta

from exchangelib import CalendarItem, Body, EWSDateTime
from src.integrations.outlook.outlook_connector import OutlookConnector

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class OutlookCalendarManager:
    """Менеджер для работы с общими событиями в календаре Outlook."""
    
    def __init__(self, outlook: OutlookConnector) -> None:
        self.account = outlook.outlook
        logger.info("OutlookCalendarManager инициализирован")

    def create_all_day_event(self, subject: str, text: str, start_date: datetime, end_date: datetime) -> str:
        """Создает многодневное событие на весь день."""
        tz = self.account.default_timezone
        try:
            start_time = start_date if start_date.tzinfo else start_date.replace(tzinfo=tz)
            end_time = end_date if end_date.tzinfo else end_date.replace(tzinfo=tz)

            start_ews = EWSDateTime.from_datetime(start_time)
            # All-day событие в Exchange должно заканчиваться в 00:00 следующего дня
            end_ews = EWSDateTime.from_datetime(end_time) + timedelta(days=1)

            event = CalendarItem(
                account=self.account,
                folder=self.account.calendar,
                subject=subject,
                body=Body(text),
                start=start_ews,
                end=end_ews,
                is_all_day=True,
                reminder_is_set=False,            # Напоминание для чужого отсутствия не нужно
                legacy_free_busy_status='Free'    # Не блокируем собственное рабочее время
            )

            event.save(send_meeting_invitations='SendToNone')
            logger.info(f"Создано событие: '{subject}' ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})")
            return str(event.id)
            
        except Exception as e:
            logger.error(f"Ошибка создания события в календаре: {subject}", exc_info=True)
            return ""