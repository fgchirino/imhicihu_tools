import json

def extraer_lccn_de_json(metadata_cruda):
    """Intenta encontrar un LCCN dentro de los distintos formatos de JSON."""
    try:
        obj = json.loads(metadata_cruda)
        data = obj.get("data", {})
        
        # Caso 1: GoogleBooks
        if "industryIdentifiers" in data:
            for id_obj in data["industryIdentifiers"]:
                if "LCCN" in id_obj.get("type", ""):
                    return id_obj.get("identifier")
        
        # Caso 2: OpenLibrary
        if "identifiers" in data:
            lccn_list = data["identifiers"].get("lccn", [])
            if lccn_list: return lccn_list[0]
            
        # Caso 3: LC-Web JSON
        if "lccn" in data:
            val = data["lccn"]
            return val[0] if isinstance(val, list) else val
            
    except:
        pass
    return None