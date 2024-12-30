import os
directory = "C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data"
print("Files in directory:", os.listdir(directory))
with open("C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/JSONLike_gdf.json", "r") as f:
    print(f.read(100))  # Read the first 100 characters
