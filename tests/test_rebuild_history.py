import tempfile
import unittest
from pathlib import Path

import pandas as pd

from collectors import scraper
from config import settings


class TestRebuildHistoricalSnapshots(unittest.TestCase):
    def setUp(self):
        self.original_historico = settings.HISTORICO_EXCEL
        self.tmpdir = tempfile.TemporaryDirectory()
        settings.HISTORICO_EXCEL = Path(self.tmpdir.name) / "historico.xlsx"

    def tearDown(self):
        settings.HISTORICO_EXCEL = self.original_historico
        self.tmpdir.cleanup()

    def test_api_dates_are_converted_to_brt(self):
        scored_lookup, pair_lookup = scraper.build_match_date_lookup({
            "upcomingMatches": [
                {
                    "homeTeam": {"name": "Colômbia"},
                    "awayTeam": {"name": "RD Congo"},
                    "scheduledAt": "2026-06-24T02:00:00.000Z",
                }
            ]
        })

        row = pd.Series({
            "mandante": "Colômbia",
            "visitante": "RD Congo",
            "placar_real_m": 2,
            "placar_real_v": 0,
        })
        self.assertEqual(scraper.resolve_match_date(row, scored_lookup, pair_lookup), "2026-06-23")

    def test_rebuild_uses_score_to_keep_repeated_matchups(self):
        palpites_file = Path(self.tmpdir.name) / "palpites.xlsx"
        pd.DataFrame([
            {
                "coleta_id": "C1",
                "partida_id": "franxiraq_C1",
                "mandante": "França",
                "visitante": "Iraque",
                "placar_real_m": 1,
                "placar_real_v": 0,
                "participante": "Part A",
                "arroba": "@a",
                "palpite_m": 1,
                "palpite_v": 0,
                "categoria": "Vencedor certo",
            },
            {
                "coleta_id": "C1",
                "partida_id": "franxiraq_C1",
                "mandante": "França",
                "visitante": "Iraque",
                "placar_real_m": 3,
                "placar_real_v": 0,
                "participante": "Part A",
                "arroba": "@a",
                "palpite_m": 3,
                "palpite_v": 0,
                "categoria": "Placar exato",
            },
        ]).to_excel(palpites_file, index=False)

        api_data = {
            "finishedMatches": [
                {
                    "homeTeamName": "França",
                    "awayTeamName": "Iraque",
                    "homeScore": 1,
                    "awayScore": 0,
                    "scheduledAt": "2026-06-11T19:00:00.000Z",
                },
                {
                    "homeTeamName": "França",
                    "awayTeamName": "Iraque",
                    "homeScore": 3,
                    "awayScore": 0,
                    "scheduledAt": "2026-06-23T19:00:00.000Z",
                },
            ]
        }

        scraper.rebuild_historical_snapshots(api_data, palpites_file)

        historico = pd.read_excel(settings.HISTORICO_EXCEL)
        historico["data"] = pd.to_datetime(historico["data_hora"]).dt.strftime("%Y-%m-%d")

        self.assertEqual(historico.loc[historico["data"] == "2026-06-11", "pontos"].iloc[0], 10)
        self.assertEqual(historico.loc[historico["data"] == "2026-06-23", "pontos"].iloc[0], 35)


if __name__ == "__main__":
    unittest.main()
