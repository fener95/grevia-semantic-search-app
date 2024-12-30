import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase
import os
import numpy as np
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
import json

# Load environment variables
load_dotenv()

# OpenAI API setup using langchain-openai
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI API key not set. Please set the OPENAI_API_KEY environment variable.")

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=openai_api_key,
    dimensions=512
)

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# Function to embed query using langchain-openai
def embed_query(query):
    return embedding_model.embed_query(query)

# Function to calculate cosine similarity
def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Function to find top providers based on query
def find_top_providers(query_embedding, top_k=5):
    query = """
    MATCH (provider:schema1__Organization)
    OPTIONAL MATCH (provider)-[:custom__hasSpecialty]->(specialty:specialties__Specialty)
    RETURN provider.schema1__name AS name,
           provider.schema1__url AS url,
           provider.schema1__description AS description,
           specialty.ns2__embedding_value AS embedding
    """
    with driver.session(database=DATABASE_NAME) as session:
        results = session.run(query)

        matches = []
        for record in results:
            if record["embedding"]:
                specialty_embedding = json.loads(record["embedding"])
                similarity = cosine_similarity(query_embedding, specialty_embedding)
                matches.append((similarity, record["name"], record["url"]))

        # Sort matches by similarity and return top_k results
        matches = sorted(matches, key=lambda x: x[0], reverse=True)[:top_k]
        return matches

# Streamlit app
st.title("Farmer's Semantic Search")
st.write("Describe your challenge or need in up to 75 words.")

# Input query
query = st.text_area("Enter your query:", max_chars=100)

if st.button("Find Providers"):
    if query:
        st.write("Embedding your query...")
        query_embedding = embed_query(query)

        st.write("Searching for providers...")
        top_providers = find_top_providers(query_embedding)

        if top_providers:
            st.write("Top matching providers:")
            for idx, (similarity, name, url) in enumerate(top_providers, start=1):
                st.markdown(f"**{idx}. {name}**")
                st.markdown(f"- [Website]({url})")
                st.markdown(f"  Similarity Score: {similarity:.4f}")
        else:
            st.write("No matching providers found.")
    else:
        st.error("Please enter a query.")
