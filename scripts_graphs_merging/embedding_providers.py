import os
import json
from rdflib import Graph, Namespace, Literal
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
# Load environment variables
load_dotenv()

# Retrieve OpenAI API Key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.")

# Initialize OpenAI Embeddings
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=openai_api_key,
    dimensions=512
)

# Load the final cleaned RDF graph
file_path = "providers_graphV3.ttl"  # Input file
output_path = "ProvidersGraph_withReal_embeddings.ttl"  # Output file with embeddings
graph = Graph()
graph.parse(file_path, format="turtle")

# Namespaces
schema1 = Namespace("http://schema.org/")
rdf_ns = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
custom_ns = Namespace("http://example.org/custom/")
ns2 = Namespace("http://example.org/embedding#")  # Namespace for embeddings
graph.bind("schema1", schema1)
graph.bind("rdf", rdf_ns)
graph.bind("custom", custom_ns)
graph.bind("ns2", ns2)

# Prepare parts to embed
parts_to_embed = []

# Embed schema:description for all entities
for s, p, o in graph.triples((None, schema1.description, None)):
    parts_to_embed.append((s, schema1.description, str(o)))

# Embed rdf:value for all specialties
for s, p, o in graph.triples((None, rdf_ns.value, None)):
    parts_to_embed.append((s, rdf_ns.value, str(o)))

# Generate embeddings and add them to the graph
for subject, predicate, text in tqdm(parts_to_embed, desc="Embedding parts"):
    try:
        # Generate real embedding using OpenAI model
        embedding = embedding_model.embed_documents([text])[0]
        
        # Create a unique embedding property name
        embedding_key = f"embedding_{predicate.split('#')[-1]}"
        
        # Add the embedding to the graph
        graph.add((subject, ns2[embedding_key], Literal(json.dumps(embedding))))
    except Exception as e:
        print(f"Error embedding text for subject {subject}: {e}")

# Save the enriched graph
graph.serialize(destination=output_path, format="turtle")
print(f"Graph with embeddings saved to {output_path}")
