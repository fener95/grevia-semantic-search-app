from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS
import json
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from tqdm import tqdm
from collections import Counter

# Define Namespaces
schema1 = Namespace("http://schema.org/")
custom = Namespace("http://example.org/custom/")
specialties = Namespace("http://example.org/specialties/")  # Updated for specialties
ns2 = Namespace("http://example.org/embedding#")

# Load the extracted specialties and embeddings
input_data_file = r"C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/providers_embeddings.json"
with open(input_data_file, "r") as f:
    data = json.load(f)

specialty_uris = data["specialty_uris"]
embeddings = data["embeddings"]

X = np.array(embeddings)
print(f"Loaded {len(specialty_uris)} specialties with embeddings.")
print(f"Embedding matrix shape: {X.shape}")

# Standardize the embeddings
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Determine the optimal number of macrocategories using the Elbow Method
inertia = []
K = range(3, 13)  # Focus on your expected range of 3-12
for k in K:
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(X_scaled)
    inertia.append(kmeans.inertia_)

plt.figure(figsize=(10, 6))
plt.plot(K, inertia, 'bx-')
plt.xlabel('Number of clusters (k)')
plt.ylabel('Inertia')
plt.title('Elbow Method For Optimal k')
plt.xticks(K)
plt.grid(True)
plt.show()

# Based on the Elbow plot, choose k=6
num_macrocategories = 6
print(f"Selected number of macrocategories: {num_macrocategories}")

# Perform K-Means clustering for macrocategories
kmeans_macro = KMeans(n_clusters=num_macrocategories, random_state=42)
macro_labels = kmeans_macro.fit_predict(X_scaled)

# Perform microcategory clustering within each macrocategory
micro_labels = {}
num_micro_per_macro = 8  # Adjust as needed or based on your predefined microcategories

for macro in range(num_macrocategories):
    indices = np.where(macro_labels == macro)[0]
    if len(indices) >= num_micro_per_macro:
        kmeans_micro = KMeans(n_clusters=num_micro_per_macro, random_state=42)
        micro_sub_labels = kmeans_micro.fit_predict(X_scaled[indices])
        micro_labels.update({idx: sub for idx, sub in zip(indices, micro_sub_labels)})
    else:
        micro_labels.update({idx: None for idx in indices})

# Load and update the Knowledge Graph (KG)
input_kg_file = r"C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/providersKG_normalized.ttl"
graph = Graph()
graph.parse(input_kg_file, format="turtle")

# Bind namespaces for easier reference
graph.bind("schema1", schema1)
graph.bind("custom", custom)
graph.bind("specialties", specialties)
graph.bind("ns2", ns2)

# Add Macrocategories
macro_uris = []
for m in range(num_macrocategories):
    macro_uri = URIRef(f"http://example.org/specialties/macrocategory_{m}")
    macro_uris.append(macro_uri)
    if (macro_uri, RDF.type, specialties.Macrocategory) not in graph:
        graph.add((macro_uri, RDF.type, specialties.Macrocategory))

# Function to Assign Meaningful Names to Macrocategories with Stopword Exclusion
def assign_macrocategory_names(graph, macro_labels, specialty_uris, num_macrocategories):
    macro_names = {}
    
    # Define a custom list of stopwords to exclude
    stopwords = set([
        'and', 'the', 'of', 'in', 'for', 'to', 'with', 'on', 'by', 'a', 'an', 'related', 'are', 'is'
    ])
    
    for m in range(num_macrocategories):
        # Get all specialties in this macro cluster
        cluster_specialties = [
            uri for label, uri in zip(macro_labels, specialty_uris) if label == m
        ]
        
        # Get the rdf:value for each specialty
        specialty_values = []
        for s in cluster_specialties:
            for o in graph.objects(URIRef(s), RDF.value):
                specialty_values.append(str(o))
        
        # Find the most common words or terms in the specialties, excluding stopwords
        word_counts = Counter()
        for val in specialty_values:
            # Replace underscores with spaces and split into words
            words = val.replace('_', ' ').split()
            # Convert words to lowercase for uniformity
            words = [word.lower() for word in words]
            # Update word counts, excluding stopwords
            filtered_words = [word for word in words if word not in stopwords]
            word_counts.update(filtered_words)
        
        # Assign the most common word as the macrocategory name
        if word_counts:
            common_word, _ = word_counts.most_common(1)[0]
            # Capitalize the first letter and append '-related' for clarity
            macro_names[m] = f"{common_word.capitalize()}-related"
        else:
            macro_names[m] = f"Macrocategory {m}"
    
    return macro_names

# Assign meaningful names
macro_names = assign_macrocategory_names(graph, macro_labels, specialty_uris, num_macrocategories)

# Update Macrocategory nodes with meaningful names
for m in range(num_macrocategories):
    macro_uri = URIRef(f"http://example.org/specialties/macrocategory_{m}")
    meaningful_name = macro_names[m]
    # Remove existing label if any
    graph.remove((macro_uri, RDFS.label, None))
    # Add new meaningful label
    graph.add((macro_uri, RDFS.label, Literal(meaningful_name)))

# Create Microcategory Nodes and Link Specialties
print("Linking Specialties to Macrocategories and Microcategories...")
microcategory_uris = {}

for idx, macro in enumerate(macro_labels):
    specialty_uri = URIRef(specialty_uris[idx])
    macro_uri = URIRef(f"http://example.org/specialties/macrocategory_{macro}")
    
    # Link specialty to macrocategory
    graph.add((specialty_uri, specialties.belongsToMacrocategory, macro_uri))
    
    # Link to microcategory if applicable
    if idx in micro_labels and micro_labels[idx] is not None:
        micro_label = micro_labels[idx]
        micro_key = (macro, micro_label)
        
        # Ensure each microcategory is created only once
        if micro_key not in microcategory_uris:
            micro_uri = URIRef(f"http://example.org/specialties/microcategory_{macro}_{micro_label}")
            microcategory_uris[micro_key] = micro_uri
            if (micro_uri, RDF.type, specialties.Microcategory) not in graph:
                graph.add((micro_uri, RDF.type, specialties.Microcategory))
                graph.add((micro_uri, specialties.belongsToMacrocategory, macro_uri))
                # Assign a basic label; can be enhanced manually later
                graph.add((micro_uri, RDFS.label, Literal(f"Microcategory {macro}_{micro_label}")))
        
        # Link specialty to its microcategory
        micro_uri = microcategory_uris[micro_key]
        graph.add((specialty_uri, specialties.isSpecializedIn, micro_uri))

# Link Companies to Macrocategories and Microcategories
print("Linking Companies to Macrocategories and Microcategories...")
for company in tqdm(graph.subjects(RDF.type, schema1.Organization), desc="Linking Companies"):
    # Get all specialties of the company
    company_specialties = list(graph.objects(company, custom.hasSpecialty))
    for specialty in company_specialties:
        # Get macrocategory
        for macro in graph.objects(specialty, specialties.belongsToMacrocategory):
            graph.add((company, custom.hasMacrocategory, macro))
        # Get microcategory
        for micro in graph.objects(specialty, specialties.isSpecializedIn):
            graph.add((company, custom.hasMicrocategory, micro))

# Save updated KG
output_kg_file = r"C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/providersKG_with_clusters.ttl"
graph.serialize(destination=output_kg_file, format="turtle")
print(f"Updated KG with clusters saved to {output_kg_file}")


# After saving the updated KG and assigning macro & micro categories, visualize them with PCA

# Redo a PCA for visualization
pca_post = PCA(n_components=2)
X_pca_post = pca_post.fit_transform(X_scaled)

plt.figure(figsize=(12, 8))
scatter = plt.scatter(X_pca_post[:, 0], X_pca_post[:, 1], c=macro_labels, cmap='tab10', alpha=0.7)

# Create a legend for macrocategories using the assigned macro_names
handles, _ = scatter.legend_elements()
legend_labels = [macro_names[m] for m in range(num_macrocategories)]
plt.legend(handles, legend_labels, title="Macrocategories", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.title("PCA of Specialties Embeddings with Assigned Macrocategories")
plt.xlabel("PCA Component 1")
plt.ylabel("PCA Component 2")
plt.tight_layout()
plt.show()

# (Optional) If you want to also visualize microcategories per macrocategory, you'd need a more elaborate plot:
# For example, you could assign different markers or use a small multiple plot per macrocategory.
# But as a first step, this PCA with macrocategories should suffice.


