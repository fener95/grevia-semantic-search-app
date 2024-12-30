import os
import json
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings
import folium
from streamlit_folium import st_folium

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

# Query Neo4j for providers and their embeddings
def find_top_providers(query_embedding, top_k=5):
    query = """
    MATCH (provider:schema1__Organization)
    OPTIONAL MATCH (provider)-[:custom__hasSpecialty]->(specialty:specialties__Specialty)
    RETURN provider.schema1__name AS name,
           provider.schema1__url AS url,
           provider.schema1__description AS description,
           provider.schema1__latitude AS lat,
           provider.schema1__longitude AS lon,
           specialty.ns2__embedding_value AS embedding
    """
    with driver.session(database=DATABASE_NAME) as session:
        results = session.run(query)

        matches_dict = {}
        # Aggregate results by provider name since a provider can have multiple specialties
        for record in results:
            name = record["name"]
            url = record["url"]
            lat = record["lat"]
            lon = record["lon"]
            embedding = record["embedding"]

            if name not in matches_dict:
                matches_dict[name] = {
                    "url": url,
                    "lat": lat,
                    "lon": lon,
                    "similarities": []
                }

            if embedding:
                try:
                    specialty_embedding = json.loads(embedding)
                    sim = cosine_similarity(query_embedding, specialty_embedding)
                    matches_dict[name]["similarities"].append(sim)
                except json.JSONDecodeError:
                    continue

        # Compute the best similarity per provider (the highest among its specialties)
        provider_scores = []
        for name, info in matches_dict.items():
            if info["similarities"]:
                best_sim = max(info["similarities"])
            else:
                # If no specialties or embeddings, skip or consider sim=0
                best_sim = 0.0
            provider_scores.append((best_sim, name, info["url"], info["lat"], info["lon"]))

        # Sort and return top_k
        provider_scores = sorted(provider_scores, key=lambda x: x[0], reverse=True)[:top_k]
        return provider_scores

# Initialize session state variables
if "top_providers" not in st.session_state:
    st.session_state.top_providers = None

if "query" not in st.session_state:
    st.session_state.query = ""

# Set page config and add custom CSS
st.set_page_config(page_title="GREVIA's Prototype", page_icon="🌱", layout="wide")
st.markdown("""
    <style>
    /* Custom styling */
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

# App Title and Subtitle
st.markdown('<h1 class="title">GREVIA\'s Prototype</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Find the best solution providers for your agricultural needs</p>', unsafe_allow_html=True)

# Input query
query = st.text_area("Enter your challenge or need (up to 100 words):", 
                     max_chars=100, 
                     height=100, 
                     key="input_query")

# Button to trigger search
col1, col2, col3 = st.columns([1,1,1])
with col2:
    search_button = st.button("Find Providers")

# Handle search button click
if search_button:
    if query.strip():
        st.session_state.query = query
        with st.spinner("Understanding your request..."):
            query_embedding = embed_query(query)
            top_providers = find_top_providers(query_embedding)
            st.session_state.top_providers = top_providers
    else:
        st.error("Please enter a query.")

# Display results if available
if st.session_state.top_providers is not None and st.session_state.query.strip():
    top_providers = st.session_state.top_providers

    # Extract coordinates for map centering
    coords = [(p[3], p[4]) for p in top_providers if p[3] is not None and p[4] is not None]
    if coords:
        avg_lat = np.mean([c[0] for c in coords])
        avg_lon = np.mean([c[1] for c in coords])
    else:
        # Default location if no coords available
        avg_lat = 0
        avg_lon = 0

    # Create a folium map
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=2)

    for idx, (similarity, name, url, lat, lon) in enumerate(top_providers, start=1):
        # Add marker to map if coordinates are available
        if lat is not None and lon is not None:
            popup_html = f"""
            <b>{name}</b><br>
            Similarity: {similarity:.4f}<br>
            <a href="{url}" target="_blank">Website</a>
            """
            folium.Marker(
                [lat, lon], 
                popup=folium.Popup(popup_html, max_width=200),
                tooltip=name
            ).add_to(m)

    # Display the map at the top
    st.markdown("### Map of Providers")
    st_folium(m, width=700, height=500)

    # Display the list of providers below the map
    st.markdown("### Top Matching Providers")
    for idx, (similarity, name, url, lat, lon) in enumerate(top_providers, start=1):
        st.markdown(f'<div class="provider-card">', unsafe_allow_html=True)
        st.markdown(f"<h4>{idx}. {name}</h4>", unsafe_allow_html=True)
        st.markdown(f'<p class="score">Similarity Score: {similarity:.4f}</p>', unsafe_allow_html=True)
        if url:
            st.markdown(f"- [Website]({url})")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Enter a query and click 'Find Providers' to see results.")
