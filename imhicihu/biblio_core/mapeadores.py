import json
import xml.etree.ElementTree as ET
from imhicihu.biblio_core.marc_parsers import (
    limpiar_namespaces_xml,
    extraer_subcampo_marc,
    extraer_multiples_subcampos_marc
)

# Diccionario utilitario para normalizar códigos de idioma ISO a MARC (008/35-37)
MAPA_IDIOMAS = {"es": "spa", "en": "eng", "fr": "fre", "pt": "por", "de": "ger", "it": "ita"}

def _plantilla_datos():
    """Garantiza que todos los mapeadores devuelvan exactamente las mismas claves."""
    return {
        "identificadores": "", "cdd": "", "entidades_personas": "", 
        "entidades_instituciones": "", "entidades_reuniones": "", 
        "titulo_uniforme_240": "", "titulo_245a": "", "subtitulo_245b": "", 
        "mencion_resp_245c": "", "titulos_variantes_246": "", "edicion_250": "", 
        "pie_lugar_260a": "", "pie_editor_260b": "", "pie_fecha_260c": "", 
        "descripcion_fisica_300": "", "serie_490": "", "notas_5XX": "", 
        "descriptores_personas_600": "", "descriptores_instituciones_610": "",
        "descriptores_temas_650": "", "descriptores_geograficos_651": "", 
        "codigo_idioma": "", "codigo_pais": ""
    }

def mapear_googlebooks(metadata_cruda):
    """Extrae datos de Google Books aplicando modelo EAV."""
    datos = _plantilla_datos()
    try:
        dict_gb = json.loads(metadata_cruda)
        
        # Identificadores (EAV)
        lista_ids = []
        for id_obj in dict_gb.get("industryIdentifiers", []):
            tipo = id_obj.get("type", "").replace("_", "-") 
            val = id_obj.get("identifier", "")
            lista_ids.append(f"[{tipo}] {val}")
        datos["identificadores"] = " | ".join(lista_ids)
        
        datos["titulo_245a"] = dict_gb.get("title", "")
        datos["subtitulo_245b"] = dict_gb.get("subtitle", "")
        datos["entidades_personas"] = " | ".join(dict_gb.get("authors", []))
        
        datos["pie_editor_260b"] = dict_gb.get("publisher", "")
        datos["pie_fecha_260c"] = str(dict_gb.get("publishedDate", ""))[:4]
        if dict_gb.get("pageCount"):
            datos["descripcion_fisica_300"] = f"{dict_gb.get('pageCount')} p."
            
        temas = dict_gb.get("categories", [])
        datos["descriptores_temas_650"] = " | ".join(temas) if temas else ""
        
        desc = str(dict_gb.get("description", "")).replace("\n", " ").replace("\r", " ").strip()
        if desc:
            datos["notas_5XX"] = f"[500] {desc}"
            
        lang = dict_gb.get("language", "")
        datos["codigo_idioma"] = MAPA_IDIOMAS.get(lang.lower(), lang)
        
    except Exception as e:
        print(f"Error parseando GoogleBooks: {e}")
    return datos

def mapear_openlibrary(metadata_cruda):
    """Extrae datos de Open Library (Soporta Books API y Solr)."""
    datos = _plantilla_datos()
    try:
        dict_ol = json.loads(metadata_cruda)
        if not dict_ol:
            return datos
            
        llave = list(dict_ol.keys())[0]
        libro = dict_ol[llave] if isinstance(dict_ol[llave], dict) else dict_ol
        
        if "author_name" in libro or "docs" in dict_ol:
            datos["titulo_245a"] = libro.get("title", "")
            datos["entidades_personas"] = " | ".join(libro.get("author_name", []))
            datos["pie_fecha_260c"] = str(libro.get("first_publish_year", ""))
            idiomas = libro.get("language", [])
            if idiomas:
                datos["codigo_idioma"] = MAPA_IDIOMAS.get(idiomas[0].lower(), idiomas[0])
            return datos
            
        datos["titulo_245a"] = libro.get("title", "")
        datos["subtitulo_245b"] = libro.get("subtitle", "")
        datos["mencion_resp_245c"] = libro.get("by_statement", "")
        
        lista_ids = []
        for tipo, valores in libro.get("identifiers", {}).items():
            tipo_limpio = tipo.upper().replace("_", "-")
            for val in valores:
                lista_ids.append(f"[{tipo_limpio}] {val}")
        datos["identificadores"] = " | ".join(lista_ids)
        
        clasificaciones = libro.get("classifications", {})
        cdd = clasificaciones.get("dewey_decimal_class", [])
        if cdd: datos["cdd"] = cdd[0]
        
        autores = [a.get("name", "") for a in libro.get("authors", []) if "name" in a]
        datos["entidades_personas"] = " | ".join(autores)
        
        editores = [e.get("name", "") for e in libro.get("publishers", []) if "name" in e]
        datos["pie_editor_260b"] = " | ".join(editores)
        
        lugares = [l.get("name", "") for l in libro.get("publish_places", []) if "name" in l]
        datos["pie_lugar_260a"] = " | ".join(lugares)
        
        datos["pie_fecha_260c"] = str(libro.get("publish_date", ""))
        
        paginas = str(libro.get("pagination", libro.get("number_of_pages", "")))
        if paginas: datos["descripcion_fisica_300"] = f"{paginas} p."
        
        # Enrutamiento semántico de temas, personas y lugares geográficos
        temas, geograficos, personas = [], [], []
        for item in libro.get("subjects", []):
            if isinstance(item, dict) and "name" in item: temas.append(item["name"])
        for item in libro.get("subject_people", []):
            if isinstance(item, dict) and "name" in item: personas.append(item["name"])
        for item in libro.get("subject_places", []):
            if isinstance(item, dict) and "name" in item: geograficos.append(item["name"])
            
        datos["descriptores_temas_650"] = " | ".join(temas)
        datos["descriptores_personas_600"] = " | ".join(personas)
        datos["descriptores_geograficos_651"] = " | ".join(geograficos)
        
        notas = libro.get("notes", "")
        if isinstance(notas, dict): notas = notas.get("value", "")
        if notas:
            texto_nota = str(notas).replace("\n", " ").replace("\r", " ").strip()
            datos["notas_5XX"] = f"[500] {texto_nota}"
            
    except Exception as e:
        print(f"Error parseando OpenLibrary: {e}")
    return datos

def mapear_lc(metadata_cruda):
    """Extrae datos de la Library of Congress accediendo al nodo 'item'."""
    datos = _plantilla_datos()
    try:
        dict_lc = json.loads(metadata_cruda)
        
        if "item" not in dict_lc and "data" in dict_lc:
            dict_lc = dict_lc["data"]
            
        item = dict_lc.get("item", {})
        
        datos["titulo_245a"] = item.get("title", dict_lc.get("title", ""))
        datos["pie_fecha_260c"] = item.get("date", dict_lc.get("date", ""))
        
        contrib = item.get("contributors", dict_lc.get("contributor", []))
        datos["entidades_personas"] = " | ".join(contrib) if contrib else ""
        
        pub = item.get("created_published", [])
        datos["pie_editor_260b"] = " | ".join(pub) if pub else ""
        
        medium = item.get("medium", [])
        datos["descripcion_fisica_300"] = " | ".join(medium) if medium else ""
        
        temas = item.get("subjects", dict_lc.get("subject", []))
        datos["descriptores_temas_650"] = " | ".join(temas) if temas else ""
        
        notas_lista = []
        for nota in item.get("notes", []):
            notas_lista.append(f"[500] {nota}")
        datos["notas_5XX"] = " | ".join(notas_lista)
        
        lang = item.get("language", dict_lc.get("language", []))
        if lang:
            datos["codigo_idioma"] = MAPA_IDIOMAS.get(lang[0].lower(), lang[0])
            
        call_num = item.get("call_number", [])
        if call_num: datos["cdd"] = call_num[0]
        
    except Exception as e:
        print(f"Error parseando LC: {e}")
    return datos

def mapear_dnb(metadata_cruda):
    """Mapeador original DNB (XML) adaptado al esquema de 27 columnas."""
    datos = _plantilla_datos()
    try:
        dict_dnb = json.loads(metadata_cruda)
        xml_limpio = limpiar_namespaces_xml(dict_dnb.get("raw_xml", ""))
        root = ET.fromstring(xml_limpio)
        
        datos["entidades_personas"] = extraer_subcampo_marc(root, "100", "a")
        datos["titulo_245a"] = extraer_subcampo_marc(root, "245", "a")
        datos["subtitulo_245b"] = extraer_subcampo_marc(root, "245", "b")
        
        datos["pie_lugar_260a"] = extraer_subcampo_marc(root, "264", "a") or extraer_subcampo_marc(root, "260", "a")
        datos["pie_editor_260b"] = extraer_subcampo_marc(root, "264", "b") or extraer_subcampo_marc(root, "260", "b")
        datos["pie_fecha_260c"] = extraer_subcampo_marc(root, "264", "c") or extraer_subcampo_marc(root, "260", "c")
        
        pag = extraer_subcampo_marc(root, "300", "a")
        dim = extraer_subcampo_marc(root, "300", "c")
        datos["descripcion_fisica_300"] = f"{pag} {dim}".strip()
        
        serie_a = extraer_subcampo_marc(root, "490", "a")
        serie_v = extraer_subcampo_marc(root, "490", "v")
        datos["serie_490"] = f"{serie_a} {serie_v}".strip()
        
        # Separación estricta de autoridades
        personas_600 = extraer_multiples_subcampos_marc(root, "600", "a")
        datos["descriptores_personas_600"] = " | ".join(personas_600)
        
        instituciones_610 = extraer_multiples_subcampos_marc(root, "610", "a")
        datos["descriptores_instituciones_610"] = " | ".join(instituciones_610)
        
        temas_650 = extraer_multiples_subcampos_marc(root, "650", "a")
        datos["descriptores_temas_650"] = " | ".join(temas_650)
        
        notas = extraer_multiples_subcampos_marc(root, "500", "a") + extraer_multiples_subcampos_marc(root, "502", "a")
        datos["notas_5XX"] = " | ".join([f"[500] {n}" for n in notas])
        
    except Exception as e:
        print(f"Error parseando DNB: {e}")
    return datos