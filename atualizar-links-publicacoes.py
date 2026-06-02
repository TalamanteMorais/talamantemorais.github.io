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
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
TIMEOUT = 60
DIAS_PERMANENCIA = 30
DIAS_PERMANENCIA_TCM_BA = 30
DIAS_PERMANENCIA_TCM_GO = 30
DIAS_PERMANENCIA_PNCP = 30
MINIMO_AUTOMATICOS_PARA_SALVAR = 20

LIMITE_AUTOMATICO_POR_ORGAO = {

    "TCU": 10,
    "STJ": 10,
    "TCE-SP": 10,
    "TCE-MG": 10,
    "TCE-SC": 10,
    "TCE-PE": 10,
    "PNCP": 30,
    "TCM-BA": 10,
    "TCM-GO": 10,
}

TCE_SP_RSS_URLS = (
    "https://www.tce.sp.gov.br/feed",
    "https://www.tce.sp.gov.br/jurisprudencia/feed",
)
TCE_SP_NOTICIAS_URLS = (
    "https://www.tce.sp.gov.br/noticias",
    "https://www.tce.sp.gov.br/noticias?page=1",
    "https://www.tce.sp.gov.br/noticias?page=2",
)

TCE_MG_NOTICIAS_URLS = (
    "https://www.tce.mg.gov.br/Noticia/?cod_secao=1ISP&cod_secao_menu=5L&tipo=1&url=",
    "https://www.tce.mg.gov.br/index.asp?cod_secao=1ISP&cod_secao_menu=5L&tipo=1&url=",
)

TCE_MG_LINKS_INSTITUCIONAIS = (
    ("Informativo de Jurisprudência", "https://www.tce.mg.gov.br/Noticia/?cod_secao=1ISP&cod_secao_menu=5L&tipo=1&url="),
    ("Pesquisa de Jurisprudência TCJuris", "https://tcjuris.tce.mg.gov.br/"),
)

TCE_SC_PORTAL_URLS = (
    "https://www.tcesc.tc.br/content/jurisprudencia",
    "https://www.tcesc.tc.br/informativo-de-jurisprud%C3%AAncia",
)

TCE_SC_SERVICOS_URLS = (
    "https://servicos.tcesc.tc.br/jurisprudencia/",
    "https://epapyrus.tce.sc.gov.br/",
)

TCE_SC_LINKS_INSTITUCIONAIS = (
    ("Jurisprudência", "https://www.tcesc.tc.br/content/jurisprudencia"),
    ("Informativos de Jurisprudência", "https://www.tcesc.tc.br/informativo-de-jurisprud%C3%AAncia"),
    ("Jurisprudência selecionada - e-Papyrus", "https://epapyrus.tce.sc.gov.br/"),
)

TCE_PE_PORTAL_URLS = (
    "https://www.tcepe.tc.br/internet/index.php/inicio-jurisprudencia",
    "https://portal.tcepe.tc.br/jurisprudencia/consulta/deliberacoes",
)

TCE_PE_SISTEMAS_URLS = (
    "https://sistemas.tce.pe.gov.br/jurisprudencia/PesquisaJurisprudencia!home.action",
)

TCE_PE_LINKS_INSTITUCIONAIS = (
    ("Jurisprudência", "https://www.tcepe.tc.br/internet/index.php/inicio-jurisprudencia"),
    ("Deliberações", "https://portal.tcepe.tc.br/jurisprudencia/consulta/deliberacoes"),
    ("Pesquisa de Jurisprudência", "https://sistemas.tce.pe.gov.br/jurisprudencia/PesquisaJurisprudencia!home.action"),
)

TCU_ACORDAOS_API = "https://dados-abertos.apps.tcu.gov.br/api/acordao/recupera-acordaos"

TCU_ACORDAOS_QUANTIDADE = 80
STJ_RSS_JURISPRUDENCIA = "https://res.stj.jus.br/hrestp-c-portalp/RSS.xml"
PNCP_BASE_URL = "https://pncp.gov.br/api/consulta"
PNCP_MODALIDADES = (4, 6, 8, 9, 12)
TCM_GO_POSTS_API = "https://www.tcmgo.tc.br/site/wp-json/wp/v2/posts"
TCM_BA_NOTICIAS_URLS = (
    "https://www.tcm.ba.gov.br/informacoes/noticias/",
    "https://www.tcm.ba.gov.br/informacoes/noticias/page/2/",
    "https://www.tcm.ba.gov.br/informacoes/noticias/page/3/",
)
TCM_BA_RSS_URLS = (
    "https://www.tcm.ba.gov.br/feed/",
)
TCM_GO_TERMOS = (
    "jurisprudência",
    "acórdão",
    "acordao",
    "decisão",
    "decisao",
    "licitação",
    "contrato",
)
TCM_BA_TERMOS = (
    "jurisprudência",
    "acórdão",
    "acordao",
    "decisão",
    "decisao",
    "licitação",
    "licitacao",
    "contrato",
    "dispensa",
    "inexigibilidade",
    "representação",
    "representacao",
    "contas",
)
PALAVRAS_CHAVE = (
    "14.133",
    "licita",
    "contrato",
    "pregão",
    "edital",
    "dispensa",
    "inexig",
    "notória especialização",
    "predominantemente intelectua",
    "registro de preços",
    "srp",
    "ata",
    "proposta",
    "credencia",
    "concorrencia",
    "compra pública",
    "acórdão",
    "acordao",
    "jurisprud",
    "decisão",
    "decisao",
    "julgado",
    "informativo",
    "sessão",
    "contas",
    "tribunal",
    "município",
    "gestor",
    "prefeito",
    "câmara",
    "denúncia",
    "representação",
    "ressarcimento",
    "inexig",
    "multa",
)

TERMOS_PRIORIDADE_ALTA = (
    "14.133",
    "lei 14.133",
    "nova lei de licitações",
    "pregão eletrônico",
    "pregao eletronico",
    "concorrência",
    "concorrencia",
    "dispensa de licitação",
    "dispensa de licitacao",
    "inexigibilidade",
    "notória especialização",
    "notoria especializacao",
    "predominantemente intelectual",
    "predominantemente intelectua",
    "credenciamento",
    "acórdão",
    "jurisprudência",
    "jurisprudencia",
    "representação",
    "representacao",
    "denúncia",
    "denuncia",
    "irregularidade",
    "ilegalidade",
    "restrição à competitividade",
    "restricao a competitividade",
    "direcionamento",
    "sobrepreço",
    "sobrepreco",
    "superfaturamento",
    "conluio",
    "sanção",
    "sancao",
    "inidoneidade",
)

TERMOS_PRIORIDADE_MEDIA = (
    "licitação",
    "licitacao",
    "contrato administrativo",
    "contrato",
    "edital",
    "estudo técnico preliminar",
    "estudo tecnico preliminar",
    "etp",
    "termo de referência",
    "termo de referencia",
    "tr",
    "matriz de riscos",
    "risco",
    "ata de registro de preços",
    "ata de registro de precos",
    "registro de preços",
    "registro de precos",
    "srp",
    "agente público",
    "agente publico",
    "fornecedor",
    "gestor",
    "prefeito",
    "câmara",
    "camara",
    "município",
    "municipio",
    "multa",
    "ressarcimento",
)
TERMOS_BAIXA_RELEVANCIA = (
    "posse",
    "homenagem",
    "reunião",
    "reuniao",
    "evento",
    "curso",
    "palestra",
    "seminário",
    "seminario",
    "expediente",
    "feriado",
    "comunicado",
    "institucional",
    "aniversário",
    "aniversario",
    "sessão ao vivo",
    "sessao ao vivo",
    "sessões",
    "sessoes",
    "pauta",
    "agenda",
    "acessibilidade",
    "alto contraste",
    "altocontraste",
    "login",
    "sistema eletrônico",
    "sistema eletronico",
    "sistema de informações",
    "sistema de informacoes",
    "mapa das câmaras",
    "mapa das camaras",
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
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
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
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
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
        r"Publicação:\s*(\d{2}/\d{2}/\d{4})",
        r"Disponibilização:\s*(\d{2}/\d{2}/\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
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
def eh_url_publicacao_direta(url: str, dominio: str) -> bool:
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        return False

    if not mesmo_dominio(url, dominio):
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    caminho = (parsed.path or "/").lower().rstrip("/")
    consulta = (parsed.query or "").lower()
    fragmento = (parsed.fragment or "").lower()
    url_normalizada = url.lower()

    if fragmento:
        return False

    caminhos_listagem = {
        "",
        "/",
        "/noticias",
        "/noticias/busca",
        "/informacoes",
        "/informacoes/noticias",
        "/tcmba-post",
        "/aviso-post",
        "/parecer-post",
    }

    if caminho in caminhos_listagem:
        return False

    extensoes_bloqueadas = (
        ".xls",
        ".xlsx",
        ".doc",
        ".docx",
        ".ppt",
        ".pptx",
        ".zip",
        ".rar",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
    )

    if caminho.endswith(extensoes_bloqueadas):
        return False

    trechos_proibidos = (
        "/wp-content/",
        "/wp-admin/",
        "/tag/",
        "/category/",
        "/author/",
        "/feed/",
        "/page/",
        "/busca",
        "/pesquisa",
        "/consulta",
        "/consultas",
        "/processo",
        "/processos",
        "/jurisprudencia/pesquisa",
        "/jurisprudencia/busca",
        "/push/",
        "/sei/",
        "/sigmat/",
        "/agenda_gestor",
        "/municipioemergencia",
        "fornecedores_impedidos",
        "controlador_externo",
        "acessibilidade",
        "altocontraste",
        "javascript:",
        "mailto:",
    )

    if any(trecho in url_normalizada for trecho in trechos_proibidos):
        return False

    parametros_proibidos = (
        "search=",
        "q=",
        "s=",
        "page=",
        "processo=",
        "numero_processo=",
        "num_processo=",
        "nr_processo=",
        "jurisprudencia=",
    )

    if any(parametro in consulta for parametro in parametros_proibidos):
        return False

    return True

def coletar_html_oficial(
    source: str,
    urls_base: Iterable[str],
    dominio: str,
    janela_func,
    prefixo: str,
) -> list[LinkItem]:
    resultados: list[LinkItem] = []
    urls_processadas: set[str] = set()

    paginas_lidas = 0
    paginas_falhas = 0
    links_lidos = 0
    links_rejeitados = 0
    sem_data = 0
    fora_janela = 0
    sem_relevancia = 0

    for url_base in urls_base:
        try:
            html = fetch_text(url_base)
            paginas_lidas += 1
        except Exception as erro:
            paginas_falhas += 1
            print(f"{source} HTML falhou: {url_base} | {type(erro).__name__}: {erro}")
            continue

        for texto_link, link in extrair_links_html(html, url_base):
            links_lidos += 1

            if not eh_url_publicacao_direta(link, dominio):
                links_rejeitados += 1
                continue

            chave = link.strip().lower()
            if chave in urls_processadas:
                continue

            try:
                detalhe = fetch_text(link)
            except Exception:
                detalhe = ""

            titulo = extrair_h1(detalhe) or extrair_title_tag(detalhe) or texto_link
            descricao = extrair_descricao(detalhe)
            data_publicacao = extrair_data_tce(detalhe) or extrair_data_tce(f"{texto_link} {html}")

            if not titulo or data_publicacao is None:
                sem_data += 1
                continue

            if not janela_func(data_publicacao):
                fora_janela += 1
                continue

            texto_analise = f"{texto_link} {titulo} {descricao}"

            if not relevante(texto_analise):
                sem_relevancia += 1
                continue

            titulo_final = normalizar_titulo(prefixo, titulo[:180].strip())
            if not titulo_final:
                continue

            resultados.append(
                LinkItem(
                    source=source,
                    title=titulo_final,
                    url=link,
                    published_at=data_publicacao.date().isoformat(),
                )
            )
            urls_processadas.add(chave)

    print(
        f"{source} HTML diagnóstico: "
        f"paginas_lidas={paginas_lidas}, "
        f"paginas_falhas={paginas_falhas}, "
        f"links_lidos={links_lidos}, "
        f"links_rejeitados={links_rejeitados}, "
        f"sem_data={sem_data}, "
        f"fora_janela={fora_janela}, "
        f"sem_relevancia={sem_relevancia}, "
        f"aceitos={len(resultados)}"
    )

    return resultados


def normalizar_busca(texto: str) -> str:
    texto = str(texto).lower()
    substituicoes = str.maketrans(
        {
            "á": "a",
            "à": "a",
            "â": "a",
            "ã": "a",
            "ä": "a",
            "é": "e",
            "è": "e",
            "ê": "e",
            "ë": "e",
            "í": "i",
            "ì": "i",
            "î": "i",
            "ï": "i",
            "ó": "o",
            "ò": "o",
            "ô": "o",
            "õ": "o",
            "ö": "o",
            "ú": "u",
            "ù": "u",
            "û": "u",
            "ü": "u",
            "ç": "c",
        }
    )
    return texto.translate(substituicoes)
def relevante(texto: str) -> bool:
    return pontuar_texto(texto) >= 3

def pontuar_texto(texto: str) -> int:
    base = normalizar_busca(texto)
    pontuacao = 0

    for termo in TERMOS_PRIORIDADE_ALTA:
        if normalizar_busca(termo) in base:
            pontuacao += 8

    for termo in TERMOS_PRIORIDADE_MEDIA:
        if normalizar_busca(termo) in base:
            pontuacao += 3

    for termo in TERMOS_BAIXA_RELEVANCIA:
        if normalizar_busca(termo) in base:
            pontuacao -= 4

    if "14.133" in base and any(
        normalizar_busca(termo) in base
        for termo in (
            "pregão eletrônico",
            "pregao eletronico",
            "concorrência",
            "concorrencia",
            "dispensa",
            "inexigibilidade",
            "credenciamento",
            "edital",
            "etp",
            "termo de referência",
            "termo de referencia",
            "contrato",
        )
    ):
        pontuacao += 10

    if any(
        normalizar_busca(termo) in base
        for termo in (
            "acórdão",
            "acordao",
            "jurisprudência",
            "jurisprudencia",
            "representação",
            "representacao",
            "denúncia",
            "denuncia",
        )
    ) and any(
        normalizar_busca(termo) in base
        for termo in (
            "licitação",
            "licitacao",
            "contrato",
            "edital",
            "dispensa",
            "inexigibilidade",
            "credenciamento",
            "pregão",
            "pregao",
            "concorrência",
            "concorrencia",
        )
    ):
        pontuacao += 10

    return pontuacao

def pontuar_item(item: LinkItem) -> int:
    return pontuar_texto(f"{item.source} {item.title}")
def data_dentro_da_janela(data_publicacao: datetime | None, dias: int) -> bool:

    if data_publicacao is None:
        return False

    agora = agora_utc()
    limite_inferior = agora - timedelta(days=dias)
    limite_superior = agora + timedelta(days=1)

    return limite_inferior <= data_publicacao <= limite_superior


def dentro_da_janela(data_publicacao: datetime | None) -> bool:
    return data_dentro_da_janela(data_publicacao, DIAS_PERMANENCIA)


def dentro_da_janela_tcm_ba(data_publicacao: datetime | None) -> bool:
    return data_dentro_da_janela(data_publicacao, DIAS_PERMANENCIA_TCM_BA)


def dentro_da_janela_tcm_go(data_publicacao: datetime | None) -> bool:
    return data_dentro_da_janela(data_publicacao, DIAS_PERMANENCIA_TCM_GO)


def dentro_da_janela_pncp(data_publicacao: datetime | None) -> bool:
    return data_dentro_da_janela(data_publicacao, DIAS_PERMANENCIA_PNCP)


def dentro_da_janela_por_orgao(item: LinkItem) -> bool:
    data_publicacao = parse_data(item.published_at)

    if item.source == "PNCP":
        return dentro_da_janela_pncp(data_publicacao)

    if item.source == "TCM-BA":
        return dentro_da_janela_tcm_ba(data_publicacao)

    if item.source == "TCM-GO":
        return dentro_da_janela_tcm_go(data_publicacao)

    return dentro_da_janela(data_publicacao)

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

        if not title or not url:
            continue
        if not source:
            if title.upper().startswith("TCU"):
                source = "TCU"
            elif title.upper().startswith("STJ"):
                source = "STJ"
            elif title.upper().startswith("TCE-SP"):
                source = "TCE-SP"
            elif title.upper().startswith("TCE-MG"):
                source = "TCE-MG"
            elif title.upper().startswith("TCE-SC"):
                source = "TCE-SC"
            elif title.upper().startswith("TCE-PE"):
                source = "TCE-PE"
            elif title.upper().startswith("PNCP"):
                source = "PNCP"
            elif title.upper().startswith("TCM-BA"):
                source = "TCM-BA"
            elif title.upper().startswith("TCM-GO"):
                source = "TCM-GO"
            else:
                source = "Manual"

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

    itens.sort(
        key=lambda item: parse_data(item.published_at) or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return itens

def salvar_links(itens: list[LinkItem]) -> None:
    payload = [item_para_dict(item) for item in itens]
    ARQUIVO_SAIDA.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def carregar_saida_atual() -> list[LinkItem]:
    if not ARQUIVO_SAIDA.exists():
        return []

    try:
        data = json.loads(ARQUIVO_SAIDA.read_text(encoding="utf-8"))
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
        published_at = str(raw.get("published_at", "")).strip()

        if not source or not title or not url or not published_at:
            continue

        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            continue

        if parse_data(published_at) is None:
            continue

        itens.append(
            LinkItem(
                source=source,
                title=title,
                url=url,
                published_at=published_at,
            )
        )

    return itens


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
        if dentro_da_janela_por_orgao(item)
    ]
    por_orgao: dict[str, list[LinkItem]] = {
        "TCU": [],
        "STJ": [],
        "TCE-SP": [],
        "TCE-MG": [],
        "TCE-SC": [],
        "TCE-PE": [],
        "PNCP": [],
        "TCM-BA": [],
        "TCM-GO": [],
    }    

    for item in filtrados:
        if item.source in por_orgao:
            por_orgao[item.source].append(item)
    resultado: list[LinkItem] = []

    for orgao in ("TCU", "STJ", "TCE-SP", "TCE-MG", "TCE-SC", "TCE-PE", "PNCP", "TCM-BA", "TCM-GO"):

        itens_orgao = por_orgao[orgao]
        itens_orgao.sort(
            key=lambda item: (
                pontuar_item(item),
                parse_data(item.published_at) or datetime.min.replace(tzinfo=timezone.utc),
            ),
            reverse=True,
        )
        limite = LIMITE_AUTOMATICO_POR_ORGAO.get(orgao, 10)
        resultado.extend(itens_orgao[:limite])

    return resultado

def coletar_tce_sp() -> list[LinkItem]:
    resultados: list[LinkItem] = []
    urls_processadas: set[str] = set()
    rss_lidos = 0
    rss_falhas = 0
    itens_lidos = 0
    links_rejeitados = 0
    sem_data = 0
    fora_janela = 0
    sem_relevancia = 0

    for rss_url in TCE_SP_RSS_URLS:
        try:
            xml_text = fetch_text(rss_url)
            root = ET.fromstring(xml_text)
            rss_lidos += 1
        except Exception as erro:
            rss_falhas += 1
            print(f"TCE-SP RSS falhou: {rss_url} | {type(erro).__name__}: {erro}")
            continue

        for item in root.findall("./channel/item"):
            itens_lidos += 1
            titulo = limpar_texto(item.findtext("title", default=""))
            link = limpar_texto(item.findtext("link", default=""))
            descricao = limpar_texto(item.findtext("description", default=""))
            pub_date_raw = limpar_texto(item.findtext("pubDate", default=""))

            if not titulo or not link:
                continue

            if not eh_url_publicacao_direta(link, "tce.sp.gov.br"):
                links_rejeitados += 1
                continue

            chave = link.strip().lower()
            if chave in urls_processadas:
                continue

            data_publicacao = parse_data_stj_rss(pub_date_raw) or parse_data(pub_date_raw)
            if data_publicacao is None:
                sem_data += 1
                continue

            if not dentro_da_janela(data_publicacao):
                fora_janela += 1
                continue

            texto_analise = f"{titulo} {descricao}"
            if not relevante(texto_analise):
                sem_relevancia += 1
                continue

            titulo_final = normalizar_titulo("TCE-SP", titulo[:180].strip())
            if not titulo_final:
                continue

            resultados.append(
                LinkItem(
                    source="TCE-SP",
                    title=titulo_final,
                    url=link,
                    published_at=data_publicacao.date().isoformat(),
                )
            )
            urls_processadas.add(chave)

    print(
        f"TCE-SP RSS diagnóstico: "
        f"rss_lidos={rss_lidos}, "
        f"rss_falhas={rss_falhas}, "
        f"itens_lidos={itens_lidos}, "
        f"links_rejeitados={links_rejeitados}, "
        f"sem_data={sem_data}, "
        f"fora_janela={fora_janela}, "
        f"sem_relevancia={sem_relevancia}, "
        f"aceitos={len(resultados)}"
    )

    html_resultados = coletar_html_oficial(
        source="TCE-SP",
        urls_base=TCE_SP_NOTICIAS_URLS,
        dominio="tce.sp.gov.br",
        janela_func=dentro_da_janela,
        prefixo="TCE-SP",
    )

    for item in html_resultados:
        chave = item.url.strip().lower()
        if chave in urls_processadas:
            continue

        resultados.append(item)
        urls_processadas.add(chave)

    print(f"TCE-SP total após RSS + HTML direto: {len(resultados)}")
    return resultados
def links_institucionais_publicacoes(
    source: str,
    entradas: Iterable[tuple[str, str]],
) -> list[LinkItem]:
    resultados: list[LinkItem] = []
    data_publicacao = hoje_iso()

    for titulo, url in entradas:
        titulo = str(titulo).strip()
        url = str(url).strip()

        if not titulo or not re.match(r"^https?://", url, flags=re.IGNORECASE):
            continue

        resultados.append(
            LinkItem(
                source=source,
                title=normalizar_titulo(source, titulo),
                url=url,
                published_at=data_publicacao,
            )
        )

    return resultados


def coletar_tce_mg() -> list[LinkItem]:
    resultados = coletar_html_oficial(
        source="TCE-MG",
        urls_base=TCE_MG_NOTICIAS_URLS,
        dominio="tce.mg.gov.br",
        janela_func=dentro_da_janela,
        prefixo="TCE-MG",
    )

    if resultados:
        return resultados

    print("TCE-MG sem itens dinâmicos aceitos. Mantidos links institucionais de referência.")
    return links_institucionais_publicacoes("TCE-MG", TCE_MG_LINKS_INSTITUCIONAIS)


def coletar_tce_sc() -> list[LinkItem]:
    resultados: list[LinkItem] = []
    urls_processadas: set[str] = set()

    for item in coletar_html_oficial(
        source="TCE-SC",
        urls_base=TCE_SC_PORTAL_URLS,
        dominio="tcesc.tc.br",
        janela_func=dentro_da_janela,
        prefixo="TCE-SC",
    ):
        chave = item.url.strip().lower()
        if chave in urls_processadas:
            continue
        resultados.append(item)
        urls_processadas.add(chave)

    for item in coletar_html_oficial(
        source="TCE-SC",
        urls_base=("https://servicos.tcesc.tc.br/jurisprudencia/",),
        dominio="tcesc.tc.br",
        janela_func=dentro_da_janela,
        prefixo="TCE-SC",
    ):
        chave = item.url.strip().lower()
        if chave in urls_processadas:
            continue
        resultados.append(item)
        urls_processadas.add(chave)

    for item in coletar_html_oficial(
        source="TCE-SC",
        urls_base=("https://epapyrus.tce.sc.gov.br/",),
        dominio="tce.sc.gov.br",
        janela_func=dentro_da_janela,
        prefixo="TCE-SC",
    ):
        chave = item.url.strip().lower()
        if chave in urls_processadas:
            continue
        resultados.append(item)
        urls_processadas.add(chave)

    if resultados:
        return resultados

    print("TCE-SC sem itens dinâmicos aceitos. Mantidos links institucionais de referência.")
    return links_institucionais_publicacoes("TCE-SC", TCE_SC_LINKS_INSTITUCIONAIS)


def coletar_tce_pe() -> list[LinkItem]:
    resultados: list[LinkItem] = []
    urls_processadas: set[str] = set()

    for item in coletar_html_oficial(
        source="TCE-PE",
        urls_base=TCE_PE_PORTAL_URLS,
        dominio="tcepe.tc.br",
        janela_func=dentro_da_janela,
        prefixo="TCE-PE",
    ):
        chave = item.url.strip().lower()
        if chave in urls_processadas:
            continue
        resultados.append(item)
        urls_processadas.add(chave)

    for item in coletar_html_oficial(
        source="TCE-PE",
        urls_base=TCE_PE_SISTEMAS_URLS,
        dominio="tce.pe.gov.br",
        janela_func=dentro_da_janela,
        prefixo="TCE-PE",
    ):
        chave = item.url.strip().lower()
        if chave in urls_processadas:
            continue
        resultados.append(item)
        urls_processadas.add(chave)

    if resultados:
        return resultados

    print("TCE-PE sem itens dinâmicos aceitos. Mantidos links institucionais de referência.")
    return links_institucionais_publicacoes("TCE-PE", TCE_PE_LINKS_INSTITUCIONAIS)

def coletar_tcu_acordaos() -> list[LinkItem]:

    resultados: list[LinkItem] = []

    url = f"{TCU_ACORDAOS_API}?inicio=0&quantidade={TCU_ACORDAOS_QUANTIDADE}"

    try:
        payload = fetch_json(url)
    except Exception:
        return resultados

    if not isinstance(payload, list):
        return resultados

    for registro in payload:
        if not isinstance(registro, dict):
            continue

        tipo = str(registro.get("tipo", "")).strip()
        ano_acordao = str(registro.get("anoAcordao", "")).strip()
        numero_acordao = str(registro.get("numeroAcordao", "")).strip()
        titulo_base = str(registro.get("titulo", "")).strip()
        colegiado = str(registro.get("colegiado", "")).strip()
        data_sessao = str(registro.get("dataSessao", "")).strip()
        relator = str(registro.get("relator", "")).strip()
        situacao = str(registro.get("situacao", "")).strip()
        sumario = str(registro.get("sumario", "")).strip()
        url_acordao = str(registro.get("urlAcordao", "")).strip()
        url_pdf = str(registro.get("urlArquivoPDF", "")).strip()
        url_arquivo = str(registro.get("urlArquivo", "")).strip()

        if not titulo_base:
            identificacao = " ".join(
                parte for parte in (tipo, numero_acordao, ano_acordao, colegiado) if parte
            ).strip()
            titulo_base = identificacao or "Acórdão do Tribunal de Contas da União"

        url_origem = url_acordao or url_pdf or url_arquivo
        if not re.match(r"^https?://", url_origem, flags=re.IGNORECASE):
            continue

        data_publicacao = parse_data(data_sessao)
        if not dentro_da_janela(data_publicacao):
            continue

        texto_analise = f"{titulo_base} {tipo} {colegiado} {relator} {situacao} {sumario}"

        if not relevante(texto_analise):
            continue

        titulo_final = normalizar_titulo("TCU", titulo_base[:180].strip())
        if not titulo_final:
            continue

        resultados.append(
            LinkItem(
                source="TCU",
                title=titulo_final,
                url=url_origem,
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
        registros_lidos = 0
        descartados_sem_data = 0
        descartados_fora_janela = 0
        descartados_sem_url = 0
        descartados_sem_relevancia = 0

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

                registros_lidos += 1

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
                    descartados_sem_url += 1
                    continue

                if not re.match(r"^https?://", url_origem, flags=re.IGNORECASE):
                    descartados_sem_url += 1
                    continue

                data_convertida = parse_data(data_publicacao)
                if data_convertida is None:
                    descartados_sem_data += 1
                    continue
                if not dentro_da_janela_pncp(data_convertida):
                    descartados_fora_janela += 1
                    continue

                texto_analise = f"{titulo_base} {modalidade_nome} {info_complementar} {amparo_nome} {amparo_descricao}"
                if not relevante(texto_analise):
                    descartados_sem_relevancia += 1
                    continue

                titulo_final = normalizar_titulo("PNCP", titulo_base[:180].strip())
                if not titulo_final:
                    continue

                resultados.append(
                    LinkItem(
                        source="PNCP",
                        title=titulo_final,
                        url=url_origem,
                        published_at=data_convertida.date().isoformat(),
                    )
                )

            total_paginas = int(payload.get("totalPaginas") or 0)
            pagina += 1
            paginas_processadas += 1

            if total_paginas and pagina > total_paginas:
                break

        print(
            f"PNCP modalidade {modalidade}: "
            f"lidos={registros_lidos}, "
            f"sem_data={descartados_sem_data}, "
            f"fora_janela={descartados_fora_janela}, "
            f"sem_url={descartados_sem_url}, "
            f"sem_relevancia={descartados_sem_relevancia}, "
            f"aceitos={len([item for item in resultados if item.source == 'PNCP'])}"
        )
    return resultados
def coletar_rss_tcm_ba() -> list[LinkItem]:
    resultados: list[LinkItem] = []
    urls_processadas: set[str] = set()
    rss_lidos = 0
    rss_falhas = 0
    itens_lidos = 0
    sem_data = 0
    fora_janela = 0
    sem_relevancia = 0
    links_rejeitados = 0

    for rss_url in TCM_BA_RSS_URLS:
        try:
            xml_text = fetch_text(rss_url)
            root = ET.fromstring(xml_text)
            rss_lidos += 1
        except Exception as erro:
            rss_falhas += 1
            print(f"TCM-BA RSS falhou: {rss_url} | {type(erro).__name__}: {erro}")
            continue

        for item in root.findall("./channel/item"):
            itens_lidos += 1

            titulo = limpar_texto(item.findtext("title", default=""))
            link = limpar_texto(item.findtext("link", default=""))
            descricao = limpar_texto(item.findtext("description", default=""))
            pub_date_raw = limpar_texto(item.findtext("pubDate", default=""))

            if not titulo or not link:
                continue

            if not eh_url_publicacao_direta(link, "tcm.ba.gov.br"):
                links_rejeitados += 1
                continue

            chave = link.strip().lower()
            if chave in urls_processadas:
                continue
            data_publicacao = parse_data_stj_rss(pub_date_raw) or parse_data(pub_date_raw)

            if data_publicacao is None:
                sem_data += 1
                continue

            if not dentro_da_janela_tcm_ba(data_publicacao):
                fora_janela += 1
                continue

            texto_analise = f"{titulo} {descricao}"

            if not relevante(texto_analise):
                sem_relevancia += 1
                continue

            titulo_final = normalizar_titulo("TCM-BA", titulo[:180].strip())

            resultados.append(
                LinkItem(
                    source="TCM-BA",
                    title=titulo_final,
                    url=link,
                    published_at=data_publicacao.date().isoformat(),
                )
            )
            urls_processadas.add(chave)
    print(
        f"TCM-BA RSS diagnóstico: "
        f"rss_lidos={rss_lidos}, "
        f"rss_falhas={rss_falhas}, "
        f"itens_lidos={itens_lidos}, "
        f"links_rejeitados={links_rejeitados}, "
        f"sem_data={sem_data}, "
        f"fora_janela={fora_janela}, "
        f"sem_relevancia={sem_relevancia}, "
        f"aceitos={len(resultados)}"
    )

    return resultados

def coletar_tcm_ba() -> list[LinkItem]:
    resultados: list[LinkItem] = []
    urls_processadas: set[str] = set()

    resultados_rss = coletar_rss_tcm_ba()

    for item in resultados_rss:
        if not eh_url_publicacao_direta(item.url, "tcm.ba.gov.br"):
            continue

        chave = item.url.strip().lower()
        if chave in urls_processadas:
            continue

        resultados.append(item)
        urls_processadas.add(chave)

    html_resultados = coletar_html_oficial(
        source="TCM-BA",
        urls_base=TCM_BA_NOTICIAS_URLS,
        dominio="tcm.ba.gov.br",
        janela_func=dentro_da_janela_tcm_ba,
        prefixo="TCM-BA",
    )

    for item in html_resultados:
        chave = item.url.strip().lower()
        if chave in urls_processadas:
            continue

        resultados.append(item)
        urls_processadas.add(chave)

    print(f"TCM-BA total após RSS + HTML direto: {len(resultados)}")
    return resultados

def coletar_tcm_go() -> list[LinkItem]:

    resultados: list[LinkItem] = []
    urls_processadas: set[str] = set()

    for termo in TCM_GO_TERMOS:
        url = (
            f"{TCM_GO_POSTS_API}"
            f"?search={termo}"
            f"&per_page=20"
            f"&_fields=date,link,title,excerpt"
        )

        try:
            payload = fetch_json(url)
        except Exception:
            continue

        if not isinstance(payload, list):
            continue

        for registro in payload:
            if not isinstance(registro, dict):
                continue

            link = str(registro.get("link", "")).strip()
            data_raw = str(registro.get("date", "")).strip()

            titulo_raw = registro.get("title") or {}
            resumo_raw = registro.get("excerpt") or {}

            titulo = ""
            resumo = ""

            if isinstance(titulo_raw, dict):
                titulo = limpar_texto(str(titulo_raw.get("rendered", "")))
            else:
                titulo = limpar_texto(str(titulo_raw))

            if isinstance(resumo_raw, dict):
                resumo = limpar_texto(str(resumo_raw.get("rendered", "")))
            else:
                resumo = limpar_texto(str(resumo_raw))

            if not titulo or not link:
                continue

            if not re.match(r"^https?://", link, flags=re.IGNORECASE):
                continue

            if not mesmo_dominio(link, "tcmgo.tc.br"):
                continue

            chave = link.lower()
            if chave in urls_processadas:
                continue

            data_publicacao = parse_data(data_raw)
            if not dentro_da_janela_tcm_go(data_publicacao):
                continue

            texto_analise = f"{titulo} {resumo} {termo}"

            if not relevante(texto_analise):
                continue

            titulo_final = normalizar_titulo("TCM-GO", titulo[:180].strip())

            resultados.append(
                LinkItem(
                    source="TCM-GO",
                    title=titulo_final,
                    url=link,
                    published_at=data_publicacao.date().isoformat(),
                )
            )
            urls_processadas.add(chave)

    return resultados

def main() -> None:
    manuais = carregar_manuais()
    tcu_acordaos = coletar_tcu_acordaos()
    stj_jurisprudencia = coletar_stj_jurisprudencia()
    tce_sp = coletar_tce_sp()
    tce_mg = coletar_tce_mg()
    tce_sc = coletar_tce_sc()
    tce_pe = coletar_tce_pe()
    pncp_contratacoes = coletar_pncp_contratacoes()

    print(f"Manuais: {len(manuais)}")
    print(f"TCU: {len(tcu_acordaos)}")
    print(f"STJ: {len(stj_jurisprudencia)}")
    print(f"TCE-SP: {len(tce_sp)}")
    print(f"TCE-MG: {len(tce_mg)}")
    print(f"TCE-SC: {len(tce_sc)}")
    print(f"TCE-PE: {len(tce_pe)}")
    print(f"PNCP: {len(pncp_contratacoes)}")

    tcm_ba = coletar_tcm_ba()
    tcm_go = coletar_tcm_go()

    print(f"TCM-BA: {len(tcm_ba)}")
    print(f"TCM-GO: {len(tcm_go)}")
    automaticos = normalizar_lista(
        [
            *tcu_acordaos,
            *stj_jurisprudencia,
            *tce_sp,
            *tce_mg,
            *tce_sc,
            *tce_pe,
            *pncp_contratacoes,
            *tcm_ba,
            *tcm_go,
        ]
    )

    print(f"Automáticos após normalização: {len(automaticos)}")

    saida_atual = carregar_saida_atual()
    automaticos_atuais = [
        item for item in saida_atual
        if item.source in LIMITE_AUTOMATICO_POR_ORGAO
    ]

    if not automaticos:
        print("Nenhum link automático válido encontrado. Mantido o links-publicacoes.json já existente.")
        return
    if len(automaticos) < MINIMO_AUTOMATICOS_PARA_SALVAR and automaticos_atuais:
        print(
            "Quantidade automática abaixo do mínimo de segurança. "
            "Mantido o links-publicacoes.json já existente."
        )
        return

    consolidados = [*manuais, *automaticos]
    print(f"Consolidados finais: {len(consolidados)}")

    fontes_consolidadas: dict[str, int] = {}
    for item in consolidados:
        fontes_consolidadas[item.source] = fontes_consolidadas.get(item.source, 0) + 1

    print(f"Fontes consolidadas antes de salvar: {fontes_consolidadas}")

    salvar_links(consolidados)

    saida_salva = carregar_saida_atual()
    fontes_salvas: dict[str, int] = {}
    for item in saida_salva:
        fontes_salvas[item.source] = fontes_salvas.get(item.source, 0) + 1

    print(f"Fontes gravadas no JSON: {fontes_salvas}")

    print(f"Atualização concluída com {len(consolidados)} links em {ARQUIVO_SAIDA}")

if __name__ == "__main__":
    main()
