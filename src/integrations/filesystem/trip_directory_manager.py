import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from src.utils import Config
from src.models import CommandTrip, LetterType


logger = logging.getLogger(__name__)

@dataclass
class _ExistingDirInfo:
    """Информация о найденном каталоге командировки."""
    path: Path
    number: int
    order_key: str
    start: datetime
    end: datetime


class TripDirectoryManager:
    """
    Менеджер каталогов командировок.

    Формат имени:
        {номер}_{дата_начала}-{дата_окончания} ({номер_приказа})
    Пример:
        01_10.01.2026-15.01.2026 (01-01-2026-1_К)

    Уникальность определяется по нормализованному номеру приказа
    (он присутствует в имени каталога). Это защищает от повторного
    создания каталога для той же командировки.

    - Создаёт каталоги ТОЛЬКО для командировок текущего года.
    - Все "наши" каталоги предыдущих лет при старте перемещаются в "{год}/".
    - Посторонние папки (01_2026, 2020, "просто билеты", ...) игнорируются.
    """

    DIR_PATTERN = re.compile(
        r'^(?P<num>\d+)_'
        r'(?P<start>\d{2}\.\d{2}\.\d{4})-(?P<end>\d{2}\.\d{2}\.\d{4})\s*'
        r'\((?P<order>[^)]+)\)$'
    )
    SUBDIR_NAME = 'отчетка'
    CONFIG_BLOCK = 'files'

    def __init__(self, settings: Config) -> None:
        self.base_path = Path(settings.trips_base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.current_year = datetime.now().year

        # Сначала архивируем прошлые годы
        self._archive_previous_years()

    def run(self, messages: List[CommandTrip]) -> None:
        # 1. Собираем уже существующие каталоги текущего года
        existing = self._scan_existing_current_year()

        # 2. Сортируем входящие по дате получения (стабильный порядок)
        sorted_messages = sorted(
            messages, key=lambda m: m.email_data.received_date
        )

        # 3. Присваиваем номера только тем NEW, для которых каталога ещё нет
        next_number = (max((info.number for info in existing), default=0)) + 1

        # order_key → существующий каталог
        existing_by_order: Dict[str, _ExistingDirInfo] = {
            info.order_key: info for info in existing
        }

        created_in_this_run: set = set()  # чтобы два одинаковых NEW в одном запуске не создали два каталога

        for message in sorted_messages:
            if message.letter_type != LetterType.NEW:
                continue
            if message.start_date.year != self.current_year:
                continue

            order_key = self._normalize_order_key(message.order_number)

            # Уже существует на диске
            if order_key in existing_by_order:
                info = existing_by_order[order_key]
                message.sequence_number = info.number
                continue

            # Уже создан в этом же запуске (два письма по одному приказу)
            if order_key in created_in_this_run:
                # Подставляем тот же номер, но _create_directory не зовём
                # (номер нужен, чтобы get_directory_path корректно работал)
                message.sequence_number = next_number - 1
                continue

            # Новый приказ → новый номер
            message.sequence_number = next_number
            self._create_directory(message)
            existing_by_order[order_key] = _ExistingDirInfo(
                path=self.base_path / self._build_directory_name(message),
                number=next_number,
                order_key=order_key,
                start=message.start_date,
                end=message.end_date,
            )
            created_in_this_run.add(order_key)
            next_number += 1

    def get_directory_path(self, trip: CommandTrip) -> Optional[Path]:
        name = self._build_directory_name(trip)
        for candidate in (
            self.base_path / name,
            self.base_path / str(trip.start_date.year) / name,
        ):
            if candidate.exists():
                return candidate
        return None

    # ---------- архивация прошлых лет ----------

    def _archive_previous_years(self) -> None:
        if not self.base_path.exists():
            return

        for item in list(self.base_path.iterdir()):
            if not item.is_dir():
                continue

            match = self.DIR_PATTERN.match(item.name)
            if not match:
                continue

            try:
                start_date = datetime.strptime(match.group('start'), '%d.%m.%Y')
            except ValueError:
                continue

            year = start_date.year
            if year >= self.current_year:
                continue

            target_dir = self.base_path / str(year)
            target_dir.mkdir(parents=True, exist_ok=True)

            target_path = target_dir / item.name
            if target_path.exists():
                continue

            try:
                shutil.move(str(item), str(target_path))
            except OSError as e:
                logger.error(f'Ошибка архивации {item}', exc_info=True)

    # ---------- сканирование ----------

    def _scan_existing_current_year(self) -> List[_ExistingDirInfo]:
        """
        Возвращает список каталогов текущего года (и в корне base_path,
        и внутри base_path/{текущий_год}/).
        """
        result: List[_ExistingDirInfo] = []
        search_roots = [
            self.base_path,
            self.base_path / str(self.current_year),
        ]

        for root in search_roots:
            if not root.exists():
                continue
            for item in root.iterdir():
                if not item.is_dir():
                    continue

                match = self.DIR_PATTERN.match(item.name)
                if not match:
                    continue

                try:
                    start_date = datetime.strptime(match.group('start'), '%d.%m.%Y')
                    end_date = datetime.strptime(match.group('end'), '%d.%m.%Y')
                except ValueError:
                    continue

                if start_date.year != self.current_year:
                    continue

                result.append(
                    _ExistingDirInfo(
                        path=item,
                        number=int(match.group('num')),
                        order_key=self._normalize_order_key(match.group('order')),
                        start=start_date,
                        end=end_date,
                    )
                )

        return result

    # ---------- утилиты ----------

    @staticmethod
    def _normalize_order_key(order_number: str) -> str:
        """
        Нормализует номер приказа для сравнения:
        - заменяет "/" на "_" (как в имени папки),
        - убирает пробелы по краям,
        - приводит к нижнему регистру.
        """
        return order_number.replace('/', '_').strip().lower()

    def _build_directory_name(self, trip: CommandTrip) -> str:
        order_number = trip.order_number.replace('/', '_')
        start = trip.start_date.strftime('%d.%m.%Y')
        end = trip.end_date.strftime('%d.%m.%Y')
        seq = getattr(trip, 'sequence_number', 1) or 1
        return f'{seq:02d}_{start}-{end} ({order_number})'

    def _create_directory(self, trip: CommandTrip) -> Optional[Path]:
        dir_name = self._build_directory_name(trip)
        trip_dir = self.base_path / dir_name

        if trip_dir.exists():
            return trip_dir

        try:
            trip_dir.mkdir(parents=True, exist_ok=True)
            subdir = trip_dir / self.SUBDIR_NAME
            subdir.mkdir(parents=True, exist_ok=True)

            logger.info(f'Создан каталог: {trip_dir}, {subdir}')
            return trip_dir
        except OSError as e:
            logger.error(f'Ошибка создания каталога', exc_info=True)
            return None