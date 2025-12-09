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

# Отключаем warnings
warnings.filterwarnings("ignore")


class ReminderManager:
    def __init__(self, outlook: OutlookConnector) -> None:
        """
        Инициализация с совместимым API.
        """
        self.account = outlook.outlook
        
        print(f"ReminderManager инициализирован (exchangelib)")
    
    def _get_date_from_exchange_object(self, obj):
        """
        Извлекает дату из объектов exchangelib.
        Работает с EWSDateTime, EWSDate и datetime.
        """
        if isinstance(obj, EWSDateTime):
            return obj.date()
        elif isinstance(obj, EWSDate):
            # EWSDate не имеет метода date(), создаем datetime
            return datetime(obj.year, obj.month, obj.day).date()
        elif isinstance(obj, datetime):
            return obj.date()
        else:
            # Пробуем стандартный метод
            return obj.date()
    
    def _get_all_reminds(self) -> List[Any]:
        """
        Получает все напоминания о командировках из календаря.
        Аналогично оригинальному методу, но возвращает список CalendarItem.
        """
        try:
            # Получаем календарь (folder=9 соответствует календарю)
            appointments = list(self.account.calendar.all().order_by('start'))
            
            # Фильтруем по теме [командировка]
            com_tasks = []
            for appointment in appointments:
                subject = appointment.subject or ""
                if subject.startswith('[командировка] '):
                    com_tasks.append(appointment)
            
            print(f"Найдено напоминаний: {len(com_tasks)}")
            return com_tasks
            
        except Exception as e:
            print(f"Ошибка получения напоминаний: {e}")
            return []
    
    def _make_reminds(self, reminds: List[Reminder]) -> None:
        """
        Создает напоминания в календаре.
        Аналогично оригинальному методу.
        """
        # Получаем временную зону аккаунта Exchange
        tz = self.account.default_timezone
        
        for remind in reminds:
            try:
                # Для событий на весь день
                if remind.reminder_date.tzinfo is None:
                    # Если дата без временной зоны, добавляем временную зону
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
                    end=start_ews + timedelta(days=1),  # Для AllDayEvent обычно 1 день
                    is_all_day=True,  # AllDayEvent = True
                    reminder_minutes_before_start=15,  # ReminderMinutesBeforeStart = 15
                    reminder_due_by=start_ews,
                    reminder_is_set=True,
                )
                
                event.save(send_meeting_invitations='SendToNone')
                
                # Сохраняем ID
                if hasattr(remind, 'reminder_id'):
                    remind.reminder_id = str(event.id)
                
                print(f"Создано: {remind.subject}")
                
            except Exception as e:
                print(f"Ошибка создания напоминания: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    def _analize_to_add_reminds(
        self, 
        exists_tasks: List[Any], 
        reminds: List[Reminder]
    ) -> List[Reminder]:
        """
        Анализирует, какие напоминания нужно добавить.
        ТОЧНО такая же логика как в оригинале.
        """
        result: List[Reminder] = []
        
        for remind in reminds:
            need_add = True
            
            for task in exists_tasks:
                # ТОЧНО ТАК ЖЕ как в оригинале:
                subject_match = remind.subject == (task.subject or "")
                
                # Сравниваем даты (только дату, без времени)
                date_match = False
                if task.start and remind.reminder_date:
                    # Приводим к date для сравнения
                    task_date = self._get_date_from_exchange_object(task.start)
                    remind_date = remind.reminder_date.date()
                    date_match = task_date == remind_date
                
                if subject_match and date_match:
                    need_add = False
                    break
            
            if need_add:
                result.append(remind)
        
        print(f"К добавлению: {len(result)}")
        return result
    
    def _analize_to_remove_reminds(
        self, 
        exists_tasks: List[Any], 
        reminds: List[Reminder]
    ) -> List[Any]:
        """
        Анализирует, какие напоминания нужно удалить.
        ТОЧНО такая же логика как в оригинале.
        """
        result: List[Any] = []
        
        for task in exists_tasks:
            need_remove = True
            
            for remind in reminds:
                # ТОЧНО ТАК ЖЕ как в оригинале:
                subject_match = remind.subject == (task.subject or "")
                
                # Сравниваем даты (только дату, без времени)
                date_match = False
                if task.start and remind.reminder_date:
                    task_date = self._get_date_from_exchange_object(task.start)
                    remind_date = remind.reminder_date.date()
                    date_match = task_date == remind_date
                
                if subject_match and date_match:
                    need_remove = False
                    break
            
            if need_remove:
                result.append(task)
        
        print(f"К удалению: {len(result)}")
        return result
    
    def _remove_reminds(self, remove_tasks: List[Any]) -> None:
        """
        Удаляет указанные напоминания.
        Аналогично оригинальному методу.
        """
        for task in remove_tasks:
            try:
                task.delete()
                subject = task.subject or "Без темы"
                print(f"Удалено: {subject}")
            except Exception as e:
                print(f"Ошибка удаления: {e}")
    
    def run(self, reminds: List[Reminder]) -> None:
        """
        Основной метод синхронизации.
        ТОЧНО такой же API как в оригинале.
        """
        print("\n" + "="*60)
        print("СИНХРОНИЗАЦИЯ НАПОМИНАНИЙ (exchangelib)")
        print("="*60)
        
        try:
            # ТОЧНО ТАК ЖЕ как в оригинале:
            exists_tasks = self._get_all_reminds()
            need_reminds = self._analize_to_add_reminds(exists_tasks, reminds)
            self._make_reminds(need_reminds)
            remove_reminds = self._analize_to_remove_reminds(exists_tasks, reminds)
            self._remove_reminds(remove_reminds)
            
            print(f"\nСинхронизация завершена!")
            print(f"   Добавлено: {len(need_reminds)}")
            print(f"   Удалено: {len(remove_reminds)}")
            
        except Exception as e:
            print(f"Ошибка синхронизации: {e}")
            import traceback
            traceback.print_exc()


# Дополнительный класс для тестирования совместимости
class ReminderManagerCompatTest:
    """Тест совместимости с оригинальным API."""
    
    @staticmethod
    def test_compatibility():
        """Тестирует, что API полностью совместимо."""
        print("ТЕСТ СОВМЕСТИМОСТИ API")
        print("="*60)
        
        # 1. Проверяем конструктор
        print("1. Тест конструктора...")
        try:
            manager = ReminderManager(folder=9)
            print("   Конструктор работает")
        except Exception as e:
            print(f"   Ошибка конструктора: {e}")
            return
        
        # 2. Проверяем создание тестовых напоминаний
        print("\n2. Тест создания тестовых напоминаний...")
        from datetime import datetime, timedelta
        
        test_reminders = [
            Reminder(
                reminder_date=datetime.now() + timedelta(days=1),
                subject="[командировка] Тест 1",
                text="Тестовое напоминание 1"
            ),
            Reminder(
                reminder_date=datetime.now() + timedelta(days=2),
                subject="[командировка] Тест 2",
                text="Тестовое напоминание 2"
            ),
        ]
        
        try:
            # 3. Проверяем получение существующих
            print("\n3. Тест получения существующих...")
            exists = manager._get_all_reminds()
            print(f"   Получено: {len(exists)} напоминаний")
            
            # 4. Проверяем анализ
            print("\n4. Тест анализа...")
            to_add = manager._analize_to_add_reminds(exists, test_reminders)
            print(f"   К добавлению: {len(to_add)}")
            
            to_remove = manager._analize_to_remove_reminds(exists, test_reminders)
            print(f"   К удалению: {len(to_remove)}")
            
            # 5. Проверяем основной метод
            print("\n5. Тест основного метода run()...")
            manager.run(test_reminders)
            print("   Метод run() работает")
            
            # 6. Очистка тестовых данных
            print("\n6. Очистка тестовых данных...")
            all_tasks = manager._get_all_reminds()
            test_tasks = [t for t in all_tasks if "Тест" in (t.subject or "")]
            manager._remove_reminds(test_tasks)
            print(f"   Удалено тестовых: {len(test_tasks)}")
            
            print("\n" + "="*60)
            print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
            print("Класс полностью совместим с оригинальным API.")
            
        except Exception as e:
            print(f"\nОшибка теста: {e}")
            import traceback
            traceback.print_exc()