import json
from pathlib import Path

ARQUIVO_SAIDA = Path("links-publicacoes.json")


def load_links() -> list[dict[str, str]]:
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

        links.append(
            {
                "title": title,
                "url": url,
            }
        )

    return links


def save_links(data: list[dict[str, str]]) -> None:
    ARQUIVO_SAIDA.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    links = load_links()
    save_links(links)
    print(f"Arquivo validado com {len(links)} links: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()