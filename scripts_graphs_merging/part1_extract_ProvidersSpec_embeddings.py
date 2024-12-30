import json
import numpy as np
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

# Load providers KG with embeddings
input_file = r"C:\Users\Utente\neo4j-projects\grevia-project-neo4j\import_data\providersKG_normalized.ttl"

graph = Graph()
graph.parse(input_file, format="turtle")

# Define Namespaces
schema1 = Namespace("http://schema.org/")
custom = Namespace("http://example.org/custom/")
specialties = Namespace("http://example.org/specialties/")  # Updated for specialties
ns2 = Namespace("http://example.org/embedding#")

# Initialize data structures for specialties and embeddings
embeddings = []
specialty_uris = []

# Iterate through all specialties in the KG
for s, p, o in graph.triples((None, RDF.type, specialties.Specialty)):
    # Find the embedding for this specialty
    for s2, p2, o2 in graph.triples((s, ns2.embedding_value, None)):
        # Parse the embedding JSON and store it
        try:
            arr = json.loads(str(o2))
            embeddings.append(arr)
            specialty_uris.append(str(s))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON for {s}: {e}")

# Convert embeddings to a NumPy array for clustering
X = np.array(embeddings)  # Shape: (num_specialties, embedding_dim)
print(f"Extracted {len(specialty_uris)} specialties with embeddings.")
print(f"Embedding matrix shape: {X.shape}")

# Save the extracted data to a JSON file for the clustering script
output_data = {
    "specialty_uris": specialty_uris,
    "embeddings": embeddings
}

output_file = r"C:\Users\Utente\neo4j-projects\grevia-project-neo4j\import_data\providers_embeddings.json"
with open(output_file, "w") as f:
    json.dump(output_data, f)

print(f"Extracted data saved to {output_file}")
