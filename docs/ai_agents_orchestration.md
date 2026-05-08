# AI Agents Orchestration: Concepts & Implementation

A comprehensive guide to understanding and implementing multi-agent orchestration for industrial equipment recommendations.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Why Agents Instead of Traditional RAG?](#why-agents-instead-of-traditional-rag)
4. [Architecture Overview](#architecture-overview)
5. [Implementation Details](#implementation-details)
6. [Code Walkthrough](#code-walkthrough)
7. [Running the System](#running-the-system)
8. [Future Enhancements](#future-enhancements)
9. [Comparison with Original Pipeline](#comparison-with-original-pipeline)

---

## Introduction

This document explains the **AI Agent Orchestration** system implemented in `agent_orchestrator.py`. It demonstrates how multiple specialized AI agents can work together to provide more transparent, modular, and extensible recommendations compared to the traditional RAG + LLM pipeline.

### What is Agent Orchestration?

**Agent orchestration** is a pattern where multiple AI agents, each specialized in a specific task, work together under a coordinator (master agent) to accomplish complex goals. Think of it like a team of specialists:

- **Diagnosis Agent** = The technician who inspects the problem
- **Product Agent** = The sales specialist who recommends solutions
- **Sustainability Agent** = The environmental analyst who calculates impact
- **Financial Agent** = The business analyst who computes ROI
- **Report Agent** = The manager who compiles everything into a recommendation

---

## Core Concepts

### 1. What is an AI Agent?

An **AI Agent** is an AI system that can:
- **Perceive** its environment (receive input)
- **Reason** about what action to take
- **Act** (execute tasks or call tools)
- **Iterate** if needed (refine based on feedback)

Unlike a simple LLM that just generates text, an agent can make decisions and take actions.

### 2. Types of Agents

| Agent Type | Description | Example |
|------------|-------------|---------|
| **LLM-powered** | Uses a language model for reasoning | Diagnosis, Product agents |
| **Rule-based** | Uses deterministic calculations | Sustainability, Financial agents |
| **Tool-calling** | Can invoke external APIs (future) | Inventory, pricing lookup |
| **Memory-enabled** | Remembers past interactions (future) | User preferences |

### 3. Agent Communication

Agents communicate through a **shared context** (dictionary) that accumulates information:

```python
context = {
    "error_description": "Valve is leaking...",
    "device_info": "VVF43.65, installed 2018",
    "diagnosis": {...},           # Added by Diagnosis Agent
    "product": {...},             # Added by Product Agent
    "sustainability": {...},      # Added by Sustainability Agent
    "financial": {...},           # Added by Financial Agent
}
```

Each agent reads from and writes to this context, passing results to the next agent.

---

## Why Agents Instead of Traditional RAG?

### The Problem with Monolithic RAG

In the original `app.py`, the RAG pipeline works like this:

```
User Query → RAG (search) → LLM (generate) → Single JSON Response
```

This has limitations:
- **Black box** - You can't see *why* the LLM made certain decisions
- **Single point of failure** - If anything goes wrong, the whole response fails
- **Hard to debug** - No visibility into which step caused an issue
- **Not modular** - Can't improve one part without affecting others

### The Agent Solution

With orchestration, each agent is:
- **Specialized** - Does one thing well
- **Testable** - Can verify each agent's output independently
- **Transparent** - You can see reasoning at each step
- **Extensible** - Add new agents without changing existing ones

---

## Architecture Overview

### High-Level Flow

```
┌─────────────┐
│    User     │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         MASTER ORCHESTRATOR             │
│    (Coordinates workflow + timing)      │
└─────────────────┬───────────────────────┘
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Diagnosis │ │Product   │ │  (Future)│
│  Agent   │ │  Agent   │ │ Tool-call│
│ (LLM)    │ │ (LLM)    │ │  Agent   │
└────┬─────┘ └────┬─────┘ └──────────┘
     │            │
     └─────┬──────┘
           ▼
┌──────────────────┐
│ Sustainability   │
│      Agent       │
└────────┬─────────┘
         ▼
┌──────────────────┐
│   Financial      │
│      Agent       │
└────────┬─────────┘
         ▼
┌──────────────────┐
│    Report        │
│      Agent       │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│            FINAL OUTPUT                  │
│  Executive Summary + Detailed Report     │
└─────────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Type | Input | Output |
|-------|------|-------|--------|
| **Master Orchestrator** | Coordinator | User query | Orchestrates workflow |
| **Diagnosis Agent** | LLM-powered | Error + device info | Root cause, severity, equipment type |
| **Product Agent** | LLM-powered | Diagnosis + catalog | SKU, price, compatibility |
| **Sustainability Agent** | Rule-based | Product + equipment | CO2e, energy savings, circularity |
| **Financial Agent** | Rule-based | Product + sustainability | TCO, payback, ROI |
| **Report Agent** | Aggregation | All outputs | Final report |

---

## Implementation Details

### File Structure

```
Retrofit-recommender/
├── agent_orchestrator.py    # Main implementation
├── app.py                   # Original RAG pipeline
├── sustainability_calculator.py  # CO2e calculations
└── catalog.json             # Product database
```

### Key Classes

#### 1. `BaseAgent` - Abstract base class

```python
class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        """Execute the agent's task"""
        raise NotImplementedError("Subclasses must implement execute()")
```

All agents inherit from this base class, ensuring consistent interface.

#### 2. `LLMWrapper` - LLM communication layer

```python
class LLMWrapper:
    """Wrapper for LLM calls with retry logic"""
    
    def __init__(self, hf_token: str):
        self.hf_token = hf_token
        self._llm = None
    
    def call(self, prompt: str) -> Dict[str, Any]:
        """Call LLM and parse JSON response"""
        # ... retry logic, JSON parsing, error handling
```

Handles:
- Model initialization (lazy loading)
- Retry logic for cold starts
- JSON extraction from LLM response

#### 3. `AgentOutput` - Standardized output

```python
@dataclass
class AgentOutput:
    agent_name: str
    status: AgentStatus  # PENDING, RUNNING, COMPLETED, FAILED
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
```

Every agent returns the same structure, making it easy to track and debug.

#### 4. Agent Status Enum

```python
class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

## Code Walkthrough

### Step 1: Initialize the System

```python
from sustainability_calculator import SustainabilityCalculator

# Load catalog
with open("catalog.json", "r") as f:
    catalog = json.load(f)

# Create sustainability calculator
sust_calc = SustainabilityCalculator(region="US_AVERAGE", electricity_rate=0.12)

# Create orchestrator with LLM wrapper
orchestrator = MasterOrchestrator(catalog, sust_calc, hf_token)
```

### Step 2: Define the Agents

```python
class MasterOrchestrator:
    def __init__(self, catalog, sust_calc, hf_token):
        # LLM wrapper for all LLM-powered agents
        self.llm_wrapper = LLMWrapper(hf_token)
        
        # Initialize all agents
        self.diagnosis_agent = DiagnosisAgent(self.llm_wrapper)
        self.product_agent = ProductAgent(self.llm_wrapper, catalog)
        self.sustainability_agent = SustainabilityAgent(sust_calc)
        self.financial_agent = FinancialAgent()
        self.report_agent = ReportAgent()
```

### Step 3: Execute the Workflow

```python
def run(self, error_description: str, device_info: str):
    # Start with user input
    context = {
        "error_description": error_description,
        "device_info": device_info
    }
    
    # Step 1: Diagnosis
    diag_output = self.diagnosis_agent.execute(context)
    context["diagnosis"] = diag_output.output
    
    # Step 2: Product Selection
    prod_output = self.product_agent.execute(context)
    context["product"] = prod_output.output
    
    # Step 3: Sustainability
    sust_output = self.sustainability_agent.execute(context)
    context["sustainability"] = sust_output.output
    
    # Step 4: Financial
    fin_output = self.financial_agent.execute(context)
    context["financial"] = fin_output.output
    
    # Step 5: Report
    report_output = self.report_agent.execute(context)
    
    return report_output.output
```

### Step 4: Diagnosis Agent (LLM-powered)

```python
class DiagnosisAgent(BaseAgent):
    def __init__(self, llm_wrapper):
        super().__init__("DiagnosisAgent", "Analyzes symptoms using LLM")
        self.llm = llm_wrapper
    
    def execute(self, context):
        error_desc = context.get("error_description", "")
        device_info = context.get("device_info", "")
        
        # Build prompt for LLM
        prompt = f"""You are an industrial equipment diagnostic specialist.
        
ERROR DESCRIPTION:
{error_desc}

DEVICE INFO:
{device_info}

Provide diagnosis in JSON format with: root_cause, severity, urgency, equipment_type
"""
        
        # Call LLM
        result = self.llm.call(prompt)
        
        # Return structured output
        return self._create_output(result, exec_time)
```

### Step 5: Product Agent (LLM-powered)

```python
class ProductAgent(BaseAgent):
    def execute(self, context):
        diagnosis = context.get("diagnosis", {})
        
        # Build catalog for LLM
        catalog_text = json.dumps([{
            "sku": p.get("sku"),
            "name": p.get("name"),
            "price": p.get("price"),
            "category": p.get("category")
        } for p in self.catalog if p.get("status") == "Available"])
        
        # Prompt LLM to select product
        prompt = f"""Based on diagnosis:
- Root cause: {diagnosis['root_cause']}
- Equipment type: {diagnosis['equipment_type']}

Catalog:
{catalog_text}

Recommend the best product in JSON: sku, name, price, reason
"""
        
        result = self.llm.call(prompt)
        
        return self._create_output({
            "primary_recommendation": result,
            "alternatives": []
        }, exec_time)
```

### Step 6: Sustainability Agent (Rule-based)

```python
class SustainabilityAgent(BaseAgent):
    def __init__(self, sustainability_calculator):
        self.calc = sustainability_calculator
    
    def execute(self, context):
        product = context.get("product", {}).get("primary_recommendation", {})
        diagnosis = context.get("diagnosis", {})
        
        # Calculate impact using existing calculator
        impact = self.calc.calculate_full_impact(
            product_sku=product.get("sku"),
            equipment_type=diagnosis.get("equipment_type", "valve"),
            purchase_price=product.get("price", 0),
            # ... other parameters
        )
        
        return self._create_output({
            "co2e_avoided_tons": impact.co2e_avoided_tons_per_year,
            "energy_savings_kwh": impact.energy_savings_kwh_per_year,
            "circularity_score": impact.circularity_score,
            # ...
        }, exec_time)
```

### Step 7: Financial Agent (Rule-based)

```python
class FinancialAgent(BaseAgent):
    def execute(self, context):
        price = product.get("price", 0)
        annual_savings = sustainability.get("cost_savings_usd", 0)
        
        # Calculate TCO, payback, ROI
        initial_investment = price + (price * 0.15)  # + installation
        payback_years = initial_investment / annual_savings
        roi_5yr = ((annual_savings * 5 - initial_investment) / initial_investment) * 100
        
        return self._create_output({
            "initial_investment": initial_investment,
            "payback_period_years": payback_years,
            "roi_5yr_percent": roi_5yr,
            # ...
        }, exec_time)
```

### Step 8: Report Agent (Aggregation)

```python
class ReportAgent(BaseAgent):
    def execute(self, context):
        # Combine all outputs into final report
        return self._create_output({
            "executive_summary": {
                "issue": diagnosis.get("root_cause"),
                "severity": severity_emoji + " " + diagnosis.get("severity"),
                "recommended_action": f"Replace with {product.get('name')}",
                "estimated_payback": f"{financial.get('payback_period_years')} years"
            },
            "diagnosis": diagnosis,
            "product_recommendation": product,
            "impact_summary": {
                "environmental": sustainability,
                "financial": financial
            },
            "next_steps": ["Order SKU", "Schedule install", "Verify"],
            "generated_at": timestamp
        }, exec_time)
```

---

## Running the System

### Prerequisites

```bash
# Install dependencies
pip install langchain-huggingface pydantic

# Set environment variable
echo "HUGGINGFACE_API_TOKEN=hf_xxxxx" > .env
```

### Run the Demo

```bash
python agent_orchestrator.py
```

### Sample Output

```
############################################################
# TEST CASE 1: Valve Leaking
############################################################

STARTING LLM-POWERED AGENT ORCHESTRATION

[1/5] Running LLM Diagnosis Agent...
   [OK] Diagnosis: Worn or damaged stem seal or O-ring

[2/5] Running LLM Product Agent...
   [OK] Product: Acvatix Eco-Line Valve (VVF53.65-ECO)

[3/5] Running Sustainability Agent...
   [OK] CO2e Savings: 25.3 tons/year

[4/5] Running Financial Agent...
   [OK] Payback: 0.1 years

[5/5] Running Report Agent...

WORKFLOW COMPLETED

EXECUTIVE SUMMARY:
  Issue: Worn or damaged stem seal or O-ring
  Severity: [HIGH] HIGH
  Action: Replace with Acvatix Eco-Line Valve
  Payback: 0.1 years

ENVIRONMENTAL:
  CO2e Saved: 25.3 tons
  Energy Saved: 65,700 kWh

FINANCIAL:
  Investment: $518
  Annual Savings: $7,884
  ROI (5yr): 6157%

WORKFLOW TIMING:
  DiagnosisAgent: 0.99s
  ProductAgent: 0.39s
  SustainabilityAgent: 0.00s
  FinancialAgent: 0.00s
  ReportAgent: 0.00s
  TOTAL: 1.38s
```

---

## Future Enhancements

### 1. Tool-Calling Agents

Give agents the ability to call external APIs:

```python
class InventoryAgent(BaseAgent):
    def execute(self, context):
        # Check real-time inventory
        inventory = external_api.get_inventory(sku=product_sku)
        
        # Check current pricing
        pricing = external_api.get_pricing(product_id)
        
        return {
            "in_stock": inventory.quantity > 0,
            "lead_time": inventory.lead_time_days,
            "current_price": pricing.amount
        }
```

### 2. Multi-Turn Dialogue

Allow agents to ask clarifying questions:

```python
if diagnosis.get("needs_clarification"):
    return {
        "requires_user_input": True,
        "questions": [
            "What is the operating pressure?",
            "Is this a safety-critical application?"
        ]
    }
```

### 3. Memory Agents

Persist user preferences and equipment history:

```python
class MemoryAgent:
    def save_interaction(self, user_id, interaction):
        # Store in database
        db.sessions.insert({
            "user_id": user_id,
            "equipment_history": ...,
            "preferences": ...
        })
    
    def get_context(self, user_id):
        return db.sessions.find_one(user_id=user_id)
```

### 4. Human-in-the-Loop

Flag critical decisions for review:

```python
if severity == "critical" or voltage_mismatch:
    return {
        "requires_approval": True,
        "approver": "Safety Engineer",
        "reason": "Critical severity - manual review required"
    }
```

### 5. LangChain Integration

Use LangChain's LCEL for declarative chains:

```python
from langchain_core.runnables import chain

@chain
def diagnosis_chain():
    return diagnosis_agent | product_agent | sustainability_agent
```

---

## Comparison with Original Pipeline

| Aspect | Original (app.py) | Agent Orchestration |
|--------|-------------------|---------------------|
| **Architecture** | Single RAG → LLM chain | Multi-agent workflow |
| **Transparency** | Black box | Visible reasoning at each step |
| **Modularity** | Monolithic | Independent, testable agents |
| **Error Handling** | Full failure | Isolated per agent |
| **Debugging** | Difficult | Agent-level tracing |
| **Extensibility** | Code changes needed | Add new agents easily |
| **Latency** | ~3-5 seconds | ~1-2 seconds (parallel possible) |
| **Code Structure** | 500+ lines in app.py | Modular ~400 lines |

### When to Use Which?

| Scenario | Recommended Approach |
|----------|---------------------|
| Simple, one-shot queries | Original RAG pipeline |
| Complex multi-step reasoning | Agent orchestration |
| Need transparency/debugging | Agent orchestration |
| Real-time inventory/pricing | Agent + tool-calling |
| Need user memory | Agent + memory |

---

## Conclusion

The AI Agent Orchestration system demonstrates a more sophisticated approach to building AI-powered applications. By splitting the responsibility across specialized agents, we gain:

1. **Better transparency** - Can see reasoning at each step
2. **Easier debugging** - Can identify which agent caused issues
3. **Improved testability** - Can test each agent independently
4. **Greater extensibility** - Can add new capabilities without rewriting

This architecture is well-suited for complex B2B applications like industrial equipment recommendations, where domain expertise, regulatory compliance, and explainability are critical.

---

## References

- [LangChain Agents Documentation](https://python.langchain.com/docs/modules/agents/)
- [AutoGen Multi-Agent Framework](https://microsoft.github.io/autogen/)
- [CrewAI Task Delegation](https://docs.crewai.com/)
- [RAGAS Evaluation Metrics](https://docs.ragas.io/)

---

*Document Version: 1.0*  
*Last Updated: May 2026*  
*Author: AI/Product Engineering Team*