# KPI Dashboard & Measurement Framework
## Retrofit-Recommender Product Metrics

---

## Dashboard Overview

**Purpose:** Real-time visibility into product performance, user engagement, sustainability impact, and business health.  
**Audience:** Product team, engineering, leadership, investors  
**Update Frequency:** Daily (automated), with weekly review meetings

---

## 1. North Star Metric

### Cumulative CO2e Avoided (Metric Tons)

**Current:** 0 tons (baseline)  
**Target:** 50,000 tons by Q4 2027

```
Calculation: Σ (Energy Savings per Retrofit × Regional Carbon Intensity × Equipment Runtime Hours)

Example:
- Retrofit: Replace Legacy Valve Gen1 → High-Efficiency Valve Pro+
- Energy Savings: 15% reduction on 50 kW system
- Annual Savings: 50 kW × 0.15 × 8,760 hours = 65,700 kWh/year
- Carbon Intensity: 0.385 kg CO2e/kWh (U.S. average)
- CO2e Avoided: 65,700 × 0.385 = 25.3 tons CO2e/year
```

**Data Sources:**
- User-reported: Equipment power rating, runtime hours
- System-calculated: Energy savings % from catalog
- External API: Electricity Maps for regional carbon intensity

**Dashboard Visualization:**
- Line chart showing cumulative tons over time
- Breakdown by customer, equipment type, region
- Comparison to SBTi pathway (1.5°C scenario)

---

## 2. Product Health KPIs

### 2.1 Recommendation Accuracy

**Definition:** % of recommendations rated as "helpful" or "implemented" by users  
**Target:** 85% (6mo) → 95% (12mo)  
**Current:** Baseline measurement in progress

**Measurement Method:**
1. **User Feedback:** After recommendation, ask "Was this helpful?" (Yes/No/Somewhat)
2. **Implementation Tracking:** Link recommendations to purchase orders (180-day window)
3. **Outcome Validation:** For implemented retrofits, measure actual vs. predicted energy savings

**Data Collection:**
```python
# In-app feedback modal after recommendation display
feedback_options = {
    "helpful_and_implemented": 1.0,
    "helpful_not_yet_implemented": 0.8,
    "somewhat_helpful": 0.5,
    "not_helpful": 0.0,
    "recommendation_was_incorrect": -1.0  # Flagged for review
}

accuracy_score = (sum(feedback_scores) / total_recommendations) * 100
```

**Dashboard Elements:**
- Accuracy trend over time
- Breakdown by scenario type (valve, sensor, controller)
- Low-performing scenarios flagged for improvement
- User comments/qualitative feedback

**Action Triggers:**
- If accuracy <80% for any scenario → Immediate review of knowledge base + RAG tuning
- If 3+ "incorrect" flags → Pause scenario, investigate root cause

---

### 2.2 User Adoption Rate (DAU/MAU)

**Definition:** Daily Active Users / Monthly Active Users × 100  
**Target:** 40% (6mo) → 60% (12mo)  
**Current:** 0% (pre-launch)

**Rationale:** High DAU/MAU indicates sticky product with regular usage (vs. one-time trial)

**Segmentation:**
- Power Users (5+ recommendations/week): Target 10% of users
- Regular Users (1-4 recommendations/week): Target 30% of users
- Occasional Users (<1/week): Target 60% of users

**Retention Cohorts:**
- Day 1, Day 7, Day 30, Day 90 retention rates
- Churn analysis: Why do users stop using the product?

**Dashboard Elements:**
- DAU/MAU ratio with 30-day moving average
- Cohort retention curves
- Feature usage heatmap (which scenarios most popular)

**Action Triggers:**
- If DAU/MAU <30% → Investigate onboarding friction, add notification system
- If D7 retention <40% → Improve time-to-value (faster onboarding)

---

### 2.3 Recommendation-to-Implementation Rate

**Definition:** % of recommendations that result in actual equipment purchases/retrofits  
**Target:** 15% (6mo) → 30% (12mo)  
**Current:** 0% (baseline)

**Tracking Mechanism:**
1. **User Self-Reported:** "Did you implement this recommendation?" checkbox with date
2. **Integration:** API hooks to procurement systems (SAP, Oracle) to auto-detect POs
3. **Survey Follow-Up:** 90-day and 180-day email asking for implementation status

**Calculation:**
```
Implementation Rate = (# Recommendations Implemented / # Total Recommendations) × 100

Filters:
- Only count recommendations >30 days old (allow time for procurement)
- Exclude "safety alert" recommendations that were blocked
```

**Dashboard Elements:**
- Implementation rate by scenario type
- Time-to-implementation distribution (median: 60 days)
- Implementation rate by customer segment (SMB vs. enterprise)
- Reasons for non-implementation (too expensive, not compatible, other)

**Benchmarking:**
- Industry baseline: ~10% for generic maintenance recommendations
- Our target: 30% (3x better due to AI precision + ROI visibility)

---

### 2.4 Time to Value

**Definition:** Days from user signup to first "high-confidence" recommendation (>80% model confidence)  
**Target:** 14 days (6mo) → 7 days (12mo)  
**Current:** Measure during pilot phase

**Breakdown:**
- Account creation to first login: Target <1 hour
- First login to asset data upload: Target <2 days
- Asset data uploaded to first recommendation: Target <1 day
- First recommendation to user validation: Target <7 days

**Dashboard Elements:**
- Funnel chart showing drop-off at each stage
- Median/P90 time to value
- Correlation between TTV and long-term retention

**Action Triggers:**
- If TTV >21 days → Simplify onboarding, add quick-start templates
- If 40%+ users abandon before first recommendation → Improve data import UX

---

## 3. Sustainability Impact KPIs

### 3.1 CO2e Impact per Customer

**Definition:** Average metric tons CO2e avoided per customer per year  
**Target:** 500 tons (6mo) → 2,000 tons (12mo)  
**Current:** 0 tons (baseline)

**Segmentation:**
- By industry: Manufacturing (target 3,000 tons), utilities (target 5,000 tons), commercial buildings (target 500 tons)
- By facility size: <500 assets (200 tons), 500-2000 assets (1,500 tons), >2000 assets (5,000 tons)

**Dashboard Elements:**
- Box plot showing distribution across customers
- Top 10 customers by impact
- Impact per recommendation (avg: 5-25 tons)

---

### 3.2 Circularity Score

**Definition:** % of recommended products with circular economy attributes  
**Target:** 30% of recommendations include refurbished/remanufactured options  
**Current:** 0% (not yet tracked)

**Circular Attributes:**
- **Refurbished:** OEM-certified used equipment with warranty
- **Remanufactured:** Restored to like-new condition
- **Recyclable:** >80% material recyclability at end of life
- **Take-Back Program:** Manufacturer accepts old equipment for recycling

**Calculation:**
```
Circularity Score = (# Recommendations with ≥1 Circular Attribute / Total Recommendations) × 100
```

**Dashboard Elements:**
- Circularity score trend
- Breakdown by attribute type
- Circular product adoption rate (do users choose circular options when offered?)

---

### 3.3 Regulatory Alignment

**Definition:** % of recommendations that help customers meet regulatory requirements  
**Target:** 80% of recommendations aligned to ≥1 standard  
**Current:** To be implemented

**Frameworks Tracked:**
- **GHG Protocol:** Scope 2 emissions (energy use)
- **EU Ecodesign:** Minimum energy performance standards
- **ISO 50001:** Energy management system requirements
- **SBTi:** Science-Based Targets initiative (1.5°C pathway)
- **CDP:** Carbon Disclosure Project reporting

**Dashboard Elements:**
- Tag recommendations with applicable standards
- Customer progress toward SBTi targets (if declared)

---

## 4. Business Health KPIs

### 4.1 Annual Recurring Revenue (ARR)

**Target:** $500K (Q4 2026) → $2M (Q4 2027)  
**Current:** $0 (pre-revenue)

**Breakdown:**
- Freemium → Professional conversions: Target 5% monthly
- Professional → Enterprise upgrades: Target 15% annually
- Churn rate: <10% annually

**Dashboard Elements:**
- ARR growth chart with targets
- MRR (Monthly Recurring Revenue) trend
- Customer segmentation (freemium/pro/enterprise)
- Expansion revenue from upsells

---

### 4.2 Customer Acquisition Cost (CAC) & Payback Period

**Target CAC:** $5,000 (blended)  
**Target Payback:** <12 months  
**Current:** To be measured during GTM

**Calculation:**
```
CAC = (Sales + Marketing Expenses) / # New Customers

Payback Period = CAC / (ARPU × Gross Margin %)

Example:
- CAC: $5,000
- ARPU: $40,000/year
- Gross Margin: 75%
- Payback: $5,000 / ($40,000 × 0.75) = 2 months ✅
```

**Dashboard Elements:**
- CAC by channel (direct sales, partners, PLG)
- Payback period trend
- LTV:CAC ratio (target 5:1)

---

### 4.3 Net Promoter Score (NPS)

**Target:** 45 (6mo) → 60 (12mo)  
**Current:** Baseline measurement during pilot

**Survey Question:** "How likely are you to recommend Retrofit-Recommender to a colleague?" (0-10 scale)

**Segmentation:**
- Promoters (9-10): Target 50%
- Passives (7-8): Target 35%
- Detractors (0-6): Target <15%

**Dashboard Elements:**
- NPS trend with qualitative feedback
- Detractor root cause analysis
- Correlation between NPS and feature usage

---

## 5. AI/ML Performance KPIs

### 5.1 RAG Relevance Score (RAGAS Framework)

**Metrics:**
- **Faithfulness:** How accurately does the answer reflect retrieved context? (Target: >0.90)
- **Answer Relevance:** How well does the answer address the query? (Target: >0.85)
- **Context Precision:** Are retrieved docs relevant? (Target: >0.80)
- **Context Recall:** Does context cover all necessary info? (Target: >0.85)

**Measurement:**
```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

# Automated evaluation on test set (100 curated query-answer pairs)
results = evaluate(
    dataset=test_queries,
    metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
)
```

**Dashboard Elements:**
- Weekly RAGAS score heatmap
- Per-scenario performance breakdown
- Flagged low-scoring queries for knowledge base improvement

**Action Triggers:**
- If faithfulness <0.80 → LLM is hallucinating, strengthen RAG grounding
- If context recall <0.75 → Knowledge base gaps, add missing content

---

### 5.2 LLM Latency (P50, P95, P99)

**Target:**
- P50: <2 seconds
- P95: <5 seconds
- P99: <10 seconds

**Breakdown by Stage:**
- Query embedding: <0.2s
- Vector search: <0.5s
- LLM inference: <2s (P50)
- Response parsing: <0.3s

**Dashboard Elements:**
- Latency distribution chart
- Latency by scenario complexity
- Correlation between latency and user satisfaction

**Action Triggers:**
- If P95 >7 seconds → Optimize prompt length, consider faster model (Llama 3.2 vs. 3.1)
- If >5% requests timeout → Investigate API rate limits, implement retry logic

---

### 5.3 Model Drift Detection

**Definition:** Accuracy degradation over time due to data distribution changes  
**Target:** <10% accuracy drop per quarter  
**Measurement:** Weekly re-evaluation on holdout test set (200 labeled examples)

**Dashboard Elements:**
- Accuracy trend with drift alerts
- Feature distribution shift detection
- Concept drift indicators (e.g., new equipment types not in training data)

**Action Triggers:**
- If accuracy drops >5% → Retrain model with recent user feedback data
- If new equipment types represent >10% of queries → Expand catalog

---

### 5.4 Safety Alert Precision & Recall

**Definition:**
- **Precision:** Of all safety alerts triggered, what % were correct? (Target: >98%)
- **Recall:** Of all actual safety issues, what % did we catch? (Target: >95%)

**Critical Scenarios:**
- Voltage mismatch (e.g., 110V device on 220V system)
- Pressure rating exceeded (e.g., 150 PSI valve on 300 PSI line)
- Incompatible materials (e.g., corrosive fluid with incompatible seals)

**Measurement:**
```
Precision = True Positives / (True Positives + False Positives)
Recall = True Positives / (True Positives + False Negatives)

True Positive: System flagged safety issue, user confirmed it was correct
False Positive: System flagged issue, user confirmed it was safe
False Negative: User reported issue system missed (post-implementation incident)
```

**Dashboard Elements:**
- Confusion matrix for safety alerts
- False positive/negative incidents logged
- Time to detect (from scenario input to alert display)

**Action Triggers:**
- If recall <95% → Safety incident risk, immediately review rule logic
- If precision <95% → Alert fatigue, tighten thresholds to reduce false positives

---

## 6. Operational Metrics

### 6.1 System Uptime

**Target:** 99.5% uptime (43 hours downtime/year allowed)  
**Current:** To be measured post-deployment

**Monitoring:**
- API availability (Hugging Face, Electricity Maps)
- Database uptime (vector store, catalog)
- Frontend availability

---

### 6.2 Support Ticket Volume

**Target:** <10 tickets per 100 active users/month  
**Categories:**
- Bug reports
- Feature requests
- Data quality issues
- "How do I..." questions

**Dashboard Elements:**
- Ticket volume trend
- Resolution time (target: <24 hours for critical, <72 hours for normal)
- Self-service deflection rate (% resolved via docs/FAQs)

---

## 7. Instrumentation Plan

### Events to Track (Mixpanel/Amplitude)

**User Actions:**
- `user_signed_up` (properties: company, industry, role)
- `scenario_selected` (properties: scenario_type, equipment_type)
- `recommendation_generated` (properties: sku, price, co2e_avoided, confidence_score)
- `feedback_submitted` (properties: rating, comment)
- `recommendation_implemented` (properties: implementation_date, actual_savings)
- `safety_alert_triggered` (properties: alert_type, user_action)

**System Events:**
- `api_request` (properties: endpoint, latency, status_code)
- `model_inference` (properties: model_version, tokens_used, latency)
- `error_occurred` (properties: error_type, stack_trace)

**Data Schema:**
```json
{
  "event": "recommendation_generated",
  "timestamp": "2026-01-29T14:32:00Z",
  "user_id": "user_12345",
  "session_id": "session_67890",
  "properties": {
    "scenario_type": "valve_efficiency",
    "equipment_id": "valve_001",
    "recommended_sku": "VALVE-HEFF-PRO-001",
    "price": 1299.99,
    "co2e_avoided_tons_per_year": 25.3,
    "confidence_score": 0.89,
    "rag_context_ids": ["kb_sec_1", "kb_sec_3", "kb_sec_7"],
    "llm_latency_ms": 1820,
    "safety_alert": false
  }
}
```

---

## 8. Reporting Cadence

### Daily (Automated)
- System health (uptime, latency, error rate)
- User activity (signups, recommendations, feedback)

### Weekly (Product Team Review)
- KPI scorecard review (vs. targets)
- Top issues/blockers
- Experiment results (A/B tests)

### Monthly (Leadership Review)
- KPI dashboard presentation
- User research insights
- Roadmap adjustments
- Customer case studies

### Quarterly (Board/Investor Update)
- Business metrics (ARR, CAC, NPS)
- Sustainability impact (cumulative CO2e)
- Strategic initiatives progress
- Competitive landscape changes

---

## 9. Experimentation Framework

### A/B Testing Infrastructure

**Hypothesis Example:**
> "Adding a visual TCO comparison chart will increase implementation rate from 15% to 22% by making ROI more tangible."

**Test Setup:**
- **Control (A):** Current text-based recommendation display
- **Variant (B):** Add 5-year TCO bar chart (equipment cost + energy cost + maintenance)
- **Sample Size:** 200 users per variant (80% power, 5% significance)
- **Duration:** 4 weeks
- **Success Metric:** Implementation rate (secondary: time to decision)

**Dashboard Elements:**
- Active experiments list
- Results tracker (statistical significance, effect size)
- Learning repository (what worked, what didn't)

---

## 10. Data Quality Metrics

### Catalog Completeness

**Definition:** % of products with all required fields populated  
**Target:** 95% completeness  
**Required Fields:**
- Technical specs (voltage, pressure, flow rate)
- Pricing
- LCA data (cradle-to-gate emissions)
- Compatibility matrix
- Warranty/lifespan

**Dashboard Elements:**
- Completeness score by product category
- Missing field heatmap
- Data enrichment backlog

---

## Document Control
**Version:** 1.0  
**Last Updated:** January 29, 2026  
**Owner:** Product Management & Analytics  
**Review Cycle:** Weekly (operational), Monthly (strategic)
