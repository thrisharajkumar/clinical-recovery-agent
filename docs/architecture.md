# Architecture

```
Patient message
      │
      ▼
┌─────────────────────┐
│  INPUT guardrail     │  ← deterministic red-flag keyword check
│  (guardrails.py)     │     runs BEFORE any LLM call
└─────────┬────────────┘
          │ triggered?
    ┌─────┴─────┐
   yes           no
    │             │
    ▼             ▼
Escalation    ┌──────────────────────┐
message,      │  Amy (LLM layer)      │
no LLM call   │  system_prompt.py     │
              │  + conversation.py    │
              │  (session history)    │
              └──────────┬────────────┘
                          │ tool_use?
                          ▼
              ┌──────────────────────┐
              │ Mock recommendation   │
              │ engine (rule-based)   │   ← Amy does not generate this content —
              │ recommendation_engine │      herself, only call it
              │ .py                   │
              └──────────┬────────────┘
                          │ structured result
                          ▼
              ┌──────────────────────┐
              │  OUTPUT guardrail     │  ← blocks disallowed claims
              │  (guardrails.py)      │     before reaching patient
              └──────────┬────────────┘
                          ▼
                    Reply to patient
```

**Key design decision:** the recommendation engine is a hard architectural
boundary, not a convenience. Amy does not generate the underlying
recommendation — it originates from the deterministic engine and is only
*communicated* by the LLM layer. This is enforced two ways: structurally
(the LLM must call `get_recommendation` via tool use to get one at all —
verified to be genuine tool calling, not prompt-injected context, by
inspecting the `stop_reason == "tool_use"` branch in `llm_client.py`), and
by an output-side provenance check (`guardrails.check_recommendation_provenance`)
that verifies the final reply text actually reflects what the tool
returned, catching the case where the tool was called correctly but the
LLM's explanation still drifted from it.
