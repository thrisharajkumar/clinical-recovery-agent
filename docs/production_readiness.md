# Prototype → Production: what changes

This prototype is deliberately narrow-footprint: no agent framework, no
vector DB, no orchestration layer, no Kubernetes. That's a considered choice
for a time-boxed, safety-first build — not a shortcut. Ordered here by
**risk**, not by infrastructure, because that's the order it actually
matters in.

## 1. Clinical validation

Who signs off that the recommendation rules, escalation criteria, and
wording are correct? Right now: nobody — the recommendation engine is a
stand-in with the same interface a real one would have, not a claim of
clinical accuracy.

## 2. Regulatory classification

**Stated precisely, not definitively**: this prototype is deliberately kept
on the coaching/education side of the line, not the regulated
clinical-decision-support side. But whether a deployed version of this
functionality falls within medical-device software regulation depends on
its actual intended purpose and functionality at the time — that's a
formal assessment, not something this document can settle. (UK MHRA
guidance on software and AI as a medical device is explicit that this
depends on intended use, not on how a product is marketed — see
"Software and artificial intelligence (AI) as a medical device" on
gov.uk.) The right framing isn't "this isn't regulated" — it's "I kept the
prototype's scope narrow so as not to accidentally expand its intended
purpose before that assessment happens."

## 3. Safety evaluation, expanded

The current golden set (`evals/golden_set.json`) documents known gaps
rather than hiding them (see README "Known limitations"). Production needs:
- A much larger, clinician-labelled test set, not just more keyword variants
- Adversarial cases: prompt injection, hallucination-fishing, scope-boundary
  probing (`requires_live_llm` cases in the golden set are a start, not
  a finished suite — they need an LLM-as-judge or human review pass,
  not just a pass/fail on whether the guardrail fired)
- Regression testing on every prompt or model change

## 4. Privacy & security

Patient conversation data is **special category personal data** under UK
GDPR (health data), not just "sensitive" in a general sense. Processing it
lawfully needs both an Article 6 lawful basis *and* a separate Article 9
condition — these are two different requirements, not one. Beyond that:
data minimisation, access control, encryption at rest and in transit,
a defined retention/deletion policy, and a DPIA where appropriate.

## 5. Reliability

What happens when the LLM API is down or slow? Right now: nothing handles
this — a failed call just fails. Production needs a graceful fallback (a
static "please contact your care team" response, not a broken coach),
retries, and circuit breakers.

## 6. Monitoring & audit events

Beyond general logging, every safety-relevant action needs to be an
auditable event, not just a log line — something like:
```json
{
  "session_id": "...", "timestamp": "...",
  "event_type": "recommendation" | "escalation" | "provenance_check_failed",
  "recommendation_id": "...", "source": "mock_recommendation_engine",
  "model_version": "...", "safety_status": "passed" | "flagged"
}
```
Track escalation rate, refusal rate, guardrail-trigger rate, provenance-check
failure rate, latency, token cost, model version, and unexpected topic
drift. This isn't built in the prototype — the point is understanding why
it's needed, not building it against a 4-day deadline.

## 7. Human escalation path

The escalation message tells the patient to contact their care team — in
production that needs to actually reach a real clinician/care team
endpoint, not just be a well-worded string.

## 8. Cost, at real volume

Token usage per conversation, tracked and budgeted — not just estimated
once, as in the README's cost section.

---

**Explicitly out of scope for this challenge, on purpose:** a real clinical
recommendation engine, real patient/EHR data, full regulatory compliance,
production-grade auth and scaling. Naming these here is the point — it
shows the production gap is understood, not missed.

**Claims this document deliberately avoids making**, because they'd be
overstated for a prototype: "the system is clinically safe," "the
guardrails prevent hallucinations," "the prototype is GDPR compliant,"
"Amy isn't regulated." The accurate claim is narrower: *this prototype
demonstrates a safety-oriented architecture* — not that it has achieved
safety, compliance, or clinical validation.
