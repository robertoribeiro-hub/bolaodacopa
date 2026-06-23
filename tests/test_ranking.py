import unittest
import pandas as pd

from app.views.ranking import build_live_points, normalize_team_name, team_names_match


class TestRankingLivePoints(unittest.TestCase):
    def test_normalize_team_name_removes_accents_and_punctuation(self):
        self.assertEqual(normalize_team_name("Áustria"), "austria")
        self.assertEqual(normalize_team_name("Côte d'Ivoire"), "cote divoire")
        self.assertEqual(normalize_team_name("  São Paulo  "), "sao paulo")

    def test_team_names_match_accepts_swapped_order(self):
        self.assertTrue(team_names_match("argentina", "austria", "austria", "argentina"))
        self.assertTrue(team_names_match("argentina", "austria", "argentina", "austria"))
        self.assertTrue(team_names_match("australia", "turquia", "turquia", "australia"))

    def test_build_live_points_returns_draw_points_for_current_score(self):
        df_palpites = pd.DataFrame([
            {
                "participante": "Maia",
                "arroba": "@maiaa",
                "mandante": "Argentina",
                "visitante": "Áustria",
                "palpite_m": 1,
                "palpite_v": 1,
            },
            {
                "participante": "Outro",
                "arroba": "@outro",
                "mandante": "Argentina",
                "visitante": "Áustria",
                "palpite_m": 2,
                "palpite_v": 1,
            },
        ])

        live_matches = [
            {
                "homeTeam": {"name": "Argentina"},
                "awayTeam": {"name": "Áustria"},
                "homeScore": 0,
                "awayScore": 0,
            }
        ]

        df_live = build_live_points(df_palpites, live_matches)
        self.assertEqual(len(df_live), 2)
        self.assertEqual(df_live.loc[df_live["arroba"] == "@maiaa", "pontos_ao_vivo"].iloc[0], 15)
        self.assertEqual(df_live.loc[df_live["arroba"] == "@outro", "pontos_ao_vivo"].iloc[0], 0)

    def test_build_live_points_does_not_double_exact_score_through_june_27(self):
        df_palpites = pd.DataFrame([
            {
                "participante": "Daniel Silveira",
                "arroba": "@copydani",
                "mandante": "Portugal",
                "visitante": "Uzbequistão",
                "palpite_m": 4,
                "palpite_v": 0,
            },
        ])

        live_matches = [
            {
                "homeTeam": {"name": "Portugal"},
                "awayTeam": {"name": "Uzbequistão"},
                "homeScore": 4,
                "awayScore": 0,
                "scheduledAt": "2026-06-27T17:00:00.000Z",
                "round": "Final",
            }
        ]

        df_live = build_live_points(df_palpites, live_matches)
        self.assertEqual(df_live["pontos_ao_vivo"].iloc[0], 25)

    def test_build_live_points_doubles_exact_score_from_june_28(self):
        df_palpites = pd.DataFrame([
            {
                "participante": "Daniel Silveira",
                "arroba": "@copydani",
                "mandante": "Portugal",
                "visitante": "Uzbequistão",
                "palpite_m": 4,
                "palpite_v": 0,
            },
        ])

        live_matches = [
            {
                "homeTeam": {"name": "Portugal"},
                "awayTeam": {"name": "Uzbequistão"},
                "homeScore": 4,
                "awayScore": 0,
                "scheduledAt": "2026-06-28T17:00:00.000Z",
            }
        ]

        df_live = build_live_points(df_palpites, live_matches)
        self.assertEqual(df_live["pontos_ao_vivo"].iloc[0], 50)

    def test_build_live_points_returns_empty_dataframe_with_columns_when_no_match(self):
        df_palpites = pd.DataFrame([
            {"participante": "Maia", "arroba": "@maiaa", "mandante": "Brasil", "visitante": "Argentina", "palpite_m": 1, "palpite_v": 1}
        ])
        live_matches = [
            {"homeTeam": {"name": "França"}, "awayTeam": {"name": "Alemanha"}, "homeScore": 0, "awayScore": 0}
        ]
        df_live = build_live_points(df_palpites, live_matches)
        self.assertListEqual(df_live.columns.tolist(), ["participante", "arroba", "pontos_ao_vivo"])
        self.assertEqual(len(df_live), 0)


if __name__ == "__main__":
    unittest.main()
