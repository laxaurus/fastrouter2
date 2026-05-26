Business plan

https://chat.deepseek.com/a/chat/s/da48cb94-bb4e-480e-be05-b82ca2a66fcc
# Two-Way LLM API Routing Business: Complete Strategic Business Plan

## Executive Summary

**Company:** [Name TBD] - A two-way LLM API routing platform bridging Western and Chinese AI ecosystems

**Problem:** 
- Western developers cannot easily access cost-effective Chinese LLMs (payment friction, registration barriers, language barriers)
- Chinese developers cannot reliably access Western LLMs like Claude (blocked, unstable, payment impossible)

**Solution:** A unified API gateway that routes requests bidirectionally with intelligent optimization, unified billing, and compliance wrappers

**Target Markets:**
- **Segment 1 (West→China):** Global developers seeking cost-effective Chinese models (DeepSeek, Qwen, Kimi, GLM)
- **Segment 2 (China→West):** Chinese enterprises and developers needing reliable Claude/GPT access

**Business Model:** Hybrid SaaS subscription + usage-based reseller with 50-70% gross margins

**Team:** 1-2 founders (technical + go-to-market)

**Initial Capital Required:** $0-5,000 (bootstrapped) or $50,000 (accelerated)

**6-Month Target:** $40-60k MRR with 60% margins

---

## Part 1: Market Analysis

### 1.1 Market Sizing

| Segment | TAM | SAM | SOM (Year 1) |
|---------|-----|-----|---------------|
| West→China LLM Access | $500M+ | $50M (devs willing to switch) | $500k |
| China→West LLM Access | $200M+ | $30M (enterprises needing Claude) | $300k |
| **Total** | **$700M+** | **$80M** | **$800k** |

**Growth Drivers:**
- Chinese models now match/beat Western on cost/performance (77% of OpenRouter traffic)
- Anthropic/OpenAI remain blocked/unreliable in China
- AI coding agents drove 300% increase in API usage in 2025

### 1.2 Competitive Landscape

| Competitor | Segment Focus | Pricing Model | Strength | Weakness |
|------------|---------------|---------------|----------|----------|
| OpenRouter | Global aggregator | Pass-through (0% markup) | Largest model selection | Poor China connectivity |
| APIYI | China→Claude | Discount reseller (20% off) | Enterprise trusted | Only Claude |
| 七牛云 AI | China domestic | Freemium + usage | Massive free tier | No international brand |
| SiliconFlow | Open-source inference | Cost savings pass-through | Optimized performance | No closed models |
| LiteLLM | Self-hosted gateway | Open source (free) | Flexible | Requires self-hosting |

### 1.3 Target Customer Personas

**Segment 1: Western Developer (West→China)**

| Persona | Characteristics | Pain Point | Willingness to Pay |
|---------|----------------|-----------|---------------------|
| Indie Hacker | Solo dev, bootstrapping, building AI side projects | Can't register for Chinese APIs (requires phone/ID) | $20-50/month |
| AI Startup | 2-10 person team, building production AI features | High costs on OpenAI/Anthropic, wants to arbitrage | $200-500/month |
| Enterprise R&D | Large company exploring AI, cost-conscious at scale | Compliance, audit trails, need approved vendor list | $2k-10k/month |

**Segment 2: Chinese Customer (China→West)**

| Persona | Characteristics | Pain Point | Willingness to Pay |
|---------|----------------|-----------|---------------------|
| AI Coding Agency | 3-20 person shop building Claude-based coding tools | No reliable Claude access for Chinese clients | $500-2k/month |
| Research Lab | University/training center needing SOTA comparisons | Need GPT-5/Claude for benchmarks | $500-1k/month |
| Enterprise Tech Co | Large Chinese tech firm with overseas business | Need legal, stable access with audit trails | $5k-20k/month |

---

## Part 2: Product & Technical Architecture

### 2.1 Core Product Features by Phase

**Phase 1 (MVP) - Month 1**
| Feature | Segment 1 | Segment 2 | Description |
|---------|-----------|-----------|-------------|
| Unified API Gateway | ✓ | ✓ | OpenAI-compatible endpoint |
| BYOK Routing | ✓ | ✗ | Customers use their own API keys |
| Basic Analytics | ✓ | ✓ | Token usage dashboard |
| Model Mapping | ✓ | ✓ | Translate model names across providers |
| Health Checks | ✓ | ✓ | Automatic failover |

**Phase 2 (Reseller) - Month 3**
| Feature | Segment 1 | Segment 2 | Description |
|---------|-----------|-----------|-------------|
| Built-in Credits | ✓ | ✓ | Pre-purchased tokens (you resell) |
| Cost Optimization | ✓ | ✗ | Auto-route to cheapest provider |
| Claude Access | ✗ | ✓ | Reliable proxy with payment |
| Subscription Bundles | ✓ | ✓ | Fixed monthly token packages |
| Webhook Alerts | ✓ | ✓ | Budget notifications |

**Phase 3 (Enterprise) - Month 6**
| Feature | Segment 1 | Segment 2 | Description |
|---------|-----------|-----------|-------------|
| SOC2 Compliance | ✓ | ✓ | Audit logs, data residency |
| Dedicated Endpoints | ✓ | ✓ | Isolated infrastructure |
| SLA Guarantees | ✓ | ✓ | 99.9% uptime commitment |
| Custom Routing Rules | ✓ | ✓ | Customer-defined provider priority |
| SSO/SAML | ✓ | ✓ | Enterprise authentication |

### 2.2 Technical Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    CDN / DDoS Protection                    │
│                    (Cloudflare Free/Pro)                    │
├─────────────────────────────────────────────────────────────┤
│                    API Gateway Layer                        │
│                 (Fly.io / Cloudflare Workers)               │
│                    $20-100/month                            │
├─────────────────────────────────────────────────────────────┤
│                 LiteLLM Proxy (Customized)                  │
│                  - Provider adapters                        │
│                  - Load balancing                           │
│                  - Retry/failover logic                     │
├─────────────────────────────────────────────────────────────┤
│                    Core Services                            │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ User/Auth    │ Routing      │ Billing      │            │
│  │ (Supabase/   │ Engine       │ (Stripe +    │            │
│  │ Auth0)       │ (Custom)     │ L402)        │            │
│  └──────────────┴──────────────┴──────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                               │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ PostgreSQL   │ Redis        │ Object Store │            │
│  │ (Neon/Turso) │ (Upstash)    │ (R2)         │            │
│  │ $0-25/month  │ $0-25/month  │ $0-10/month  │            │
│  └──────────────┴──────────────┴──────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                    Observability                            │
│              (Grafana Cloud - Free tier)                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Provider Integration Roadmap

**Phase 1 (Launch):**
| Provider | Region | Segment | Integration Complexity |
|----------|--------|---------|----------------------|
| DeepSeek | China | 1 | Low (OpenAI-compatible) |
| SiliconFlow | China | 1 | Low |
| Alibaba Qwen | China | 1 | Medium |
| OpenAI | US | 2 (via proxy) | Low |

**Phase 2 (Expand):**
| Provider | Region | Segment | Integration Complexity |
|----------|--------|---------|----------------------|
| Kimi (Moonshot) | China | 1 | Medium |
| Zhipu (GLM) | China | 1 | Medium |
| Anthropic Claude | US | 2 | High (via APIYI partnership) |
| Baichuan | China | 1 | Low |

**Phase 3 (Scale):**
| Provider | Region | Segment | Notes |
|----------|--------|---------|-------|
| MiniMax | China | 1 | Growing rapidly |
| StepFun | China | 1 | Emerging player |
| 360 Zhinao | China | 1 | Enterprise focus |
| Google Gemini | US | 2 | Direct access |

---

## Part 3: Business Model & Pricing

### 3.1 Revenue Model Summary

| Revenue Stream | Segment | Model | Expected % of Revenue |
|----------------|---------|-------|----------------------|
| BYOK Subscriptions | 1 | $19-99/month SaaS | 15% |
| Token Resale (West→China) | 1 | $0.20-1.00/1M tokens | 35% |
| Claude Access (China→West) | 2 | $29-249/month subscriptions | 40% |
| Enterprise Contracts | Both | $500-5000/month | 10% |

### 3.2 Detailed Pricing By Phase

**Phase 1 Pricing (Months 1-2) - Low Risk**

| Plan | Price | Segment | What Customer Gets | Your Cost |
|------|-------|---------|-------------------|-----------|
| Free | $0 | 1 | 10K tokens/month (BYOK only) | $0 |
| Routing Pro | $19/month | 1 | Unlimited routing (BYOK), 5 models | $0 (server) |
| Claude Basic | $29/month | 2 | 1M Claude tokens, best-effort | $24 (wholesale) |

**Phase 2 Pricing (Months 3-4) - Medium Risk**

| Plan | Price | Segment | What Customer Gets | Margin |
|------|-------|---------|-------------------|--------|
| Starter | $19/month | 1 | 500K tokens (any Chinese model) | 60% |
| Pro | $79/month | 1 | 3M tokens + advanced routing | 65% |
| Claude Pro | $79/month | 2 | 5M Claude tokens + priority | 50% |
| Dual Access | $99/month | Both | 2M Chinese + 2M Claude | 55% |

**Phase 3 Pricing (Months 5-6) - Scale**

| Plan | Price | Segment | Features | Margin |
|------|-------|---------|----------|--------|
| Business | $299/month | 1 | 15M tokens, advanced analytics | 60% |
| Claude Business | $249/month | 2 | 20M Claude tokens, SLA | 55% |
| Global AI | $599/month | Both | 50M Chinese + 30M Claude | 50% |
| Enterprise | Custom | Both | Dedicated, audit logs, SSO | 40-60% |

### 3.3 Unit Economics

| Metric | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|
| CAC (organic) | $0 | $50 | $100 |
| CAC (paid) | Not yet | $100-200 | $200-300 |
| LTV (Segment 1) | $200 | $500 | $1,000+ |
| LTV (Segment 2) | $300 | $800 | $2,000+ |
| Gross Margin | 85-95% | 55-70% | 50-65% |
| Churn (target) | <10% | <5% | <3% |

---

## Part 4: Phased Implementation Plan

### Phase 0: Preparation (Week 1-2)

**Goal:** Legal entity, infrastructure, provider access

| Activity | Owner | Timeline | Cost |
|----------|-------|----------|------|
| Register US LLC (Delaware) | Founder | Day 1-3 | $500 |
| Open business bank account | Founder | Day 3-5 | $0 |
| Set up Stripe + Alipay/WeChat | Founder | Day 4-6 | $0 |
| Apply for provider API credits | Founder | Day 5-10 | $0 |
| Set up cloud infrastructure (Fly.io) | Founder | Day 7-10 | $20 |
| Configure LiteLLM base proxy | Founder | Day 10-14 | $0 |
| Create landing page + docs | Founder | Day 10-14 | $0 |

**Deliverable:** Working prototype with 2 providers (DeepSeek, OpenAI via proxy)

**Exit criteria:** You can make a successful API call through your gateway from both segments

### Phase 1: MVP Launch - West→China Focus (Month 1)

**Goal:** Validate Segment 1 demand with minimal risk

**Product:**
| Feature | Status | Priority |
|---------|--------|----------|
| BYOK routing (West→China) | ✅ Build | P0 |
| Unified OpenAI-compatible API | ✅ Build | P0 |
| Basic usage dashboard | ✅ Build | P1 |
| Free tier (10K tokens) | ✅ Build | P1 |
| 5 Chinese providers integrated | 🔄 Ongoing | P1 |

**Go-to-Market:**
| Activity | Channel | Timeline | Budget |
|----------|---------|----------|--------|
| Launch on Hacker News | Organic | Week 3 | $0 |
| Post on Reddit (r/LocalLLaMA, r/OpenAI) | Organic | Week 3 | $0 |
| Product Hunt launch | Organic | Week 4 | $0 |
| Write benchmark post (DeepSeek vs GPT) | Content | Week 4 | $0 |
| Collect email waitlist | Landing page | Ongoing | $0 |

**Success Metrics:**
- 100 free users signed up
- 10 paying BYOK customers ($19/month)
- 5 active daily users providing feedback
- Zero server downtime

**Team: 1 founder (technical)**

**Burn Rate: $200/month**

### Phase 2: Add China→West Direction (Month 2-3)

**Goal:** Launch Segment 2 (Claude access) and begin reseller model

**Product:**
| Feature | Status | Priority |
|---------|--------|----------|
| Claude access via APIYI partnership | ✅ Build | P0 |
| Reseller model (you buy tokens, resell) | ✅ Build | P0 |
| Subscription bundles (tiered token packages) | ✅ Build | P1 |
| Cost optimization routing | ✅ Build | P1 |
| Unified dashboard for both segments | ✅ Build | P2 |
| WeChat/Alipay payments integration | ✅ Build | P1 |

**Go-to-Market:**
| Activity | Channel | Timeline | Budget |
|----------|---------|----------|--------|
| Launch on Chinese dev forums (V2EX, CSDN) | Organic | Month 2 | $0 |
| Write "How to access Claude from China" guide | Content | Month 2 | $0 |
| Partner with 1-2 AI coding agencies | Direct sales | Month 2 | $0 |
| Launch referral program | In-product | Month 3 | $0 |
| Basic Google Ads (test) | Paid | Month 3 | $500 |

**Success Metrics:**
- 50 Segment 1 paying customers ($19-79)
- 20 Segment 2 paying customers ($29-79)
- 5 enterprise leads in pipeline
- $3-5k MRR

**Team: 2 founders (technical + sales/marketing)**

**Burn Rate: $1,000-2,000/month**

### Phase 3: Scale & Enterprise (Month 4-6)

**Goal:** Establish as legitimate two-way routing platform with enterprise capabilities

**Product:**
| Feature | Status | Priority |
|---------|--------|----------|
| SOC2 Type 1 compliance | 🔄 Start | P0 |
| Dedicated endpoints for enterprise | ✅ Build | P0 |
| Audit logging (compliance) | ✅ Build | P0 |
| SLA guarantees (99.9%) | ✅ Build | P1 |
| Bulk discounts for high volume | ✅ Build | P1 |
| Custom routing rules per customer | ✅ Build | P2 |

**Go-to-Market:**
| Activity | Channel | Timeline | Budget |
|----------|---------|----------|--------|
| Hire first sales person (commission-only) | Recruiting | Month 4 | $0 |
| Apply to Cloudflare Workers AI as provider | Partnership | Month 4 | $0 |
| Write case studies with early customers | Content | Month 4 | $0 |
| Launch self-serve enterprise portal | Product | Month 5 | $0 |
| Attend AI infrastructure conference (virtual) | Event | Month 6 | $500 |

**Success Metrics:**
- 200 Segment 1 customers (mix of BYOK + reseller)
- 100 Segment 2 customers
- 5-10 enterprise contracts
- $40-60k MRR
- Positive cash flow

**Team: 2 founders + 1 sales contractor + 1 support (offshore)**

**Burn Rate: $5,000-8,000/month (covered by revenue)**

---

## Part 5: Operational Plan

### 5.1 Customer Support Tiers

| Tier | Response Time | Channels | Cost | Staffing |
|------|---------------|----------|------|----------|
| Free/BYOK | 48 hours | Email only | $0 | Founder |
| Paid (<$100/month) | 24 hours | Email + Discord | $0 | Founder |
| Pro ($100-500/month) | 4 hours | Email + Slack | $200/month | Offshore part-time |
| Enterprise (>$500/month) | 1 hour | Dedicated Slack | $1,000/month | Dedicated support |

### 5.2 Provider Relationship Management

| Provider | Relationship Type | Volume Discount | Risk Mitigation |
|----------|-------------------|-----------------|-----------------|
| DeepSeek | Direct API | No (already cheap) | Multiple accounts |
| Alibaba Qwen | Official partner application | Tier 1 at 1M+ tokens/month | Backup providers |
| Kimi | Direct API | Negotiate at scale | Monitor uptime |
| APIYI (Claude) | Wholesale partner | 20% off standard | Secondary proxy backup |
| Zhipu | Direct API | Apply for volume | Use international pricing |

### 5.3 Risk Management

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Provider TOS violation (reselling) | Medium | High | Legal review, BYOK option always available | Founder |
| Claude access blocked | Medium | High | Multiple proxy partners, domestic fallback | Tech founder |
| Customer abuse (free credits) | Medium | Low | Rate limiting, abuse detection | Tech founder |
| Payment processor issues | Low | Medium | Multiple processors (Stripe + crypto) | Founder |
| Server downtime | Low | Medium | Multi-region deployment | Tech founder |
| Regulatory changes (China data laws) | Low | High | Keep EU/US infra for western customers | Founder |

---

## Part 6: Financial Projections

### 6.1 Month-by-Month Revenue Forecast (Conservative)

| Month | Segment 1 MRR | Segment 2 MRR | Enterprise MRR | Total MRR | Cumulative |
|-------|---------------|---------------|----------------|-----------|------------|
| 1 | $190 (10×$19) | $0 | $0 | $190 | $190 |
| 2 | $570 (30×$19) | $290 (10×$29) | $0 | $860 | $1,050 |
| 3 | $1,500 (50×$30 avg) | $1,000 (20×$50 avg) | $0 | $2,500 | $3,550 |
| 4 | $4,000 (80×$50) | $3,000 (40×$75) | $1,000 | $8,000 | $11,550 |
| 5 | $8,000 (120×$67) | $6,000 (60×$100) | $3,000 | $17,000 | $28,550 |
| 6 | $15,000 (180×$83) | $12,000 (80×$150) | $8,000 | $35,000 | $63,550 |

**Phase 3 adjusted target:** $40-60k MRR (more aggressive growth possible with paid acquisition)

### 6.2 Expense Forecast

| Category | Month 1-2 | Month 3-4 | Month 5-6 |
|----------|-----------|-----------|-----------|
| Cloud infrastructure | $50 | $200 | $500 |
| Payment processing | $20 | $200 | $800 |
| Marketing (organic/ads) | $0 | $500 | $2,000 |
| Contractor (support/sales) | $0 | $1,000 | $3,000 |
| Legal/compliance | $0 | $500 | $1,000 |
| Software subscriptions | $30 | $100 | $200 |
| **Total monthly** | **$100** | **$2,500** | **$7,500** |

### 6.3 Profitability Timeline

| Metric | Month 2 | Month 4 | Month 6 |
|--------|---------|---------|---------|
| Revenue | $860 | $8,000 | $35,000 |
| Expenses | $100 | $2,500 | $7,500 |
| Profit/Loss | +$760 | +$5,500 | +$27,500 |
| Gross Margin | 85% | 65% | 60% |
| Cumulative profit | $760 | $6,500 | $45,000 |

**Breakeven point:** Month 2 (thanks to low-cost BYOK model)

### 6.4 Capital Requirements

| Scenario | Capital Needed | Use of Funds | Timeline to Profitability |
|----------|---------------|--------------|---------------------------|
| Bootstrapped (slow) | $0-5,000 | Server costs only | Month 2 |
| Accelerated (medium) | $25,000 | Marketing, contractor, upfront token purchase | Month 4 |
| Funded (aggressive) | $100,000 | Team of 4, paid ads, enterprise sales | Month 6 |

**Recommendation:** Start bootstrapped. Validate with BYOK model (zero cost). Reinvest profits into reseller model. Only raise if you hit $10k MRR and see clear path to $100k.

---

## Part 7: Legal & Compliance Framework

### 7.1 Entity Structure

**Recommended:** US LLC (Delaware) + Singapore Pte Ltd (for Asia operations)

| Entity | Purpose | Cost | Timeline |
|--------|---------|------|----------|
| Delaware LLC | Primary entity, Stripe, US customers | $500 + $300/year | Week 1 |
| Singapore company | Asia operations, WeChat/Alipay, Claude resale | $2,000 | Month 3 |

### 7.2 Critical Legal Documents (MVP)

| Document | Purpose | Vendor | Cost |
|----------|---------|--------|------|
| Terms of Service | User agreement | LegalZoom template + customization | $200 |
| Privacy Policy | Data handling | Generated + reviewed | $100 |
| DPA (Data Processing Addendum) | Enterprise compliance | Template + legal review | $500 |
| Provider Agreements | Terms with APIYI, etc. | Negotiated per provider | $0 |

### 7.3 Key Compliance Items

| Requirement | Segment 1 | Segment 2 | Status |
|-------------|-----------|-----------|--------|
| Data residency (GDPR) | ✓ | ✗ | Use EU servers |
| Data residency (China laws) | ✗ | ✓ | Use Singapore entity |
| Export compliance (US models to China) | ✗ | ✓ | Requires legal review |
| SOC2 Type 1 | Optional | Required for enterprise | Month 5 |
| PCI DSS (payment processing) | ✓ | ✓ | Stripe handles |

**Note on Export Compliance:** Reselling Anthropic/OpenAI access to mainland China entities is legally restricted. The China→West segment must operate through a non-China entity (Singapore) and only serve customers with legitimate overseas operations. Consult legal counsel before scaling this segment.

---

## Part 8: Success Metrics & KPIs

### 8.1 Leading Indicators (Daily/Weekly)

| Metric | Target (Phase 1) | Target (Phase 3) | Tool |
|--------|-----------------|------------------|------|
| New signups (free) | 10/day | 50/day | Dashboard |
| Free → Paid conversion | 5% | 10% | Stripe |
| API requests per customer | 1,000/day | 10,000/day | Grafana |
| Average latency (ms) | <500ms | <200ms | Custom |
| Provider error rate | <1% | <0.1% | Health checks |

### 8.2 Lagging Indicators (Monthly)

| Metric | Target (Phase 1) | Target (Phase 3) |
|--------|-----------------|------------------|
| MRR | $190 | $40,000+ |
| Gross margin | 85% | 60% |
| Customer churn | <10% | <3% |
| LTV/CAC | 3:1 | 5:1 |
| Net Promoter Score | 30 | 50 |

### 8.3 Segment-Specific Metrics

**Segment 1 (West→China):**
- Cost savings shown vs OpenAI (target: 70% cheaper)
- Number of Chinese providers used per customer (target: 3+)
- Average tokens per month (target: 5M)

**Segment 2 (China→West):**
- Claude uptime (target: 99.5%)
- Payment method mix (Alipay/WeChat vs card)
- Enterprise contract value (target: $2k average)

---

## Part 9: Team & Hiring Plan

### 9.1 Founder Roles (1-2 people)

| Role | Responsibilities | Time Split | When Needed |
|------|-----------------|------------|--------------|
| Technical Founder | Architecture, coding, DevOps, provider integrations | 100% | Day 1 |
| Go-to-Market Founder | Sales, marketing, partnerships, customer support | 100% (if 2nd founder) | Month 2 |

**If solo founder:** You must be technical AND handle GTM for first 3 months.

### 9.2 Hiring Plan

| Role | Type | Cost | Timeline | Trigger |
|------|------|------|----------|---------|
| Sales Contractor | Commission-only (10%) | $0 base | Month 4 | >50 active leads |
| Support (offshore) | Part-time ($15/hour) | $1,000/month | Month 4 | >100 customers |
| Marketing Contractor | Freelance ($50/hour) | $2,000/month | Month 5 | >$10k MRR |
| Full-stack Developer | Full-time ($8k/month) | $8,000/month | Month 8 | >$30k MRR and growing |

### 9.3 Advisory Board (Optional)

| Role | Expertise | Equity | Cost |
|------|-----------|--------|------|
| Legal Advisor | Export compliance, cross-border data | 0.5-1% | $0 |
| AI Infrastructure Expert | Provider relationships, scaling | 0.5-1% | $0 |
| China Market Expert | WeChat/Alipay, local partnerships | 0.5-1% | $0 |

---

## Part 10: Risk Register & Mitigation

### 10.1 Top 5 Risks with Mitigation Plans

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|-------------|--------|------------|-------|
| 1 | Anthropic/OpenAI block resale channels | Medium | High | Partner with authorized Asian distributors, maintain BYOK option | Founder |
| 2 | Chinese providers cut off western access | Low | High | Cache models locally, use open-source fallbacks | Tech |
| 3 | Payment processor drops you (high risk) | Low | Medium | Multiple processors, crypto option | Founder |
| 4 | Enterprise sales cycle too long | Medium | Medium | Build self-serve for mid-market first | Sales |
| 5 | Customer churn due to price fluctuations | Medium | Low | Hedge with multiple providers, pass-through pricing | Tech |

### 10.2 Operational Risk Dashboard (Weekly Review)

| Check | Threshold | Action if Exceeded |
|-------|-----------|---------------------|
| Provider error rate | >1% | Failover to backup, alert provider |
| Customer support response | >24 hours (paid) | Hire temporary support |
| Monthly burn | >$5,000 | Cut non-essential marketing |
| Churn rate | >5% (monthly) | Interview churned customers |

---

## Part 11: Exit Strategy & Long-term Vision

### 11.1 Potential Exit Paths

| Path | Valuation | Timeline | Likelihood |
|------|-----------|----------|------------|
| Bootstrap lifestyle business | $1-3M (3-5x annual profit) | 2-3 years | High |
| Acquisition by AI infrastructure company (Cloudflare, Replit, Vercel) | $5-15M | 3-4 years | Medium |
| Acquisition by Chinese provider (Alibaba, DeepSeek) | $10-20M | 3-5 years | Low |
| Series A funding → Scale → IPO | $50M+ | 5-7 years | Very low (requires team) |

### 11.2 Long-term Vision (5 Years)

**Near-term (Year 1-2):** Dominant two-way routing layer for AI inference
**Mid-term (Year 2-3):** Add model fine-tuning, deployment, and evaluation
**Long-term (Year 3-5):** Become the "Stripe for AI" - unified interface for all AI services globally

### 11.3 Moats You're Building

| Moat | Description | Strength |
|------|-------------|----------|
| Provider relationships | Volume discounts, preferred access | Medium |
| Routing intelligence | Proprietary cost/latency optimization | Medium |
| Compliance wrappers | SOC2, data residency, audit logs | High |
| Two-way network effects | More customers → better routing → more customers | High |
| Developer trust | Open-source contributions, transparent pricing | Low (earned over time) |

---

## Part 12: Immediate Next Steps (Week 1 Action Plan)

### Day 1-2: Legal & Entity
- [ ] Register Delaware LLC (ZenBusiness or LegalZoom)
- [ ] Apply for EIN from IRS
- [ ] Open Mercury or Brex business bank account

### Day 3-5: Infrastructure
- [ ] Set up Fly.io account + Cloudflare
- [ ] Deploy LiteLLM base proxy
- [ ] Get API keys from DeepSeek (easiest first provider)

### Day 6-10: Product MVP
- [ ] Build simple FastAPI wrapper for auth + rate limiting
- [ ] Create basic dashboard (React + Supabase)
- [ ] Implement free tier (10K tokens)
- [ ] Test end-to-end: customer signup → API call → provider

### Day 11-14: Launch Preparation
- [ ] Create landing page (Framer or Vercel template)
- [ ] Write documentation (GitBook or Mintlify)
- [ ] Draft Hacker News launch post
- [ ] Set up Stripe payment link for $19/month

### Day 15: Launch
- [ ] Post on Hacker News ("Show HN: Unified API for Chinese LLMs")
- [ ] Cross-post to Reddit r/LocalLLaMA
- [ ] Monitor signups and feedback
- [ ] Iterate daily

---

## Conclusion: The Skeleton for Future Prompting

This business plan provides the foundational framework for your two-way LLM routing business. For subsequent prompts, you can reference specific sections:

| Future Prompt Topic | Reference Section |
|--------------------|-------------------|
| Technical architecture deep dive | Part 2 (Product & Architecture) |
| Pricing strategy refinement | Part 3 (Business Model) |
| Go-to-market tactics | Part 4 (Phased Implementation) |
| Financial modeling | Part 6 (Financial Projections) |
| Legal/compliance questions | Part 7 (Legal Framework) |
| Risk scenarios | Part 10 (Risk Register) |
| Hiring/team building | Part 9 (Team Plan) |

**The core insight:** Start with the low-risk BYOK model for Segment 1 to validate demand and generate immediate margin. Reinvest profits into Segment 2 (Claude access) and the reseller model. Keep burn near-zero until you hit $10k MRR. The two-way nature creates natural hedging—if China restricts western models, Segment 1 grows; if west restricts Chinese models, Segment 2 grows.

**You're ready to build.**
