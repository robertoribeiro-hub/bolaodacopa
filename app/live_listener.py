import threading
import time
import logging

from playwright.sync_api import sync_playwright

from config import settings

from collectors import session_manager, scraper


logger = logging.getLogger("bolao.live_listener")


def _match_team_name(match: dict, side: str) -> str:
    nested = match.get(f"{side}Team")
    if isinstance(nested, dict):
        name = nested.get("name")
        if name:
            return str(name).strip()

    for key in (f"{side}TeamName", f"{side}_team_name", side):
        value = match.get(key)
        if value:
            return str(value).strip()

    return ""


def _live_matches_signature(live_matches: list[dict]) -> tuple[str, ...]:
    """Identifica partidas ao vivo sem depender de placar/minuto/status."""
    signature = []
    for idx, match in enumerate(live_matches or []):
        match_id = (
            match.get("id")
            or match.get("matchId")
            or match.get("match_id")
            or match.get("gameId")
            or match.get("game_id")
        )
        if match_id:
            signature.append(str(match_id))
            continue

        home = _match_team_name(match, "home")
        away = _match_team_name(match, "away")
        scheduled = str(match.get("scheduledAt") or match.get("date") or "").strip()
        if home or away or scheduled:
            signature.append(f"{scheduled}|{home}|{away}")
        else:
            signature.append(f"live-match-{idx}")

    return tuple(sorted(signature))


def _listener_loop(poll_live_interval: int = 10, poll_idle_interval: int = 600, live_sync_retry_interval: int = 120):
    """Loop que mantém a conexão com a API em background e persiste `liveMatches`.

    - Quando há partidas ao vivo, verifica mais frequentemente (`poll_live_interval`).
    - Quando não há partidas, reduz frequência (`poll_idle_interval`).
    - Ao descobrir uma nova partida ao vivo, sincroniza `palpites.xlsx`.
    """
    if not settings.has_dacopa_config():
        logger.info("DaCopa config ausente; listener não iniciado.")
        return

    last_synced_live_signature = None
    last_sync_attempt_signature = None
    last_sync_attempt_at = 0.0

    try:
        with sync_playwright() as p:
            context = session_manager.get_authenticated_context(p)
            page = context.new_page()
            logger.info("Live listener iniciado e autenticado.")

            while True:
                try:
                    api_data = scraper.fetch_leaderboard_api(page)
                    live_matches = api_data.get("liveMatches", []) or []
                    scraper.save_live_matches(live_matches)

                    if live_matches:
                        live_signature = _live_matches_signature(live_matches)
                        now = time.monotonic()
                        can_retry = (
                            live_signature == last_sync_attempt_signature
                            and now - last_sync_attempt_at >= live_sync_retry_interval
                        )
                        should_sync = live_signature != last_synced_live_signature

                        if should_sync and (live_signature != last_sync_attempt_signature or can_retry):
                            logger.info("Partida ao vivo detectada; sincronizando palpites para atualizar ranking ao vivo.")
                            last_sync_attempt_signature = live_signature
                            last_sync_attempt_at = now

                            if scraper.sync_palpites_from_api_data(page, api_data):
                                last_synced_live_signature = live_signature
                                logger.info("Palpites sincronizados após detecção de live match.")
                            else:
                                logger.warning("Sincronização de palpites após live match não gravou novos dados.")

                        time.sleep(poll_live_interval)
                    else:
                        last_synced_live_signature = None
                        last_sync_attempt_signature = None
                        last_sync_attempt_at = 0.0
                        time.sleep(poll_idle_interval)

                except Exception as e:
                    logger.error(f"Erro no loop do live listener: {e}", exc_info=True)
                    time.sleep(30)

            # fecha contexto quando o loop terminar (teoricamente nunca)
            try:
                page.close()
            except Exception:
                pass
            try:
                context.close()
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Falha ao iniciar live listener: {e}", exc_info=True)


def start_live_listener() -> bool:
    """Inicia a thread de background que escuta atualizações ao vivo.

    Retorna True se a thread foi criada com sucesso.
    """
    try:
        t = threading.Thread(target=_listener_loop, daemon=True, name="bolao-live-listener")
        t.start()
        logger.info("Thread do live listener iniciada.")
        return True
    except Exception as e:
        logger.error(f"Não foi possível iniciar a thread do live listener: {e}")
        return False
