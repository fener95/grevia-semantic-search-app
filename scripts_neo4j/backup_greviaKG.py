import os
import shutil
from datetime import datetime

# Paths
neo4j_data_path = r"C:\Users\Utente\.Neo4jDesktop\relate-data\dbmss\dbms-f4acfeb5-9195-427b-b2ca-7f385fffaab4\data\databases\greviakg"
backup_dir = r"C:\Users\Utente\neo4j-projects\grevia-project-neo4j\backups"

# Timestamped backup folder
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"greviakg_backup_{timestamp}")

# Copy the database folder
if os.path.exists(neo4j_data_path):
    shutil.copytree(neo4j_data_path, backup_path)
    print(f"Backup completed: {backup_path}")
else:
    print("Neo4j database folder not found.")
