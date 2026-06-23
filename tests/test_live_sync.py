import unittest
from unittest.mock import patch

from app import live_listener
from collectors import scraper


class TestLiveMatchSync(unittest.TestCase):
    def test_live_signature_ignores_score_minute_and_order(self):
        first = [
            {
                "homeTeam": {"name": "Portugal"},
                "awayTeam": {"name": "Uzbequistão"},
                "scheduledAt": "2026-06-23T19:00:00Z",
                "homeScore": 0,
                "awayScore": 0,
                "matchMinute": 4,
            },
            {
                "homeTeam": {"name": "Inglaterra"},
                "awayTeam": {"name": "Gana"},
                "scheduledAt": "2026-06-23T21:00:00Z",
                "homeScore": 1,
                "awayScore": 0,
                "matchMinute": 11,
            },
        ]
        second = [
            {
                "homeTeam": {"name": "Inglaterra"},
                "awayTeam": {"name": "Gana"},
                "scheduledAt": "2026-06-23T21:00:00Z",
                "homeScore": 2,
                "awayScore": 1,
                "matchMinute": 52,
            },
            {
                "homeTeam": {"name": "Portugal"},
                "awayTeam": {"name": "Uzbequistão"},
                "scheduledAt": "2026-06-23T19:00:00Z",
                "homeScore": 1,
                "awayScore": 0,
                "matchMinute": 73,
            },
        ]

        self.assertEqual(
            live_listener._live_matches_signature(first),
            live_listener._live_matches_signature(second),
        )

    def test_collect_palpites_for_ranking_fetches_members_and_saves_snapshot(self):
        page = object()
        ranking = [
            {"nome": "Ana", "arroba": "@ana"},
            {"participante": "Beto", "arroba": "beto"},
        ]
        calls = []

        def fake_fetch(page_arg, handle, nome, arroba, coleta_id):
            calls.append((page_arg, handle, nome, arroba, coleta_id))
            return [{"participante": nome, "arroba": arroba, "palpite_m": 1, "palpite_v": 0}]

        with (
            patch.object(scraper, "fetch_palpites_membro", side_effect=fake_fetch),
            patch.object(scraper, "save_palpites_snapshot", return_value=True) as save_mock,
        ):
            success = scraper.collect_palpites_for_ranking(page, ranking, coleta_id="C1")

        self.assertTrue(success)
        self.assertEqual(calls, [
            (page, "ana", "Ana", "@ana", "C1"),
            (page, "beto", "Beto", "@beto", "C1"),
        ])
        save_mock.assert_called_once()
        saved_palpites, saved_coleta_id = save_mock.call_args.args
        self.assertEqual(saved_coleta_id, "C1")
        self.assertEqual(len(saved_palpites), 2)


if __name__ == "__main__":
    unittest.main()
