import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ARQUIVO_SAIDA = Path("links-publicacoes.json")
ARQUIVO_MANUAIS = Path("links-publicacoes-manuais.json")
USER_AGENT = "Mozilla/5.0 (compatible; Projeto-Site-60/1.0; +https://talamante-adv.com.br)"
TIMEOUT = 25
DIAS_PERMANENCIA = 7
LIMITE_AUTOMATICO_POR_ORGAO = {
    "TCU": 10,
    "STJ": 10,
    "TCE-SP": 10,
    "PNCP": 30,
}
TCE_SP_LISTAGENS = [
    "https://www.tce.sp.gov.br/publicacoes",
]
TCU_LISTAGENS_NOTICIAS = [
    "https://portal.tcu.gov.br/imprensa/noticias",
]
STJ_RSS_JURISPRUDENCIA = "https://res.stj.jus.br/hrestp-c-portalp/RSS.xml"
PNCP_BASE_URL = "https://pncp.gov.br/api/consulta"
PNCP_MODALIDADES = (4, 6, 8, 9, 12)


PALAVRAS_CHAVE = (

    "14.133",
    "licita",
    "contrato",
    "pregão",
    "edital",
    "dispensa",
    "inexig",
    "registro de preços",
    "srp",
    "ata",
    "proposta",
    "credencia",
    "concorrencia",
    "compra pública",
    "acórdão",
    "acordao",
)
@dataclass
class LinkItem:
    source: str
    title: str
    url: str
    published_at: str


def agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def hoje_iso() -> str:
    return agora_utc().date().isoformat()

def fetch_text(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urlopen(req, timeout=TIMEOUT) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def fetch_json(url: str) -> dict | list:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urlopen(req, timeout=TIMEOUT) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset, errors="replace"))


def limpar_texto(texto: str) -> str:
    texto = re.sub(r"<script\b.*?</script>", " ", texto, flags=re.IGNORECASE | re.DOTALL)
    texto = re.sub(r"<style\b.*?</style>", " ", texto, flags=re.IGNORECASE | re.DOTALL)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = unescape(texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def extrair_title_tag(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return limpar_texto(match.group(1))
    return ""


def extrair_h1(html: str) -> str:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return limpar_texto(match.group(1))
    return ""


def extrair_descricao(html: str) -> str:
    meta_patterns = [
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
    ]
    for pattern in meta_patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return limpar_texto(match.group(1))
    return ""


def normalizar_titulo(prefixo: str, titulo: str) -> str:
    titulo = re.sub(r"\s+", " ", titulo).strip(" -–—")
    if not titulo:
        return ""
    if titulo.lower().startswith(prefixo.lower() + " - "):
        return titulo
    return f"{prefixo} - {titulo}"

def parse_data(texto: str) -> datetime | None:
    texto = str(texto).strip()

    formatos = (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d/%m/%y",
    )

    for fmt in formatos:
        try:
            data = datetime.strptime(texto, fmt)
            if data.tzinfo is None:
                return data.replace(tzinfo=timezone.utc)
            return data.astimezone(timezone.utc)
        except ValueError:
            continue

    return None


def parse_data_stj_rss(texto: str) -> datetime | None:
    texto = str(texto).strip()

    mapa_semana = {
        "seg": "Mon",
        "ter": "Tue",
        "qua": "Wed",
        "qui": "Thu",
        "sex": "Fri",
        "sáb": "Sat",
        "sab": "Sat",
        "dom": "Sun",
    }

    mapa_mes = {
        "jan": "Jan",
        "fev": "Feb",
        "mar": "Mar",
        "abr": "Apr",
        "mai": "May",
        "jun": "Jun",
        "jul": "Jul",
        "ago": "Aug",
        "set": "Sep",
        "out": "Oct",
        "nov": "Nov",
        "dez": "Dec",
    }

    texto_normalizado = texto

    for pt, en in mapa_semana.items():
        texto_normalizado = re.sub(rf"\b{pt}\b", en, texto_normalizado, flags=re.IGNORECASE)

    for pt, en in mapa_mes.items():
        texto_normalizado = re.sub(rf"\b{pt}\b", en, texto_normalizado, flags=re.IGNORECASE)

    formatos = (
        "%a, %b %d %Y %H:%M:%S",
        "%a, %d %b %Y %H:%M:%S",
    )

    for fmt in formatos:
        try:
            return datetime.strptime(texto_normalizado, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def extrair_data_tce(html: str) -> datetime | None:
    texto = limpar_texto(html)

    patterns = [
        r"Data de Publicação:\s*(\d{2}/\d{2}/\d{4})",
        r"Data de Publicação\s*(\d{2}/\d{2}/\d{4})",
        r"Publicado em\s*(\d{2}/\d{2}/\d{4})",
        r"(\d{2}/\d{2}/\d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, texto, flags=re.IGNORECASE)
        if match:
            data = parse_data(match.group(1))
            if data:
                return data

    return None


def extrair_links_html(html: str, base_url: str) -> list[tuple[str, str]]:
    encontrados: list[tuple[str, str]] = []

    for href, inner in re.findall(
        r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        texto = limpar_texto(inner)
        if not texto:
            continue

        url = urljoin(base_url, unescape(href).strip())
        encontrados.append((texto, url))

    return encontrados


def mesmo_dominio(url: str, dominio: str) -> bool:
    try:
        return urlparse(url).netloc.endswith(dominio)
    except Exception:
        return False


def relevante(texto: str) -> bool:
    base = texto.lower()
    return any(palavra in base for palavra in PALAVRAS_CHAVE)


def dentro_da_janela(data_publicacao: datetime | None) -> bool:
    if data_publicacao is None:
        return False

    limite = agora_utc() - timedelta(days=DIAS_PERMANENCIA)
    return data_publicacao >= limite
def item_para_dict(item: LinkItem) -> dict[str, str]:
    return {
        "source": item.source,
        "title": item.title,
        "url": item.url,
        "published_at": item.published_at,
    }


def data_pncp_param(days_back: int = 7) -> tuple[str, str]:
    data_final = agora_utc().date()
    data_inicial = data_final - timedelta(days=days_back)
    return (
        data_inicial.strftime("%Y%m%d"),
        data_final.strftime("%Y%m%d"),
    )

def carregar_manuais() -> list[LinkItem]:
    if not ARQUIVO_MANUAIS.exists():
        return []

    try:
        data = json.loads(ARQUIVO_MANUAIS.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    itens: list[LinkItem] = []

    for raw in data:
        if not isinstance(raw, dict):
            continue

        source = str(raw.get("source", "")).strip().upper()
        title = str(raw.get("title", "")).strip()
        url = str(raw.get("url", "")).strip()
        published_at = str(raw.get("published_at", "")).strip() or hoje_iso()

        if not source or not title or not url:
            continue

        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            continue

        if parse_data(published_at) is None:
            published_at = hoje_iso()

        itens.append(
            LinkItem(
                source=source,
                title=title,
                url=url,
                published_at=published_at,
            )
        )

    return itens


def salvar_links(itens: list[LinkItem]) -> None:
    payload = [item_para_dict(item) for item in itens]
    ARQUIVO_SAIDA.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

def normalizar_lista(itens: Iterable[LinkItem]) -> list[LinkItem]:
    unicos: dict[str, LinkItem] = {}

    for item in itens:
        chave = item.url.strip().lower()
        if not chave:
            continue

        atual = unicos.get(chave)
        if atual is None:
            unicos[chave] = item
            continue

        data_item = parse_data(item.published_at) or datetime.min.replace(tzinfo=timezone.utc)
        data_atual = parse_data(atual.published_at) or datetime.min.replace(tzinfo=timezone.utc)

        if data_item >= data_atual:
            unicos[chave] = item

    filtrados = [
        item
        for item in unicos.values()
        if dentro_da_janela(parse_data(item.published_at))
    ]

    por_orgao: dict[str, list[LinkItem]] = {
        "TCU": [],
        "STJ": [],
        "TCE-SP": [],
        "PNCP": [],
    }

    for item in filtrados:
        if item.source in por_orgao:
            por_orgao[item.source].append(item)

    resultado: list[LinkItem] = []

    for orgao, itens_orgao in por_orgao.items():
        itens_orgao.sort(
            key=lambda item: parse_data(item.published_at) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        limite = LIMITE_AUTOMATICO_POR_ORGAO.get(orgao, 10)
        resultado.extend(itens_orgao[:limite])

    resultado.sort(
        key=lambda item: parse_data(item.published_at) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return resultado

def coletar_tce_sp() -> list[LinkItem]:
    resultados: list[LinkItem] = []

    for url_listagem in TCE_SP_LISTAGENS:
        try:
            html = fetch_text(url_listagem)
        except Exception:
            continue

        for texto_link, url in extrair_links_html(html, url_listagem):
            if not mesmo_dominio(url, "tce.sp.gov.br"):
                continue

            if "/publicacoes" not in url:
                continue

            try:
                detalhe = fetch_text(url)
            except Exception:
                continue

            titulo = extrair_h1(detalhe) or extrair_title_tag(detalhe) or texto_link
            descricao = extrair_descricao(detalhe)
            data_publicacao = extrair_data_tce(detalhe)

            texto_analise = f"{texto_link} {titulo} {descricao}"

            if not relevante(texto_analise):
                continue

            if not dentro_da_janela(data_publicacao):
                continue

            titulo_final = normalizar_titulo("TCE-SP", titulo)
            if not titulo_final:
                continue

            resultados.append(
                LinkItem(
                    source="TCE-SP",
                    title=titulo_final,
                    url=url,
                    published_at=data_publicacao.date().isoformat(),
                )
            )

    return resultados

def coletar_tcu_noticias() -> list[LinkItem]:
    resultados: list[LinkItem] = []

    for url_listagem in TCU_LISTAGENS_NOTICIAS:
        try:
            html = fetch_text(url_listagem)
        except Exception:
            continue

        for texto_link, url in extrair_links_html(html, url_listagem):
            if not mesmo_dominio(url, "portal.tcu.gov.br"):
                continue

            if "/imprensa/noticias/" not in url:
                continue

            texto_limpo = re.sub(r"\s+", " ", texto_link).strip()
            match_data = re.match(r"^\s*(\d{2}/\d{2}/\d{4})\s+(.*)$", texto_limpo, flags=re.DOTALL)

            if match_data:
                data_publicacao = parse_data(match_data.group(1))
                conteudo = re.sub(r"\s+", " ", match_data.group(2)).strip()
            else:
                data_publicacao = agora_utc()
                conteudo = texto_limpo

            if not conteudo:
                continue

            if not dentro_da_janela(data_publicacao):
                continue

            if not relevante(conteudo):
                continue

            titulo = conteudo.split(". ")[0].strip()
            titulo = titulo[:180].strip()

            if not titulo:
                continue

            titulo_final = normalizar_titulo("TCU", titulo)

            resultados.append(
                LinkItem(
                    source="TCU",
                    title=titulo_final,
                    url=url,
                    published_at=data_publicacao.date().isoformat(),
                )
            )

    return resultados
def coletar_stj_jurisprudencia() -> list[LinkItem]:
    resultados: list[LinkItem] = []
    ns = {"content": "https://purl.org/rss/1.0/modules/content/"}

    try:
        xml_text = fetch_text(STJ_RSS_JURISPRUDENCIA)
        root = ET.fromstring(xml_text)
    except Exception:
        return resultados

    for item in root.findall("./channel/item"):
        titulo = limpar_texto(item.findtext("title", default=""))
        url = limpar_texto(item.findtext("link", default=""))
        descricao = limpar_texto(item.findtext("description", default=""))
        pub_date_raw = limpar_texto(item.findtext("pubDate", default=""))
        conteudo_expandido = limpar_texto(item.findtext("content:encoded", default="", namespaces=ns))

        data_publicacao = parse_data_stj_rss(pub_date_raw)
        texto_analise = f"{titulo} {descricao} {conteudo_expandido}"

        if not titulo or not url:
            continue

        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            continue

        if not dentro_da_janela(data_publicacao):
            continue

        if not relevante(texto_analise):
            continue

        titulo_final = normalizar_titulo("STJ", titulo)
        if not titulo_final:
            continue

        resultados.append(
            LinkItem(
                source="STJ",
                title=titulo_final,
                url=url,
                published_at=data_publicacao.date().isoformat(),
            )
        )

    return resultados

def coletar_pncp_contratacoes() -> list[LinkItem]:
    resultados: list[LinkItem] = []
    data_inicial, data_final = data_pncp_param(DIAS_PERMANENCIA)

    for modalidade in PNCP_MODALIDADES:
        pagina = 1
        paginas_processadas = 0

        while paginas_processadas < 5:
            url = (
                f"{PNCP_BASE_URL}/v1/contratacoes/publicacao"
                f"?dataInicial={data_inicial}"
                f"&dataFinal={data_final}"
                f"&codigoModalidadeContratacao={modalidade}"
                f"&pagina={pagina}"
                f"&tamanhoPagina=50"
            )

            try:
                payload = fetch_json(url)
            except Exception:
                break

            if not isinstance(payload, dict):
                break

            registros = payload.get("data") or []
            if not isinstance(registros, list) or not registros:
                break

            for registro in registros:
                if not isinstance(registro, dict):
                    continue

                titulo_base = str(registro.get("objetoCompra", "")).strip()
                numero_controle = str(registro.get("numeroControlePNCP", "")).strip()
                link_sistema_origem = str(registro.get("linkSistemaOrigem", "")).strip()
                data_publicacao = str(registro.get("dataPublicacaoPncp", "")).strip()
                modalidade_nome = str(registro.get("modalidadeNome", "")).strip()
                info_complementar = str(registro.get("informacaoComplementar", "")).strip()

                amparo = registro.get("amparoLegal") or {}
                amparo_nome = str(amparo.get("nome", "")).strip() if isinstance(amparo, dict) else ""
                amparo_descricao = str(amparo.get("descricao", "")).strip() if isinstance(amparo, dict) else ""

                url_origem = link_sistema_origem
                if not url_origem and numero_controle:
                    url_origem = f"https://pncp.gov.br/app/editais/{numero_controle}"

                if not titulo_base or not url_origem or not data_publicacao:
                    continue

                if not re.match(r"^https?://", url_origem, flags=re.IGNORECASE):
                    continue

                if not dentro_da_janela(parse_data(data_publicacao)):
                    continue

                texto_analise = f"{titulo_base} {modalidade_nome} {info_complementar} {amparo_nome} {amparo_descricao}"
                if not relevante(texto_analise):
                    continue

                titulo_final = normalizar_titulo("PNCP", titulo_base[:180].strip())
                if not titulo_final:
                    continue

                resultados.append(
                    LinkItem(
                        source="PNCP",
                        title=titulo_final,
                        url=url_origem,
                        published_at=data_publicacao[:10],
                    )
                )

            total_paginas = int(payload.get("totalPaginas") or 0)
            pagina += 1
            paginas_processadas += 1

            if total_paginas and pagina > total_paginas:
                break

    return resultados

def main() -> None:
    manuais = carregar_manuais()
    tce_sp = coletar_tce_sp()
    tcu_noticias = coletar_tcu_noticias()
    stj_jurisprudencia = coletar_stj_jurisprudencia()
    pncp_contratacoes = coletar_pncp_contratacoes()

    print(f"Manuais: {len(manuais)}")
    print(f"TCE-SP: {len(tce_sp)}")
    print(f"TCU: {len(tcu_noticias)}")
    print(f"STJ: {len(stj_jurisprudencia)}")
    print(f"PNCP: {len(pncp_contratacoes)}")

    automaticos = normalizar_lista(
        [
            *tce_sp,
            *tcu_noticias,
            *stj_jurisprudencia,
            *pncp_contratacoes,
        ]
    )

    print(f"Automáticos após normalização: {len(automaticos)}")

    consolidados = [*manuais, *automaticos]

    print(f"Consolidados finais: {len(consolidados)}")

    salvar_links(consolidados)

    print(f"Atualização concluída com {len(consolidados)} links em {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
