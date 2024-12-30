import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS

# Load the normalized KG
input_file = "C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/providersKG_normalized.ttl"
output_file = "providersKG_with_microcategories.ttl"

graph = Graph()
graph.parse(input_file, format="turtle")

# Define Namespaces
specialties = Namespace("http://example.org/specialties/")
custom = Namespace("http://example.org/custom/")
schema1 = Namespace("http://schema.org/")
ns2 = Namespace("http://example.org/embedding#")

graph.bind("specialties", specialties)
graph.bind("custom", custom)
graph.bind("schema1", schema1)
graph.bind("ns2", ns2)

# Load the specialty to microcategory assignments
assignment_file = "C:/Users/Utente/neo4j-projects/grevia-project-neo4j/import_data/specialty_to_microcategory_assignment.json"
with open(assignment_file, "r") as f:
    assignments = json.load(f)

# Load macrocategory and microcategory anchors
macro_anchors = {
  "Agriculture & Crop Management": [
    "agriculture", "crop", "farming", "precision agriculture", "agtech",
    "crop breeding", "trait genomics", "plant innate immunity", "resistance management",
    "vertical farming", "mixed cropping", "cover crop", "winter soil cover", "no_till"
  ],
  "Soil Health & Regenerative Practices": [
    "soil", "regenerative", "conservation", "biofertilizer", "biostimulant",
    "soil health", "soil fertility", "biopesticides", "biofertilizers", 
    "microbial inoculant", "organic fertilization", "composting", "mineral amendments",
    "enhanced rock weathering", "agroecology", "organic farming", "improved manure management and storage"
  ],
  "Carbon Capture & Climate Solutions": [
    "carbon", "ccu", "net zero", "climate", 
    "carbon capture", "carbon removal", "direct air capture", "carbon dioxide removal",
    "ghg emissions reduction", "nature based solution", "cds", "neg_emission_tech"
  ],
  "Biotech & Bio-based Innovations": [
    "biotech", "microalgae", "synthetic biology", "fermentation", "gene editing",
    "insect protein", "cultured meat", "next_generation_sequencing_analysis"
  ],
  "Precision & Data-Driven Tools": [
    "big data", "iot sensors", "remote sensing", "data modeling", "blockchain",
    "mrv platform", "carbon accounting", "variable_rate_application", "traceability"
  ],
  "Food & Feed Processing": [
    "food technology", "alternative proteins", "fermentation", 
    "cultured meat", "prebiotics", "functional foods", "probiotics",
    "organic food", "improved shelf-life", "processing innovation", "feed additives for enteric fermentation reduction"
  ],
  "Environmental & Ecosystem Management": [
    "ecosystem", "biodiversity", "deforestation monitoring", "reforestation", 
    "high nature value farming", "landscape features", "semi-natural habitat creation",
    "agro-forestry", "buffer strips", "pollinator habitats", "minimum water table level in peatland"
  ],
  "Biochar": [
    "biochar", "charcoal soil amendment", "pyrolysis", "carbonized biomass"
  ],
  "Seabed": [
    "seabed", "marine sediment", "ocean floor", "blue carbon", "coastal ecosystems"
  ],
  "Education & Financial Support": [
    "education", "training", "capacity building", "financial support", "funding", "investment"
  ],
  "Carbon Data Tools": [
    "carbon data", "ghg monitoring", "data quality verification",
    "carbon measurement", "quantifying carbon"
  ],
  "Carbon Credits": [
    "carbon credits", "offset markets", "carbon certification", "verra", "gold standard"
  ],
  "Husbandry & Animal Welfare": [
    "animal welfare", "antimicrobial resistance control", "free farrowing",
    "improved housing conditions", "feeding plans", "biosecurity", "open air access",
    "breed resilience"
  ],
  "Agro-forestry": [
    "silvo-pastoral systems", "forest farming", "trees_in_pasture", "agroforestry systems"
  ],
  "Carbon Farming": [
    "carbon farming", "conservation agriculture", "peatland rewetting", 
    "permanent grassland", "extensive grass-based system", "soil carbon sequestration"
  ],
  "Protecting Water Resources": [
    "protecting water quality", "managing crop water demand", "improving irrigation efficiency",
    "avoiding nutrient runoff"
  ],
  "Renewable Energy & Circular Bioeconomy": [
    "green energy", "biogas", "waste_to_energy", "circular economy", "bio_refinery",
    "biofuel", "renewable feedstocks"
  ],
  "Organic & Agro-ecological Farming": [
    "organic conversion", "maintenance of organic farming",
    "integrated pest management", "buffer strips without pesticide",
    "paludiculture", "mix species sward", "ecological_farming"
  ],
  "Improved Nutrient Management": [
    "nutrient traps", "optimal pH management", "soil sampling beyond mandatory",
    "circular nutrient use"
  ]
}
# Create Macrocategory Nodes
macro_uris = {}
for macro_name in macro_anchors:
    macro_uri = URIRef(f"http://example.org/specialties/macrocategory/{macro_name.replace(' ', '_')}")
    macro_uris[macro_name] = macro_uri
    if (macro_uri, RDF.type, specialties.Macrocategory) not in graph:
        graph.add((macro_uri, RDF.type, specialties.Macrocategory))
        graph.add((macro_uri, RDFS.label, Literal(macro_name)))

# Create Microcategories and Link to Macrocategories
micro_uris = {}
for specialty_uri, details in assignments.items():
    macro_name = details["macrocategory"]
    micro_anchor = details["microcategory_anchor"]
    macro_uri = macro_uris[macro_name]

    # Create Microcategory URI
    micro_uri = URIRef(f"http://example.org/specialties/microcategory/{micro_anchor.replace(' ', '_')}")
    if micro_uri not in micro_uris:
        micro_uris[micro_anchor] = micro_uri
        if (micro_uri, RDF.type, specialties.Microcategory) not in graph:
            graph.add((micro_uri, RDF.type, specialties.Microcategory))
            graph.add((micro_uri, RDFS.label, Literal(micro_anchor)))
            # Link Microcategory to Macrocategory
            graph.add((micro_uri, specialties.belongsToMacrocategory, macro_uri))

    # Link Specialty to Microcategory
    specialty_node = URIRef(specialty_uri)
    graph.add((specialty_node, specialties.hasMicrocategory, micro_uri))

# Validate No Grandparent Links (Optional Check)
# Remove any unintended Macrocategory → Specialty links if they exist
for macro_uri in macro_uris.values():
    for specialty in graph.objects(macro_uri, specialties.hasMicrocategory):
        if (specialty, RDF.type, specialties.Specialty) in graph:
            graph.remove((macro_uri, specialties.hasMicrocategory, specialty))

# Save the updated graph
graph.serialize(destination=output_file, format="turtle")
print(f"Updated KG with microcategories saved to {output_file}")
