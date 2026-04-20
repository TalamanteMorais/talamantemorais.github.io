import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

ARQUIVO_SAIDA = Path("links-publicacoes.json")

LIMITE_TCU = 5
LIMITE_TCESP = 5

URL_TCU = "https://portal.tcu.gov.br/jurisprudencia?tipo=Informativo+de+Licita%C3%A7%C3%B5es+e+Contratos"
URL_TCESP_PAGINAS = [
    "https://www.tce.sp.gov.br/noticias",
    "https://www.tce.sp.gov.br/noticias?page=1",
    "https://www.tce.sp.gov.br/noticias?page=2",
    "https://www.tce.sp.gov.br/noticias?page=3",
]

PREFIXOS_AUTOMATICOS = (
    "TCU - ",
    "TCE-SP - ",
)


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def compact_spaces(text: str) -> str:
    text = re.sub(r"<.*?>", " ", text, flags=re.DOTALL)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_existing_links() -> list[dict[str, str]]:
    if not ARQUIVO_SAIDA.exists():
        return []

    try:
        data = json.loads(ARQUIVO_SAIDA.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    links: list[dict[str, str]] = []

    for item in data:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()

        if not title or not url:
            continue

        links.append({"title": title, "url": url})

    return links


def split_manual_links(links: list[dict[str, str]]) -> list[dict[str, str]]:
    manual_links: list[dict[str, str]] = []

    for item in links:
        title = item["title"]
        if title.startswith(PREFIXOS_AUTOMATICOS):
            continue
        manual_links.append(item)

    return manual_links


def unique_links(items: list[dict[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for item in items:
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()

        if not title or not url or url in seen_urls:
            continue

        seen_urls.add(url)
        result.append({"title": title, "url": url})

    return result


def extract_tcu_links(html: str, limite: int) -> list[dict[str, str]]:
    pattern = re.compile(
        r"Informativo de Licitações e Contratos\s+(\d+).*?href=\"([^\"]+)\"[^>]*>\s*PDF",
        re.IGNORECASE | re.DOTALL,
    )

    links: list[dict[str, str]] = []

    for numero, href in pattern.findall(html):
        url = urljoin(URL_TCU, href)
        links.append(
            {
                "title": f"TCU - Informativo de Licitações e Contratos {numero}",
                "url": url,
            }
        )
        if len(links) >= limite:
            break

    return unique_links(links)


def extract_tcesp_links(html: str, base_url: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"<a[^>]+href=\"([^\"]*boletim-atualizacao-licitacoes-e-contratos[^\"]*)\"[^>]*>(.*?)</a>",
        re.IGNORECASE | re.DOTALL,
    )

    links: list[dict[str, str]] = []

    for href, raw_title in pattern.findall(html):
        title = compact_spaces(raw_title)
        if "Boletim de Atualização de Licitações e Contratos" not in title:
            continue

        url = urljoin(base_url, href)
        links.append(
            {
                "title": f"TCE-SP - {title}",
                "url": url,
            }
        )

    return unique_links(links)


def collect_tcu() -> list[dict[str, str]]:
    html = fetch_text(URL_TCU)
    return extract_tcu_links(html, LIMITE_TCU)


def collect_tcesp() -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []

    for page_url in URL_TCESP_PAGINAS:
        html = fetch_text(page_url)
        collected.extend(extract_tcesp_links(html, page_url))
        collected = unique_links(collected)

        if len(collected) >= LIMITE_TCESP:
            break

    return collected[:LIMITE_TCESP]


def save_links(data: list[dict[str, str]]) -> None:
    ARQUIVO_SAIDA.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    existing_links = load_existing_links()
    manual_links = split_manual_links(existing_links)

    auto_links: list[dict[str, str]] = []

    try:
        auto_links.extend(collect_tcu())
    except Exception as exc:
        print(f"Falha TCU: {exc}")

    try:
        auto_links.extend(collect_tcesp())
    except Exception as exc:
        print(f"Falha TCE-SP: {exc}")

    final_links = unique_links(auto_links + manual_links)
    save_links(final_links)

    print(
        f"Arquivo atualizado com {len(final_links)} links: {ARQUIVO_SAIDA}"
    )


if __name__ == "__main__":
    main()