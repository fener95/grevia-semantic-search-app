import os
import json
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings

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

# Set page config and add custom CSS
st.set_page_config(page_title="Farmer's Semantic Search", page_icon="🌱", layout="wide")
st.markdown("""
    <style>
    /* Add some custom styling */
    body {
        background: #f9f9f9;
        color: #333333;
        font-family: "Helvetica Neue", sans-serif;
    }
    .title {
        text-align: center;
        color: #2C5F2D;
        font-weight: 600;
        font-size: 2.5rem;
        margin-bottom: 0.5em;
    }
    .subtitle {
        text-align: center;
        color: #4B8B3B;
        font-size: 1.2rem;
        margin-bottom: 1em;
    }
    .stTextArea textarea {
        background: #ffffff;
        border: 1px solid #4B8B3B;
        color: #000000 !important;
    }
    .stButton button {
        background-color: #4B8B3B !important;
        color: #ffffff !important;
        border: none;
        border-radius: 5px;
        font-weight: 600;
    }
    .provider-card {
        background: #ffffff;
        border: 1px solid #4B8B3B20;
        border-radius: 8px;
        padding: 1em;
        margin-bottom: 0.5em;
    }
    .provider-card h4 {
        color: #2C5F2D;
        margin: 0;
    }
    .score {
        font-size: 0.9rem;
        color: #555555;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">GREVIA\'s Prototype</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Find the best solution providers for your agricultural needs</p>', unsafe_allow_html=True)

# Input query
query = st.text_area("Enter your challenge or need (up to 100 words):", max_chars=100, height=100)

col1, col2, col3 = st.columns([1,1,1])
with col2:
    search_button = st.button("Find Providers")

if search_button:
    if query.strip():
        with st.spinner("Understanding your request..."):
            query_embedding = embed_query(query)
            top_providers = find_top_providers(query_embedding)

        if top_providers:
            st.markdown("### Top Matching Providers")
            for idx, (similarity, name, url) in enumerate(top_providers, start=1):
                st.markdown(f'<div class="provider-card">', unsafe_allow_html=True)
                st.markdown(f"<h4>{idx}. {name}</h4>", unsafe_allow_html=True)
                st.markdown(f'<p class="score">Similarity Score: {similarity:.4f}</p>', unsafe_allow_html=True)
                if url:
                    st.markdown(f"- [Website]({url})")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("No matching providers found.")
    else:
        st.error("Please enter a query.")

#streamlit run
