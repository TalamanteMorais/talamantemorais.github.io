from __future__ import annotations

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
ARQUIVO_SAIDA = Path("links-publicacoes.json")

FONTE_AUTOMATICA_ATIVA = "stj"
LIMITE_AUTOMATICO = 5

FONTES_AUTOMATICAS = {
    "sicaf": {
        "feeds": [
            {
                "url": "https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/manual-fase-externa/manual-sicaf/RSS",
                "title_fixo": None,
            },
        ],
        "fixos": [
            {
                "title": "IN nº 3/2018 - SICAF Normativo",
                "url": "https://www.gov.br/compras/pt-br/acesso-a-informacao/perguntas-frequentes/sicaf-normativo",
            }
        ],
    },
    "stj": {
        "feeds": [
            {
                "url": "https://res.stj.jus.br/hrestp-c-portalp/RSS.xml",
                "title_fixo": None,
            },
        ],
        "fixos": [],
    },
}


MANUAL_LINKS = [
    {
        "title": "Justiça do Trabalho decreta suspensão de precatórios dos Correios por 90 dias",
        "url": "https://www.tst.jus.br/-/justica-do-trabalho-decreta-suspensao-de-precatorios-dos-correios-por-90-dias",
    },
    {
        "title": "Avaliação do nível de implementação da Lei 14.133/21 pelos Órgãos e Entidades Públicas",
        "url": "https://sites.tcu.gov.br/nova-lei-de-licitacoes-e-contratos/#encontrou",
    },
    {
        "title": "Contratação de Serviços Técnicos Especializados de Natureza Predominantemente Intelectual",
        "url": "https://www.tcm.ba.gov.br/wp-content/uploads/2023/08/elaboracao-pilulas-art-74-inciso-iii-lei-14-133-2021.pdf",
    },
    {
        "title": "Fim da relativização de estupro de crianças e demais vulneráveis vai a sanção - Fonte: Agência Senado",
        "url": "https://www12.senado.leg.br/noticias/materias/2026/02/25/fim-da-relativizacao-de-estupro-de-criancas-e-demais-vulneraveis-vai-a-sancao",
    },
    {
        "title": "16º Encontro Regional/TCM-GO - Orientações para Gestão Municipal",
        "url": "https://www.tcmgo.tc.br/site/2026/02/encontros-regionais-2026-do-tcmgo-oferecem-agenda-estrategica-para-fortalecer-a-governanca-e-a-gestao-publica/",
    },
    {
        "title": "Prefeitos protestam em Brasília contra aumento de despesas municipais - Agência Câmara de Notícias",
        "url": "https://www.camara.leg.br/noticias/1247114-prefeitos-protestam-em-brasilia-contra-aumento-de-despesas-municipais/",
    },
    {
        "title": "STJ Afasta a aplicabilidade de retroatividade no Direito Administrativo Sancionador na Lei 14.133 de 2021",
        "url": "https://processo.stj.jus.br/processo/julgamento/eletronico/documento/mediado/?documento_tipo=5&documento_sequencial=358100040&registro_numero=202402450422&publicacao_data=20260226&formato=PDF",
    },
]

TITLE_MAP = {
    "MODELO DE SOLICITACAO DE ALTERACAO DO RESPONSAVEL NO SICAF GOVERNO.docx": "Modelo de Alteração do Responsável no SICAF",
    "Manual-Normativo SICAF.pdf": "Manual Normativo SICAF",
    "Manual_do_Sicaf__versao_final_sistema_Fornecedor-1.5.pdf": "Manual do SICAF - Fornecedor",
    "Manual do Sicaf para Empresas Estrangeiras.pdf": "Manual do SICAF - Empresas Estrangeiras",
    "Manual_SICAF_Espanhol_.pdf": "Manual do SICAF - Espanhol",
    "SICAF Operational Manual.pdf": "Manual do SICAF - Inglês",
}

TITLES_EXCLUIDOS = {
    "Manual do SICAF - Espanhol",
    "Manual do SICAF - Inglês",
}

NS = {
    "rss": "http://purl.org/rss/1.0/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def fetch_xml(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def shorten_title(title: str) -> str:
    clean = compact_spaces(title)
    return TITLE_MAP.get(clean, clean)

def load_rss_items(url: str, limite: int, title_fixo: str | None = None) -> list[dict[str, str]]:
    xml_content = fetch_xml(url)
    root = ET.fromstring(xml_content)
    items: list[dict[str, str]] = []

    for item in root.findall("rss:item", NS):
        title_text = item.findtext("rss:title", default="", namespaces=NS)
        link_text = item.findtext("rss:link", default="", namespaces=NS)
        date_text = item.findtext("dc:date", default="", namespaces=NS)

        if not link_text:
            continue

        short_title = title_fixo or shorten_title(title_text)

        if short_title in TITLES_EXCLUIDOS:
            continue

        items.append(
            {
                "title": short_title.strip(),
                "url": link_text.strip(),
                "date": date_text.strip(),
            }
        )

    items.sort(key=lambda x: x.get("date", ""), reverse=True)

    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for item in items:
        url_item = item["url"]
        if url_item in seen:
            continue
        seen.add(url_item)
        result.append({"title": item["title"], "url": url_item})
        if len(result) >= limite:
            break

    return result


def merge_links(auto_links: list[dict[str, str]], manual_links: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[str] = set()

    for item in auto_links + manual_links:
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        if not title or not url or url in seen:
            continue
        seen.add(url)
        merged.append({"title": title, "url": url})

    return merged


def save_json(data: list[dict[str, str]], output_file: Path) -> None:
    output_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
def build_auto_links() -> list[dict[str, str]]:
    config = FONTES_AUTOMATICAS[FONTE_AUTOMATICA_ATIVA]

    auto_links: list[dict[str, str]] = []

    for feed in config.get("feeds", []):
        auto_links.extend(
            load_rss_items(
                feed["url"],
                LIMITE_AUTOMATICO,
                feed.get("title_fixo"),
            )
        )

    auto_links = merge_links(auto_links, config.get("fixos", []))
    return auto_links
def main() -> None:
    auto_links = build_auto_links()
    final_links = merge_links(auto_links, MANUAL_LINKS)
    save_json(final_links, ARQUIVO_SAIDA)
    print(
        f"Arquivo atualizado com {len(final_links)} links: {ARQUIVO_SAIDA} "
        f"(fonte automática: {FONTE_AUTOMATICA_ATIVA})"
    )


if __name__ == "__main__":
    main()
