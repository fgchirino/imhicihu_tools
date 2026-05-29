import re

def limpiar_namespaces_xml(xml_string):
    """Elimina los namespaces del XML para buscar etiquetas limpiamente"""
    if not xml_string:
        return ""
    return re.sub(r'\sxmlns="[^"]+"', '', str(xml_string), count=1)

def extraer_subcampo_marc(root, tag, code):
    """Busca en el árbol XML un tag y extrae la PRIMERA coincidencia"""
    if root is None:
        return ""
    for df in root.findall(f".//datafield[@tag='{tag}']"):
        for sf in df.findall(f"subfield[@code='{code}']"):
            if sf.text:
                return sf.text.strip()
    return ""

def extraer_multiples_subcampos_marc(root, tag, code):
    """Busca en el árbol XML un tag y extrae TODAS las coincidencias (ej: 650$a)"""
    resultados = []
    if root is None:
        return resultados
    for df in root.findall(f".//datafield[@tag='{tag}']"):
        for sf in df.findall(f"subfield[@code='{code}']"):
            if sf.text:
                resultados.append(sf.text.strip())
    return resultados