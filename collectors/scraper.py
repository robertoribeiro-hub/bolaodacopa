"""
Módulo de coleta de dados do DaCopa.

ESTRATÉGIA: Em vez de raspar HTML (frágil, quebra quando o layout muda),
usamos a API REST oficial do DaCopa:
  GET https://api.dacopa.com/groups/{group_id}/leaderboard

A API retorna JSON com dois arrays principais:
  - standings: classificação com todos os dados de cada participante
  - finishedMatches: partidas finalizadas

A chamada é feita via page.evaluate() para reutilizar os cookies de sessão
do Playwright, que já realizou o login em app.dacopa.com.
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import unicodedata
from typing import Optional
from playwright.sync_api import sync_playwright, Page
from config import settings
from collectors import session_manager

logger = session_manager.logger

# URL base da API (diferente da URL do app)
DACOPA_API_BASE = "https://api.dacopa.com"
LOCAL_TIMEZONE = "America/Sao_Paulo"

# Fallback para reconstruir o histórico quando a API do dashboard não retorna
# partidas finalizadas. As datas abaixo seguem as janelas das rodadas usadas
# no dashboard: primeira rodada (11/06-17/06) e segunda rodada (18/06-23/06).
FALLBACK_MATCH_DATES = [
    ("2026-06-11", "México", "África do Sul", 2, 0),
    ("2026-06-11", "Coreia do Sul", "República Tcheca", 2, 1),
    ("2026-06-12", "Canadá", "Bósnia", 1, 1),
    ("2026-06-12", "Estados Unidos", "Paraguai", 4, 1),
    ("2026-06-13", "Catar", "Suíça", 1, 1),
    ("2026-06-13", "Brasil", "Marrocos", 1, 1),
    ("2026-06-13", "Haiti", "Escócia", 0, 1),
    ("2026-06-14", "Austrália", "Turquia", 2, 0),
    ("2026-06-14", "Alemanha", "Curaçao", 7, 1),
    ("2026-06-14", "Holanda", "Japão", 2, 2),
    ("2026-06-14", "Costa do Marfim", "Equador", 1, 0),
    ("2026-06-14", "Suécia", "Tunísia", 5, 1),
    ("2026-06-15", "Espanha", "Cabo Verde", 0, 0),
    ("2026-06-15", "Bélgica", "Egito", 1, 1),
    ("2026-06-15", "Arábia Saudita", "Uruguai", 1, 1),
    ("2026-06-15", "Irã", "Nova Zelândia", 2, 2),
    ("2026-06-16", "França", "Senegal", 3, 1),
    ("2026-06-16", "Iraque", "Noruega", 1, 4),
    ("2026-06-16", "Argentina", "Argélia", 3, 0),
    ("2026-06-17", "Áustria", "Jordânia", 3, 1),
    ("2026-06-17", "Portugal", "RD Congo", 1, 1),
    ("2026-06-17", "Inglaterra", "Croácia", 4, 2),
    ("2026-06-17", "Gana", "Panamá", 1, 0),
    ("2026-06-17", "Uzbequistão", "Colômbia", 1, 3),
    ("2026-06-18", "República Tcheca", "África do Sul", 1, 1),
    ("2026-06-18", "Suíça", "Bósnia", 4, 1),
    ("2026-06-18", "Canadá", "Catar", 6, 0),
    ("2026-06-18", "México", "Coreia do Sul", 1, 0),
    ("2026-06-19", "Estados Unidos", "Austrália", 2, 0),
    ("2026-06-19", "Escócia", "Marrocos", 0, 1),
    ("2026-06-19", "Brasil", "Haiti", 3, 0),
    ("2026-06-20", "Turquia", "Paraguai", 0, 1),
    ("2026-06-20", "Holanda", "Suécia", 5, 1),
    ("2026-06-20", "Alemanha", "Costa do Marfim", 2, 1),
    ("2026-06-20", "Equador", "Curaçao", 0, 0),
    ("2026-06-21", "Tunísia", "Japão", 0, 4),
    ("2026-06-21", "Espanha", "Arábia Saudita", 4, 0),
    ("2026-06-21", "Bélgica", "Irã", 0, 0),
    ("2026-06-21", "Uruguai", "Cabo Verde", 2, 2),
    ("2026-06-21", "Nova Zelândia", "Egito", 1, 3),
    ("2026-06-22", "Argentina", "Áustria", 2, 0),
    ("2026-06-22", "França", "Iraque", 3, 0),
    ("2026-06-22", "Noruega", "Senegal", 3, 2),
    ("2026-06-23", "Jordânia", "Argélia", 1, 2),
    ("2026-06-23", "Portugal", "Uzbequistão", None, None),
    ("2026-06-23", "Inglaterra", "Gana", None, None),
    ("2026-06-23", "Panamá", "Croácia", None, None),
    ("2026-06-23", "Colômbia", "RD Congo", None, None),
]


# ──────────────────────────────────────────────────────────────
# Funções de inicialização / persistência
# ──────────────────────────────────────────────────────────────

def init_membros_excel():
    """Garante que o arquivo membros.xlsx exista com a estrutura correta."""
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not settings.MEMBROS_EXCEL.exists():
        logger.info(f"Criando arquivo membros.xlsx inicial em {settings.MEMBROS_EXCEL}")
        df = pd.DataFrame(columns=["nome", "arroba"])
        df.to_excel(settings.MEMBROS_EXCEL, index=False)
    else:
        logger.debug("Arquivo membros.xlsx já existe.")


def init_historico_excel():
    """Garante que o arquivo historico.xlsx exista com a estrutura correta."""
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not settings.HISTORICO_EXCEL.exists():
        logger.info(f"Criando arquivo historico.xlsx inicial em {settings.HISTORICO_EXCEL}")
        df = pd.DataFrame(columns=[
            "data_hora", "coleta_id", "participante", "arroba", "posicao", "pontos",
            "placar_exato", "gols_vencedor", "saldo_gols", "gols_perdedor", "vencedor_certo", "sem_pontos"
        ])
        df.to_excel(settings.HISTORICO_EXCEL, index=False)
    else:
        logger.debug("Arquivo historico.xlsx já existe.")


def update_membros_list(novos_membros: list[dict]):
    """
    Atualiza a lista de membros no Excel.
    Adiciona apenas membros novos (comparando pelo arroba).
    RN004: Participantes removidos no DaCopa permanecem no histórico do Excel.
    """
    init_membros_excel()

    if not novos_membros:
        logger.warning("Nenhum membro extraído para atualizar.")
        return

    try:
        df_atual = pd.read_excel(settings.MEMBROS_EXCEL)

        if "nome" not in df_atual.columns or "arroba" not in df_atual.columns:
            df_atual = pd.DataFrame(columns=["nome", "arroba"])

        df_novos = pd.DataFrame(novos_membros)
        df_novos = df_novos.drop_duplicates(subset=["arroba"])

        if not df_atual.empty:
            arrobas_atuais = set(df_atual["arroba"].dropna().astype(str).tolist())
            df_adicionar = df_novos[~df_novos["arroba"].astype(str).isin(arrobas_atuais)]
        else:
            df_adicionar = df_novos

        if not df_adicionar.empty:
            df_final = pd.concat([df_atual, df_adicionar], ignore_index=True)
            df_final.to_excel(settings.MEMBROS_EXCEL, index=False)
            logger.info(f"Adicionado(s) {len(df_adicionar)} novo(s) membro(s): {df_adicionar['arroba'].tolist()}")
        else:
            logger.info("Nenhum membro novo detectado. Lista já atualizada.")

    except Exception as e:
        logger.error(f"Erro ao atualizar membros.xlsx: {e}")
        raise e


def save_ranking_snapshot(ranking: list[dict]) -> bool:
    """
    Salva o ranking atual como um snapshot em historico.xlsx de forma incremental.
    Evita gravar se o ranking for idêntico ao último snapshot cadastrado.
    """
    init_historico_excel()

    if not ranking:
        logger.warning("Lista de ranking vazia, nada a salvar no histórico.")
        return False

    try:
        now = datetime.now()
        data_hora_str = now.strftime("%Y-%m-%d %H:%M:%S")
        coleta_id = now.strftime("%Y%m%d%H%M%S")

        df_atual = pd.read_excel(settings.HISTORICO_EXCEL)

        # Verificação de redundância para evitar gravar snapshots estéreis
        if not df_atual.empty:
            ultimo_coleta_id = df_atual["coleta_id"].iloc[-1]
            df_ultimo = df_atual[df_atual["coleta_id"] == ultimo_coleta_id]

            comparar_cols = ["posicao", "pontos", "placar_exato", "gols_vencedor",
                             "saldo_gols", "gols_perdedor", "vencedor_certo", "sem_pontos"]

            ultimo_map = {
                row["arroba"]: tuple(row.get(col, 0) for col in comparar_cols)
                for _, row in df_ultimo.iterrows()
            }
            novo_map = {
                item["arroba"]: tuple(item.get(col, 0) for col in comparar_cols)
                for item in ranking
            }

            if (len(ultimo_map) == len(novo_map) and
                    all(k in novo_map and ultimo_map[k] == novo_map[k] for k in ultimo_map)):
                logger.info("Ranking idêntico ao último snapshot. Gravação ignorada.")
                return False

        linhas_novas = [{
            "data_hora":       data_hora_str,
            "coleta_id":       coleta_id,
            "participante":    item["nome"],
            "arroba":          item["arroba"],
            "posicao":         item["posicao"],
            "pontos":          item["pontos"],
            "placar_exato":    item.get("placar_exato", 0),
            "gols_vencedor":   item.get("gols_vencedor", 0),
            "saldo_gols":      item.get("saldo_gols", 0),
            "gols_perdedor":   item.get("gols_perdedor", 0),
            "vencedor_certo":  item.get("vencedor_certo", 0),
            "sem_pontos":      item.get("sem_pontos", 0),
        } for item in ranking]

        df_novos = pd.DataFrame(linhas_novas)
        df_final = pd.concat([df_atual, df_novos], ignore_index=True)
        df_final.to_excel(settings.HISTORICO_EXCEL, index=False)
        logger.info(f"Novo snapshot gravado! Coleta ID: {coleta_id}")
        return True

    except Exception as e:
        logger.error(f"Erro ao salvar snapshot em historico.xlsx: {e}")
        raise e


# ──────────────────────────────────────────────────────────────
# Acesso à API REST do DaCopa via contexto autenticado
# ──────────────────────────────────────────────────────────────

def _extract_api_authorization_token(page: Page) -> Optional[str]:
    """Captura o header Authorization usado pelo app para chamadas à API."""
    auth_token = None

    def capture_request(request):
        nonlocal auth_token
        url = request.url
        if 'api.dacopa.com' not in url:
            return

        authorization = request.headers.get('authorization') or request.headers.get('Authorization')
        if authorization and authorization.strip().lower().startswith('bearer '):
            auth_token = authorization.strip()

    page.on('request', capture_request)
    try:
        page.wait_for_timeout(1200)
    finally:
        try:
            page.off('request', capture_request)
        except Exception:
            pass

    return auth_token


def _fetch_api_json(page: Page, url: str, headers: dict) -> dict:
    return page.evaluate(
        "async ({ url, headers }) => {"
        "  const resp = await fetch(url, {"
        "    method: 'GET',"
        "    credentials: 'include',"
        "    headers: headers"
        "  });"
        "  if (!resp.ok) {"
        "    throw new Error('API retornou HTTP ' + resp.status + ' - ' + await resp.text());"
        "  }"
        "  return await resp.json();"
        "}",
        {"url": url, "headers": headers},
    )


def fetch_leaderboard_api(page: Page) -> dict:
    """
    Chama as APIs necessárias do DaCopa usando o contexto de sessão já autenticado
    do Playwright.

    Retorna um dict contendo o ranking do grupo e as partidas ao vivo.
    """
    dashboard_url = f"{DACOPA_API_BASE}/dashboard"
    leaderboard_url = f"{DACOPA_API_BASE}/groups/{settings.DACOPA_GROUP_ID}/leaderboard"

    app_url = f"{settings.DACOPA_BASE_URL}/groups/{settings.DACOPA_GROUP_ID}/leaderboard"
    logger.info(f"Navegando para {app_url} para validar sessão...")

    auth_token = None
    def capture_request(request):
        nonlocal auth_token
        url = request.url
        if 'api.dacopa.com' not in url:
            return

        authorization = request.headers.get('authorization') or request.headers.get('Authorization')
        if authorization and authorization.strip().lower().startswith('bearer '):
            auth_token = authorization.strip()

    page.on('request', capture_request)
    try:
        page.goto(app_url, timeout=30000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
    finally:
        try:
            page.off('request', capture_request)
        except Exception:
            pass

    if auth_token:
        logger.info("Token de autorização extraído do navegador para chamadas API.")
    else:
        logger.warning("Não foi possível extrair token de autorização. Tentando chamada API sem Authorization header.")

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    if auth_token:
        headers['Authorization'] = auth_token

    logger.info(f"Chamando API de grupo: GET {leaderboard_url}")
    leaderboard_data = _fetch_api_json(page, leaderboard_url, headers)

    logger.info(f"Chamando API do dashboard: GET {dashboard_url}")
    dashboard_data = _fetch_api_json(page, dashboard_url, headers)

    # Se a API do dashboard indicar que NÃO há partidas ao vivo,
    # forçamos `liveMatches` para uma lista vazia. Alguns endpoints
    # podem retornar dados antigos mesmo quando não há jogos ao vivo.
    has_live = dashboard_data.get('hasLiveMatches', False)
    live_matches = dashboard_data.get('liveMatches', []) if has_live else []
    if not has_live and dashboard_data.get('liveMatches'):
        logger.info("API retornou 'liveMatches' porém 'hasLiveMatches' está False — ignorando resultados.")

    result = {**leaderboard_data}
    result['liveMatches'] = live_matches
    result['finishedMatches'] = dashboard_data.get('finishedMatches', [])
    result['upcomingMatches'] = dashboard_data.get('upcomingMatches', [])
    result['banners'] = dashboard_data.get('banners', [])
    result['groupRankings'] = dashboard_data.get('groupRankings', [])
    result['hasLiveMatches'] = has_live

    standings_count = len(result.get('standings', []))
    matches_count = len(result.get('finishedMatches', []))
    logger.info(f"API retornou {standings_count} participantes e {matches_count} partidas finalizadas.")
    return result


def parse_standings(api_data: dict) -> tuple[list[dict], list[dict]]:
    """
    Extrai membros e ranking a partir do JSON retornado pela API.

    Mapeamento dos campos da API → nosso modelo:
      rank                  → posicao
      totalPoints           → pontos
      exactScoreCount       → placar_exato       (25 pts cada)
      winnersGoalsCount     → gols_vencedor      (18 pts cada) — "Venc. + Gols"
      goalDifferenceCount   → saldo_gols         (15 pts cada)
      losersGoalsCount      → gols_perdedor      (12 pts cada)
      correctWinnerCount    → vencedor_certo     (10 pts cada)
      drawGuaranteeCount    → empate_garantido   (não exibido, mas calculado)
      predictionsCount - soma_acertos → sem_pontos

      user.displayName      → nome
      user.handle           → arroba
    """
    standings = api_data.get("standings", [])

    membros  = []
    ranking  = []

    for entry in standings:
        user   = entry.get("user", {})
        nome   = user.get("displayName", "Desconhecido")
        handle = user.get("handle", "")
        arroba = f"@{handle}" if handle and not handle.startswith("@") else handle

        # Contagens de acerto por categoria
        placar_exato   = int(entry.get("exactScoreCount",    0))
        gols_vencedor  = int(entry.get("winnersGoalsCount",  0))
        saldo_gols     = int(entry.get("goalDifferenceCount", 0))
        gols_perdedor  = int(entry.get("losersGoalsCount",   0))
        vencedor_certo = int(entry.get("correctWinnerCount", 0))
        empate_gar     = int(entry.get("drawGuaranteeCount", 0))

        # "Sem Pontos" = palpites totais menos todos os que pontuaram
        total_palpites = int(entry.get("predictionsCount", 0))
        total_pontuados = (placar_exato + gols_vencedor + saldo_gols +
                           gols_perdedor + vencedor_certo + empate_gar)
        sem_pontos = max(0, total_palpites - total_pontuados)

        membros.append({"nome": nome, "arroba": arroba})

        ranking.append({
            "posicao":        int(entry.get("rank", 0)),
            "nome":           nome,
            "arroba":         arroba,
            "pontos":         int(entry.get("totalPoints", 0)),
            "placar_exato":   placar_exato,
            "gols_vencedor":  gols_vencedor,
            "saldo_gols":     saldo_gols,
            "gols_perdedor":  gols_perdedor,
            "vencedor_certo": vencedor_certo,
            "sem_pontos":     sem_pontos,
        })

        logger.info(
            f"  #{entry.get('rank'):>2} {nome:<35} (@{handle:<25}) "
            f"{int(entry.get('totalPoints', 0)):>4} pts | "
            f"PE={placar_exato} GV={gols_vencedor} SG={saldo_gols} "
            f"GP={gols_perdedor} VC={vencedor_certo} SP={sem_pontos}"
        )

    return membros, ranking


def normalize_team_key(value: str) -> str:
    """Normaliza nomes de times para cruzar HTML/API/fallback sem depender de acentos."""
    if pd.isna(value):
        return ""

    normalized = unicodedata.normalize("NFKD", str(value).strip().lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _safe_int(value) -> Optional[int]:
    if pd.isna(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _local_date_from_api(value) -> Optional[str]:
    if not value:
        return None

    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None

    return parsed.tz_convert(LOCAL_TIMEZONE).strftime("%Y-%m-%d")


def _extract_match_team(match: dict, side: str) -> str:
    nested = match.get(f"{side}Team")
    if isinstance(nested, dict):
        name = nested.get("name")
        if name:
            return name

    return (
        match.get(f"{side}TeamName")
        or match.get(f"{side}_team_name")
        or match.get(side)
        or ""
    )


def _extract_match_score(match: dict, side: str) -> Optional[int]:
    possible_keys = [
        f"{side}Score",
        f"{side}TeamScore",
        f"{side}_score",
        f"{side}Goals",
    ]
    for key in possible_keys:
        if key in match:
            return _safe_int(match.get(key))

    score = match.get("score")
    if isinstance(score, dict):
        for key in possible_keys:
            if key in score:
                return _safe_int(score.get(key))

    return None


def _match_pair_key(home: str, away: str) -> tuple[str, str]:
    return normalize_team_key(home), normalize_team_key(away)


def _match_score_key(home: str, away: str, home_score, away_score) -> Optional[tuple[str, str, int, int]]:
    home_score = _safe_int(home_score)
    away_score = _safe_int(away_score)
    if home_score is None or away_score is None:
        return None

    home_key, away_key = _match_pair_key(home, away)
    return home_key, away_key, home_score, away_score


def build_match_date_lookup(api_data: dict) -> tuple[dict, dict]:
    """
    Monta lookup de datas por partida.

    Prioriza dados da API quando disponíveis e completa com o calendário conhecido
    das duas primeiras rodadas para permitir reconstrução após limpar storage/.
    """
    scored_lookup = {}
    pair_dates = {}

    def add_match(date_str: Optional[str], home: str, away: str, home_score=None, away_score=None):
        if not date_str or not home or not away:
            return

        pair_key = _match_pair_key(home, away)
        pair_dates.setdefault(pair_key, set()).add(date_str)

        score_key = _match_score_key(home, away, home_score, away_score)
        if score_key is not None:
            scored_lookup[score_key] = date_str

    for date_str, home, away, home_score, away_score in FALLBACK_MATCH_DATES:
        add_match(date_str, home, away, home_score, away_score)

    for collection_name in ("finishedMatches", "liveMatches", "upcomingMatches"):
        for match in api_data.get(collection_name, []) or []:
            date_str = _local_date_from_api(match.get("scheduledAt") or match.get("date"))
            home = _extract_match_team(match, "home")
            away = _extract_match_team(match, "away")
            home_score = _extract_match_score(match, "home")
            away_score = _extract_match_score(match, "away")
            add_match(date_str, home, away, home_score, away_score)

    unique_pair_lookup = {
        pair_key: next(iter(dates))
        for pair_key, dates in pair_dates.items()
        if len(dates) == 1
    }
    return scored_lookup, unique_pair_lookup


def resolve_match_date(row: pd.Series, scored_lookup: dict, pair_lookup: dict) -> Optional[str]:
    home = row.get("mandante", "")
    away = row.get("visitante", "")
    score_key = _match_score_key(home, away, row.get("placar_real_m"), row.get("placar_real_v"))

    if score_key is not None and score_key in scored_lookup:
        return scored_lookup[score_key]

    return pair_lookup.get(_match_pair_key(home, away))



def init_palpites_excel():

    """Garante que o arquivo palpites.xlsx exista com a estrutura correta."""
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    if not settings.PALPITES_EXCEL.exists():
        logger.info(f"Criando arquivo palpites.xlsx inicial em {settings.PALPITES_EXCEL}")
        df = pd.DataFrame(columns=[
            "coleta_id", "partida_id", "mandante", "visitante",
            "placar_real_m", "placar_real_v",
            "participante", "arroba",
            "palpite_m", "palpite_v", "categoria"
        ])
        df.to_excel(settings.PALPITES_EXCEL, index=False)
    else:
        logger.debug("Arquivo palpites.xlsx já existe.")


def fetch_palpites_membro(page, handle: str, nome: str, arroba: str, coleta_id: str) -> list[dict]:
    """
    Navega para a página de palpites de um membro e extrai os dados
    de cada partida: equipes, placar real e palpite do participante.

    Estrutura do HTML (extraída via exploração):
      [Horário]
      [Mandante] [GolsM x GolsV] [Visitante]
      PALPITE
      [PalpiteM] : [PalpiteV]
      [Categoria]
    """
    url = f"{settings.DACOPA_BASE_URL}/groups/{settings.DACOPA_GROUP_ID}/leaderboard/{handle}"
    logger.info(f"  Buscando palpites de @{handle} em {url}")

    try:
        page.goto(url, timeout=30000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)

        # Extrai os dados via JavaScript
        dados = page.evaluate(r"""() => {
            const palpites = [];
            
            // O texto da página é a fonte mais confiável
            // Pattern observado:
            //   [Hora] [mandante] [GolsM x GolsV] [visitante] PALPITE [M] : [V] [categoria] [+pts]
            // Usamos os elementos do DOM para identificar cada bloco de partida
            
            // Encontra todos os itens de partida via os elementos que contêm "PALPITE"
            const bodyText = document.body.innerText;
            const lines = bodyText.split('\n').map(l => l.trim()).filter(l => l.length > 0);
            
            let i = 0;
            while (i < lines.length) {
                // Detecta a linha "PALPITE"
                if (lines[i] === 'PALPITE') {
                    // Busca para trás para encontrar o bloco deste jogo
                    // Estrutura típica: [hora] \n [mandante] \n [GolsM x GolsV] \n [visitante] \n PALPITE
                    // Ou pode variar. Tenta capturar mandante, placar e visitante
                    
                    let mandante = '', placarReal = '', visitante = '';
                    let palpiteStr = '', categoria = '';
                    
                    // Placar real é uma linha anterior que contém " x " (com espaços)
                    for (let j = i - 1; j >= Math.max(0, i - 8); j--) {
                        if (lines[j].match(/^\d+ x \d+$/)) {
                            placarReal = lines[j];
                            // Visitante está logo abaixo do placar
                            // Mandante está logo acima
                            if (j + 1 < i) visitante = lines[j + 1];
                            if (j - 1 >= 0) mandante = lines[j - 1];
                            break;
                        }
                    }
                    
                    // Palpite está logo abaixo de PALPITE, formato "M : V"
                    if (i + 1 < lines.length && lines[i + 1].match(/^\d+ : \d+$/)) {
                        palpiteStr = lines[i + 1];
                        if (i + 2 < lines.length) categoria = lines[i + 2];
                    }
                    
                    if (placarReal && palpiteStr) {
                        const [rm, rv] = placarReal.split(' x ').map(Number);
                        const [pm, pv] = palpiteStr.split(' : ').map(Number);
                        palpites.push({
                            mandante,
                            visitante,
                            placar_real_m: rm,
                            placar_real_v: rv,
                            palpite_m: pm,
                            palpite_v: pv,
                            categoria: categoria.replace('+', '').trim()
                        });
                    }
                    
                    i += 3;
                } else {
                    i++;
                }
            }
            
            return palpites;
        }""")

        registros = []
        for idx, d in enumerate(dados):
            partida_id = f"{d['mandante'].lower()[:4]}x{d['visitante'].lower()[:4]}_{coleta_id}"
            registros.append({
                "coleta_id": coleta_id,
                "partida_id": partida_id,
                "mandante": d["mandante"],
                "visitante": d["visitante"],
                "placar_real_m": d.get("placar_real_m", -1),
                "placar_real_v": d.get("placar_real_v", -1),
                "participante": nome,
                "arroba": arroba,
                "palpite_m": d.get("palpite_m", -1),
                "palpite_v": d.get("palpite_v", -1),
                "categoria": d.get("categoria", "")
            })

        logger.info(f"    → {len(registros)} palpites coletados de @{handle}")
        return registros

    except Exception as e:
        logger.error(f"  ERRO ao buscar palpites de @{handle}: {e}")
        return []


def save_palpites_snapshot(palpites: list[dict], coleta_id: str) -> bool:
    """
    Salva o snapshot de palpites individuais em palpites.xlsx.
    Remove os registros da mesma coleta_id antes de salvar (idempotente).
    """
    init_palpites_excel()

    if not palpites:
        logger.warning("Lista de palpites vazia, nada a salvar.")
        return False

    try:
        df_atual = pd.read_excel(settings.PALPITES_EXCEL)

        # Remove registros da mesma coleta (permite re-sincronização idempotente)
        if not df_atual.empty and "coleta_id" in df_atual.columns:
            df_atual = df_atual[df_atual["coleta_id"].astype(str) != str(coleta_id)]

        df_novos = pd.DataFrame(palpites)
        df_final = pd.concat([df_atual, df_novos], ignore_index=True)
        
        # Deduplica mantendo partidas repetidas entre os mesmos times quando o placar real muda.
        df_final = df_final.drop_duplicates(
            subset=["participante", "mandante", "visitante", "placar_real_m", "placar_real_v"],
            keep="last",
        )
        
        df_final.to_excel(settings.PALPITES_EXCEL, index=False)
        logger.info(f"Palpites salvos em palpites.xlsx. Total: {len(df_novos)} registros (coleta {coleta_id}).")
        return True

    except Exception as e:
        logger.error(f"Erro ao salvar palpites.xlsx: {e}")
        return False


def save_live_matches(live_matches: list[dict]) -> bool:
    """
    Persiste a lista de partidas ao vivo em um arquivo JSON.
    """
    try:
        settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        with open(settings.LIVE_MATCHES_FILE, "w", encoding="utf-8") as f:
            json.dump(live_matches or [], f, ensure_ascii=False, indent=2)

        logger.info(f"liveMatches salvos em: {settings.LIVE_MATCHES_FILE}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar live_matches.json: {e}")
        return False


def rebuild_historical_snapshots(api_data: dict, palpites_file: Path):
    """
    Recalcula o ranking dia a dia com base nos palpites salvos e nas partidas finalizadas da API,
    reescrevendo o historico.xlsx completo.
    """
    try:
        if not palpites_file.exists():
            return

        df_palpites = pd.read_excel(palpites_file)
        if df_palpites.empty:
            return

        scored_lookup, pair_lookup = build_match_date_lookup(api_data)
        if not scored_lookup and not pair_lookup:
            logger.warning("Nenhuma data de partida disponível para reconstruir o histórico.")
            return

        df_palpites["data_partida"] = df_palpites.apply(
            lambda row: resolve_match_date(row, scored_lookup, pair_lookup),
            axis=1,
        )
        
        # Filtra apenas palpites de partidas que ganharam data.
        df_validos = df_palpites[df_palpites["data_partida"].notna()].copy()
        if df_validos.empty:
            logger.warning("Nenhum palpite conseguiu ser associado a uma data de partida.")
            return

        # Dias de jogos em ordem cronológica
        dias_jogos = sorted(df_validos["data_partida"].unique())
        
        PONTOS_MAP = {
            'Placar exato': 25,
            'Gols do vencedor': 18,
            'Saldo de gols': 15,
            'Gols do perdedor': 12,
            'Vencedor certo': 10,
            'Sem pontos': 0
        }

        historico_rows = []
        
        for idx_dia, dia_atual in enumerate(dias_jogos):
            # Para este dia, consideramos todas as partidas até este dia
            df_ate_hoje = df_validos[df_validos["data_partida"] <= dia_atual].copy()
            df_ate_hoje["pontos_calculados"] = df_ate_hoje["categoria"].map(PONTOS_MAP).fillna(0)
            
            # Agrupa por participante
            grouped = df_ate_hoje.groupby(["participante", "arroba"])
            
            pontos = grouped["pontos_calculados"].sum()
            cats = df_ate_hoje.groupby(["participante", "arroba", "categoria"]).size().unstack(fill_value=0)
            
            # Para cada participante, monta um registro
            registros_dia = []
            for (part, arr) in pontos.index:
                pts = int(pontos.loc[(part, arr)])
                row_cats = cats.loc[(part, arr)] if (part, arr) in cats.index else pd.Series()
                pe = int(row_cats.get("Placar exato", 0))
                gv = int(row_cats.get("Gols do vencedor", 0))
                sg = int(row_cats.get("Saldo de gols", 0))
                gp = int(row_cats.get("Gols do perdedor", 0))
                vc = int(row_cats.get("Vencedor certo", 0))
                sp = int(row_cats.get("Sem pontos", 0))
                
                registros_dia.append({
                    "data_hora": f"{dia_atual} 23:59:59",
                    "coleta_id": dia_atual.replace("-", "") + "235959",
                    "participante": part,
                    "arroba": arr,
                    "pontos": pts,
                    "placar_exato": pe,
                    "gols_vencedor": gv,
                    "saldo_gols": sg,
                    "gols_perdedor": gp,
                    "vencedor_certo": vc,
                    "sem_pontos": sp
                })
            
            df_dia = pd.DataFrame(registros_dia)
            # Ordena: pontos desc, placar_exato desc, participante asc
            df_dia = df_dia.sort_values(by=["pontos", "placar_exato", "participante"], ascending=[False, False, True]).reset_index(drop=True)
            df_dia["posicao"] = df_dia.index + 1
            
            historico_rows.extend(df_dia.to_dict('records'))
            
        df_historico_reconstruido = pd.DataFrame(historico_rows)
        # Substitui o histórico atual
        df_historico_reconstruido.to_excel(settings.HISTORICO_EXCEL, index=False)
        logger.info(f"Histórico retroativo reconstruído para {len(dias_jogos)} dias de jogos.")

    except Exception as e:
        logger.error(f"Erro ao reconstruir histórico: {e}", exc_info=True)


# ──────────────────────────────────────────────────────────────
# Funções públicas de coleta
# ──────────────────────────────────────────────────────────────

def run_coleta_completa() -> bool:
    """
    Ponto de entrada principal. Realiza a sincronização completa:
      1. Faz login (ou reusa sessão salva)
      2. Chama a API REST do DaCopa
      3. Extrai membros e ranking do JSON
      4. Persiste os dados nos arquivos Excel
      5. Coleta palpites individuais por membro (via scraping HTML)
    """
    logger.info("─" * 60)
    logger.info("Iniciando Sincronização Completa via API DaCopa")
    logger.info("─" * 60)

    missing_env = settings.missing_dacopa_env_vars()
    if missing_env:
        logger.error(
            "Configuração DaCopa incompleta no .env. Variáveis faltando: %s",
            ", ".join(missing_env),
        )
        return False

    try:
        with sync_playwright() as p:
            context = session_manager.get_authenticated_context(p)
            page = context.new_page()

            # 1. Chama a API
            api_data = fetch_leaderboard_api(page)

            # 2. Parseia o JSON
            membros, ranking = parse_standings(api_data)

            if not ranking:
                logger.error("Nenhum participante retornado pela API.")
                context.close()
                return False

            # 3. Persiste membros
            update_membros_list(membros)

            # 4. Persiste liveMatches
            save_live_matches(api_data.get("liveMatches", []))

            # 5. Persiste snapshot de ranking
            coleta_id = datetime.now().strftime("%Y%m%d%H%M%S")
            save_ranking_snapshot(ranking)

            # 6. Coleta palpites individuais de cada membro
            logger.info("─" * 40)
            logger.info("Coletando palpites individuais por membro...")
            todos_palpites = []
            for item in ranking:
                handle = item["arroba"].lstrip("@")
                palpites_membro = fetch_palpites_membro(
                    page, handle, item["nome"], item["arroba"], coleta_id
                )
                todos_palpites.extend(palpites_membro)

            save_palpites_snapshot(todos_palpites, coleta_id)

            # 6. Reconstrução do histórico retroativo dia-a-dia
            logger.info("Reconstruindo histórico retroativo dia a dia...")
            rebuild_historical_snapshots(api_data, settings.PALPITES_EXCEL)

            context.close()
            logger.info("─" * 60)
            logger.info("Sincronização via API finalizada com SUCESSO!")
            logger.info("─" * 60)
            return True

    except Exception as e:
        logger.error(f"Erro na sincronização: {e}", exc_info=True)
        return False


# Mantidos por compatibilidade com chamadas legadas
def run_coleta_membros() -> bool:
    return run_coleta_completa()


def run_coleta_ranking() -> bool:
    return run_coleta_completa()


if __name__ == "__main__":
    run_coleta_completa()
