import streamlit as st
import json
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import re
from sustainability_calculator import SustainabilityCalculator, format_impact_summary
from agent_orchestrator import (
    MasterOrchestrator, DiagnosisAgent, ProductAgent,
    SustainabilityAgent, FinancialAgent, ReportAgent,
    LLMWrapper, AgentStatus
)
import time

# Load environment variables
load_dotenv()

# LLM RETRY LOGIC FOR MODEL WARMING
def call_llm_with_retry(chain, inputs, max_retries=3, initial_delay=10):
    """Call LLM with retry logic for model warming (handles cold start)"""
    for attempt in range(max_retries):
        try:
            return chain.invoke(inputs)
        except Exception as e:
            error_msg = str(e)
            if "model_pending_deploy" in error_msg and attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)  # Exponential backoff: 10s, 20s, 40s
                st.warning(f"⏳ Model warming up... Retrying in {delay} seconds (attempt {attempt + 2}/{max_retries})")
                time.sleep(delay)
            else:
                raise e
    return None

# 1. PAGE CONFIG
st.set_page_config(page_title="Retrofit Recommender - AI Sustainability Platform", layout="wide")
st.title("🏭 Retrofit Recommender: AI-Enabled Sustainability Platform")
st.markdown("""
**AI-Powered Industrial Decarbonization** | `RAG + GenAI` + `CO2e Impact Tracking` + `MLOps Observability`  
*Transform maintenance decisions into measurable sustainability outcomes with explainable AI recommendations.*
""")

# 2. SIDEBAR - CONFIGURATION
st.sidebar.header("⚙️ Configuration")

# API Token
default_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
if default_token and default_token != "your_token_here":
    st.sidebar.success("✓ Token loaded from .env file")
    hf_token = default_token
else:
    hf_token = st.sidebar.text_input("Enter Hugging Face Token (hf_...)", type="password")
    st.sidebar.caption("Get one for free at huggingface.co/settings/tokens")
    st.sidebar.info("💡 Tip: Store your token in the .env file to avoid entering it each time")

# Analysis Mode toggle
st.sidebar.markdown("---")
analysis_mode = st.sidebar.radio(
    "Analysis Mode",
    ["Standard (RAG + LLM)", "Multi-Agent Pipeline (5 Agents)"],
    help="Standard: single LLM call with RAG. Multi-Agent: 5 specialized agents run in sequence."
)

# Sustainability Settings
st.sidebar.markdown("---")
st.sidebar.subheader("🌍 Sustainability Settings")
region = st.sidebar.selectbox(
    "Carbon Intensity Region",
    ["US_AVERAGE", "US_CALIFORNIA", "EU_AVERAGE", "GERMANY", "UK", "GLOBAL_AVERAGE"],
    help="Select your region for accurate CO2e calculations"
)
electricity_rate = st.sidebar.number_input(
    "Electricity Rate ($/kWh)",
    min_value=0.01,
    max_value=0.50,
    value=0.12,
    step=0.01,
    help="Your local electricity cost for ROI calculations"
)

# Initialize sustainability calculator
@st.cache_resource
def get_sustainability_calculator(region, rate):
    return SustainabilityCalculator(region=region, electricity_rate=rate)

sustainability_calc = get_sustainability_calculator(region, electricity_rate)

# 3. LOAD CATALOG
@st.cache_data
def load_catalog():
    """Load product catalog from JSON file"""
    catalog_path = os.path.join(os.path.dirname(__file__), "catalog.json")
    with open(catalog_path, 'r') as f:
        return json.load(f)

catalog_data = load_catalog()

# Show catalog stats and sustainability metrics in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📦 Product Catalog")
st.sidebar.metric("Total Products", len(catalog_data))
available_count = sum(1 for item in catalog_data if item['status'] == 'Available')
st.sidebar.metric("Available", available_count)

# Add KPI tracking section
st.sidebar.markdown("---")
st.sidebar.subheader("📊 KPIs (Demo)")
if 'total_recommendations' not in st.session_state:
    st.session_state.total_recommendations = 0
if 'total_co2e_avoided' not in st.session_state:
    st.session_state.total_co2e_avoided = 0.0
if 'feedback_scores' not in st.session_state:
    st.session_state.feedback_scores = []

st.sidebar.metric("Recommendations", st.session_state.total_recommendations)
st.sidebar.metric("CO2e Avoided (tons)", f"{st.session_state.total_co2e_avoided:.1f}")
if st.session_state.feedback_scores:
    accuracy = (sum(st.session_state.feedback_scores) / len(st.session_state.feedback_scores)) * 100
    st.sidebar.metric("User Satisfaction", f"{accuracy:.0f}%")

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

# Use text_area without fixed keys so values update with scenario selection
input_error = st.text_area("Error/Issue Description:", value=scenario_data["error"], height=80, key=f"error_{scenario}")
input_device = st.text_area("Current Device Info:", value=scenario_data["device"], height=80, key=f"device_{scenario}")

if st.button("🔍 Analyze & Recommend", use_container_width=True):
    start_time = time.time()
    error_desc = input_error
    device_context = input_device

    # FAISS retrieval — runs in both modes (RAG context available to all agents)
    query = f"{error_desc} {device_context}"
    relevant_knowledge = retrieve_knowledge(query, top_k=3)
    knowledge_context = "\n\n".join(relevant_knowledge)
    retrieval_time = time.time() - start_time

    # =========================================================
    # STANDARD MODE
    # =========================================================
    if analysis_mode == "Standard (RAG + LLM)":
        with st.spinner("Analyzing scenario with expert knowledge..."):
            try:
                # INITIALIZE LLM
                parser = JsonOutputParser(pydantic_object=ProductRecommendation)
                llm_start = time.time()
                llm_endpoint = HuggingFaceEndpoint(
                    repo_id="meta-llama/Llama-3.1-8B-Instruct",
                    task="conversational",
                    max_new_tokens=300,
                    temperature=0.05,
                    top_p=0.95,
                    repetition_penalty=1.1,
                    huggingfacehub_api_token=hf_token,
                )
                llm = ChatHuggingFace(llm=llm_endpoint)

                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are an industrial equipment specialist. Always respond with valid JSON containing ALL required fields."),
                    ("human", """EXPERT KNOWLEDGE:
{knowledge}

PRODUCT CATALOG:
{catalog}

CURRENT SITUATION:
Error/Issue: {error}
Existing Device: {device}

INSTRUCTIONS:
1. Diagnose the issue based on expert knowledge
2. Select a product from the catalog that solves this issue
3. Include the price from the catalog (with € symbol)
4. For voltage mismatches, issue a safety alert

You MUST return a JSON object with ALL these fields:
- "diagnosis": technical diagnosis of the fault
- "product_name": exact name from catalog
- "sku": exact SKU from catalog
- "reason": why this product solves the issue
- "safety_alert": safety warning or "None"
- "price": price with € symbol (e.g., "€215")

Return ONLY valid JSON:""")
                ])

                # RUN CHAIN WITH RETRY LOGIC
                chain = prompt | llm
                response = call_llm_with_retry(
                    chain,
                    {
                        "knowledge": knowledge_context,
                        "catalog": json.dumps(catalog_data),
                        "error": error_desc,
                        "device": device_context
                    },
                    max_retries=3,
                    initial_delay=10
                )
                raw_output = response.content if hasattr(response, 'content') else str(response)

                llm_time = time.time() - llm_start
                total_time = time.time() - start_time

                try:
                    cleaned_output = extract_json(raw_output)
                    result = parser.parse(cleaned_output)
                except Exception as parse_error:
                    st.error(f"JSON parsing failed: {parse_error}")
                    with st.expander("Show raw model output for debugging"):
                        st.code(raw_output)
                    raise

                result.setdefault('diagnosis', 'Analysis completed')
                result.setdefault('product_name', 'Unknown Product')
                result.setdefault('sku', 'N/A')
                result.setdefault('reason', 'See diagnosis for details')
                result.setdefault('safety_alert', 'None')
                result.setdefault('price', '€0')

                price_display = result['price'].replace('â,¬', '€').replace('â‚¬', '€')
                price_str = price_display.replace('€', '').replace(',', '').strip()
                try:
                    price_float = float(price_str)
                except Exception:
                    price_float = 1000.0

                equipment_type = "valve"
                efficiency_improvement = 15.0
                runtime = "continuous"
                baseline_power = 50.0

                if "valve" in result['product_name'].lower():
                    equipment_type = "valve"
                    efficiency_improvement = 15.0
                    baseline_power = 50.0
                elif "actuator" in result['product_name'].lower():
                    equipment_type = "actuator"
                    efficiency_improvement = 10.0
                    baseline_power = 30.0
                elif "sensor" in result['product_name'].lower():
                    equipment_type = "sensor"
                    efficiency_improvement = 5.0
                    baseline_power = 10.0
                    runtime = "standard"
                elif "controller" in result['product_name'].lower():
                    equipment_type = "controller"
                    efficiency_improvement = 20.0
                    baseline_power = 100.0
                elif "bundle" in result['product_name'].lower() or "package" in result['product_name'].lower():
                    equipment_type = "valve"
                    efficiency_improvement = 25.0
                    baseline_power = 150.0

                sustainability_impact = sustainability_calc.calculate_full_impact(
                    product_sku=result['sku'],
                    catalog_data=catalog_data,
                    equipment_type=equipment_type,
                    efficiency_improvement_pct=efficiency_improvement,
                    purchase_price=price_float,
                    installation_cost=price_float * 0.15,
                    annual_maintenance_cost=price_float * 0.05,
                    runtime_category=runtime,
                    equipment_lifespan_years=15,
                    baseline_power_kw=baseline_power
                )

                st.session_state.total_recommendations += 1
                st.session_state.total_co2e_avoided += sustainability_impact.co2e_avoided_tons_per_year

                st.success(f"✅ Analysis Complete in {total_time:.2f}s (RAG: {retrieval_time:.2f}s, LLM: {llm_time:.2f}s)")

                tab1, tab2, tab3, tab4 = st.tabs(["📋 Recommendation", "🌱 Sustainability Impact", "💰 Financial Analysis", "🔍 Explainability"])

                with tab1:
                    st.info(f"**Diagnosis:** {result['diagnosis']}")

                    if result['safety_alert'] != "None":
                        st.error(f"⚠️ **SAFETY ALERT:** {result['safety_alert']}")

                    col1, col2 = st.columns([1, 2])
                    with col1:
                        rating_colors = {"A+": "🟢", "A": "🟢", "B+": "🟡", "B": "🟡", "C": "🟠", "D": "🔴"}
                        st.markdown(f"### {rating_colors.get(sustainability_impact.sustainability_rating, '⚪')} Rating: {sustainability_impact.sustainability_rating}")
                        st.metric("Price", price_display)
                        st.metric("Payback Period", f"{sustainability_impact.payback_period_years} years")

                    with col2:
                        st.markdown(f"### {result['product_name']}")
                        st.caption(f"**SKU:** {result['sku']}")
                        st.write(result['reason'])

                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("CO2e Avoided", f"{sustainability_impact.co2e_avoided_tons_per_year:.1f} tons/yr", help="Annual carbon reduction")
                        with col_b:
                            st.metric("Energy Savings", f"{sustainability_impact.energy_savings_kwh_per_year:,.0f} kWh/yr")
                        with col_c:
                            st.metric("Cost Savings", f"${sustainability_impact.cost_savings_usd_per_year:,.0f}/yr")

                with tab2:
                    st.markdown(format_impact_summary(sustainability_impact))

                    st.subheader("📊 Impact Visualization")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Environmental Metrics**")
                        st.progress(min(sustainability_impact.circularity_score / 100, 1.0))
                        st.caption(f"Circularity Score: {sustainability_impact.circularity_score:.0f}/100")
                        st.markdown(f"**Product Lifecycle Emissions:** {sustainability_impact.lifecycle_emissions_kg_co2e:.0f} kg CO2e")
                        st.caption("One-time emissions from manufacturing (amortized over 15-year lifespan)")

                    with col2:
                        st.markdown("**Equivalencies**")
                        cars_equivalent = sustainability_impact.co2e_avoided_tons_per_year / 4.6
                        trees_equivalent = sustainability_impact.co2e_avoided_tons_per_year * 50
                        st.markdown(f"🚗 **{cars_equivalent:.1f}** cars off the road for 1 year")
                        st.markdown(f"🌳 **{trees_equivalent:.0f}** tree-years of carbon sequestration")
                        st.markdown(f"💡 **{sustainability_impact.energy_savings_kwh_per_year/8760:.1f} kW** continuous power reduction")

                with tab3:
                    st.subheader("💰 Total Cost of Ownership (5-Year)")

                    initial_cost = price_float + (price_float * 0.15)
                    maintenance_5yr = price_float * 0.05 * 5
                    energy_savings_5yr = sustainability_impact.cost_savings_usd_per_year * 5

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Initial Investment", f"${initial_cost:,.0f}")
                        st.caption("Equipment + Installation")
                        st.metric("Maintenance (5yr)", f"${maintenance_5yr:,.0f}")
                    with col2:
                        st.metric("Energy Savings (5yr)", f"${energy_savings_5yr:,.0f}")
                        st.metric("Net TCO", f"${sustainability_impact.total_cost_of_ownership_5yr:,.0f}")

                    roi_5yr = ((energy_savings_5yr - initial_cost - maintenance_5yr) / initial_cost) * 100
                    st.success(f"**5-Year ROI:** {roi_5yr:.0f}% | **Payback:** {sustainability_impact.payback_period_years:.1f} years")

                    st.markdown("---")
                    st.markdown("**Business Case Summary**")
                    st.markdown(f"""
- **Initial Investment:** ${initial_cost:,.0f}
- **Annual Operating Savings:** ${sustainability_impact.cost_savings_usd_per_year:,.0f}/year
- **Break-even:** {sustainability_impact.payback_period_years:.1f} years
- **10-Year NPV (5% discount):** ${(sustainability_impact.cost_savings_usd_per_year * 7.72 - initial_cost):,.0f}
                    """)

                with tab4:
                    st.subheader("🔍 Explainability & Transparency")

                    st.markdown("**Why this recommendation?**")
                    st.info(f"This recommendation is based on {len(relevant_knowledge)} relevant sections from our expert knowledge base combined with product catalog analysis.")

                    with st.expander("📚 View Retrieved Expert Knowledge"):
                        for i, section in enumerate(relevant_knowledge, 1):
                            st.markdown(f"**Source {i}:**")
                            st.text(section[:500] + "..." if len(section) > 500 else section)
                            st.markdown("---")

                    st.markdown("**AI Model Details**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Model", "Llama 3.1-8B")
                    with col2:
                        st.metric("RAG Retrieval", f"{retrieval_time:.2f}s")
                    with col3:
                        st.metric("LLM Inference", f"{llm_time:.2f}s")

                    st.markdown("**Compliance & Standards**")
                    if sustainability_impact.compliance_frameworks:
                        for framework in sustainability_impact.compliance_frameworks:
                            st.markdown(f"✓ {framework}")
                    else:
                        st.caption("ℹ️ Limited compliance applicability for this recommendation")

                st.markdown("---")
                st.subheader("📝 Was this recommendation helpful?")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("👍 Very Helpful"):
                        st.session_state.feedback_scores.append(1.0)
                        st.success("Thank you for your feedback!")
                with col2:
                    if st.button("✅ Helpful"):
                        st.session_state.feedback_scores.append(0.8)
                        st.success("Thank you for your feedback!")
                with col3:
                    if st.button("🤔 Somewhat"):
                        st.session_state.feedback_scores.append(0.5)
                        st.info("Thank you! We'll improve.")
                with col4:
                    if st.button("👎 Not Helpful"):
                        st.session_state.feedback_scores.append(0.0)
                        st.warning("Thank you! We'll review this.")

            except Exception as e:
                st.error(f"Error: {e}")
                st.warning("Note: Free tier models may time out if the server is busy. Try clicking 'Analyze' again.")

    # =========================================================
    # MULTI-AGENT PIPELINE MODE
    # =========================================================
    else:
        try:
            llm_wrapper = LLMWrapper(hf_token)
            diagnosis_agent = DiagnosisAgent(llm_wrapper)
            product_agent = ProductAgent(llm_wrapper, catalog_data)
            sustainability_agent = SustainabilityAgent(sustainability_calc)
            financial_agent = FinancialAgent()
            report_agent = ReportAgent()

            context = {
                "error_description": error_desc,
                "device_info": device_context,
                "knowledge_context": knowledge_context,
            }
            workflow_trace = []

            with st.status("Running Multi-Agent Pipeline...", expanded=True) as pipeline_status:
                # Step 1 — Diagnosis
                st.write("🔍 **[1/5] DiagnosisAgent** — analyzing root cause with expert knowledge...")
                diag_output = diagnosis_agent.execute(context)
                workflow_trace.append(diag_output)
                if diag_output.status == AgentStatus.FAILED:
                    raise Exception(f"DiagnosisAgent failed: {diag_output.error}")
                context["diagnosis"] = diag_output.output
                st.write(f"   ✅ {diag_output.output.get('root_cause', 'N/A')[:100]} ({diag_output.execution_time:.1f}s)")

                # Step 2 — Product selection
                st.write("📦 **[2/5] ProductAgent** — selecting best match from catalog...")
                prod_output = product_agent.execute(context)
                workflow_trace.append(prod_output)
                if prod_output.status == AgentStatus.FAILED:
                    raise Exception(f"ProductAgent failed: {prod_output.error}")
                context["product"] = prod_output.output
                product_info = prod_output.output.get("primary_recommendation", {})
                st.write(f"   ✅ {product_info.get('name', 'N/A')} / SKU: {product_info.get('sku', 'N/A')} ({prod_output.execution_time:.1f}s)")

                # Step 3 — Sustainability
                st.write("🌱 **[3/5] SustainabilityAgent** — calculating CO2e & circularity...")
                sust_output = sustainability_agent.execute(context)
                workflow_trace.append(sust_output)
                if sust_output.status == AgentStatus.FAILED:
                    raise Exception(f"SustainabilityAgent failed: {sust_output.error}")
                context["sustainability"] = sust_output.output
                st.write(f"   ✅ CO2e avoided: {sust_output.output.get('co2e_avoided_tons', 0):.1f} tons/yr ({sust_output.execution_time:.1f}s)")

                # Step 4 — Financial
                st.write("💰 **[4/5] FinancialAgent** — computing TCO, ROI & payback...")
                fin_output = financial_agent.execute(context)
                workflow_trace.append(fin_output)
                if fin_output.status == AgentStatus.FAILED:
                    raise Exception(f"FinancialAgent failed: {fin_output.error}")
                context["financial"] = fin_output.output
                st.write(f"   ✅ Payback: {fin_output.output.get('payback_period_years', 0):.1f} yrs | ROI: {fin_output.output.get('roi_5yr_percent', 0):.0f}% ({fin_output.execution_time:.1f}s)")

                # Step 5 — Report
                st.write("📋 **[5/5] ReportAgent** — compiling executive summary...")
                report_output = report_agent.execute(context)
                workflow_trace.append(report_output)
                if report_output.status == AgentStatus.FAILED:
                    raise Exception(f"ReportAgent failed: {report_output.error}")

                total_time = time.time() - start_time
                pipeline_status.update(
                    label=f"✅ Multi-Agent Pipeline Complete in {total_time:.2f}s (RAG: {retrieval_time:.2f}s + 5 agents)",
                    state="complete",
                    expanded=False
                )

            # Extract normalized outputs
            diagnosis = context["diagnosis"]
            product = context["product"].get("primary_recommendation", {})
            sustainability = context["sustainability"]
            financial = context["financial"]

            # Derive safety alert from severity (Phase 5c)
            if diagnosis.get("severity") == "critical":
                safety_alert = f"Critical issue detected: {diagnosis.get('root_cause', 'Unknown')}"
            else:
                safety_alert = "None"

            price_float = float(product.get("price") or 0)
            price_display = f"€{price_float:,.0f}"

            st.session_state.total_recommendations += 1
            st.session_state.total_co2e_avoided += sustainability.get("co2e_avoided_tons", 0)

            tab1, tab2, tab3, tab4 = st.tabs(["📋 Recommendation", "🌱 Sustainability Impact", "💰 Financial Analysis", "🔍 Explainability"])

            with tab1:
                diag_text = (
                    f"{diagnosis.get('root_cause', 'N/A')} — "
                    f"Severity: **{diagnosis.get('severity', 'N/A').upper()}** | "
                    f"Urgency: {diagnosis.get('urgency', 'N/A')}"
                )
                st.info(f"**Diagnosis:** {diag_text}")

                if safety_alert != "None":
                    st.error(f"⚠️ **SAFETY ALERT:** {safety_alert}")

                rating = sustainability.get("sustainability_rating", "B")
                rating_colors = {"A+": "🟢", "A": "🟢", "B+": "🟡", "B": "🟡", "C": "🟠", "D": "🔴"}

                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(f"### {rating_colors.get(rating, '⚪')} Rating: {rating}")
                    st.metric("Price", price_display)
                    st.metric("Payback Period", f"{financial.get('payback_period_years', 0):.1f} years")

                with col2:
                    st.markdown(f"### {product.get('name', 'Unknown Product')}")
                    st.caption(f"**SKU:** {product.get('sku', 'N/A')}")
                    st.write(product.get("reason", ""))

                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("CO2e Avoided", f"{sustainability.get('co2e_avoided_tons', 0):.1f} tons/yr", help="Annual carbon reduction")
                    with col_b:
                        st.metric("Energy Savings", f"{sustainability.get('energy_savings_kwh', 0):,.0f} kWh/yr")
                    with col_c:
                        st.metric("Cost Savings", f"${sustainability.get('cost_savings_usd', 0):,.0f}/yr")

            with tab2:
                st.subheader("📊 Impact Visualization")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Environmental Metrics**")
                    circularity = sustainability.get("circularity_score", 0)
                    st.progress(min(circularity / 100, 1.0))
                    st.caption(f"Circularity Score: {circularity:.0f}/100")
                    st.metric("CO2e Avoided/year", f"{sustainability.get('co2e_avoided_tons', 0):.1f} tons")
                    st.metric("Energy Saved/year", f"{sustainability.get('energy_savings_kwh', 0):,.0f} kWh")

                with col2:
                    st.markdown("**Equivalencies**")
                    co2e = sustainability.get("co2e_avoided_tons", 0)
                    energy_kwh = sustainability.get("energy_savings_kwh", 0)
                    st.markdown(f"🚗 **{co2e / 4.6:.1f}** cars off the road for 1 year")
                    st.markdown(f"🌳 **{co2e * 50:.0f}** tree-years of carbon sequestration")
                    st.markdown(f"💡 **{energy_kwh / 8760:.1f} kW** continuous power reduction")

                st.markdown("**Compliance Frameworks**")
                frameworks = sustainability.get("compliance_frameworks", [])
                if frameworks:
                    for fw in frameworks:
                        st.markdown(f"✓ {fw}")
                else:
                    st.caption("ℹ️ Limited compliance applicability for this recommendation")

            with tab3:
                st.subheader("💰 Total Cost of Ownership (5-Year)")

                annual_savings = financial.get("annual_savings", 0)
                annual_maintenance = financial.get("annual_maintenance", 0)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Initial Investment", f"${financial.get('initial_investment', 0):,.0f}")
                    st.caption("Equipment + Installation")
                    st.metric("Maintenance (5yr)", f"${annual_maintenance * 5:,.0f}")
                with col2:
                    st.metric("Energy Savings (5yr)", f"${annual_savings * 5:,.0f}")
                    st.metric("Net TCO", f"${financial.get('net_tco_5yr', 0):,.0f}")

                roi = financial.get("roi_5yr_percent", 0)
                payback = financial.get("payback_period_years", 0)
                st.success(f"**5-Year ROI:** {roi:.0f}% | **Payback:** {payback:.1f} years")

                st.markdown("---")
                st.markdown("**Business Case Summary**")
                st.markdown(f"""
- **Initial Investment:** ${financial.get('initial_investment', 0):,.0f}
- **Annual Operating Savings:** ${annual_savings:,.0f}/year
- **Break-even:** {payback:.1f} years
- **5-Year NPV:** ${financial.get('npv_5yr', 0):,.0f}
                """)

            with tab4:
                st.subheader("🔍 Agent Execution Timeline")

                agent_labels = {
                    "DiagnosisAgent": "🔍 Diagnosis",
                    "ProductAgent": "📦 Product",
                    "SustainabilityAgent": "🌱 Sustainability",
                    "FinancialAgent": "💰 Financial",
                    "ReportAgent": "📋 Report",
                }
                total_agent_time = sum(t.execution_time for t in workflow_trace)
                st.markdown(f"**Total pipeline: {total_agent_time:.2f}s** | RAG retrieval: {retrieval_time:.2f}s | Grand total: {total_time:.2f}s")

                cols = st.columns(len(workflow_trace))
                for col, trace in zip(cols, workflow_trace):
                    status_icon = "✅" if trace.status == AgentStatus.COMPLETED else "❌"
                    with col:
                        st.metric(
                            agent_labels.get(trace.agent_name, trace.agent_name),
                            f"{trace.execution_time:.2f}s",
                            delta=status_icon,
                            delta_color="off"
                        )

                st.markdown("---")
                st.markdown("**RAG Knowledge Injected into DiagnosisAgent**")
                st.info(f"FAISS retrieved {len(relevant_knowledge)} sections in {retrieval_time:.2f}s — prepended to DiagnosisAgent prompt as expert context.")
                with st.expander("📚 View Retrieved Expert Knowledge"):
                    for i, section in enumerate(relevant_knowledge, 1):
                        st.markdown(f"**Source {i}:**")
                        st.text(section[:500] + "..." if len(section) > 500 else section)
                        st.markdown("---")

                st.markdown("**Model**")
                st.caption("Meta Llama 3.1-8B via HuggingFace Inference API — invoked by DiagnosisAgent and ProductAgent")

            st.markdown("---")
            st.subheader("📝 Was this recommendation helpful?")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("👍 Very Helpful", key="ma_fb_1"):
                    st.session_state.feedback_scores.append(1.0)
                    st.success("Thank you for your feedback!")
            with col2:
                if st.button("✅ Helpful", key="ma_fb_2"):
                    st.session_state.feedback_scores.append(0.8)
                    st.success("Thank you for your feedback!")
            with col3:
                if st.button("🤔 Somewhat", key="ma_fb_3"):
                    st.session_state.feedback_scores.append(0.5)
                    st.info("Thank you! We'll improve.")
            with col4:
                if st.button("👎 Not Helpful", key="ma_fb_4"):
                    st.session_state.feedback_scores.append(0.0)
                    st.warning("Thank you! We'll review this.")

        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("Note: Free tier models may time out if the server is busy. Try clicking 'Analyze' again.")
