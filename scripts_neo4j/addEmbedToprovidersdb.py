from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF
import json
from neo4j import GraphDatabase
from tqdm import tqdm
import os
# Path to JSON file with embeddings
embedding_file = "C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/macro_anchors_with_avg_embeddings.json"

# Neo4j connection details
NEO4J_URI = os.getenv("URI")
NEO4J_USERNAME = os.getenv("USERNAME")
NEO4J_PASSWORD = os.getenv("PWD")


# Neo4j namespaces align with RDF prefixes
NS2 = "ns2__embedding_value"

# Load embeddings from JSON
with open(embedding_file, "r") as f:
    embeddings_data = json.load(f)

# Define Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Function to update macrocategory and microcategory embeddings
def update_embeddings(tx, macro_name, macro_embedding, micro_embeddings):
    # Update macrocategory embedding
    result = tx.run(
        """
        MATCH (macro:specialties__Macrocategory {rdfs__label: $macro_name})
        SET macro.ns2__embedding_value = $macro_embedding
        RETURN macro.rdfs__label AS MacroLabel
        """,
        macro_name=macro_name,
        macro_embedding=macro_embedding,
    )
    if not result.single():
        print(f"Warning: Macrocategory '{macro_name}' not found in Neo4j.")

    # Update microcategory embeddings
    for micro_anchor, micro_embedding in micro_embeddings.items():
        result = tx.run(
            """
            MATCH (micro:specialties__Microcategory {rdfs__label: $micro_anchor})
            SET micro.ns2__embedding_value = $micro_embedding
            RETURN micro.rdfs__label AS MicroLabel
            """,
            micro_anchor=micro_anchor,
            micro_embedding=micro_embedding,
        )
        if not result.single():
            print(f"Warning: Microcategory '{micro_anchor}' not found in Neo4j.")

# Define Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Main process
with driver.session(database="providersdb") as session:  # Specify your database name
    for macro_name, data in tqdm(embeddings_data.items(), desc="Loading embeddings"):
        macro_embedding = json.dumps(data["macro_avg_embedding"])  # Convert to JSON string
        micro_embeddings = {
            anchor: json.dumps(embedding)
            for anchor, embedding in zip(data["anchors"], data["anchor_embeddings"])
        }
        session.write_transaction(update_embeddings, macro_name, macro_embedding, micro_embeddings)

print("All embeddings successfully loaded into Neo4j.")

# Close driver
driver.close()
