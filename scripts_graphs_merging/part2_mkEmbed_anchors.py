import os
import json
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
import numpy as np

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

# Prepare a dictionary to store the embeddings
macro_anchors_embeddings = {}

for macro_name, anchors in tqdm(macro_anchors.items(), desc="Embedding Macro Anchors"):
    # Embed all anchors at once
    anchor_embeddings = embedding_model.embed_documents(anchors)
    
    # Compute average embedding for the macrocategory
    avg_embedding = np.mean(anchor_embeddings, axis=0).tolist()
    
    # Store both anchor embeddings and the average macro embedding
    macro_anchors_embeddings[macro_name] = {
        "anchors": anchors,
        "anchor_embeddings": anchor_embeddings,
        "macro_avg_embedding": avg_embedding
    }

# Save the macro anchors embeddings to a JSON file
output_file = "macro_anchors_with_avg_embeddings.json"
with open(output_file, "w") as f:
    json.dump(macro_anchors_embeddings, f, indent=2)

print(f"Macro anchors with average embeddings saved to {output_file}")
