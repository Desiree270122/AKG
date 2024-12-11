import json
from rdflib import Graph, Namespace
import re

# Charger les données RDF
graph_rdf = Graph()
graph_rdf.parse("teaching_akg.ttl", format="ttl")

# Définir les namespaces
akg_namespace = Namespace("http://sonfack.com/2023/12/tao/")

# Fonction pour extraire les noms sans URI
def extract_name(uri):
    name = re.sub(r'http://sonfack\.com/2023/12/(tao)/', '', uri)
    return name

# Extraire les données RDF et les transformer en JSON
def rdf_to_json(graph_rdf):
    data = []
    for subj, pred, obj in graph_rdf:
        subj_label = extract_name(str(subj))
        pred_label = extract_name(str(pred))
        obj_label = extract_name(str(obj))
        
        # Ajouter les triplets sous forme de dictionnaire
        data.append({
            "subject": subj_label,
            "predicate": pred_label,
            "object": obj_label
        })
    return data

# Convertir le graphe RDF en structure JSON
data_json = rdf_to_json(graph_rdf)

# Sauvegarder dans un fichier JSON
with open('graph_data.json', 'w', encoding='utf-8') as f:
    json.dump(data_json, f, ensure_ascii=False, indent=4)

print("Les données RDF ont été converties et sauvegardées dans graph_data.json")
