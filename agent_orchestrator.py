"""
AI Agent Orchestration with LLM Integration for Retrofit Recommender
Multi-agent workflow: Master -> Diagnosis (LLM) -> Product (LLM) -> Sustainability -> Financial -> Report
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import time
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

load_dotenv()


class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentOutput:
    agent_name: str
    status: AgentStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        raise NotImplementedError("Subclasses must implement execute()")
    
    def _create_output(self, output: Dict[str, Any], exec_time: float) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            output=output,
            execution_time=exec_time
        )
    
    def _create_error(self, error: str, exec_time: float) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            status=AgentStatus.FAILED,
            error=error,
            execution_time=exec_time
        )


class LLMWrapper:
    """Wrapper for LLM calls with retry logic"""
    
    def __init__(self, hf_token: str):
        self.hf_token = hf_token
        self._llm = None
        self._parser = None
    
    def _get_llm(self):
        if self._llm is None:
            llm_endpoint = HuggingFaceEndpoint(
                repo_id="meta-llama/Llama-3.1-8B-Instruct",
                task="conversational",
                max_new_tokens=500,
                temperature=0.05,
                top_p=0.95,
                repetition_penalty=1.1,
                huggingfacehub_api_token=self.hf_token,
            )
            self._llm = ChatHuggingFace(llm=llm_endpoint)
        return self._llm
    
    def call(self, prompt: str) -> Dict[str, Any]:
        """Call LLM and parse JSON response"""
        llm = self._get_llm()
        
        for attempt in range(3):
            try:
                response = llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                
                print(f"      [DEBUG] Raw LLM response: {content[:200]}...")
                
                try:
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        return parsed
                except Exception as pe:
                    print(f"      [DEBUG] JSON parse failed: {pe}")
                
                return {"raw_response": content}
                
            except Exception as e:
                print(f"      [DEBUG] LLM error: {e}")
                if "model_pending_deploy" in str(e) and attempt < 2:
                    delay = 10 * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise


class DiagnosisAgent(BaseAgent):
    """Agent that uses LLM to analyze symptoms and identify root cause"""
    
    def __init__(self, llm_wrapper: LLMWrapper):
        super().__init__("DiagnosisAgent", "Analyzes symptoms using LLM to identify root cause and severity")
        self.llm = llm_wrapper
    
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        start_time = time.time()
        
        error_desc = context.get("error_description", "")
        device_info = context.get("device_info", "")
        knowledge_context = context.get("knowledge_context", "")
        
        knowledge_section = f"""EXPERT KNOWLEDGE:
{knowledge_context}

""" if knowledge_context else ""
        
        prompt = f"""You are an industrial equipment diagnostic specialist. Analyze the following issue and provide a structured diagnosis.

{knowledge_section}ERROR DESCRIPTION:
{error_desc}

DEVICE INFO:
{device_info}

Provide a diagnosis in JSON format:
{{
    "root_cause": "What is the most likely root cause?",
    "severity": "critical, high, medium, or low",
    "urgency": "immediate, within 1 week, within 1 month, or planned maintenance",
    "equipment_type": "valve, actuator, sensor, controller, or system",
    "needs_clarification": false,
    "clarification_questions": []
}}

Return ONLY valid JSON:"""

        try:
            result = self.llm.call(prompt)
            
            if isinstance(result, dict):
                diagnosis = result
            else:
                diagnosis = {
                    "root_cause": "Analysis required",
                    "severity": "medium",
                    "urgency": "planned maintenance",
                    "equipment_type": "unknown",
                    "needs_clarification": True,
                    "clarification_questions": ["What type of equipment is this?"]
                }
            
            exec_time = time.time() - start_time
            return self._create_output(diagnosis, exec_time)
            
        except Exception as e:
            exec_time = time.time() - start_time
            return self._create_error(str(e), exec_time)


class ProductAgent(BaseAgent):
    """Agent that uses LLM to recommend products from catalog"""
    
    def __init__(self, llm_wrapper: LLMWrapper, catalog: List[Dict]):
        super().__init__("ProductAgent", "Uses LLM to recommend products from catalog based on diagnosis")
        self.llm = llm_wrapper
        self.catalog = catalog
    
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        start_time = time.time()
        
        diagnosis = context.get("diagnosis", {})
        error_desc = context.get("error_description", "")
        device_info = context.get("device_info", "")
        
        catalog_text = json.dumps([{
            "sku": p.get("sku"),
            "name": p.get("name"),
            "price": p.get("price"),
            "category": p.get("category"),
            "status": p.get("status")
        } for p in self.catalog if p.get("status") == "Available" and p.get("price")], indent=2)
        
        prompt = f"""You are a product specialist for industrial equipment. Based on the diagnosis, recommend the best product from the catalog.

DIAGNOSIS:
- Root Cause: {diagnosis.get('root_cause', 'Unknown')}
- Equipment Type: {diagnosis.get('equipment_type', 'unknown')}
- Severity: {diagnosis.get('severity', 'medium')}

ERROR: {error_desc}
DEVICE: {device_info}

PRODUCT CATALOG (Available items with prices):
{catalog_text}

Provide a recommendation in JSON format:
{{
    "sku": "exact SKU from catalog",
    "name": "exact product name from catalog",
    "price": price as number,
    "reason": "why this product solves the issue",
    "compatibility_notes": ["any voltage/spec considerations"],
    "alternatives": ["alternative SKUs if any"]
}}

Return ONLY valid JSON:"""

        try:
            result = self.llm.call(prompt)
            
            if isinstance(result, dict):
                product = {
                    "sku": result.get("sku", "N/A"),
                    "name": result.get("name", "Unknown Product"),
                    "price": result.get("price", 0),
                    "reason": result.get("reason", "Based on diagnosis"),
                    "compatibility_notes": result.get("compatibility_notes", []),
                    "alternatives": result.get("alternatives", [])
                }
            else:
                product = {"sku": "N/A", "name": "Unknown Product", "price": 0, "reason": "LLM response parsing failed"}
            
            exec_time = time.time() - start_time
            return self._create_output({
                "primary_recommendation": product,
                "alternatives": []
            }, exec_time)
            
        except Exception as e:
            exec_time = time.time() - start_time
            return self._create_error(str(e), exec_time)


class SustainabilityAgent(BaseAgent):
    """Agent that calculates sustainability impact"""
    
    def __init__(self, sustainability_calculator):
        super().__init__("SustainabilityAgent", "Calculates CO2e savings and sustainability metrics")
        self.calc = sustainability_calculator
    
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        start_time = time.time()
        
        product = context.get("product", {}).get("primary_recommendation", {})
        diagnosis = context.get("diagnosis", {})
        
        equipment_type = diagnosis.get("equipment_type", "valve")
        price = product.get("price") or 0
        
        efficiency_map = {
            "valve": 15.0,
            "actuator": 10.0,
            "sensor": 5.0,
            "controller": 20.0,
            "system": 25.0
        }
        
        efficiency = efficiency_map.get(equipment_type, 10.0)
        
        try:
            impact = self.calc.calculate_full_impact(
                product_sku=product.get("sku", ""),
                catalog_data=[],
                equipment_type=equipment_type,
                efficiency_improvement_pct=efficiency,
                purchase_price=price,
                installation_cost=price * 0.15,
                annual_maintenance_cost=price * 0.05,
                runtime_category="continuous" if equipment_type != "sensor" else "standard",
                equipment_lifespan_years=15,
                baseline_power_kw=50.0
            )
            
            output = {
                "co2e_avoided_tons": impact.co2e_avoided_tons_per_year,
                "energy_savings_kwh": impact.energy_savings_kwh_per_year,
                "cost_savings_usd": impact.cost_savings_usd_per_year,
                "circularity_score": impact.circularity_score,
                "sustainability_rating": impact.sustainability_rating,
                "compliance_frameworks": impact.compliance_frameworks,
                "equivalencies": {
                    "cars_removed": impact.co2e_avoided_tons_per_year / 4.6,
                    "trees_planted": impact.co2e_avoided_tons_per_year * 50
                }
            }
        except Exception as e:
            output = {
                "co2e_avoided_tons": 0,
                "energy_savings_kwh": 0,
                "cost_savings_usd": 0,
                "circularity_score": 0,
                "sustainability_rating": "N/A",
                "compliance_frameworks": [],
                "error": str(e)
            }
        
        exec_time = time.time() - start_time
        return self._create_output(output, exec_time)


class FinancialAgent(BaseAgent):
    """Agent that calculates financial metrics and ROI"""
    
    def __init__(self):
        super().__init__("FinancialAgent", "Calculates TCO, payback period, and ROI")
    
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        start_time = time.time()
        
        product = context.get("product", {}).get("primary_recommendation", {})
        sustainability = context.get("sustainability", {})
        
        price = product.get("price") or 0
        annual_savings = sustainability.get("cost_savings_usd", 0)
        
        installation = price * 0.15
        maintenance_annual = price * 0.05
        
        initial_investment = price + installation
        annual_operating_cost = maintenance_annual
        
        total_cost_5yr = initial_investment + (maintenance_annual * 5)
        savings_5yr = annual_savings * 5
        net_tco_5yr = total_cost_5yr - savings_5yr
        
        if initial_investment > 0 and annual_savings > 0:
            payback_years = initial_investment / annual_savings
        else:
            payback_years = 999
        
        roi_5yr = ((savings_5yr - total_cost_5yr) / total_cost_5yr * 100) if total_cost_5yr > 0 else 0
        
        npv_5yr = sum(
            annual_savings / (1.05 ** year) 
            for year in range(1, 6)
        ) - initial_investment
        
        output = {
            "initial_investment": initial_investment,
            "installation_cost": installation,
            "annual_maintenance": maintenance_annual,
            "annual_savings": annual_savings,
            "total_cost_5yr": total_cost_5yr,
            "total_savings_5yr": savings_5yr,
            "net_tco_5yr": net_tco_5yr,
            "payback_period_years": payback_years,
            "roi_5yr_percent": roi_5yr,
            "npv_5yr": npv_5yr,
            "recommendation": "Approved" if payback_years < 3 else "Review required" if payback_years < 5 else "Not recommended"
        }
        
        exec_time = time.time() - start_time
        return self._create_output(output, exec_time)


class ReportAgent(BaseAgent):
    """Agent that compiles final report from all agent outputs"""
    
    def __init__(self):
        super().__init__("ReportAgent", "Compiles comprehensive report from all agent outputs")
    
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        start_time = time.time()
        
        diagnosis = context.get("diagnosis", {})
        product = context.get("product", {}).get("primary_recommendation", {})
        sustainability = context.get("sustainability", {})
        financial = context.get("financial", {})
        
        severity_text = {
            "critical": "[CRITICAL]",
            "high": "[HIGH]", 
            "medium": "[MEDIUM]",
            "low": "[LOW]",
            "unknown": "[UNKNOWN]"
        }
        
        output = {
            "executive_summary": {
                "issue": diagnosis.get("root_cause", "Unknown"),
                "severity": f"{severity_text.get(diagnosis.get('severity', 'unknown'), '[UNKNOWN]')} {diagnosis.get('severity', 'unknown').upper()}",
                "recommended_action": f"Replace with {product.get('name', 'recommended product')}",
                "estimated_payback": f"{financial.get('payback_period_years', 0):.1f} years"
            },
            "diagnosis": diagnosis,
            "product_recommendation": {
                "sku": product.get("sku"),
                "name": product.get("name"),
                "price": product.get("price"),
                "reason": product.get("reason")
            },
            "impact_summary": {
                "environmental": {
                    "co2e_saved_annually": f"{sustainability.get('co2e_avoided_tons', 0):.1f} tons",
                    "energy_saved": f"{sustainability.get('energy_savings_kwh', 0):,.0f} kWh",
                    "circularity_score": sustainability.get("circularity_score", 0)
                },
                "financial": {
                    "initial_investment": financial.get("initial_investment", 0),
                    "annual_savings": financial.get("annual_savings", 0),
                    "payback_period": financial.get("payback_period_years", 0),
                    "roi_5yr": financial.get("roi_5yr_percent", 0)
                }
            },
            "compliance": sustainability.get("compliance_frameworks", []),
            "next_steps": [
                f"1. Order {product.get('sku', 'recommended product')}",
                "2. Schedule installation window",
                "3. Document baseline for verification",
                "4. Plan post-installation verification"
            ],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        exec_time = time.time() - start_time
        return self._create_output(output, exec_time)


class MasterOrchestrator:
    """Master agent that coordinates the LLM-powered workflow"""
    
    def __init__(self, catalog: List[Dict], sustainability_calculator, hf_token: str):
        self.llm_wrapper = LLMWrapper(hf_token)
        self.diagnosis_agent = DiagnosisAgent(self.llm_wrapper)
        self.product_agent = ProductAgent(self.llm_wrapper, catalog)
        self.sustainability_agent = SustainabilityAgent(sustainability_calculator)
        self.financial_agent = FinancialAgent()
        self.report_agent = ReportAgent()
    
    def run(self, error_description: str, device_info: str, knowledge_context: str = "") -> Dict[str, Any]:
        """Execute the full LLM-powered agent workflow"""
        
        workflow_trace = []
        
        context = {
            "error_description": error_description,
            "device_info": device_info,
            "knowledge_context": knowledge_context,
        }
        
        # Step 1: LLM-powered Diagnosis
        diag_output = self.diagnosis_agent.execute(context)
        workflow_trace.append(diag_output)
        
        if diag_output.status == AgentStatus.FAILED:
            return {"error": diag_output.error, "workflow_trace": workflow_trace}
        
        context["diagnosis"] = diag_output.output
        
        # Step 2: LLM-powered Product Selection
        prod_output = self.product_agent.execute(context)
        workflow_trace.append(prod_output)
        
        if prod_output.status == AgentStatus.FAILED:
            return {"error": prod_output.error, "workflow_trace": workflow_trace}
        
        context["product"] = prod_output.output
        
        # Step 3: Sustainability Calculation
        sust_output = self.sustainability_agent.execute(context)
        workflow_trace.append(sust_output)
        
        if sust_output.status == AgentStatus.FAILED:
            return {"error": sust_output.error, "workflow_trace": workflow_trace}
        
        context["sustainability"] = sust_output.output
        
        # Step 4: Financial Analysis
        fin_output = self.financial_agent.execute(context)
        workflow_trace.append(fin_output)
        
        if fin_output.status == AgentStatus.FAILED:
            return {"error": fin_output.error, "workflow_trace": workflow_trace}
        
        context["financial"] = fin_output.output
        
        # Step 5: Report Generation
        report_output = self.report_agent.execute(context)
        workflow_trace.append(report_output)
        
        return {
            "result": report_output.output,
            "workflow_trace": workflow_trace
        }


def demo():
    """Demo function to show the LLM-powered agent orchestration"""
    from sustainability_calculator import SustainabilityCalculator
    
    hf_token = os.getenv("HUGGINGFACE_API_TOKEN", "")
    if not hf_token:
        print("ERROR: HUGGINGFACE_API_TOKEN not set in .env")
        return
    
    with open("catalog.json", "r") as f:
        catalog = json.load(f)
    
    sust_calc = SustainabilityCalculator(region="US_AVERAGE", electricity_rate=0.12)
    
    orchestrator = MasterOrchestrator(catalog, sust_calc, hf_token)
    
    test_cases = [
        {
            "error": "Our control valve is leaking from the stem. Pressure drops observed.",
            "device": "Valve: VVF43.65 (PN16, DN65), installed 2018"
        },
        {
            "error": "Actuator failed. Controller output is 230V but actuator requires 24V. Safety shutdown triggered.",
            "device": "Controller: RWD62 (230V output), Actuator: old 24V model"
        },
        {
            "error": "Temperature readings inconsistent. Sensor drift detected. Readings vary +/-3C from reference.",
            "device": "Current Sensor: QAE2120.010 (installed 2018)"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'#'*60}")
        print(f"# TEST CASE {i}")
        print(f"{'#'*60}")
        
        result = orchestrator.run(
            error_description=test["error"],
            device_info=test["device"]
        )
        
        if "error" in result:
            print(f"ERROR: {result['error']}")
            continue
        
        print("\nEXECUTIVE SUMMARY:")
        summary = result["result"]["executive_summary"]
        print(f"  Issue: {summary['issue']}")
        print(f"  Severity: {summary['severity']}")
        print(f"  Action: {summary['recommended_action']}")
        print(f"  Payback: {summary['estimated_payback']}")
        
        impact = result["result"]["impact_summary"]
        print("\nENVIRONMENTAL:")
        print(f"  CO2e Saved: {impact['environmental']['co2e_saved_annually']}")
        print(f"  Energy Saved: {impact['environmental']['energy_saved']}")
        
        print("\nFINANCIAL:")
        print(f"  Investment: ${impact['financial']['initial_investment']:,.0f}")
        print(f"  Annual Savings: ${impact['financial']['annual_savings']:,.0f}")
        print(f"  ROI (5yr): {impact['financial']['roi_5yr']:.0f}%")
        
        print("\nWORKFLOW TIMING:")
        total_time = 0
        for trace in result["workflow_trace"]:
            print(f"  {trace.agent_name}: {trace.execution_time:.2f}s")
            total_time += trace.execution_time
        print(f"  TOTAL: {total_time:.2f}s")


if __name__ == "__main__":
    demo()