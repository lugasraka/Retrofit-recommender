import streamlit as st
import json
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# 1. PAGE CONFIG
st.set_page_config(page_title="Siemens Eco-Fix (Hugging Face)", layout="wide")
st.title("🏭 Siemens Eco-Fix: Hugging Face Edition")
st.markdown("""
**Architecture:** `LangChain` + `Hugging Face Inference API` (Free Tier).
*Demonstrates utilizing the world's largest open-source model hub for rapid prototyping.*
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

# 3. MOCK CATALOG
catalog_data = [
    {"sku": "VVF43.65-OLD", "name": "Legacy Valve Gen1", "specs": "PN16, DN65", "status": "Obsolete"},
    {"sku": "VVF53.65-ECO", "name": "Acvatix Eco-Line Valve", "specs": "PN25, DN65, High Efficiency", "status": "Available", "price": "€450"},
    {"sku": "SAX61.03", "name": "Actuator 24V", "specs": "24V, 0-10V Signal", "status": "Available", "price": "€120"},
    {"sku": "SAX31.00", "name": "Actuator 230V", "specs": "230V, 3-point Signal", "status": "Available", "price": "€115"}
]

# 4. DEFINE OUTPUT STRUCTURE
class ProductRecommendation(BaseModel):
    diagnosis: str = Field(description="Technical diagnosis of the fault")
    product_name: str = Field(description="Name of the recommended product")
    sku: str = Field(description="SKU of the recommended product")
    reason: str = Field(description="Reason for recommendation")
    safety_alert: str = Field(description="Safety warning if voltage/pressure mismatch, else 'None'")
    price: str = Field(description="Price of the item")

# 5. UI INPUTS
scenario = st.selectbox("Scenario:", ["Scenario A: Efficiency Upgrade", "Scenario B: Safety Risk"])

input_error = "Alert 404: Pump overworking. Flow resistance high." if "Scenario A" in scenario else "Actuator failed. Controller output is 230V."
input_device = "Old Valve: VVF43.65 (PN16)" if "Scenario A" in scenario else "Current Setup: 230V Output"

col1, col2 = st.columns(2)
with col1:
    error_desc = st.text_area("Error Log", value=input_error)
with col2:
    device_context = st.text_area("Device Specs", value=input_device)

# 6. AI LOGIC
if st.button("Analyze with Hugging Face"):
    if not hf_token:
        st.error("Please enter a Hugging Face Token.")
    else:
        try:
            with st.spinner("Calling Hugging Face API (Llama-3.1-8B)..."):
                
                # SETUP HUGGING FACE ENDPOINT
                # Using Meta's Llama-3.1-8B model
                repo_id = "meta-llama/Llama-3.1-8B"
                
                llm = HuggingFaceEndpoint(
                    repo_id=repo_id,
                    max_new_tokens=512,
                    temperature=0.1, # Keep it low for factual accuracy
                    huggingfacehub_api_token=hf_token,
                    task="text-generation"
                )

                # PARSER & PROMPT
                parser = JsonOutputParser(pydantic_object=ProductRecommendation)
                
                prompt = PromptTemplate(
                    template="""You are a Siemens Technical Assistant. Analyze the error and device context, then recommend the EXACT product from the catalog that matches the requirements.

CATALOG:
{catalog}

ERROR LOG: {error}
CURRENT DEVICE: {device}

CRITICAL MATCHING RULES:
1. For actuator failures with 230V controller output → Recommend "SAX31.00" (Actuator 230V)
2. For actuator failures with 24V controller output → Recommend "SAX61.03" (Actuator 24V)
3. For valve efficiency upgrades → Recommend "VVF53.65-ECO" (Acvatix Eco-Line Valve)
4. VOLTAGE MISMATCH = SAFETY ALERT: If controller voltage doesn't match actuator voltage, issue a safety warning
5. Use EXACT product names and SKUs from the catalog above

{format_instructions}

Return ONLY the JSON object with no extra text:""",
                    input_variables=["catalog", "error", "device"],
                    partial_variables={"format_instructions": parser.get_format_instructions()},
                )

                # RUN CHAIN
                chain = prompt | llm
                raw_output = chain.invoke({
                    "catalog": json.dumps(catalog_data),
                    "error": error_desc,
                    "device": device_context
                })
                
                # Try to parse the output
                try:
                    result = parser.parse(raw_output)
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