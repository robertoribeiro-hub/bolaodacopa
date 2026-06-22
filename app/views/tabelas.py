import streamlit as st
import pandas as pd


def render(df_historico: pd.DataFrame) -> None:
    st.markdown("<div class='section-title'>Rankings por Rodada</div>", unsafe_allow_html=True)

    if df_historico.empty:
        st.info("Nenhum dado cadastrado. Atualize o bolão no Painel Admin.")
        return

    df_rounds = df_historico.copy()
    df_rounds["data_hora"] = pd.to_datetime(df_rounds["data_hora"], errors="coerce")
    df_rounds = df_rounds.sort_values(by=["data_hora", "coleta_id"])

    def render_ranking_table(titulo: str, data_inicio: str, data_fim: str):
        inicio = pd.to_datetime(data_inicio)
        fim = pd.to_datetime(data_fim) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_faixa = df_rounds[(df_rounds["data_hora"] >= inicio) & (df_rounds["data_hora"] <= fim)].copy()

        if df_faixa.empty:
            st.info(f"Nenhum ranking registrado para {titulo} ({data_inicio} a {data_fim}).")
            return

        idx_ultima = df_faixa.sort_values(["participante", "arroba", "data_hora"]).groupby(["participante", "arroba"])["data_hora"].idxmax()
        df_ultima = df_faixa.loc[idx_ultima, ["participante", "arroba", "pontos"]].copy()
        df_ultima = df_ultima.rename(columns={"pontos": "pontos_ultima"})

        df_antes = df_rounds[df_rounds["data_hora"] < inicio].copy()
        if not df_antes.empty:
            idx_antes = df_antes.sort_values(["participante", "arroba", "data_hora"]).groupby(["participante", "arroba"])["data_hora"].idxmax()
            df_antes = df_antes.loc[idx_antes, ["participante", "arroba", "pontos"]].copy()
            df_antes = df_antes.rename(columns={"pontos": "pontos_antes"})
        else:
            df_antes = pd.DataFrame(columns=["participante", "arroba", "pontos_antes"])

        df_ranking = df_ultima.merge(df_antes, on=["participante", "arroba"], how="left")
        df_ranking["pontos_antes"] = df_ranking["pontos_antes"].fillna(0)
        df_ranking["Pontuação"] = (df_ranking["pontos_ultima"] - df_ranking["pontos_antes"]).clip(lower=0)
        df_ranking = df_ranking.sort_values(by=["Pontuação", "participante", "arroba"], ascending=[False, True, True]).reset_index(drop=True)
        df_ranking.insert(0, "Posição", range(1, len(df_ranking) + 1))
        df_ranking = df_ranking[["Posição", "participante", "arroba", "Pontuação"]].rename(columns={
            "participante": "Participante",
            "arroba": "Usuário (@)"
        })

        st.markdown(
            f"<div style='font-weight:700; margin-bottom:8px;'>{titulo} <span style='font-weight:400; color:#64748b; font-size:0.95rem;'>{data_inicio} a {data_fim}</span></div>",
            unsafe_allow_html=True,
        )
        st.dataframe(df_ranking, use_container_width=True, hide_index=True, height=520)

    rodadas = [
        {
            "titulo": "Primeira Rodada",
            "data_inicio": "2026-06-11",
            "data_fim": "2026-06-17",
        },
        {
            "titulo": "Segunda Rodada",
            "data_inicio": "2026-06-18",
            "data_fim": "2026-06-23",
        },
        {
            "titulo": "Terceira Rodada",
            "data_inicio": "2026-06-24",
            "data_fim": "2026-06-27",
        },
        {
            "titulo": "Playoffs",
            "data_inicio": "2026-06-28",
            "data_fim": "2026-07-19",
        },
    ]

    hoje = pd.Timestamp.now().normalize()

    def format_rodada_label(rodada: dict) -> str:
        inicio = pd.to_datetime(rodada["data_inicio"])
        fim = pd.to_datetime(rodada["data_fim"])
        label = f"{rodada['titulo']} ({inicio.strftime('%d/%m')} a {fim.strftime('%d/%m')})"
        if hoje < inicio:
            label += " - indisponível"
        return label

    labels = [format_rodada_label(rodada) for rodada in rodadas]
    default_index = 0
    for index, rodada in enumerate(rodadas):
        if hoje >= pd.to_datetime(rodada["data_inicio"]):
            default_index = index

    selecionado = st.selectbox("Selecione a rodada", labels, index=default_index)
    rodada_escolhida = rodadas[labels.index(selecionado)]
    rodada_inicio = pd.to_datetime(rodada_escolhida["data_inicio"])

    if hoje < rodada_inicio:
        st.warning(
            f"A opção '{rodada_escolhida['titulo']}' estará disponível a partir de "
            f"{rodada_inicio.strftime('%d/%m/%Y')}."
        )
        return

    render_ranking_table(
        rodada_escolhida["titulo"],
        rodada_escolhida["data_inicio"],
        rodada_escolhida["data_fim"],
    )
