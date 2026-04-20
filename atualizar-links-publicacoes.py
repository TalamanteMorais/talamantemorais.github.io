import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ARQUIVO_SAIDA = Path("links-publicacoes.json")
ARQUIVO_MANUAIS = Path("links-publicacoes-manuais.json")
USER_AGENT = "Mozilla/5.0 (compatible; Projeto-Site-60/1.0; +https://talamante-adv.com.br)"
TIMEOUT = 25
DIAS_PERMANENCIA = 7
LIMITE_JSON = 30

TCE_SP_LISTAGENS = [
    "https://www.tce.sp.gov.br/publicacoes",
]

TCU_LISTAGENS_NOTICIAS = [
    "https://portal.tcu.gov.br/imprensa/noticias",
]

PALAVRAS_CHAVE = (
    "14.133",
    "licita",
    "contrata",
    "contrato",
    "pregão",
    "edital",
    "dispensa",
    "inexig",
    "registro de preços",
    "srp",
    "ata",
    "compra pública",
)


@dataclass
class LinkItem:
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
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%d/%m/%y",
    )

    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).replace(tzinfo=timezone.utc)
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
        "title": item.title,
        "url": item.url,
        "published_at": item.published_at,
    }


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

        title = str(raw.get("title", "")).strip()
        url = str(raw.get("url", "")).strip()
        published_at = str(raw.get("published_at", "")).strip() or hoje_iso()

        if not title or not url:
            continue

        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            continue

        if parse_data(published_at) is None:
            published_at = hoje_iso()

        itens.append(
            LinkItem(
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

    filtrados.sort(
        key=lambda item: parse_data(item.published_at) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return filtrados[:LIMITE_JSON]


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

            if not relevante(texto_link):
                continue

            try:
                detalhe = fetch_text(url)
            except Exception:
                continue

            titulo = extrair_h1(detalhe) or extrair_title_tag(detalhe) or texto_link
            descricao = extrair_descricao(detalhe)
            data_publicacao = extrair_data_tce(detalhe)

            texto_analise = f"{titulo} {descricao}"

            if not relevante(texto_analise):
                continue

            if not dentro_da_janela(data_publicacao):
                continue

            titulo_final = normalizar_titulo("TCE-SP", titulo)
            if not titulo_final:
                continue

            resultados.append(
                LinkItem(
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

            match_data = re.match(r"^\s*(\d{2}/\d{2}/\d{4})\s+(.*)$", texto_link, flags=re.DOTALL)
            if not match_data:
                continue

            data_publicacao = parse_data(match_data.group(1))
            conteudo = re.sub(r"\s+", " ", match_data.group(2)).strip()

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
                    title=titulo_final,
                    url=url,
                    published_at=data_publicacao.date().isoformat(),
                )
            )

    return resultados


def main() -> None:
    manuais = carregar_manuais()
    tce_sp = coletar_tce_sp()
    tcu_noticias = coletar_tcu_noticias()

    consolidados = normalizar_lista(
        [
            *manuais,
            *tce_sp,
            *tcu_noticias,
        ]
    )

    salvar_links(consolidados)

    print(f"Atualização concluída com {len(consolidados)} links em {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()