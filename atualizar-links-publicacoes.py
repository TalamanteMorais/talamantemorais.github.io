from __future__ import annotations

import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

RSS_URL = "https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/manual-fase-externa/manual-sicaf/RSS"
LIMITE_SICAF = 5
ARQUIVO_SAIDA = Path("links-publicacoes.json")

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
    {
        "title": "IN nº 3/2018 - Perguntas_Respostas_SICAF_Compras_Gov",
        "url": "https://www.gov.br/compras/pt-br/acesso-a-informacao/perguntas-frequentes/sicaf-normativo",
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


def load_sicaf_items() -> list[dict[str, str]]:
    xml_content = fetch_xml(RSS_URL)
    root = ET.fromstring(xml_content)
    items: list[dict[str, str]] = []

    for item in root.findall("rss:item", NS):
        title_text = item.findtext("rss:title", default="", namespaces=NS)
        link_text = item.findtext("rss:link", default="", namespaces=NS)
        date_text = item.findtext("dc:date", default="", namespaces=NS)

        if not title_text or not link_text:
            continue

        items.append(
            {
                "title": shorten_title(title_text),
                "url": link_text.strip(),
                "date": date_text.strip(),
            }
        )

    items.sort(key=lambda x: x.get("date", ""), reverse=True)

    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for item in items:
        url = item["url"]
        if url in seen:
            continue
        seen.add(url)
        result.append({"title": item["title"], "url": url})
        if len(result) >= LIMITE_SICAF:
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


def main() -> None:
    auto_links = load_sicaf_items()
    final_links = merge_links(auto_links, MANUAL_LINKS)
    save_json(final_links, ARQUIVO_SAIDA)
    print(f"Arquivo atualizado com {len(final_links)} links: {ARQUIVO_SAIDA}")


if __name__ == "__main__":
    main()
