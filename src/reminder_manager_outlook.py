import warnings
from datetime import datetime, timedelta
from typing import List, Any

from exchangelib import (
    EWSDate,
    CalendarItem, 
    Body, 
    EWSDateTime
)

from .outlook_connector import OutlookConnector
from .models import Reminder
from .reminder_storage import ReminderStorage

# Отключаем warnings
warnings.filterwarnings("ignore")


class ReminderManager:
    def __init__(self, outlook: OutlookConnector) -> None:
        """
        Инициализация с совместимым API.
        """
        self.account = outlook.outlook
        self.storage = ReminderStorage()
        print(f"ReminderManager инициализирован (с локальным хранилищем)")
    
    def _make_reminds(self, reminds: List[Reminder]) -> None:
        """
        Создает напоминания в календаре.
        """
        # Получаем временную зону аккаунта Exchange
        tz = self.account.default_timezone
        
        created_reminders = []
        
        for remind in reminds:
            try:
                # Для событий на весь день
                if remind.reminder_date.tzinfo is None:
                    start_time = remind.reminder_date.replace(tzinfo=tz)
                else:
                    start_time = remind.reminder_date
                
                # Для AllDayEvent используем EWSDateTime.from_datetime с timezone
                start_ews = EWSDateTime.from_datetime(start_time)
                
                # Создаем событие на весь день
                event = CalendarItem(
                    account=self.account,
                    folder=self.account.calendar,
                    subject=remind.subject,
                    body=Body(remind.text or ""),
                    start=start_ews,
                    end=start_ews + timedelta(days=1),
                    is_all_day=True,
                    reminder_minutes_before_start=15,
                    reminder_due_by=start_ews,
                    reminder_is_set=True,
                )
                
                event.save(send_meeting_invitations='SendToNone')
                
                # Сохраняем ID
                remind.reminder_id = str(event.id)
                created_reminders.append(remind)
                
                print(f"Создано: {remind.subject} на {remind.reminder_date.strftime('%d.%m.%Y')}")
                
            except Exception as e:
                print(f"Ошибка создания напоминания: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Сохраняем созданные напоминания в хранилище
        if created_reminders:
            added_count = self.storage.add_reminders(created_reminders)
            print(f"Сохранено в хранилище: {added_count} напоминаний")
    
    def _remove_reminds(self, remove_reminders: List[Reminder]) -> None:
        """
        Удаляет указанные напоминания из календаря.
        """
        # Удаляем из календаря (если есть ID)
        for reminder in remove_reminders:
            try:
                if hasattr(reminder, 'reminder_id') and reminder.reminder_id:
                    # Пытаемся найти и удалить событие по ID
                    try:
                        item = self.account.calendar.get(id=reminder.reminder_id)
                        if item:
                            item.delete()
                            print(f"Удалено из календаря: {reminder.subject}")
                    except Exception as e:
                        print(f"Не удалось найти событие для удаления: {e}")
                
                # Удаляем из хранилища
                self.storage.remove_reminder(reminder)
                
            except Exception as e:
                print(f"Ошибка удаления напоминания: {e}")
    
    def run(self, reminds: List[Reminder]) -> None:
        """
        Основной метод синхронизации.
        """
        print("\n" + "="*60)
        print("СИНХРОНИЗАЦИЯ НАПОМИНАНИЙ (локальное хранилище)")
        print("="*60)
        
        try:
            # Получаем список напоминаний для создания
            to_add = self.storage.get_reminders_to_add(reminds)
            
            # Получаем список напоминаний для удаления
            to_remove = self.storage.get_reminders_to_remove(reminds)
            
            print(f"Текущих напоминаний в хранилище: {len(self.storage.get_all_reminders())}")
            print(f"Новых напоминаний для создания: {len(to_add)}")
            print(f"Напоминаний для удаления: {len(to_remove)}")
            
            # Создаем новые напоминания
            if to_add:
                self._make_reminds(to_add)
            
            # Удаляем старые напоминания
            if to_remove:
                self._remove_reminds(to_remove)
            
            print(f"\nСинхронизация завершена!")
            print(f"   Добавлено: {len(to_add)}")
            print(f"   Удалено: {len(to_remove)}")
            
        except Exception as e:
            print(f"Ошибка синхронизации: {e}")
            import traceback
            traceback.print_exc()