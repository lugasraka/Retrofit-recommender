# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered industrial equipment retrofit recommender using RAG (Retrieval-Augmented Generation) to suggest optimal retrofits with sustainability impact calculations. Built as a Streamlit application with a focus on CO2e tracking and compliance reporting.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py

# Test sustainability calculator standalone
python sustainability_calculator.py
```

**Environment Setup:** Create a `.env` file with `HUGGINGFACE_API_TOKEN=hf_your_token_here`

**Note:** `.env` is gitignored - never commit API tokens or secrets.

## Architecture

### Core Components

1. **RAG Pipeline** ([app.py:113-146](app.py#L113-L146))
   - Embeddings: SentenceTransformer (`all-MiniLM-L6-v2`) on CPU
   - Vector store: FAISS (IndexFlatL2)
   - Knowledge retrieval: Top-3 sections from `knowledge_base.txt`
   - LLM: Meta Llama 3.1-8B via HuggingFace Inference API

2. **Sustainability Calculator** ([sustainability_calculator.py](sustainability_calculator.py))
   - `SustainabilityCalculator` class handles all impact calculations
   - `SustainabilityImpact` dataclass holds metrics (CO2e, energy savings, TCO, circularity score)
   - Regional carbon intensity factors (US, EU, Global)
   - Compliance framework mapping (GHG Protocol, ISO 50001, CDP, TCFD)

3. **Product Catalog** ([catalog.json](catalog.json))
   - 30 products: valves, actuators, sensors, controllers, services, bundles
   - Each has SKU, name, specs, status, category, price (in EUR)

4. **Knowledge Base** ([knowledge_base.txt](knowledge_base.txt))
   - 11 sections covering: voltage mismatches, valve upgrades, sensor calibration, controller upgrades, preventive maintenance, system optimization, pressure sensors, actuator selection, bundle recommendations, service packages, failure patterns

### Data Flow

```
User Input → RAG Retrieval (FAISS) → LLM (Llama 3.1-8B) → JSON Response
                                                              ↓
                                    Sustainability Calculator ← Product Catalog
                                                              ↓
                                    4-Tab UI (Recommendation, Sustainability, Financial, Explainability)
```

### Key Functions

- `retrieve_knowledge(query, top_k)` - FAISS similarity search on knowledge base
- `call_llm_with_retry()` - Handles model cold starts with exponential backoff
- `SustainabilityCalculator.calculate_full_impact()` - Comprehensive impact calculation
- `extract_json()` - Regex-based JSON extraction from LLM output

### Session State

KPIs tracked in `st.session_state`:
- `total_recommendations` - Counter
- `total_co2e_avoided` - Cumulative tons
- `feedback_scores` - User satisfaction ratings

## Key Technical Details

- LLM temperature: 0.05 (low for consistent outputs)
- LLM output: Structured JSON with diagnosis, product_name, sku, reason, safety_alert, price
- Safety alerts triggered for voltage mismatches (230V/24V incompatibilities)
- Equipment efficiency estimates by type: valve (15%), actuator (10%), sensor (5%), controller (20%)

## Docs Folder

The `docs/` folder contains product management artifacts (strategy, roadmap, KPIs, GTM, MLOps, user research). These are documentation only, not code dependencies.
