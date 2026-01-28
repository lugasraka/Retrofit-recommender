import streamlit as st
import json
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re

# Load environment variables
load_dotenv()

# 1. PAGE CONFIG
st.set_page_config(page_title="Retrofit Recommender (Hugging Face)", layout="wide")
st.title("🏭 Retrofit Recommender: Hugging Face Edition")
st.markdown("""
**Architecture:** `LangChain` + `Hugging Face Inference API` (Free Tier) + `RAG with FAISS`.
*Demonstrates utilizing the world's largest open-source model hub with expert knowledge retrieval.*
""")

# 2. SIDEBAR - API KEY INPUT
st.sidebar.header("Configuration")

# Try to load token from .env file first
default_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
if default_token and default_token != "your_token_here":
    st.sidebar.success("✓ Token loaded from .env file")
    hf_token = default_token
else:
    hf_token = st.sidebar.text_input("Enter Hugging Face Token (hf_...)", type="password")
    st.sidebar.caption("Get one for free at huggingface.co/settings/tokens")
    st.sidebar.info("💡 Tip: Store your token in the .env file to avoid entering it each time")

# 3. LOAD CATALOG
@st.cache_data
def load_catalog():
    """Load product catalog from JSON file"""
    catalog_path = os.path.join(os.path.dirname(__file__), "catalog.json")
    with open(catalog_path, 'r') as f:
        return json.load(f)

catalog_data = load_catalog()

# Show catalog stats in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📦 Product Catalog")
st.sidebar.metric("Total Products", len(catalog_data))
available_count = sum(1 for item in catalog_data if item['status'] == 'Available')
st.sidebar.metric("Available", available_count)

# 3.5. LOAD KNOWLEDGE BASE WITH VECTOR SEARCH
@st.cache_resource
def load_knowledge_base():
    """Load knowledge base and create FAISS index"""
    kb_path = os.path.join(os.path.dirname(__file__), "knowledge_base.txt")
    with open(kb_path, 'r') as f:
        content = f.read()
    
    # Split into sections
    sections = []
    for section in content.split('\n## '):
        if section.strip():
            if not section.startswith('#'):
                section = '## ' + section
            sections.append(section.strip())
    
    # Create embeddings (force CPU to avoid CUDA compatibility issues)
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    embeddings = model.encode(sections)
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings.astype('float32'))
    
    return sections, index, model

kb_sections, kb_index, kb_model = load_knowledge_base()

def retrieve_knowledge(query, top_k=3):
    """Retrieve relevant knowledge sections for the query"""
    query_embedding = kb_model.encode([query])
    distances, indices = kb_index.search(query_embedding.astype('float32'), top_k)
    return [kb_sections[i] for i in indices[0]]

# 4. DEFINE OUTPUT STRUCTURE
class ProductRecommendation(BaseModel):
    diagnosis: str = Field(description="Technical diagnosis of the fault")
    product_name: str = Field(description="Name of the recommended product")
    sku: str = Field(description="SKU of the recommended product")
    reason: str = Field(description="Reason for recommendation")
    safety_alert: str = Field(description="Safety warning if voltage/pressure mismatch, else 'None'")
    price: str = Field(description="Price of the item")

# Helper function for JSON extraction
def extract_json(text):
    """Extract JSON object from text that may contain extra content"""
    # Find JSON object pattern
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return text

# 5. UI INPUTS
scenarios = {
    "Valve Efficiency Upgrade": {
        "error": "Alert 404: Pump overworking. Flow resistance high. Energy consumption 15% above baseline.",
        "device": "Old Valve: VVF43.65 (PN16, DN65)"
    },
    "Actuator Voltage Mismatch": {
        "error": "Actuator failed. Controller output is 230V but actuator requires 24V. Safety shutdown triggered.",
        "device": "Current Setup: 230V Controller Output, 24V Actuator (Mismatch)"
    },
    "Sensor Drift/Inaccuracy": {
        "error": "Temperature readings inconsistent. Sensor drift detected. Readings vary ±3°C from reference.",
        "device": "Current Sensor: QAE2120.010 (installed 2018)"
    },
    "Controller Upgrade Needed": {
        "error": "Legacy controller lacks Modbus support. Cannot integrate with BMS. Manual operation required.",
        "device": "Current Controller: RWD62 (no network capability)"
    },
    "Preventive Maintenance": {
        "error": "No error. System running for 5 years without maintenance. Performance degradation observed.",
        "device": "Full System: 8 valves, 8 actuators, 12 sensors, 1 controller"
    },
    "Complete System Optimization": {
        "error": "Energy consumption high. Manual control inefficient. Need automated optimization.",
        "device": "Mixed legacy system: 15+ year old components, no centralized control"
    },
    "Pressure Sensor Failure": {
        "error": "Pressure sensor out of range. Differential pressure not measurable. System bypass active.",
        "device": "Current Setup: No functional pressure measurement"
    }
}

scenario = st.selectbox("Select Scenario:", list(scenarios.keys()))
scenario_data = scenarios[scenario]

input_error = scenario_data["error"]
input_device = scenario_data["device"]

st.text_area("Error/Issue Description:", value=input_error, height=80, key="error")
st.text_area("Current Device Info:", value=input_device, height=80, key="device")

if st.button("🔍 Analyze & Recommend", use_container_width=True):
    with st.spinner("Analyzing scenario with expert knowledge..."):
        try:
            error_desc = st.session_state.error
            device_context = st.session_state.device
            
            # Retrieve relevant knowledge
            query = f"{error_desc} {device_context}"
            relevant_knowledge = retrieve_knowledge(query, top_k=3)
            knowledge_context = "\n\n".join(relevant_knowledge)
            
            # INITIALIZE LLM
            parser = JsonOutputParser(pydantic_object=ProductRecommendation)
            llm = HuggingFaceEndpoint(
                repo_id="meta-llama/Llama-3.1-8B",
                task="text-generation",
                max_new_tokens=300,
                temperature=0.05,
                top_p=0.95,
                repetition_penalty=1.1,
                huggingfacehub_api_token=hf_token
            )
            
            prompt = PromptTemplate(
                template="""You are an industrial equipment specialist with expert knowledge. Use the provided expert knowledge to make accurate recommendations.

EXPERT KNOWLEDGE (Use this to guide your recommendation):
{knowledge}

PRODUCT CATALOG:
{catalog}

CURRENT SITUATION:
Error/Issue: {error}
Existing Device: {device}

INSTRUCTIONS:
1. Review the expert knowledge above for guidance on this type of issue
2. Identify the root cause and follow expert recommendations
3. Select the exact product/service/bundle from the catalog by SKU
4. For voltage mismatches, ALWAYS issue a safety alert
5. Use exact names and SKUs from the catalog

OUTPUT FORMAT:
{format_instructions}

Return ONLY the JSON object:""",
                input_variables=["knowledge", "catalog", "error", "device"],
                partial_variables={"format_instructions": parser.get_format_instructions()},
            )
            
            # RUN CHAIN
            chain = prompt | llm
            raw_output = chain.invoke({
                "knowledge": knowledge_context,
                "catalog": json.dumps(catalog_data),
                "error": error_desc,
                "device": device_context
            })
            
            # Try to parse the output
            try:
                cleaned_output = extract_json(raw_output)
                result = parser.parse(cleaned_output)
            except Exception as parse_error:
                # Show the raw output for debugging
                st.error(f"JSON parsing failed: {parse_error}")
                with st.expander("Show raw model output for debugging"):
                    st.code(raw_output)
                raise

            # DISPLAY RESULTS
            st.success("Analysis Complete")
            
            st.info(f"**Diagnosis:** {result['diagnosis']}")
            
            if result['safety_alert'] != "None":
                st.error(f"⚠️ {result['safety_alert']}")
            
            st.subheader("🛒 Recommendation")
            c1, c2 = st.columns([1, 3])
            with c2:
                st.markdown(f"### {result['product_name']}")
                st.caption(f"SKU: {result['sku']}")
                st.write(result['reason'])
                st.metric("Price", result['price'])

        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("Note: Free tier models may time out if the server is busy. Try clicking 'Analyze' again.")
