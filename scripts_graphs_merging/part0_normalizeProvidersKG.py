from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS

# Load the KG
input_file = "C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/providersKG_embed.ttl"
output_file = "providersKG_normalized.ttl"

graph = Graph()
graph.parse(input_file, format="turtle")

# Define Namespaces
specialties = Namespace("http://example.org/specialties/")  # Add specialties prefix
custom = Namespace("http://example.org/custom/")
schema1 = Namespace("http://schema.org/")
ns1 = Namespace("http://example.org/embedding#embedding_http://schema.org/")  # Keep ns1 prefix
ns2 = Namespace("http://example.org/embedding#")

# Function to normalize specialty URIs
def normalize_specialty_uri(uri):
    uri_str = str(uri)
    if "example.org/specialties/" in uri_str:
        # Normalize the URI by keeping only the relevant part after "example.org/specialties/"
        normalized_part = uri_str.split("example.org/specialties/")[-1].strip("/")
        # Reconstruct the correct URI
        return URIRef(f"http://example.org/specialties/{normalized_part}")
    return uri


# Function to adjust schema1:name usage for specialties
def adjust_specialty_schema_name(uri, predicate, obj):
    if predicate == schema1.name:
        uri_str = str(uri)
        if uri_str.startswith("http://example.org/specialties/"):
            # Replace schema1:name with rdf:value for specialties
            return RDF.value, Literal(uri_str.replace("http://example.org/specialties/", ""))
    return predicate, obj

# Create a new graph for the updated data
normalized_graph = Graph()
normalized_graph.bind("specialties", specialties)  # Bind specialties prefix
normalized_graph.bind("custom", custom)
normalized_graph.bind("schema1", schema1)
normalized_graph.bind("ns1", ns1)  # Bind ns1 explicitly
normalized_graph.bind("ns2", ns2)

# Iterate through triples to normalize and adjust
for s, p, o in graph:
    # Normalize specialty URIs
    if isinstance(s, URIRef):
        s = normalize_specialty_uri(s)
    if isinstance(o, URIRef):
        o = normalize_specialty_uri(o)
    
    # Adjust schema1:name usage for specialties
    p, o = adjust_specialty_schema_name(s, p, o)
    
    # Add the normalized triple to the new graph
    normalized_graph.add((s, p, o))

# Save the updated graph
normalized_graph.serialize(destination=output_file, format="turtle")
print(f"Normalized KG saved to {output_file}")
