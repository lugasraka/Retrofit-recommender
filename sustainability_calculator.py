"""
Sustainability Impact Calculator
Calculates CO2e reductions, TCO, and sustainability scores for retrofit recommendations
"""

import json
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SustainabilityImpact:
    """Data class for sustainability impact metrics"""
    co2e_avoided_tons_per_year: float
    energy_savings_kwh_per_year: float
    cost_savings_usd_per_year: float
    payback_period_years: float
    total_cost_of_ownership_5yr: float
    circularity_score: float  # 0-100
    sustainability_rating: str  # A+ to D
    lifecycle_emissions_kg_co2e: float
    compliance_frameworks: list


class SustainabilityCalculator:
    """Calculate sustainability metrics for equipment retrofits"""
    
    # Regional carbon intensity factors (kg CO2e per kWh)
    # Source: IEA 2025, Electricity Maps
    CARBON_INTENSITY = {
        "US_AVERAGE": 0.385,
        "US_CALIFORNIA": 0.201,
        "US_TEXAS": 0.429,
        "EU_AVERAGE": 0.255,
        "GERMANY": 0.311,
        "FRANCE": 0.052,  # Heavy nuclear
        "UK": 0.233,
        "CHINA": 0.555,
        "INDIA": 0.708,
        "GLOBAL_AVERAGE": 0.475
    }
    
    # Equipment baseline power consumption (kW)
    EQUIPMENT_POWER = {
        "valve": 0.5,  # Actuator power
        "actuator": 0.3,
        "sensor": 0.01,
        "controller": 0.05,
        "pump": 15.0,
        "compressor": 30.0,
        "hvac_system": 50.0
    }
    
    # Typical annual runtime hours by equipment type
    RUNTIME_HOURS = {
        "continuous": 8760,  # 24/7 operation
        "standard": 6000,    # 250 days × 24 hours
        "intermittent": 3000,  # 50% duty cycle
        "seasonal": 2000     # HVAC seasonal
    }
    
    # Product lifecycle emissions (kg CO2e per unit) - cradle-to-gate
    # Estimated based on material composition and manufacturing
    LIFECYCLE_EMISSIONS = {
        "VALVE-HEFF-PRO-001": 85.0,  # Steel + machining
        "VALVE-ECO-BASIC-001": 65.0,
        "ACT-24V-STD-001": 45.0,
        "ACT-MOD-001": 55.0,
        "SENSOR-TEMP-HIGH-001": 12.0,
        "SENSOR-TEMP-BASIC-001": 8.0,
        "SENSOR-PRESS-DIFF-001": 15.0,
        "CTRL-MOD-ADV-001": 120.0,  # Electronics + PCB
        "CTRL-BASIC-001": 80.0,
        "SERVICE-PM-BASIC": 5.0,  # Minimal emissions
        "SERVICE-PM-PRO": 8.0,
        "SERVICE-RETROFIT": 50.0,
        "BUNDLE-VALVE-ACT": 130.0,
        "BUNDLE-CTRL-SENSOR": 155.0,
        "BUNDLE-ENERGY-OPT": 300.0
    }
    
    # Circularity attributes (scoring factors)
    CIRCULARITY_ATTRIBUTES = {
        "refurbished": 40,
        "remanufactured": 35,
        "recyclable_high": 20,  # >80% recyclable
        "recyclable_medium": 10,  # 50-80%
        "take_back_program": 15,
        "modular_design": 10,
        "extended_warranty": 5
    }
    
    def __init__(self, region: str = "US_AVERAGE", electricity_rate: float = 0.12):
        """
        Initialize calculator with regional parameters
        
        Args:
            region: Carbon intensity region (e.g., "US_AVERAGE", "EU_AVERAGE")
            electricity_rate: Electricity cost in USD per kWh
        """
        self.carbon_intensity = self.CARBON_INTENSITY.get(region, self.CARBON_INTENSITY["GLOBAL_AVERAGE"])
        self.electricity_rate = electricity_rate
        self.region = region
    
    def calculate_energy_savings(
        self,
        equipment_type: str,
        efficiency_improvement_pct: float,
        runtime_category: str = "standard",
        baseline_power_kw: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Calculate annual energy and cost savings
        
        Args:
            equipment_type: Type of equipment (valve, actuator, etc.)
            efficiency_improvement_pct: Expected efficiency improvement (e.g., 15 for 15%)
            runtime_category: Runtime profile (continuous, standard, intermittent, seasonal)
            baseline_power_kw: Override default power consumption
        
        Returns:
            Tuple of (energy_savings_kwh_per_year, cost_savings_usd_per_year)
        """
        # Get baseline power consumption
        power_kw = baseline_power_kw or self.EQUIPMENT_POWER.get(equipment_type, 1.0)
        
        # Get annual runtime hours
        runtime_hours = self.RUNTIME_HOURS.get(runtime_category, 6000)
        
        # Calculate baseline energy consumption
        baseline_kwh = power_kw * runtime_hours
        
        # Calculate savings
        energy_savings_kwh = baseline_kwh * (efficiency_improvement_pct / 100)
        cost_savings_usd = energy_savings_kwh * self.electricity_rate
        
        return energy_savings_kwh, cost_savings_usd
    
    def calculate_co2e_avoided(
        self,
        energy_savings_kwh_per_year: float,
        equipment_lifespan_years: int = 10
    ) -> float:
        """
        Calculate CO2e emissions avoided over equipment lifespan
        
        Args:
            energy_savings_kwh_per_year: Annual energy savings
            equipment_lifespan_years: Expected equipment lifespan
        
        Returns:
            Total CO2e avoided in metric tons
        """
        annual_co2e_kg = energy_savings_kwh_per_year * self.carbon_intensity
        annual_co2e_tons = annual_co2e_kg / 1000
        total_co2e_tons = annual_co2e_tons * equipment_lifespan_years
        
        return round(total_co2e_tons, 2)
    
    def calculate_tco(
        self,
        purchase_price: float,
        installation_cost: float,
        annual_maintenance_cost: float,
        annual_energy_cost_savings: float,
        years: int = 5
    ) -> float:
        """
        Calculate Total Cost of Ownership over specified period
        
        Args:
            purchase_price: Initial equipment cost
            installation_cost: One-time installation cost
            annual_maintenance_cost: Yearly maintenance expense
            annual_energy_cost_savings: Yearly energy cost reduction (negative = savings)
            years: Analysis period
        
        Returns:
            Total cost of ownership in USD
        """
        total_maintenance = annual_maintenance_cost * years
        total_energy_savings = annual_energy_cost_savings * years
        
        tco = purchase_price + installation_cost + total_maintenance - total_energy_savings
        
        return round(tco, 2)
    
    def calculate_payback_period(
        self,
        initial_investment: float,
        annual_savings: float
    ) -> float:
        """
        Calculate simple payback period
        
        Args:
            initial_investment: Upfront cost (equipment + installation)
            annual_savings: Yearly cost reduction
        
        Returns:
            Payback period in years (returns 999 if no positive savings)
        """
        if annual_savings <= 0:
            return 999.0
        
        payback = initial_investment / annual_savings
        return round(payback, 1)
    
    def calculate_circularity_score(self, product_sku: str, catalog_data: Dict) -> float:
        """
        Calculate circularity score (0-100) based on product attributes
        
        Args:
            product_sku: Product SKU to evaluate
            catalog_data: Product catalog dictionary
        
        Returns:
            Circularity score (0-100)
        """
        # Find product in catalog
        product = next((p for p in catalog_data if p['sku'] == product_sku), None)
        if not product:
            return 0.0
        
        score = 0.0
        
        # Check for circularity attributes in product specs/name
        specs_lower = product.get('specs', '').lower()
        name_lower = product.get('name', '').lower()
        combined_text = f"{specs_lower} {name_lower}"
        
        if 'refurbished' in combined_text:
            score += self.CIRCULARITY_ATTRIBUTES['refurbished']
        if 'remanufactured' in combined_text:
            score += self.CIRCULARITY_ATTRIBUTES['remanufactured']
        if 'recyclable' in combined_text or 'aluminum' in combined_text:
            score += self.CIRCULARITY_ATTRIBUTES['recyclable_high']
        if 'modular' in combined_text:
            score += self.CIRCULARITY_ATTRIBUTES['modular_design']
        if 'warranty' in combined_text and any(str(y) in combined_text for y in ['5', '10', 'extended']):
            score += self.CIRCULARITY_ATTRIBUTES['extended_warranty']
        
        # Services inherently have high circularity (repair vs replace)
        if product.get('category') == 'Services':
            score += 25
        
        return min(score, 100.0)
    
    def get_sustainability_rating(self, impact: SustainabilityImpact) -> str:
        """
        Calculate overall sustainability rating (A+ to D)
        
        Args:
            impact: SustainabilityImpact object
        
        Returns:
            Rating string (A+, A, B+, B, C, D)
        """
        # Weighted scoring criteria
        score = 0
        
        # CO2e impact (40% weight)
        if impact.co2e_avoided_tons_per_year >= 50:
            score += 40
        elif impact.co2e_avoided_tons_per_year >= 20:
            score += 30
        elif impact.co2e_avoided_tons_per_year >= 10:
            score += 20
        elif impact.co2e_avoided_tons_per_year >= 5:
            score += 10
        
        # Payback period (30% weight)
        if impact.payback_period_years <= 2:
            score += 30
        elif impact.payback_period_years <= 3:
            score += 25
        elif impact.payback_period_years <= 5:
            score += 15
        elif impact.payback_period_years <= 7:
            score += 5
        
        # Circularity (20% weight)
        score += (impact.circularity_score / 100) * 20
        
        # Lifecycle emissions (10% weight)
        if impact.lifecycle_emissions_kg_co2e < 50:
            score += 10
        elif impact.lifecycle_emissions_kg_co2e < 100:
            score += 7
        elif impact.lifecycle_emissions_kg_co2e < 200:
            score += 4
        
        # Assign rating
        if score >= 85:
            return "A+"
        elif score >= 75:
            return "A"
        elif score >= 65:
            return "B+"
        elif score >= 55:
            return "B"
        elif score >= 45:
            return "C"
        else:
            return "D"
    
    def get_compliance_frameworks(self, co2e_avoided: float, has_documentation: bool = True) -> list:
        """
        Identify which sustainability frameworks this retrofit supports
        
        Args:
            co2e_avoided: Annual CO2e reduction in tons
            has_documentation: Whether proper documentation exists
        
        Returns:
            List of applicable framework names
        """
        frameworks = []
        
        if co2e_avoided > 0 and has_documentation:
            frameworks.append("GHG Protocol Scope 2")
            frameworks.append("ISO 50001 (Energy Management)")
            
        if co2e_avoided >= 10:
            frameworks.append("CDP Climate Change Response")
            frameworks.append("SBTi - Science Based Targets")
            
        if co2e_avoided >= 50:
            frameworks.append("TCFD (Task Force on Climate-related Financial Disclosures)")
            frameworks.append("EU CSRD (Corporate Sustainability Reporting Directive)")
        
        return frameworks
    
    def calculate_full_impact(
        self,
        product_sku: str,
        catalog_data: list,
        equipment_type: str,
        efficiency_improvement_pct: float,
        purchase_price: float,
        installation_cost: float = 0.0,
        annual_maintenance_cost: float = 0.0,
        runtime_category: str = "standard",
        equipment_lifespan_years: int = 10,
        baseline_power_kw: Optional[float] = None
    ) -> SustainabilityImpact:
        """
        Calculate comprehensive sustainability impact for a retrofit recommendation
        
        Args:
            product_sku: SKU of recommended product
            catalog_data: Product catalog
            equipment_type: Type of equipment
            efficiency_improvement_pct: Expected efficiency gain
            purchase_price: Product cost
            installation_cost: Installation expense
            annual_maintenance_cost: Yearly maintenance cost
            runtime_category: Operation profile
            equipment_lifespan_years: Expected lifespan
            baseline_power_kw: Override power consumption
        
        Returns:
            SustainabilityImpact object with all metrics
        """
        # Calculate energy and cost savings
        energy_savings_kwh, cost_savings_usd = self.calculate_energy_savings(
            equipment_type,
            efficiency_improvement_pct,
            runtime_category,
            baseline_power_kw
        )
        
        # Calculate CO2e avoided
        co2e_avoided = self.calculate_co2e_avoided(energy_savings_kwh, equipment_lifespan_years)
        annual_co2e = co2e_avoided / equipment_lifespan_years
        
        # Calculate TCO
        tco_5yr = self.calculate_tco(
            purchase_price,
            installation_cost,
            annual_maintenance_cost,
            cost_savings_usd,
            years=5
        )
        
        # Calculate payback
        initial_investment = purchase_price + installation_cost
        payback = self.calculate_payback_period(initial_investment, cost_savings_usd)
        
        # Calculate circularity score
        circularity = self.calculate_circularity_score(product_sku, catalog_data)
        
        # Get lifecycle emissions
        lifecycle_emissions = self.LIFECYCLE_EMISSIONS.get(product_sku, 100.0)
        
        # Get compliance frameworks
        frameworks = self.get_compliance_frameworks(annual_co2e)
        
        # Create impact object
        impact = SustainabilityImpact(
            co2e_avoided_tons_per_year=annual_co2e,
            energy_savings_kwh_per_year=energy_savings_kwh,
            cost_savings_usd_per_year=cost_savings_usd,
            payback_period_years=payback,
            total_cost_of_ownership_5yr=tco_5yr,
            circularity_score=circularity,
            sustainability_rating="",  # Will be set below
            lifecycle_emissions_kg_co2e=lifecycle_emissions,
            compliance_frameworks=frameworks
        )
        
        # Calculate overall rating
        impact.sustainability_rating = self.get_sustainability_rating(impact)
        
        return impact


def format_impact_summary(impact: SustainabilityImpact, currency: str = "USD") -> str:
    """
    Format sustainability impact as human-readable summary
    
    Args:
        impact: SustainabilityImpact object
        currency: Currency symbol
    
    Returns:
        Formatted summary string
    """
    summary = f"""
### 🌱 Sustainability Impact Summary

**Rating:** {impact.sustainability_rating} | **Payback Period:** {impact.payback_period_years} years

#### Environmental Impact
- **CO2e Avoided:** {impact.co2e_avoided_tons_per_year:.1f} tons/year
- **Energy Savings:** {impact.energy_savings_kwh_per_year:,.0f} kWh/year
- **Lifecycle Emissions:** {impact.lifecycle_emissions_kg_co2e:.0f} kg CO2e (product manufacturing)
- **Circularity Score:** {impact.circularity_score:.0f}/100

#### Financial Impact
- **Annual Cost Savings:** ${impact.cost_savings_usd_per_year:,.0f}/year
- **5-Year TCO:** ${impact.total_cost_of_ownership_5yr:,.0f}
- **ROI:** {(impact.cost_savings_usd_per_year * 5 / impact.total_cost_of_ownership_5yr * 100):.0f}%

#### Compliance & Reporting
{chr(10).join([f"✓ {fw}" for fw in impact.compliance_frameworks]) if impact.compliance_frameworks else "ℹ️ Minimal impact - limited compliance applicability"}
"""
    return summary


# Example usage for testing
if __name__ == "__main__":
    # Initialize calculator for US average
    calc = SustainabilityCalculator(region="US_AVERAGE", electricity_rate=0.12)
    
    # Example: High-efficiency valve upgrade
    sample_catalog = [
        {
            "sku": "VALVE-HEFF-PRO-001",
            "name": "High-Efficiency Valve Pro+",
            "specs": "PN25, DN65, Stainless Steel, 95% efficiency",
            "category": "Valves",
            "price": "€1,299.99"
        }
    ]
    
    impact = calc.calculate_full_impact(
        product_sku="VALVE-HEFF-PRO-001",
        catalog_data=sample_catalog,
        equipment_type="valve",
        efficiency_improvement_pct=15.0,
        purchase_price=1299.99,
        installation_cost=200.0,
        annual_maintenance_cost=50.0,
        runtime_category="continuous",
        equipment_lifespan_years=15,
        baseline_power_kw=50.0  # 50kW pump system
    )
    
    print(format_impact_summary(impact))
    print(f"\nDetailed Metrics:")
    print(f"  CO2e/year: {impact.co2e_avoided_tons_per_year:.2f} tons")
    print(f"  Payback: {impact.payback_period_years:.1f} years")
    print(f"  Rating: {impact.sustainability_rating}")
