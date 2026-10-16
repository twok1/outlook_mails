import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src.trip_directory_manager import TripDirectoryManager
from src.models.dataclasses import CommandTrip, EmailData, LetterType


class TestTripDirectoryManager(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())

        # Фиксируем "текущий год" = 2026
        self.patcher = patch(
            'src.trip_directory_manager.datetime',
            wraps=datetime,
        )
        self.mock_dt = self.patcher.start()
        self.mock_dt.now.return_value = datetime(2026, 6, 1)
        self.mock_dt.strptime = datetime.strptime

        self.manager = TripDirectoryManager(str(self.tmpdir))

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_trip(self, order_number="01-01-2026-1/К",
                   start=datetime(2026, 1, 10),
                   end=datetime(2026, 1, 15),
                   letter_type=LetterType.NEW,
                   recieved=datetime(2026, 1, 1)):
        email = EmailData(
            message_id="id",
            subject="Test",
            sender="test@example.com",
            body="Body",
            recieved_date=recieved,
            msg_class=1,
        )
        return CommandTrip(
            email_data=email,
            start_date=start,
            end_date=end,
            order_date=datetime(2026, 1, 1),
            order_number=order_number,
            location="Москва",
            purpose="Цель",
            letter_type=letter_type,
        )

    # --- формат имени ---

    def test_directory_name_format(self):
        trip = self._make_trip()
        self.manager.run([trip])

        expected_name = "01_10.01.2026-15.01.2026 (01-01-2026-1_К)"
        trip_dir = self.tmpdir / expected_name

        self.assertTrue(trip_dir.exists(),
                        f"Ожидался каталог: {expected_name}, "
                        f"есть: {[d.name for d in self.tmpdir.iterdir()]}")
        self.assertTrue((trip_dir / "отчетка").exists())

    def test_slash_replaced_with_underscore(self):
        trip = self._make_trip(order_number="01/02/2026")
        self.manager.run([trip])

        dirs = [d.name for d in self.tmpdir.iterdir() if d.is_dir()]
        self.assertTrue(any("(01_02_2026)" in d for d in dirs),
                        f"Не найден каталог с заменённым слэшем: {dirs}")

    def test_pattern_matches_new_format(self):
        name = "01_10.01.2026-15.01.2026 (01-01-2026-1_К)"
        match = TripDirectoryManager.DIR_PATTERN.match(name)
        self.assertIsNotNone(match)
        self.assertEqual(match.group('num'), '01')
        self.assertEqual(match.group('start'), '10.01.2026')
        self.assertEqual(match.group('end'), '15.01.2026')
        self.assertEqual(match.group('order'), '01-01-2026-1_К')

    def test_pattern_does_not_match_foreign(self):
        for name in (
            "01_2026",
            "2020",
            "просто билеты",
            "02_24.03-16.06.2026",
            "03_17.06-13.08.2026",
            "04_28.09-18.11.2026",
        ):
            self.assertIsNone(
                TripDirectoryManager.DIR_PATTERN.match(name),
                f"Не должен матчиться: {name}",
            )

    # --- создание ---

    def test_create_directory_for_current_year(self):
        trip = self._make_trip()
        self.manager.run([trip])
        self.assertTrue(
            (self.tmpdir / "01_10.01.2026-15.01.2026 (01-01-2026-1_К)").exists()
        )

    def test_previous_year_trip_is_skipped(self):
        trip = self._make_trip(
            start=datetime(2025, 1, 10),
            end=datetime(2025, 1, 15),
        )
        self.manager.run([trip])

        own_dirs = [
            d for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        ]
        self.assertEqual(own_dirs, [])

    def test_future_year_trip_is_skipped(self):
        trip = self._make_trip(
            start=datetime(2027, 1, 10),
            end=datetime(2027, 1, 15),
        )
        self.manager.run([trip])

        own_dirs = [
            d for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        ]
        self.assertEqual(own_dirs, [])

    def test_update_does_not_create_directory(self):
        trip = self._make_trip(letter_type=LetterType.UPDATE)
        self.manager.run([trip])
        self.assertEqual(len(list(self.tmpdir.iterdir())), 0)

    # --- архивация ---

    def test_previous_year_directory_is_archived(self):
        old_name = "01_10.01.2025-15.01.2025 (01-01-2025-1_К)"
        old_dir = self.tmpdir / old_name
        old_dir.mkdir()
        (old_dir / "отчетка").mkdir()

        # Пересоздаём менеджер — при init должна пройти архивация
        self.manager = TripDirectoryManager(str(self.tmpdir))

        self.assertFalse(old_dir.exists())
        self.assertTrue((self.tmpdir / "2025" / old_name).exists())

    def test_current_year_directory_is_not_archived(self):
        cur_name = "01_10.01.2026-15.01.2026 (01-01-2026-1_К)"
        cur_dir = self.tmpdir / cur_name
        cur_dir.mkdir()

        self.manager = TripDirectoryManager(str(self.tmpdir))

        self.assertTrue(cur_dir.exists())

    def test_foreign_directory_is_not_archived(self):
        for name in ("01_2026", "2020", "просто билеты"):
            (self.tmpdir / name).mkdir()

        self.manager = TripDirectoryManager(str(self.tmpdir))

        for name in ("01_2026", "2020", "просто билеты"):
            self.assertTrue((self.tmpdir / name).exists())

    def test_archive_does_not_overwrite_existing(self):
        old_name = "01_10.01.2025-15.01.2025 (01-01-2025-1_К)"

        archive_dir = self.tmpdir / "2025"
        archive_dir.mkdir()
        existing = archive_dir / old_name
        existing.mkdir()
        (existing / "file.txt").write_text("keep me")

        # Дубликат в корне
        dup = self.tmpdir / old_name
        dup.mkdir()

        self.manager = TripDirectoryManager(str(self.tmpdir))

        self.assertEqual((existing / "file.txt").read_text(), "keep me")
        self.assertTrue(dup.exists())  # не перемещён, т.к. в архиве уже есть

    # --- нумерация ---

    def test_sequence_counts_only_current_year(self):
        (self.tmpdir / "01_10.01.2025-15.01.2025 (01-01-2025-1_К)").mkdir()
        (self.tmpdir / "01_10.01.2026-15.01.2026 (01-01-2026-1_К)").mkdir()

        self.manager = TripDirectoryManager(str(self.tmpdir))
        trip = self._make_trip(order_number="02-01-2026-2/К")
        self.manager.run([trip])

        names = sorted(
            d.name for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        )
        self.assertIn("02_10.01.2026-15.01.2026 (02-01-2026-2_К)", names)

    def test_sequence_continues_numbering(self):
        trips = [
            self._make_trip(order_number="A", recieved=datetime(2026, 1, 1)),
            self._make_trip(order_number="B", recieved=datetime(2026, 1, 2)),
            self._make_trip(order_number="C", recieved=datetime(2026, 1, 3)),
        ]
        self.manager.run(trips)

        dirs = sorted(
            d.name for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        )
        self.assertEqual(len(dirs), 3)
        self.assertTrue(dirs[0].startswith("01_"))
        self.assertTrue(dirs[1].startswith("02_"))
        self.assertTrue(dirs[2].startswith("03_"))


if __name__ == '__main__':
    unittest.main()