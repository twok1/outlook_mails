    # --- защита от дубликатов ---

    def test_same_order_does_not_recreate_directory(self):
        """Повторный запуск с тем же приказом не создаёт новый каталог."""
        trip = self._make_trip(order_number="01-01-2026-1/К")

        self.manager.run([trip])
        dirs_after_first = sorted(
            d.name for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        )
        self.assertEqual(len(dirs_after_first), 1)

        # Второй запуск с тем же письмом
        self.manager.run([trip])
        dirs_after_second = sorted(
            d.name for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        )
        self.assertEqual(dirs_after_first, dirs_after_second)

    def test_same_order_with_changed_dates_does_not_recreate(self):
        """UPDATE-письмо с изменёнными датами не создаёт новый каталог."""
        # Сначала NEW
        new_trip = self._make_trip(
            order_number="01-01-2026-1/К",
            start=datetime(2026, 1, 10),
            end=datetime(2026, 1, 15),
            letter_type=LetterType.NEW,
            recieved=datetime(2026, 1, 1),
        )
        self.manager.run([new_trip])

        # Потом UPDATE с новыми датами
        upd_trip = self._make_trip(
            order_number="01-01-2026-1/К",
            start=datetime(2026, 1, 12),
            end=datetime(2026, 1, 17),
            letter_type=LetterType.UPDATE,
            recieved=datetime(2026, 1, 6),
        )
        self.manager.run([upd_trip])

        dirs = sorted(
            d.name for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        )
        # Каталог должен быть только один — с исходными датами
        self.assertEqual(len(dirs), 1)
        self.assertEqual(dirs[0], "01_10.01.2026-15.01.2026 (01-01-2026-1_К)")

    def test_new_order_after_existing_gets_next_number(self):
        """Новый приказ получает следующий номер, существующий не трогается."""
        (self.tmpdir / "01_10.01.2026-15.01.2026 (01-01-2026-1_К)").mkdir()

        trip = self._make_trip(order_number="02-01-2026-2/К")
        self.manager.run([trip])

        dirs = sorted(
            d.name for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        )
        self.assertIn("02_10.01.2026-15.01.2026 (02-01-2026-2_К)", dirs)
        self.assertIn("01_10.01.2026-15.01.2026 (01-01-2026-1_К)", dirs)

    def test_order_key_normalization(self):
        """Номер приказа нормализуется: слэш → '_', регистр не важен."""
        self.assertEqual(
            TripDirectoryManager._normalize_order_key("01-01-2026-1/К"),
            "01-01-2026-1_к",
        )
        self.assertEqual(
            TripDirectoryManager._normalize_order_key("01-01-2026-1_К"),
            "01-01-2026-1_к",
        )

    def test_two_new_same_order_in_one_run_creates_one_dir(self):
        """Два NEW-письма по одному приказу в одном запуске → один каталог."""
        t1 = self._make_trip(
            order_number="01-01-2026-1/К",
            recieved=datetime(2026, 1, 1),
        )
        t2 = self._make_trip(
            order_number="01-01-2026-1/К",
            recieved=datetime(2026, 1, 2),
        )
        self.manager.run([t1, t2])

        dirs = [
            d.name for d in self.tmpdir.iterdir()
            if d.is_dir() and TripDirectoryManager.DIR_PATTERN.match(d.name)
        ]
        self.assertEqual(len(dirs), 1)