"""
Populador de Cache — Filmes do Mês
Busca todos os 12 meses x todos os anos e salva em cache.json.

Rodar uma vez só:
    uv run populate.py

Forçar atualização de anos recentes:
    uv run populate.py --force-recent
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
import os

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
FILMES_POR_ANO = int(os.getenv("FILMES_POR_ANO", 20))
TMDB_BASE = "https://api.themoviedb.org/3/discover/movie"
CACHE_FILE= Path("cache.json")
ANO_ATUAL = datetime.now().year
ANO_INICIAL = 1960
#

MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def carregar_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def salvar_cache(cache: dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def deve_buscar(cache: dict, mes: int, ano: int, force_recent: bool) -> bool:
    chave = f"{mes}-{ano}"
    if chave not in cache:
        return True

    # Re-busca se a entrada existe mas está vazia (aka busca anterior falhou)
    if not cache[chave].get("filmes"):
        return True

    agora = datetime.now().timestamp()
    timestamp = cache[chave].get("timestamp", 0)
    idade_dias = (agora - timestamp) / 86400

    if ano < ANO_ATUAL - 3:
        return False  # permanente
    elif ano < ANO_ATUAL:
        return idade_dias > 7 or force_recent  # semanal
    else:
        return idade_dias > 1  # diário


def buscar_filmes(ano: int, mes: int) -> list:
    mes_str = f"{mes:02d}"
    prefixo = f"{ano}-{mes_str}"
    encontrados = []
    pagina = 1

    while len(encontrados) < FILMES_POR_ANO:
        params = urlencode(
            {
                "api_key": TMDB_API_KEY,
                "language": "pt-BR",
                "sort_by": "vote_average.desc",
                "vote_count.gte": 10,
                "vote_average.gte": 5.5,
                "primary_release_year": ano,
                "page": pagina,
            }
        )
        try:
            with urlopen(f"{TMDB_BASE}?{params}", timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  ❌ Erro {ano}/{mes_str} página {pagina}: {e}")
            break

        results = data.get("results", [])
        total_pages = data.get("total_pages", 1)

        for f in results:
            release_date = f.get("release_date", "")
            if release_date.startswith(prefixo):
                encontrados.append(
                    {
                        "id": f.get("id"),
                        "titulo": f.get("title", "N/A"),
                        "nota": round(f.get("vote_average", 0), 1),
                        "poster": f"https://image.tmdb.org/t/p/w300{f['poster_path']}"
                        if f.get("poster_path")
                        else None,
                        "resumo": f.get("overview", ""),
                        "data_lancamento": release_date,
                        "link": f"https://www.themoviedb.org/movie/{f.get('id')}",
                    }
                )

        if pagina >= total_pages or pagina >= FILMES_POR_ANO:
            break
        pagina += 1
        time.sleep(0.1)  # respeita rate limit

    encontrados.sort(key=lambda x: x["nota"], reverse=True)
    return encontrados[:FILMES_POR_ANO]


def validar_key() -> bool:
    """Faz uma requisição simples pra confirmar que a API key é válida."""
    if not TMDB_API_KEY:
        print("TMDB_API_KEY não encontrada no .env")
        return False
    try:
        params = urlencode({"api_key": TMDB_API_KEY})
        with urlopen(
            f"https://api.themoviedb.org/3/authentication?{params}", timeout=10
        ) as resp:
            data = json.loads(resp.read())
            if data.get("success"):
                print("API key válida!")
                return True
            else:
                print(
                    f"API key inválida: {data.get('status_message', 'erro desconhecido')}"
                )
                return False
    except Exception as e:
        print(f"Erro ao validar API key: {e}")
        return False


def popular(force_recent: bool = False):
    if not validar_key():
        print("Obtenha sua chave em: https://www.themoviedb.org/settings/api")
        sys.exit(1)

    cache = carregar_cache()
    anos = list(range(ANO_ATUAL, ANO_INICIAL - 1, -1))
    meses = list(range(1, 13))

    # Monta lista de tarefas pendentes
    tarefas = [
        (mes, ano)
        for mes in meses
        for ano in anos
        if deve_buscar(cache, mes, ano, force_recent)
    ]

    total = len(tarefas)
    if total == 0:
        print("Cache já está completo e atualizado!")
        return

    print(f"{total} combinações para buscar ({len(anos)} anos × {len(meses)} meses)")
    print(f"Estimativa: ~{total // 10} segundos\n")

    concluidos = 0
    erros = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(buscar_filmes, ano, mes): (mes, ano) for mes, ano in tarefas
        }

        for future in as_completed(futures):
            mes, ano = futures[future]
            chave = f"{mes}-{ano}"
            try:
                filmes = future.result()
                cache[chave] = {
                    "filmes": filmes,
                    "timestamp": datetime.now().timestamp(),
                }
                concluidos += 1
                status = f" {MESES_PT[mes]}/{ano} — {len(filmes)} filmes"
            except Exception as e:
                erros += 1
                status = f" {MESES_PT[mes]}/{ano} — erro: {e}"

            print(f"[{concluidos + erros}/{total}] {status}")

            # Salva a cada 20 buscas pra não perder progresso
            if (concluidos + erros) % 20 == 0:
                salvar_cache(cache)

    salvar_cache(cache)
    print(f"\nConcluído! {concluidos} salvos, {erros} erros.")
    print(f"Cache salvo em {CACHE_FILE.resolve()}")


if __name__ == "__main__":
    force_recent = "--force-recent" in sys.argv
    if force_recent:
        print("Modo force-recent: atualizando últimos 3 anos...\n")
    popular(force_recent)
