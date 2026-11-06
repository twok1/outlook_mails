from typing import Any, List

from src.core.interfaces import BaseMailProcessor
from src.integrations.filesystem import VacationStorage
from src.integrations.outlook import OutlookCalendarManager


class VacationProcessor(BaseMailProcessor):
    def __init__(self, vacation_storage: VacationStorage, calendar_manager: OutlookCalendarManager) -> None:
        self.storage = vacation_storage
        self.calendar_manager = calendar_manager
    
    def process(self, items: List[Any]) -> None:
        self.storage.save_vacations(vacations=items)
        
        for item in items:
            # Пропускаем, если парсер вернул некорректные данные
            if not hasattr(item, 'main_dates') or not hasattr(item, 'main_person'):
                continue
                
            subject = f"Отсутствие {item.main_person}"
            
            # Формируем тело сообщения с информацией о заместителях
            text_lines = []
            substitutes = getattr(item, 'substitutes', [])
            if substitutes:
                text_lines.append("Замещают:")
                for sub in substitutes:
                    dates_str = ""
                    if sub.dates:
                        # Поддержка дат в виде объектов (AbsencePeriod) или строк
                        if isinstance(sub.dates[0], str):
                            dates_str = ", ".join(sub.dates)
                        else:
                            dates_str = ", ".join([
                                f"{p.start_date.strftime('%d.%m.%Y')}-{p.end_date.strftime('%d.%m.%Y')}" 
                                for p in sub.dates
                            ])
                    text_lines.append(f"- {sub.person} ({dates_str})")
            
            text = "\n".join(text_lines) if text_lines else "Заместители не указаны"
            
            # Передаем задачи на создание событий в OutlookCalendarManager
            for period in item.main_dates:
                if hasattr(period, 'start_date') and hasattr(period, 'end_date'):
                    self.calendar_manager.create_all_day_event(
                        subject=subject,
                        text=text,
                        start_date=period.start_date,
                        end_date=period.end_date
                    )