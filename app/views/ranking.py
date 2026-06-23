import unicodedata
import json
from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

from config import settings


LIVE_DOUBLE_POINTS_START_DATE = pd.Timestamp("2026-06-28").date()
LIVE_MATCH_TIMEZONE = "America/Sao_Paulo"


def normalize_team_name(value: str) -> str:
    if not isinstance(value, str):
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.casefold()
    normalized = "".join(ch for ch in normalized if ch.isalnum() or ch.isspace())
    return " ".join(normalized.split())


def team_names_match(home: str, away: str, live_home: str, live_away: str) -> bool:
    if not home or not away or not live_home or not live_away:
        return False

    if home == live_home and away == live_away:
        return True
    if home == live_away and away == live_home:
        return True

    if home in live_home and away in live_away:
        return True
    if home in live_away and away in live_home:
        return True

    if live_home in home and live_away in away:
        return True
    if live_home in away and live_away in home:
        return True

    if len(home) >= 3 and len(away) >= 3 and len(live_home) >= 3 and len(live_away) >= 3:
        if home[:4] == live_home[:4] and away[:4] == live_away[:4]:
            return True
        if home[:4] == live_away[:4] and away[:4] == live_home[:4]:
            return True

    return False


def calculate_live_points(pred_m: int, pred_v: int, actual_m: int, actual_v: int) -> int:
    try:
        pred_m = int(pred_m)
        pred_v = int(pred_v)
        actual_m = int(actual_m)
        actual_v = int(actual_v)
    except Exception:
        return 0

    if pred_m == actual_m and pred_v == actual_v:
        return 25

    pred_diff = pred_m - pred_v
    actual_diff = actual_m - actual_v
    pred_outcome = "draw" if pred_diff == 0 else "home" if pred_diff > 0 else "away"
    actual_outcome = "draw" if actual_diff == 0 else "home" if actual_diff > 0 else "away"

    if actual_outcome == "draw" and pred_outcome == "draw":
        return 15

    if actual_outcome == pred_outcome:
        winner_goals_actual = actual_m if actual_outcome == "home" else actual_v
        winner_goals_pred = pred_m if pred_outcome == "home" else pred_v
        if winner_goals_pred == winner_goals_actual:
            return 18

        if pred_diff == actual_diff:
            return 15

        loser_goals_pred = pred_v if pred_outcome == "home" else pred_m
        loser_goals_actual = actual_v if actual_outcome == "home" else actual_m
        if loser_goals_pred == loser_goals_actual:
            return 12

        return 10

    return 0


def get_match_date(value) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        if len(raw) == 10:
            parsed_date = pd.to_datetime(raw, errors="coerce")
            if not pd.isna(parsed_date):
                return parsed_date.date()
    elif pd.isna(value):
        return None

    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None

    return parsed.tz_convert(LIVE_MATCH_TIMEZONE).date()


def get_match_multiplier(match: dict) -> int:
    if not isinstance(match, dict):
        return 1

    match_date = get_match_date(match.get("scheduledAt") or match.get("date"))
    if match_date is None:
        return 1

    return 2 if match_date >= LIVE_DOUBLE_POINTS_START_DATE else 1


def render_live_matches(live_matches: list[dict]) -> None:
    if not live_matches:
        return

    st.markdown("<div class='section-title'>Partidas ao Vivo</div>", unsafe_allow_html=True)
    for match in live_matches:
        home = match.get("homeTeam", {}).get("name", "?")
        away = match.get("awayTeam", {}).get("name", "?")
        home_score = match.get("homeScore", "-")
        away_score = match.get("awayScore", "-")
        status = match.get("status", "")
        minute = match.get("matchMinute")
        scheduled = match.get("scheduledAt", "")

        label = status.replace("_", " ").title() if status else "Ao Vivo"
        if minute is not None:
            label = f"{label} • {minute}'"

        schedule_html = ""
        if scheduled:
            schedule_html = (
                f"<div style='margin-top:12px; color:#64748b; font-size:0.85rem;'>"
                f"Agendado: {scheduled}</div>"
            )

        st.markdown(
            f"""
            <div style='padding:16px; border-radius:16px; background:#f8fafc; border:1px solid #e2e8f0; margin-bottom:12px;'>
                <div style='font-size:0.95rem; color:#64748b; margin-bottom:8px;'>{label}</div>
                <div style='display:flex; align-items:center; justify-content:space-between; gap:16px;'>
                    <div style='text-align:right; flex:1;'>
                        <div style='font-size:1rem; color:#0f172a; font-weight:700;'>{home}</div>
                        <div style='font-size:0.85rem; color:#475569;'>Mandante</div>
                    </div>
                    <div style='font-size:1.8rem; font-weight:800; color:#15803d;'>
                        {home_score} x {away_score}
                    </div>
                    <div style='text-align:left; flex:1;'>
                        <div style='font-size:1rem; color:#0f172a; font-weight:700;'>{away}</div>
                        <div style='font-size:0.85rem; color:#475569;'>Visitante</div>
                    </div>
                </div>
                {schedule_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def build_live_points(df_palpites: pd.DataFrame, live_matches: list[dict]) -> pd.DataFrame:
    if df_palpites is None or df_palpites.empty or not live_matches:
        return pd.DataFrame(columns=["participante", "arroba", "pontos_ao_vivo"])

    live_map = {}
    for match in live_matches:
        home = normalize_team_name(match.get("homeTeam", {}).get("name", ""))
        away = normalize_team_name(match.get("awayTeam", {}).get("name", ""))
        if home and away:
            live_map[(home, away)] = (
                int(match.get("homeScore", 0)),
                int(match.get("awayScore", 0)),
                get_match_multiplier(match),
            )

    pontos = {}
    for _, row in df_palpites.iterrows():
        home = normalize_team_name(row.get("mandante", ""))
        away = normalize_team_name(row.get("visitante", ""))
        score_match = live_map.get((home, away)) or live_map.get((away, home))
        if score_match is None:
            for (live_home, live_away), match_score in live_map.items():
                if team_names_match(home, away, live_home, live_away):
                    score_match = match_score
                    break
        if score_match is None:
            continue

        actual_m, actual_v, multiplier = score_match
        pts = calculate_live_points(row.get("palpite_m", 0), row.get("palpite_v", 0), actual_m, actual_v)
        pts = pts * multiplier
        key = (row.get("participante", ""), row.get("arroba", ""))
        pontos[key] = pontos.get(key, 0) + pts

    results = [
        {"participante": participante, "arroba": arroba, "pontos_ao_vivo": score}
        for (participante, arroba), score in pontos.items()
    ]
    if not results:
        return pd.DataFrame(columns=["participante", "arroba", "pontos_ao_vivo"])
    return pd.DataFrame(results)


def render(df_historico: pd.DataFrame, df_palpites: pd.DataFrame = None, live_matches: Optional[list[dict]] = None) -> None:
    st.markdown("<div class='section-title'>Classificação Geral da Copa</div>", unsafe_allow_html=True)

    if df_historico.empty:
        st.info("Nenhum dado cadastrado. Atualize o bolão no Painel Admin.")
        return

    ultimo_coleta_id = df_historico["coleta_id"].iloc[-1]
    df_ranking = df_historico[df_historico["coleta_id"] == ultimo_coleta_id].copy()
    df_ranking = df_ranking.sort_values(by="posicao")
    # Recarrega o arquivo `live_matches.json` diretamente para garantir
    # que a renderização utilize o estado mais recente persistido pelo listener.
    try:
        if settings.LIVE_MATCHES_FILE.exists():
            with open(settings.LIVE_MATCHES_FILE, "r", encoding="utf-8") as f:
                live_matches = json.load(f) or []
    except Exception as e:
        st.error(f"Erro ao ler {settings.LIVE_MATCHES_FILE}: {e}")

    if live_matches is not None and df_palpites is not None:
        render_live_matches(live_matches)
        st.markdown(
            "<div style='margin-bottom:10px; color:#475569;'>"
            "Pontos Ao Vivo mostram quantos pontos o participante ganharia se "
            "as partidas ao vivo terminassem com o placar atual.</div>",
            unsafe_allow_html=True,
        )
        df_live_points = build_live_points(df_palpites, live_matches)
        if not df_live_points.empty:
            df_ranking = df_ranking.merge(
                df_live_points,
                on=["participante", "arroba"],
                how="left"
            )
            df_ranking["pontos_ao_vivo"] = df_ranking["pontos_ao_vivo"].fillna(0).astype(int)
        else:
            st.info("Nenhum palpite encontrado para as partidas ao vivo atuais. Pontos Ao Vivo serão exibidos como 0.")
            df_ranking["pontos_ao_vivo"] = 0
    else:
        df_ranking["pontos_ao_vivo"] = 0

    df_ranking["pontuacao_esperada"] = (df_ranking["pontos"] + df_ranking["pontos_ao_vivo"]).astype(int)

    df_exibicao = df_ranking[[
        "posicao", "participante", "arroba", "pontos", "pontuacao_esperada", "pontos_ao_vivo",
        "placar_exato", "gols_vencedor", "saldo_gols",
        "gols_perdedor", "vencedor_certo", "sem_pontos"
    ]].rename(columns={
        "posicao": "Posição",
        "participante": "Participante",
        "arroba": "Usuário (@)",
        "pontos": "Pontuação",
        "pontuacao_esperada": "Pontuação Esperada",
        "pontos_ao_vivo": "Pontos Ao Vivo (se acabar agora)",
        "placar_exato": "🎯 Placar Exato (25 pts)",
        "gols_vencedor": "⚽ Gols Vencedor (18 pts)",
        "saldo_gols": "⚖️ Saldo Gols (15 pts)",
        "gols_perdedor": "📉 Gols Perdedor (12 pts)",
        "vencedor_certo": "🏆 Vencedor Certo (10 pts)",
        "sem_pontos": "❌ Sem Pontos (0 pts)"
    })

    def medalha(pos):
        if pos == 1:
            return "🥇 1º"
        if pos == 2:
            return "🥈 2º"
        if pos == 3:
            return "🥉 3º"
        if pos == 4:
            return "🎖️ 4º"
        if pos == 5:
            return "🎖️ 5º"
        return f"🏃 {pos}º"

    df_exibicao["Posição"] = df_exibicao["Posição"].apply(medalha)

    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        height=780
    )
