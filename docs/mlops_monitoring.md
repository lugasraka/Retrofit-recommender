# MLOps & Model Monitoring Framework
## AI Performance Observability for Retrofit-Recommender

**Version:** 1.0  
**Date:** January 29, 2026  
**Owner:** ML Engineering + Product Management

---

## Overview

This document outlines the MLOps practices and monitoring infrastructure for maintaining high-quality AI recommendations in production. Our approach ensures **95%+ accuracy**, **<5s P95 latency**, and **<10% quarterly drift** through continuous monitoring, automated testing, and human-in-the-loop validation.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  INSTRUMENTATION LAYER                                          │
│  - Request logging (timestamp, user_id, scenario_type)         │
│  - Latency tracking (RAG retrieval, LLM inference, total)      │
│  - Input validation & sanitization                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  RAG PIPELINE                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │   Embedding  │───▶│ Vector Search│───▶│   Reranking     │  │
│  │   (0.2s)     │    │ FAISS (0.5s) │    │ Cross-Encoder   │  │
│  └──────────────┘    └──────────────┘    └─────────────────┘  │
│                                                                 │
│  Metrics: Context precision, context recall, retrieval latency │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  LLM INFERENCE (Llama 3.1-8B)                                   │
│  - Prompt construction with retrieved context                  │
│  - Temperature: 0.05 (deterministic)                           │
│  - Max tokens: 300                                             │
│  - Safety validation (voltage/pressure checks)                 │
│                                                                 │
│  Metrics: Latency, token count, faithfulness, answer relevance │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST-PROCESSING                                                │
│  - JSON parsing & validation                                   │
│  - Sustainability impact calculation                           │
│  - Confidence score assignment                                 │
│  - Safety alert flagging                                       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  MONITORING & FEEDBACK                                          │
│  - Log recommendation (SKU, price, CO2e, confidence)           │
│  - User feedback collection (helpful/not helpful)              │
│  - Implementation tracking (did user purchase?)                │
│  - Error alerting (parsing failures, safety violations)        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Metrics & Thresholds

### 1. Model Accuracy

#### Primary Metric: User Satisfaction Score
**Definition:** % of recommendations rated "helpful" or "very helpful" by users

**Target:** 85% (6mo) → 95% (12mo)

**Measurement:**
```python
satisfaction_score = (
    (very_helpful * 1.0) + 
    (helpful * 0.8) + 
    (somewhat * 0.5) + 
    (not_helpful * 0.0)
) / total_ratings * 100
```

**Alert Thresholds:**
- 🟢 **Healthy:** ≥85%
- 🟡 **Warning:** 80-85% (review within 48 hours)
- 🔴 **Critical:** <80% (immediate investigation)

**Action Plan (if <80%):**
1. Analyze low-rated recommendations for patterns
2. Review RAG context quality (was relevant knowledge retrieved?)
3. Check for LLM hallucinations (answer vs. context mismatch)
4. Test prompt variations with A/B testing
5. Retrain if systemic issue identified

---

#### Secondary Metric: Implementation Rate
**Definition:** % of recommendations that result in actual equipment purchases

**Target:** 15% (6mo) → 30% (12mo)

**Tracking:** 
- User self-reports via "Did you implement this?" checkbox
- API integration with procurement systems (automated detection)
- 90-day and 180-day follow-up surveys

**Alert Threshold:**
- 🔴 **Critical:** <10% (indicates recommendations not actionable)

---

### 2. RAG Performance (RAGAS Metrics)

#### Faithfulness
**Definition:** How accurately does the answer reflect the retrieved context? (0-1 scale)

**Target:** >0.90

**Measurement:** Automated using RAGAS library
```python
from ragas import evaluate
from ragas.metrics import faithfulness

score = faithfulness.score(
    question=user_query,
    answer=llm_output,
    contexts=retrieved_docs
)
```

**Interpretation:**
- **1.0:** Answer fully grounded in context, no hallucination
- **0.8-0.9:** Mostly accurate with minor extrapolations
- **<0.8:** Significant hallucination, unreliable

**Action:** If faithfulness <0.80 for 3+ days, strengthen RAG grounding (increase context weight, reduce LLM creativity)

---

#### Answer Relevance
**Definition:** How well does the answer address the user's query?

**Target:** >0.85

**Measurement:**
```python
from ragas.metrics import answer_relevancy

score = answer_relevancy.score(
    question=user_query,
    answer=llm_output
)
```

**Alert:** If <0.75, query understanding is poor → Improve query expansion or prompt engineering

---

#### Context Precision
**Definition:** Are the retrieved documents relevant to the query?

**Target:** >0.80

**Measurement:** % of retrieved docs actually used in the answer

**Action:** If <0.70, vector search is noisy → Tune embedding model or add reranking

---

#### Context Recall
**Definition:** Does the retrieved context contain all necessary information?

**Target:** >0.85

**Measurement:** Are all facts in the answer supported by retrieved docs?

**Action:** If <0.75, retrieval is missing key info → Expand knowledge base or increase top-k

---

### 3. Latency

#### P50 (Median)
**Target:** <2 seconds (end-to-end)

**Breakdown:**
- Embedding: <0.2s
- Vector search: <0.5s
- LLM inference: <1.5s
- Post-processing: <0.3s

#### P95 (95th Percentile)
**Target:** <5 seconds

**Alert:** If P95 >7s for 1 hour, investigate bottlenecks

#### P99 (99th Percentile)
**Target:** <10 seconds

**Action Plan (if P95 >7s):**
1. Check Hugging Face API rate limits (are we throttled?)
2. Optimize prompt length (reduce tokens)
3. Consider faster model (Llama 3.2 vs. 3.1)
4. Add caching for common queries

---

### 4. Model Drift

#### Accuracy Drift
**Definition:** Change in recommendation accuracy over time (compared to baseline)

**Target:** <10% degradation per quarter

**Measurement:**
- **Baseline:** Accuracy on holdout test set (200 labeled examples) at launch
- **Weekly Check:** Re-evaluate same test set, track accuracy trend
- **Drift Detected:** If accuracy drops >5% from baseline for 2 consecutive weeks

**Example:**
```
Week 1: 87% accuracy (baseline)
Week 5: 85% accuracy (within threshold)
Week 8: 81% accuracy (5% drop) → WARNING
Week 9: 80% accuracy (>5% drop persists) → DRIFT DETECTED
```

**Action:** Retrain model with recent user feedback data

---

#### Concept Drift
**Definition:** User query distribution changes (e.g., new equipment types not in training data)

**Detection:**
- Monitor scenario type distribution
- Flag queries with low embedding similarity to existing knowledge base (<0.6)
- Track "no relevant context found" errors

**Example:**
- Baseline: 80% valve queries, 10% sensor, 10% controller
- Week 12: 60% valve, 25% sensor (shift detected)
- Action: Expand sensor-related knowledge base content

---

### 5. Safety Metrics

#### Safety Alert Precision
**Definition:** Of all safety alerts triggered, what % were correct?

**Target:** >98% (minimize false positives)

**Measurement:**
```python
precision = true_positives / (true_positives + false_positives)

# True Positive: System flagged voltage mismatch, user confirmed it was correct
# False Positive: System flagged issue, user confirmed it was safe
```

**Alert:** If precision <95%, users will ignore safety warnings → Tighten thresholds

---

#### Safety Alert Recall
**Definition:** Of all actual safety issues, what % did we catch?

**Target:** >95% (catch every real hazard)

**Measurement:**
```python
recall = true_positives / (true_positives + false_negatives)

# False Negative: System didn't flag issue, user reported problem post-implementation
```

**Critical:** If recall <90%, we're missing safety risks → Add more validation rules

---

### 6. System Health

#### Uptime
**Target:** 99.5% (43 hours downtime/year allowed)

**Monitoring:** Health check endpoint (`/health`) polled every 60 seconds

**Dependencies:**
- Hugging Face Inference API: 99.9% SLA
- FAISS vector store: Local (no external dependency)
- Streamlit hosting: 99.5% (AWS/Cloud)

**Incident Response:**
- **P0 (Critical):** Service down >5 minutes → Page on-call engineer
- **P1 (High):** Degraded performance (latency >10s) → Investigate within 1 hour
- **P2 (Medium):** Intermittent errors <5% → Fix within 24 hours

---

#### Error Rate
**Target:** <1% of requests result in errors

**Error Types:**
1. **JSON Parsing Failures:** LLM output not valid JSON
2. **API Timeouts:** Hugging Face API unresponsive (>30s)
3. **Safety Validation Errors:** Critical incompatibility detected
4. **Unknown SKU:** Recommended product not in catalog

**Monitoring:**
```python
error_rate = (failed_requests / total_requests) * 100
```

**Alert:** If error rate >2% for 1 hour → Investigate

---

## Monitoring Dashboard

### Real-Time View (Auto-refresh every 60s)

```
┌─────────────────────────────────────────────────────────────────┐
│  RETROFIT-RECOMMENDER: LIVE MONITORING                         │
├─────────────────────────────────────────────────────────────────┤
│  Last Updated: 2026-01-29 14:32:00 UTC                         │
└─────────────────────────────────────────────────────────────────┘

┌───────────────────┬───────────────────┬───────────────────────┐
│ ACCURACY          │ LATENCY           │ SYSTEM HEALTH         │
├───────────────────┼───────────────────┼───────────────────────┤
│ 🟢 87.5%          │ 🟢 P50: 1.8s      │ 🟢 Uptime: 99.8%      │
│ Target: >85%      │ 🟢 P95: 4.2s      │ 🟢 Error Rate: 0.3%   │
│ ↑ +2.1% (7d)      │ 🟡 P99: 8.1s      │ 🟢 API Available      │
└───────────────────┴───────────────────┴───────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│  RAG PERFORMANCE (RAGAS Metrics - Last 100 Requests)         │
├───────────────────────────────────────────────────────────────┤
│  Faithfulness:        🟢 0.91  [████████████████████░░] 91%   │
│  Answer Relevance:    🟢 0.87  [█████████████████░░░░] 87%   │
│  Context Precision:   🟡 0.78  [███████████████░░░░░░] 78%   │
│  Context Recall:      🟢 0.89  [██████████████████░░░] 89%   │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│  SAFETY METRICS (Last 7 Days)                                │
├───────────────────────────────────────────────────────────────┤
│  Alerts Triggered:    47                                      │
│  Precision:           🟢 98.9% (46/47 confirmed correct)      │
│  Recall:              🟢 95.8% (46/48 hazards caught)         │
│  False Negatives:     🔴 2 (under review)                     │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│  USER ENGAGEMENT (Today)                                      │
├───────────────────────────────────────────────────────────────┤
│  Recommendations:     152                                     │
│  Unique Users:        43                                      │
│  Feedback Received:   29 (19%)                               │
│  Satisfaction:        🟢 89.7% (26 helpful / 29 total)        │
└───────────────────────────────────────────────────────────────┘
```

---

### Weekly Report (Email to stakeholders)

**Subject:** [Weekly AI Report] Retrofit-Recommender Performance (Week 4, 2026)

**Summary:**
- ✅ Recommendation accuracy: **87.5%** (target: 85%) — **ON TRACK**
- ✅ P95 latency: **4.2s** (target: <5s) — **HEALTHY**
- ⚠️ Context precision: **78%** (target: 80%) — **NEEDS ATTENTION**
- ✅ Uptime: **99.8%** (target: 99.5%) — **EXCEEDING**

**Highlights:**
- Processed **1,247 recommendations** (+18% vs. last week)
- Implementation rate: **17.3%** (up from 14.2%, on track for 20% target)
- Safety alerts: **47 triggered**, 0 false negatives

**Action Items:**
1. Investigate context precision drop (78% vs. 82% last week) — ML team
2. Analyze 2 false negative safety incidents — Safety review committee
3. Celebrate: First week with >1,000 recommendations 🎉

---

## Experimentation Framework (A/B Testing)

### Test 1: TCO Chart Impact on Implementation Rate
**Hypothesis:** Adding a visual TCO chart will increase implementation rate from 15% to 22%

**Setup:**
- **Control (A):** Text-only recommendation display
- **Variant (B):** Add 5-year TCO bar chart
- **Sample Size:** 200 users per variant (80% power, 5% significance)
- **Duration:** 4 weeks
- **Primary Metric:** Implementation rate (% of recommendations → purchases)
- **Secondary Metrics:** Time to decision, user satisfaction

**Results (Example):**
```
Control:   15.2% implementation (30/197)
Variant:   23.1% implementation (47/203)
Lift:      +52% 🎉
P-value:   0.023 (statistically significant)
Decision:  SHIP to 100% of users
```

---

### Test 2: Prompt Optimization for Accuracy
**Hypothesis:** Shorter prompt reduces latency without sacrificing accuracy

**Setup:**
- **Control (A):** Current prompt (500 tokens)
- **Variant (B):** Condensed prompt (300 tokens)
- **Primary Metric:** Recommendation accuracy
- **Secondary Metrics:** P95 latency

**Results (Example):**
```
Control:   87.5% accuracy, 4.2s P95 latency
Variant:   85.1% accuracy, 3.1s P95 latency
Decision:  DO NOT SHIP (accuracy drop too high)
Learning:  Prompt length is critical for quality
```

---

### Test 3: Multi-Option vs. Single Recommendation
**Hypothesis:** Showing top 3 options (cost-optimized, carbon-optimized, reliability-optimized) increases user satisfaction

**Setup:**
- **Control (A):** Single best recommendation
- **Variant (B):** Top 3 with rationale
- **Primary Metric:** User satisfaction (NPS)
- **Secondary Metrics:** Time on page, feedback rate

---

## Model Retraining Pipeline

### Trigger Conditions for Retraining
1. **Accuracy Drift:** >5% drop from baseline for 2 consecutive weeks
2. **User Feedback:** 500+ new labeled examples collected (helpful/not helpful)
3. **Concept Drift:** >20% of queries in new domain (e.g., new equipment category)
4. **Scheduled:** Quarterly retraining (even if no drift detected)

---

### Retraining Process (Manual, Q1-Q2; Automated, Q3+)

**Step 1: Data Collection**
- Export user feedback (recommendation_id, rating, comment)
- Export implementation outcomes (did user purchase? Actual savings?)
- Label additional test cases (PM + domain expert review)

**Step 2: Data Preparation**
- Clean & deduplicate feedback
- Create balanced dataset (50% positive, 50% negative examples)
- Split: 70% train, 15% validation, 15% test

**Step 3: Model Update**
- Fine-tune embedding model (SentenceTransformer) on domain-specific data
- Optimize vector search (tune top-k, distance metric)
- Update LLM prompt based on error analysis

**Step 4: Validation**
- Evaluate on holdout test set (target: >90% accuracy)
- Human review of 50 sample outputs
- A/B test new model vs. current model (1 week, 20% traffic)

**Step 5: Deployment**
- If A/B test shows improvement → Gradual rollout (20% → 50% → 100%)
- If no improvement → Investigate further, do not deploy

**Step 6: Monitoring**
- Watch accuracy, latency, error rate for 48 hours post-deployment
- Rollback if any metric degrades >10%

---

## Incident Response Playbook

### Scenario 1: Accuracy Drops Below 80%
**Alert:** Email + Slack to #ai-incidents channel

**Triage (within 1 hour):**
1. Check last 50 low-rated recommendations for patterns
2. Is drift sudden (1 day) or gradual (weeks)?
3. Are errors concentrated in specific scenario type?

**Investigation:**
- Review recent knowledge base changes (did someone edit content?)
- Check Hugging Face API status (model version change?)
- Analyze RAG context quality (faithfulness score)

**Resolution:**
- **Quick fix:** Revert to last known good model/prompt
- **Long-term:** Retrain with recent feedback, add missing knowledge

---

### Scenario 2: Safety Alert Missed (False Negative)
**Severity:** P0 (Critical) — Customer safety at risk

**Immediate Action:**
1. Identify affected recommendation (SKU, scenario, user)
2. Contact user within 2 hours (email + phone call)
3. Understand what happened (was voltage mismatch not detected?)
4. Add rule to prevent recurrence

**Post-Incident Review (within 1 week):**
- Root cause analysis (why did validation logic miss this?)
- Update safety rules (add edge case)
- Test on historical data (would new rule have caught it?)
- Document in incident log

---

### Scenario 3: Hugging Face API Down
**Impact:** Service unavailable (0 recommendations generated)

**Immediate Action:**
1. Display user-friendly error: "AI service temporarily unavailable. Please try again in 5 minutes."
2. Activate fallback: Rule-based recommendations (simple logic, no LLM)
3. Monitor Hugging Face status page

**Recovery:**
- When API restored, resume normal operation
- Review error logs (were any requests lost?)
- Consider adding redundancy (backup model provider)

---

## Data Privacy & Security

### PII Handling
**Policy:** Retrofit-Recommender does NOT collect personally identifiable information

**Data Collected:**
- Equipment specs (non-sensitive technical data)
- Error descriptions (operational data)
- User feedback (ratings, comments)

**NOT Collected:**
- Names, emails (unless user volunteers for follow-up)
- Company-specific asset IDs (anonymized)
- Financial data beyond aggregated TCO

---

### Data Retention
- **Recommendation Logs:** 2 years (for model improvement)
- **User Feedback:** 5 years (required for regulatory compliance)
- **Error Logs:** 90 days (sufficient for debugging)

---

### Compliance
- **GDPR:** Users can request data deletion (email privacy@retrofit-recommender.com)
- **CCPA:** California users can opt out of data collection
- **SOC 2 Type II:** Planned certification (Q4 2026)

---

## Continuous Improvement Process

### Weekly AI Review (Fridays, 2pm)
**Attendees:** PM, ML Engineer, Data Analyst

**Agenda:**
1. Review KPI dashboard (10 min)
2. Discuss user feedback highlights (5 min)
3. Analyze errors/edge cases (10 min)
4. Prioritize improvements (5 min)

---

### Monthly Model Performance Review
**Attendees:** Full product/eng team

**Deep Dives:**
- Accuracy trends (by scenario type, user segment)
- Latency distribution (P50/P95/P99)
- Safety incident review
- Experimentation results

---

### Quarterly Strategic Review
**Attendees:** Leadership team

**Topics:**
- Model capabilities vs. roadmap
- Competitive AI landscape
- Investment priorities (more data? Better model?)

---

## Tools & Infrastructure

### Current Stack
- **LLM:** Meta Llama 3.1-8B (Hugging Face Inference API)
- **Embeddings:** SentenceTransformer (all-MiniLM-L6-v2)
- **Vector DB:** FAISS (local, CPU)
- **Monitoring:** Custom (Streamlit session state)
- **Experimentation:** Manual A/B testing

### Planned Upgrades (Q2-Q3)
- **Monitoring:** Datadog OR Prometheus + Grafana
- **Experimentation:** LaunchDarkly (feature flags + A/B testing)
- **Vector DB:** Pinecone (cloud, more scalable)
- **LLM:** Upgrade to Llama 3.2 OR GPT-4 Turbo (if budget allows)
- **MLOps:** Weights & Biases (experiment tracking)

---

## Glossary

- **Faithfulness:** LLM answer accuracy vs. retrieved context
- **Context Precision:** Relevance of retrieved documents
- **Context Recall:** Completeness of retrieved information
- **RAGAS:** Retrieval-Augmented Generation Assessment framework
- **P50/P95/P99:** Latency percentiles (50th, 95th, 99th)
- **Drift:** Model performance degradation over time
- **False Negative:** System missed a real safety issue
- **False Positive:** System flagged a non-issue

---

## Document Control
**Version:** 1.0  
**Owner:** ML Engineering + Product  
**Review Cycle:** Quarterly  
**Next Review:** April 30, 2026
