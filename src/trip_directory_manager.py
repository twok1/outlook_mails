import configparser
import re
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .models.dataclasses import CommandTrip, LetterType
from .russian_calendar import get_app_root


class TripDirectoryManager:
    """
    Менеджер каталогов командировок.

    Формат имени:
        {номер}_{дата_начала}-{дата_окончания} ({номер_приказа})
    Пример:
        01_10.01.2026-15.01.2026 (01-01-2026-1_К)

    Слэш в номере приказа заменяется на "_" (Windows не разрешает "/" в именах).

    - Создаёт каталоги ТОЛЬКО для командировок текущего года.
    - Все "наши" каталоги предыдущих лет при старте перемещаются в "{год}/".
    - Посторонние папки (01_2026, 2020, "просто билеты", ...) игнорируются.
    """

    # Группы: num, start, end, order
    # Пример матча: "01_10.01.2026-15.01.2026 (01-01-2026-1_К)"
    DIR_PATTERN = re.compile(
        r'^(?P<num>\d+)_'
        r'(?P<start>\d{2}\.\d{2}\.\d{4})-(?P<end>\d{2}\.\d{2}\.\d{4})\s*'
        r'\((?P<order>[^)]+)\)$'
    )
    SUBDIR_NAME = 'отчетка'
    CONFIG_BLOCK = 'files'
    CONFIG_KEY = 'TRIPS_BASE_PATH'

    def __init__(self, base_path: Optional[str] = None) -> None:
        if base_path is None:
            base_path = self._read_base_path_from_config()
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.current_year = datetime.now().year

        # Сначала архивируем прошлые годы, чтобы они не мешали нумерации
        self._archive_previous_years()

    # ---------- конфиг ----------

    @classmethod
    def _read_base_path_from_config(cls) -> str:
        config_path = get_app_root() / 'config_mails.ini'
        config = configparser.ConfigParser()
        if not config.read(str(config_path), encoding='utf-8'):
            raise FileNotFoundError(f"Не найден конфиг: {config_path}")
        return config.get(cls.CONFIG_BLOCK, cls.CONFIG_KEY)

    # ---------- публичный API ----------

    def run(self, messages: List[CommandTrip]) -> None:
        sorted_messages = sorted(
            messages, key=lambda m: m.email_data.recieved_date
        )
        self._assign_sequence_numbers(sorted_messages)

        for message in sorted_messages:
            if message.letter_type != LetterType.NEW:
                continue
            if message.start_date.year != self.current_year:
                print(
                    f'[TripDirectoryManager] Пропуск (год {message.start_date.year} '
                    f'!= текущий {self.current_year}): '
                    f'{message.order_number}'
                )
                continue
            self._create_directory(message)

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
                print(
                    f'[TripDirectoryManager] Архив: уже есть {target_path}, '
                    f'пропуск перемещения {item}'
                )
                continue

            try:
                shutil.move(str(item), str(target_path))
                print(f'[TripDirectoryManager] Архив: {item.name} -> {year}/')
            except OSError as e:
                print(f'[TripDirectoryManager] Ошибка архивации {item}: {e}')

    # ---------- нумерация ----------

    def _assign_sequence_numbers(self, messages: List[CommandTrip]) -> None:
        existing_numbers = self._scan_current_year_numbers()
        next_number = (max(existing_numbers) + 1) if existing_numbers else 1

        for message in messages:
            if message.letter_type != LetterType.NEW:
                continue
            if message.start_date.year != self.current_year:
                continue

            message.sequence_number = next_number
            next_number += 1

    def _scan_current_year_numbers(self) -> List[int]:
        numbers: List[int] = []
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
                except ValueError:
                    continue
                if start_date.year != self.current_year:
                    continue
                numbers.append(int(match.group('num')))

        return numbers

    # ---------- создание ----------

    def _build_directory_name(self, trip: CommandTrip) -> str:
        # Windows не разрешает "/" в имени папки → заменяем на "_"
        order_number = trip.order_number.replace('/', '_')
        start = trip.start_date.strftime('%d.%m.%Y')
        end = trip.end_date.strftime('%d.%m.%Y')
        seq = getattr(trip, 'sequence_number', 1) or 1
        return f'{seq:02d}_{start}-{end} ({order_number})'

    def _create_directory(self, trip: CommandTrip) -> Optional[Path]:
        dir_name = self._build_directory_name(trip)
        trip_dir = self.base_path / dir_name

        if trip_dir.exists():
            print(f'[TripDirectoryManager] Каталог уже существует: {trip_dir}')
            return trip_dir

        try:
            trip_dir.mkdir(parents=True, exist_ok=True)
            subdir = trip_dir / self.SUBDIR_NAME
            subdir.mkdir(parents=True, exist_ok=True)

            print(f'[TripDirectoryManager] Создан каталог: {trip_dir}')
            print(f'[TripDirectoryManager] Создан подкаталог: {subdir}')
            return trip_dir
        except OSError as e:
            print(f'[TripDirectoryManager] Ошибка создания каталога: {e}')
            return None