from neo4j import GraphDatabase
import json
from tqdm import tqdm
import os
file_path = "C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/JSONLike_gdf.json"
print("Path exists:", os.path.exists(file_path))
print("Absolute Path:", os.path.abspath(file_path))

# Neo4j connection details
NEO4J_URI = os.getenv("URI")
NEO4J_USERNAME = os.getenv("USERNAME")
NEO4J_PASSWORD = os.getenv("PWD")
DATABASE_NAME = "providersdb"  # Specify the database

# Load JSON file
with open(json_file, "r") as f:
    data = json.load(f)

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Function to update location information
def update_location(tx, website, latitude, longitude):
    tx.run(
        """
        MATCH (provider:schema1__Organization {schema1__url: $website})
        SET provider.schema1__latitude = $latitude,
            provider.schema1__longitude = $longitude
        """,
        website=website,
        latitude=latitude,
        longitude=longitude,
    )

# Process each feature in the JSON file
with driver.session(database=DATABASE_NAME) as session:  # Explicitly specify the database
    for feature in tqdm(data["features"], desc="Updating locations"):
        properties = feature["properties"]
        website = properties.get("website")
        latitude = properties.get("latitude")
        longitude = properties.get("longitude")

        # Skip entries without a website, latitude, or longitude
        if not website or latitude is None or longitude is None:
            continue

        # Update location in Neo4j
        session.write_transaction(update_location, website, latitude, longitude)

print("Locations successfully updated in Neo4j.")

# Close the driver
driver.close()
