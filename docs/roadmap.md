# Product Roadmap: Retrofit-Recommender
## 18-Month Strategic Development Plan

**Last Updated:** January 29, 2026  
**Owner:** Product Management  
**Review Cycle:** Monthly

---

## Vision & Strategic Themes

**Product Vision:** Transform industrial maintenance from reactive firefighting into proactive, data-driven sustainability optimization that delivers measurable environmental and financial outcomes.

**Strategic Pillars:**
1. **AI Excellence:** Best-in-class recommendation accuracy through RAG + GenAI
2. **Sustainability First:** Every feature advances decarbonization goals
3. **Enterprise Ready:** Production-grade reliability, security, and compliance
4. **Ecosystem Integration:** Seamless connectivity with existing industrial systems

---

## Roadmap Overview

```
Q1 2026 (Now)        Q2 2026              Q3 2026              Q4 2026              Q1-Q2 2027
Foundation           Scale                Differentiation      Enterprise           Innovation
─────────────────────────────────────────────────────────────────────────────────────────────
✅ MVP               MLOps                GenAI                Compliance           Next-Gen AI
✅ RAG               A/B Testing          Personalization      Human-in-Loop        Multi-modal
🔄 CO2e Calc         API Integration      Multi-objective      Portfolio Mgmt       RL Optimization
🔄 User Research     Dashboard            Predictive Maint     Carbon Platform      Marketplace
                     Monitoring           Catalog Expansion    Mobile App           Global Scale
```

---

## Q1 2026: Foundation & Validation ✅

**Theme:** Prove Product-Market Fit with Design Partners

**Status:** 60% Complete (as of Jan 29, 2026)

### Completed ✅
- [x] MVP with RAG-based recommendations (7 scenarios)
- [x] Safety validation logic (voltage/pressure mismatch)
- [x] Product catalog (30 items)
- [x] Knowledge base with vector search (FAISS)
- [x] Basic Streamlit UI
- [x] Product strategy document
- [x] KPI framework defined

### In Progress 🔄
- [ ] **CO2e calculation engine** (80% complete)
  - ✅ Regional carbon intensity factors
  - ✅ Equipment baseline power consumption
  - ✅ TCO calculator
  - 🔄 Integration with UI (THIS RELEASE)
  - ⏳ User testing & validation
  
- [ ] **User feedback loop** (40% complete)
  - ✅ In-app feedback buttons (helpful/not helpful)
  - 🔄 Implementation tracking (manual survey)
  - ⏳ Automated outcome collection
  
- [ ] **User research documentation** (70% complete)
  - ✅ 12 interviews completed
  - ✅ Personas developed
  - ✅ Journey maps
  - 🔄 Usability testing (3 sessions scheduled)

### Planned ⏳
- [ ] **Analytics instrumentation**
  - Event tracking (Mixpanel/Amplitude)
  - Recommendation accuracy measurement
  - Latency monitoring
  
- [ ] **Catalog expansion to 50 products**
  - Add LCA data (lifecycle emissions)
  - Circularity attributes
  - Expanded compatibility matrix

### Success Metrics (Q1)
- ✅ 3 design partners onboarded
- 🎯 50+ recommendations generated
- 🎯 10+ user interviews completed
- 🎯 80%+ recommendation accuracy (user feedback)
- 🎯 Baseline CO2e calculation validated

---

## Q2 2026: Scale & Measure

**Theme:** Enterprise-Ready Product with Full Observability

**Target Launch:** April 1, 2026

### Features

#### 1. MLOps & Model Monitoring 🤖
**Priority:** P0 (Blocker for enterprise sales)

**User Stories:**
- As a **Product Manager**, I want to see real-time recommendation accuracy trends, so I can identify when model performance degrades
- As an **Engineering Lead**, I want automated drift detection, so I can retrain models proactively
- As a **User**, I want confidence scores, so I know how much to trust each recommendation

**Implementation:**
- Integrate RAGAS metrics (faithfulness, relevance, context precision)
- Model versioning and A/B testing infrastructure
- Weekly accuracy reports on holdout test set
- Drift detection alerts (email + Slack)

**Success Criteria:**
- P95 latency <5 seconds
- Recommendation accuracy >85%
- <10% accuracy drift per quarter

**Effort:** 3 weeks (1 ML engineer)

---

#### 2. A/B Testing Framework 🧪
**Priority:** P0 (Required for data-driven iteration)

**User Stories:**
- As a **PM**, I want to test if TCO charts increase implementation rate, so I can validate design decisions
- As an **Engineer**, I want to A/B test prompt variations, so I can optimize LLM performance

**Implementation:**
- Statistical testing framework (Bayesian A/B testing)
- Experimentation dashboard
- Stratified randomization (by user segment)

**Example Tests:**
1. Control (text-only recommendation) vs. Variant (with CO2e chart) → Measure implementation rate
2. Short prompt vs. Long prompt → Measure accuracy & latency
3. Top-3 options vs. Single recommendation → Measure user satisfaction

**Success Criteria:**
- Run 5+ experiments per quarter
- 80% statistical power for primary metric

**Effort:** 2 weeks (1 full-stack engineer)

---

#### 3. Advanced RAG (Reranking + Query Expansion) 🔍
**Priority:** P1 (Improves accuracy)

**Current Limitation:** Basic vector similarity sometimes retrieves irrelevant context

**Enhancement:**
- **Reranking:** Use cross-encoder to re-score retrieved docs for relevance
- **Query Expansion:** Rephrase user query to improve recall
- **Hybrid Search:** Combine semantic (vector) + keyword (BM25) search

**Expected Impact:**
- Context precision: 0.75 → 0.85
- Answer relevance: 0.80 → 0.90

**Effort:** 2 weeks (1 ML engineer)

---

#### 4. API for BMS/ERP Integration 🔌
**Priority:** P1 (Enterprise customer requirement)

**User Stories:**
- As an **IT Director**, I want to integrate Retrofit-Recommender with our Maximo CMMS, so maintenance teams don't need to switch tools
- As a **Facilities Manager**, I want recommendations triggered automatically when equipment degrades, so I don't miss proactive opportunities

**Implementation:**
- RESTful API (FastAPI)
- Authentication (OAuth 2.0, API keys)
- Webhooks for event notifications
- SDK for common ERP systems (SAP, Oracle, Maximo)

**Endpoints:**
```python
POST /api/v1/recommendations
{
  "equipment_id": "valve_001",
  "error_description": "Flow resistance high",
  "device_specs": {...},
  "preferences": {"optimize_for": "carbon"}
}

Response:
{
  "recommendation_id": "rec_12345",
  "product": {...},
  "sustainability_impact": {...},
  "confidence_score": 0.89
}
```

**Success Criteria:**
- 3 pilot integrations (SAP, Maximo, proprietary CMMS)
- API latency <2 seconds (P95)
- 99.5% uptime

**Effort:** 4 weeks (2 engineers)

---

#### 5. Sustainability Dashboard (CDP/TCFD Reporting) 📊
**Priority:** P1 (Key differentiation)

**User Stories:**
- As a **Sustainability Director**, I want a dashboard showing cumulative CO2e avoided across all recommendations, so I can report progress to the Board
- As an **ESG Analyst**, I want export functionality aligned to CDP format, so I don't need to reformat data

**Implementation:**
- Portfolio-level metrics (all recommendations aggregated)
- Time-series charts (monthly CO2e avoided)
- Export to Excel (CDP/TCFD templates)
- Filterable by facility, equipment type, time period

**Metrics Displayed:**
- Cumulative CO2e avoided (tons)
- Energy savings (MWh)
- Cost savings ($)
- Recommendations by status (pending, approved, implemented)
- Compliance framework coverage

**Success Criteria:**
- 100% of pilot customers use dashboard monthly
- 5+ customers reference dashboard in sustainability reports

**Effort:** 3 weeks (1 full-stack engineer + 1 designer)

---

#### 6. Catalog Expansion (50 → 200 products) 📦
**Priority:** P2 (Important but not blocking)

**Focus:**
- Add LCA data (cradle-to-gate emissions) for all products
- Expand circularity attributes (refurbished, take-back programs)
- Include 3+ vendors per product category (vendor-neutral)

**Partnerships:**
- Ecoinvent (LCA database subscription)
- Grainger, MSC Industrial (catalog data)

**Success Criteria:**
- 200 products with complete data (specs, LCA, pricing)
- 95% catalog completeness

**Effort:** Ongoing (4 weeks total, distributed)

---

### Q2 Milestones
- **April 15:** MLOps monitoring live
- **May 1:** API beta launch (3 partners)
- **May 15:** Dashboard v1.0 launch
- **June 1:** Advanced RAG deployed
- **June 30:** Q2 retrospective & planning

### Q2 Success Metrics
- **10 paying customers** (convert from pilots)
- **500 recommendations** generated
- **15% implementation rate**
- **200 tons CO2e avoided** (cumulative)
- **85% recommendation accuracy**
- **$200K ARR**

---

## Q3 2026: Differentiation & GTM

**Theme:** Market Leadership with Unique AI Capabilities

**Target Launch:** July 1, 2026

### Features

#### 1. GenAI Personalization (Fine-Tuning) 🧠
**Priority:** P0 (Competitive differentiation)

**Current Limitation:** Generic recommendations don't account for customer-specific context (e.g., preferred vendors, past purchasing patterns)

**Enhancement:**
- Fine-tune Llama model on customer asset data
- Personalized recommendations based on historical decisions
- Learning from implementation outcomes

**Example:**
- Customer A always buys Siemens products → Prioritize Siemens-compatible options
- Customer B has 5-year warranty requirement → Filter for products with ≥5yr warranty
- Customer C operates in corrosive environment → Prioritize stainless steel, exclude brass

**Success Criteria:**
- 20% higher implementation rate for personalized recommendations
- 90% recommendation accuracy (vs. 85% generic)

**Effort:** 4 weeks (1 ML engineer)

---

#### 2. Multi-Objective Optimization 🎯
**Priority:** P0 (User research finding #6)

**User Stories:**
- As a **Sustainability Director**, I want to see top 3 options sorted by carbon reduction, so I can maximize environmental impact
- As a **Facilities Manager**, I want to sort by reliability, so I can minimize downtime
- As a **CFO**, I want to sort by TCO, so I can optimize capital allocation

**Implementation:**
- Pareto frontier analysis (cost vs. carbon vs. reliability)
- User-configurable weighting (e.g., 50% cost, 30% carbon, 20% reliability)
- Visual comparison chart

**UI Mockup:**
```
┌─────────────────────────────────────────────┐
│ Optimization Goals (drag to adjust):       │
│ ▓▓▓▓▓▓▓▓░░ Cost (40%)                      │
│ ▓▓▓▓▓▓░░░░ Carbon (30%)                    │
│ ▓▓▓▓▓░░░░░ Reliability (30%)               │
└─────────────────────────────────────────────┘

Top 3 Recommendations:
1. VALVE-HEFF-PRO → Best Carbon (25 tons/yr)
2. VALVE-ECO → Best Cost ($800 TCO)
3. VALVE-ULTRA → Best Reliability (MTBF 10 years)
```

**Success Criteria:**
- 60%+ users adjust optimization weights
- 10% increase in user satisfaction (NPS)

**Effort:** 3 weeks (1 engineer + 1 designer)

---

#### 3. Predictive Maintenance Integration 📈
**Priority:** P1 (Proactive vs. reactive)

**User Stories:**
- As a **Maintenance Manager**, I want to receive proactive retrofit recommendations 90 days before equipment fails, so I can avoid unplanned downtime

**Implementation:**
- Time-series anomaly detection on equipment sensor data
- Integration with IoT platforms (ThingWorx, AWS IoT)
- Predictive failure scoring (0-100% risk)
- Automated recommendations when risk >70%

**Example Workflow:**
1. Sensor detects valve vibration increasing 15% over 30 days
2. AI predicts 80% failure risk within 90 days
3. System auto-generates retrofit recommendation
4. Notification sent to maintenance manager

**Success Criteria:**
- 30% of recommendations triggered proactively (vs. 100% reactive)
- 50% reduction in unplanned downtime for pilot customers

**Effort:** 5 weeks (1 ML engineer + 1 IoT integration specialist)

---

#### 4. Catalog Expansion (200+ products with full LCA) 📚
- Expand to 250 products
- 100% LCA data coverage
- Add "refurbished" options for 30% of categories

**Effort:** 4 weeks (1 data engineer)

---

#### 5. White-Label Partner Channel 🤝
**Priority:** P2 (GTM expansion)

**Strategy:** Enable sustainability consultancies (Deloitte, EY, local firms) to resell Retrofit-Recommender under their brand

**Implementation:**
- White-label UI (custom branding, logo)
- Partner training program
- Revenue share: 70% us / 30% partner
- Partner dashboard (track client usage, outcomes)

**Target:** 5 partners signed by Q3 end

**Effort:** 3 weeks (1 PM + 1 engineer)

---

### Q3 Milestones
- **July 15:** GenAI personalization beta
- **August 1:** Multi-objective optimization launch
- **September 1:** Predictive maintenance pilot (3 customers)
- **September 30:** Q3 review

### Q3 Success Metrics
- **25 paying customers**
- **85% recommendation accuracy**
- **1,000 tons CO2e avoided** (cumulative)
- **$600K ARR**
- **3 public case studies**

---

## Q4 2026: Enterprise & Compliance

**Theme:** Regulatory Compliance & Enterprise Sales Readiness

### Features

#### 1. Compliance Validation (ISO 50001, EU Ecodesign) ✅
- Automated compliance checking
- Generate audit documentation
- Track regulatory changes

#### 2. Human-in-the-Loop Approval Workflows 👨‍💼
- Safety-critical recommendations require engineer approval
- Audit trail for regulatory compliance
- Role-based access control (RBAC)

#### 3. Portfolio Optimization (Facility-Wide) 🏢
- Prioritize retrofits across 1000+ assets
- Budget constraint optimization
- Carbon budget allocation

#### 4. Carbon Platform Integration (Watershed, Persefoni) 🌍
- API connectors to carbon accounting software
- Auto-sync CO2e data
- Scope 2 emission tracking

#### 5. Mobile App (iOS/Android) 📱
- Field technician access
- Barcode scanning for equipment identification
- Offline mode

### Q4 Success Metrics
- **40 paying customers**
- **90% customer retention**
- **3,000 tons CO2e avoided**
- **$1.2M ARR**
- **NPS 50+**

---

## Q1-Q2 2027: AI Innovation & Scale

**Theme:** Next-Generation AI & Global Expansion

### Features

#### 1. Multi-Modal AI (Analyze Photos + Datasheets) 📸
- Upload equipment photo → Auto-identify make/model
- Parse PDF datasheets → Extract specs

#### 2. Reinforcement Learning from Outcomes 🔁
- Learn from implementation results
- Improve recommendations based on actual vs. predicted savings

#### 3. Circular Economy Marketplace 🔄
- Resale platform for removed equipment
- Refurbishment certification
- Carbon credit generation

#### 4. Global Expansion (APAC, LATAM) 🌏
- Localized compliance (China GB standards, Japan JIS)
- Multi-language support
- Regional carbon intensity data

#### 5. Strategic OEM Partnerships 🏭
- Co-development with Emerson, Honeywell, Siemens
- Preferential catalog placement
- Joint go-to-market

### Q1-Q2 2027 Success Metrics
- **80+ paying customers**
- **10,000 tons CO2e avoided** (cumulative)
- **$2M+ ARR**
- **95% recommendation accuracy**

---

## Feature Request Backlog (Not Prioritized)

### User-Requested Features (from research)
- [ ] **Collaboration:** Share recommendations with team, commenting
- [ ] **Custom knowledge base:** Upload company-specific maintenance procedures
- [ ] **Equipment lifecycle tracking:** Full cradle-to-grave carbon accounting
- [ ] **Warranty tracking:** Alert when warranty expires
- [ ] **Bulk import:** Upload 1000+ assets at once
- [ ] **Email alerts:** Weekly digest of recommendations
- [ ] **Carbon offsetting:** Purchase offsets for residual emissions
- [ ] **Benchmarking:** Compare performance vs. industry peers

### Technical Debt
- [ ] Migrate from Streamlit to React (better UX)
- [ ] Move from FAISS (CPU) to Pinecone (cloud vector DB)
- [ ] Upgrade to Llama 4 when released
- [ ] Implement caching layer (Redis)
- [ ] Load testing (1000+ concurrent users)

---

## Dependencies & Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **LLM API rate limits** (Hugging Face free tier) | High | Migrate to paid tier OR self-host model (cost: $2K/mo) |
| **LCA data access** (Ecoinvent subscription $10K/yr) | Medium | Use proxy data short-term, budget for subscription in Q2 |
| **Slow enterprise sales cycles** (9-18 months) | High | Focus on PLG (product-led growth) with freemium tier |
| **Competitor copies features** | Medium | Build data moat (customer outcome data), file patents |
| **Regulatory changes invalidate calculations** | Low | Monitor GHG Protocol updates, modular architecture |

---

## Resource Requirements

### Q2 2026
- **Engineering:** 2 FTE (1 full-stack, 1 ML)
- **Product:** 1 FTE
- **Design:** 0.5 FTE
- **Customer Success:** 0.5 FTE
- **Budget:** $250K (salaries + tools + partnerships)

### Q3-Q4 2026
- **Engineering:** 3 FTE (add 1 IoT specialist)
- **Product:** 1 FTE
- **Design:** 0.5 FTE
- **Sales:** 1 FTE (add for GTM)
- **Customer Success:** 1 FTE
- **Budget:** $400K/quarter

---

## Success Definition

**Product-Market Fit Achieved When:**
- ✅ 40%+ weekly active user rate (DAU/MAU)
- ✅ 20%+ implementation rate (recommendations → purchases)
- ✅ NPS >40 with 50+ responses
- ✅ 3+ customers willing to provide public testimonials
- ✅ Organic inbound leads (word-of-mouth)

**Ready to Scale When:**
- ✅ 95%+ uptime over 90 days
- ✅ <10 critical bugs per 1000 users
- ✅ Documented AI governance framework
- ✅ $1M ARR achieved
- ✅ 5,000 tons CO2e avoided (proof of impact)

---

## Document Control
**Version:** 1.0  
**Last Updated:** January 29, 2026  
**Owner:** Product Management  
**Next Review:** February 28, 2026 (monthly)  
**Stakeholders:** Engineering Lead, Design Lead, Sales Lead, CEO
