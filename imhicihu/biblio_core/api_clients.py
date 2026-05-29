import requests
import urllib.parse
import time

# --- CONFIGURACIÓN GLOBAL ---
# Es fundamental identificarse educadamente ante las bibliotecas nacionales para evitar bloqueos
HEADERS_CORTESIA = {
    'User-Agent': 'MineriaReinhardt/1.0 (https://imhicihu.conicet.gov.ar/; mail: chirinofaustino@conicet.gov.ar)',
    'From': 'chirinofaustino@conicet.gov.ar'
}

# --- FUNCIONES DE CONSULTA A REPOSITORIOS (ALTA PRECISIÓN) ---

def consultar_dnb(query_data, tipo='isbn'):
    print(f"   > [DNB] Buscando...", end="\r")
    try:
        if tipo == 'isbn':
            isbn_clean = str(query_data).replace("-", "").replace(" ", "").strip()
            url = f"https://services.dnb.de/sru/dnb?version=1.1&operation=searchRetrieve&query=NUM={isbn_clean}&maximumRecords=1&recordSchema=MARC21-xml"
        else:
            partes = []
            if query_data.get('autor'): partes.append(f'PER="{query_data["autor"]}"')
            if query_data.get('titulo'): partes.append(f'TIT="{query_data["titulo"]}"')
            query_string = " AND ".join(partes)
            url = f"https://services.dnb.de/sru/dnb?version=1.1&operation=searchRetrieve&query={urllib.parse.quote(query_string)}&maximumRecords=1&recordSchema=MARC21-xml"
            
        res = requests.get(url, headers=HEADERS_CORTESIA, timeout=15)
        if res.status_code == 200 and "<datafield" in res.text:
            return {"formato": "MARCXML", "raw_xml": res.text}
    except: pass
    return None

def consultar_bne(query_data, tipo='isbn'):
    print(f"   > [BNE] Buscando...", end="\r")
    try:
        if tipo == 'isbn':
            isbn_clean = str(query_data).replace("-", "").replace(" ", "").strip()
            url = f"https://catalogo.bne.es/view/sru/34BNE_INST?operation=searchRetrieve&version=1.2&query=alma.isbn=%22{isbn_clean}%22&recordSchema=marcxml&maximumRecords=1"
        else:
            partes = []
            if query_data.get('autor'): partes.append(f'alma.creator="{query_data["autor"]}"')
            if query_data.get('titulo'): partes.append(f'alma.title="{query_data["titulo"]}"')
            query_string = " AND ".join(partes)
            url = f"https://catalogo.bne.es/view/sru/34BNE_INST?operation=searchRetrieve&version=1.2&query={urllib.parse.quote(query_string)}&recordSchema=marcxml&maximumRecords=1"
            
        res = requests.get(url, headers=HEADERS_CORTESIA, timeout=15)
        if res.status_code == 200 and "<datafield" in res.text:
            return {"formato": "MARCXML", "raw_xml": res.text}
    except: pass
    return None

def consultar_lc(query_data, tipo='isbn'):
    print(f"   > [LC] Buscando...", end="\r")
    isbn_clean = str(query_data).replace("-", "").replace(" ", "").strip() if tipo == 'isbn' else ""

    # INTENTO 1: SRU (Servidor Profesional)
    if isbn_clean:
        try:
            url_sru = f"https://lx2.loc.gov/lx2/sru/lc?operation=searchRetrieve&version=1.1&query=bf.isbn={isbn_clean}&recordSchema=marcxml&maximumRecords=1"
            res = requests.get(url_sru, headers=HEADERS_CORTESIA, timeout=10)
            if res.status_code == 200 and ("<marc:record" in res.text or "<record" in res.text):
                return {"formato": "MARCXML", "raw_xml": res.text}
        except: pass

    # INTENTO 2: Buscador Web Fallback
    intentos_url = []
    if tipo == 'isbn':
        intentos_url.append(f"https://www.loc.gov/books/?q=isbn:{isbn_clean}&fo=json")
        intentos_url.append(f"https://www.loc.gov/books/?q={isbn_clean}&fo=json")
    else:
        autor = urllib.parse.quote(query_data.get('autor', ''))
        titulo = urllib.parse.quote(f'"{query_data.get("titulo", "")}"')
        intentos_url.append(f"https://www.loc.gov/books/?q={titulo}+{autor}&fo=json")

    for url in intentos_url:
        try:
            res = requests.get(url, headers=HEADERS_CORTESIA, timeout=15)
            if res.status_code == 200:
                datos = res.json()
                if datos.get('results'):
                    validos = [r for r in datos['results'] if r.get('title')]
                    if validos: return validos[0]
        except: continue
        time.sleep(0.5)

    return None

def consultar_ol(query_data, tipo='isbn'):
    print(f"   > [OpenLibrary] Buscando...", end="\r")
    try:
        if tipo == 'isbn':
            isbn_clean = str(query_data).replace("-", "").replace(" ", "").strip()
            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn_clean}&format=json&jscmd=data"
            res = requests.get(url, headers=HEADERS_CORTESIA, timeout=12)
            if res.status_code == 200 and res.json(): return res.json()
        else:
            autor = urllib.parse.quote(query_data.get('autor', ''))
            titulo = urllib.parse.quote(query_data.get('titulo', ''))
            url = f"https://openlibrary.org/search.json?author={autor}&title={titulo}&limit=1"
            res = requests.get(url, headers=HEADERS_CORTESIA, timeout=12)
            if res.status_code == 200:
                datos = res.json()
                if datos.get('numFound', 0) > 0: return datos['docs'][0]
    except: pass
    return None

def consultar_gb(query_data, tipo='isbn'):
    print(f"   > [GoogleBooks] Buscando...", end="\r")
    try:
        if tipo == 'isbn':
            isbn_clean = str(query_data).replace("-", "").replace(" ", "").strip()
            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_clean}"
        else:
            partes = []
            if query_data.get('autor'): partes.append(f'inauthor:"{query_data["autor"]}"')
            if query_data.get('titulo'): partes.append(f'intitle:"{query_data["titulo"]}"')
            query_string = "+".join(partes)
            url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query_string)}"
            
        res = requests.get(url, headers=HEADERS_CORTESIA, timeout=12)
        if res.status_code == 200:
            datos = res.json()
            if datos.get('totalItems', 0) > 0: return datos['items'][0]['volumeInfo']
    except: pass
    return None


def consultar_lc_sru_por_lccn(lccn):
    """Consulta específica a la LC para traer MARCXML puro via LCCN."""
    # La variable HEADERS_CORTESIA ya existe al principio de este archivo
    url = f"https://lx2.loc.gov/lx2/sru/lc?operation=searchRetrieve&version=1.1&query=bf.lccn={lccn.strip()}&recordSchema=marcxml&maximumRecords=1"
    try:
        res = requests.get(url, headers=HEADERS_CORTESIA, timeout=15)
        if res.status_code == 200 and ("<marc:record" in res.text or "<record" in res.text):
            return {"formato": "MARCXML", "raw_xml": res.text}
    except:
        pass
    return None