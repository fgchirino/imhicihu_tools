import json
import xml.etree.ElementTree as ET
from imhicihu.biblio_core.marc_parsers import (
    limpiar_namespaces_xml,
    extraer_subcampo_marc,
    extraer_multiples_subcampos_marc
)

def mapear_dnb(metadata_cruda):
    """Extrae TODOS los datos de la DNB (MARCXML)"""
    datos = {"autor": "", "titulo": "", "editorial": "", "anio": "", 
             "lugar": "", "paginas": "", "serie": "", "temas": "", "notas": ""}
    try:
        dict_dnb = json.loads(metadata_cruda)
        xml_limpio = limpiar_namespaces_xml(dict_dnb.get("raw_xml", ""))
        root = ET.fromstring(xml_limpio)
        
        datos["autor"] = extraer_subcampo_marc(root, "100", "a")
        
        titulo_a = extraer_subcampo_marc(root, "245", "a")
        titulo_b = extraer_subcampo_marc(root, "245", "b")
        datos["titulo"] = f"{titulo_a} {titulo_b}".strip()
        
        # Publicación
        datos["lugar"] = extraer_subcampo_marc(root, "264", "a") or extraer_subcampo_marc(root, "260", "a")
        datos["editorial"] = extraer_subcampo_marc(root, "264", "b") or extraer_subcampo_marc(root, "260", "b")
        datos["anio"] = extraer_subcampo_marc(root, "264", "c") or extraer_subcampo_marc(root, "260", "c")
        
        # Descripción Física y Serie
        pag = extraer_subcampo_marc(root, "300", "a")
        dim = extraer_subcampo_marc(root, "300", "c")
        datos["paginas"] = f"{pag} {dim}".strip()
        
        serie_a = extraer_subcampo_marc(root, "490", "a")
        serie_v = extraer_subcampo_marc(root, "490", "v")
        datos["serie"] = f"{serie_a} {serie_v}".strip()
        
        # Temas (650 materias, 600 personas)
        temas = extraer_multiples_subcampos_marc(root, "650", "a") + extraer_multiples_subcampos_marc(root, "600", "a")
        datos["temas"] = " | ".join(temas)
        
        # Notas (500 generales, 502 tesis)
        notas = extraer_multiples_subcampos_marc(root, "500", "a") + extraer_multiples_subcampos_marc(root, "502", "a")
        datos["notas"] = " | ".join(notas)
        
    except Exception as e:
        print(f"Error parseando DNB: {e}")
    return datos

def mapear_openlibrary(metadata_cruda):
    """Extrae TODOS los datos de Open Library (JSON Dinámico)"""
    datos = {"autor": "", "titulo": "", "editorial": "", "anio": "", 
             "lugar": "", "paginas": "", "serie": "", "temas": "", "notas": ""}
    try:
        dict_ol = json.loads(metadata_cruda)
        if dict_ol:
            llave = list(dict_ol.keys())[0]
            libro = dict_ol[llave]
            
            datos["titulo"] = libro.get("title", "")
            
            autores = libro.get("authors", [])
            if autores: datos["autor"] = autores[0].get("name", "")
                
            editoriales = libro.get("publishers", [])
            if editoriales: datos["editorial"] = editoriales[0].get("name", "")
                
            lugares = libro.get("publish_places", [])
            if lugares: datos["lugar"] = lugares[0].get("name", "")
                
            datos["anio"] = str(libro.get("publish_date", ""))
            datos["paginas"] = str(libro.get("pagination", libro.get("number_of_pages", "")))
            
            temas_lista = []
            for key in ["subjects", "subject_people", "subject_places"]:
                for item in libro.get(key, []):
                    if isinstance(item, dict) and "name" in item:
                        temas_lista.append(item["name"])
            datos["temas"] = " | ".join(temas_lista)
            
            notas = libro.get("notes", "")
            if isinstance(notas, dict): notas = notas.get("value", "")
            datos["notas"] = str(notas).replace("\n", " ").replace("\r", " ").strip()
            
    except Exception as e:
        print(f"Error parseando OpenLibrary: {e}")
    return datos

def mapear_googlebooks(metadata_cruda):
    """Extrae TODOS los datos de Google Books (JSON)"""
    datos = {"autor": "", "titulo": "", "editorial": "", "anio": "", 
             "lugar": "", "paginas": "", "serie": "", "temas": "", "notas": ""}
    try:
        dict_gb = json.loads(metadata_cruda)
        datos["titulo"] = dict_gb.get("title", "")
        
        autores = dict_gb.get("authors", [])
        if autores: datos["autor"] = ", ".join(autores)
            
        datos["editorial"] = dict_gb.get("publisher", "")
        datos["anio"] = str(dict_gb.get("publishedDate", ""))[:4]
        datos["paginas"] = str(dict_gb.get("pageCount", ""))
        
        temas = dict_gb.get("categories", [])
        datos["temas"] = " | ".join(temas) if temas else ""
        
        datos["notas"] = str(dict_gb.get("description", "")).replace("\n", " ").replace("\r", " ").strip()
    except Exception as e:
        print(f"Error parseando GoogleBooks: {e}")
    return datos

def mapear_lc(metadata_cruda):
    """Extrae TODOS los datos de Library of Congress (JSON)"""
    datos = {"autor": "", "titulo": "", "editorial": "", "anio": "", 
             "lugar": "", "paginas": "", "serie": "", "temas": "", "notas": ""}
    try:
        dict_lc = json.loads(metadata_cruda)
        datos["titulo"] = dict_lc.get("title", "")
        
        contrib = dict_lc.get("contributor", [])
        if contrib: datos["autor"] = contrib[0]
            
        datos["anio"] = str(dict_lc.get("date", ""))
        
        lugares = dict_lc.get("location", [])
        if lugares: datos["lugar"] = lugares[0]
        
        desc = dict_lc.get("description", [])
        if desc: datos["paginas"] = desc[0]
        
        temas = dict_lc.get("subject", [])
        datos["temas"] = " | ".join(temas) if temas else ""
        
        notas = dict_lc.get("notes", [])
        datos["notas"] = " | ".join(notas) if notas else ""
        
    except Exception as e:
        print(f"Error parseando LC: {e}")
    return datos