from rdflib_neo4j import Neo4jStoreConfig, Neo4jStore, HANDLE_VOCAB_URI_STRATEGY 
from rdflib import Graph, Namespace
from dotenv import load_dotenv
import os
# Load environment variables
load_dotenv()
# Neo4j connection details (loaded from environment variables)
NEO4J_URI = os.getenv("URI")
NEO4J_USERNAME = os.getenv("USERNAME")
NEO4J_PASSWORD = os.getenv("PWD")

# Define Neo4j connection details
auth_data = {
    'uri':NEO4J_URI ,
    'database': "greviakg",  # Default database name
    'user': NEO4J_USERNAME,
    'pwd':NEO4J_PASSWORD 
}

# Define prefixes
prefixes = {
    'ns': Namespace('http://data.europa.eu/s66/ontology#'),
    'ns1': Namespace('http://data.europa.eu/s66#'),
    'ns2': Namespace('http://data.europa.eu/s66/ontology/embedding#'),
    'rdf': Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
    'rdfs': Namespace('http://www.w3.org/2000/01/rdf-schema#'),
    'xsd': Namespace('http://www.w3.org/2001/XMLSchema#')
}

# Configure Neo4j Store
config = Neo4jStoreConfig(
    auth_data=auth_data,
    custom_prefixes=prefixes,
    handle_vocab_uri_strategy=HANDLE_VOCAB_URI_STRATEGY.IGNORE,
    batching=True
)

# Initialize the graph
graph_store = Graph(store=Neo4jStore(config=config))

# File paths
file_path = "import_data/cordisKG_embed.ttl"

# Parse and ingest the data
graph_store.parse(file_path, format="ttl")
graph_store.close(True)

print("TTL file successfully imported into Neo4j Desktop.")
