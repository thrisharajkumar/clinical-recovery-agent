"""
Runs the golden set against the guardrail layer deterministically (fast, no
LLM calls, no flakiness, no cost) and optionally against the live local
Ollama model (--live flag, requires `ollama serve` running), to catch
prompt regressions too.

Usage:
    python -m evals.run_evals            # guardrail-only, deterministic, free
    python -m evals.run_evals --live      # also exercises the real local LLM call
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core import guardrails

GOLDEN_SET_PATH = Path(__file__).parent / "golden_set.json"


def run_deterministic():
    cases = json.loads(GOLDEN_SET_PATH.read_text())
    passed, failed, known_limitations = 0, [], []

    for case in cases:
        result = guardrails.check_red_flags(case["input"])
        expected = case.get("expect_escalation", False)
        ok = result.triggered == expected
        (passed := passed + 1) if ok else failed.append(case["id"])
        category = case["category"]
        if category.startswith("known_limitation"):
            known_limitations.append(case["id"])
            status = "⚠️  KNOWN GAP (expected)"
        elif category == "open_policy_question":
            status = "❔ OPEN POLICY (expected, undecided)"
        elif category == "requires_live_llm":
            status = "⏭️  SKIPPED (needs --live)"
        else:
            status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['id']} ({category}): "
              f"expected_escalation={expected} got={result.triggered}")

    print(f"\n{passed}/{len(cases)} checks matched their documented expectation.")
    if known_limitations:
        print(f"⚠️  {len(known_limitations)} of those are DOCUMENTED SAFETY GAPS, "
              f"not verified-safe behaviour: {known_limitations}")
        print("   These pass because the test documents the actual (imperfect) "
              "current behaviour — see the 'note' field in golden_set.json.")
    if failed:
        print(f"Failed (unexpected): {failed}")
        sys.exit(1)


def run_live():
    from app.core import conversation, llm_client
    cases = json.loads(GOLDEN_SET_PATH.read_text())
    for case in cases:
        if case.get("expect_escalation"):
            continue  # these never reach the LLM — guardrail intercepts first
        session_id = f"eval-{case['id']}"
        conversation.append_turn(session_id, "user", case["input"])
        reply, used_engine, recommendation = llm_client.generate_reply(conversation.get_history(session_id))
        flag = "⚠️ " if case.get("expect_tool_call") and not used_engine else ""
        print(f"{flag}{case['id']}: used_engine={used_engine}\n  → {reply[:200]}\n")


if __name__ == "__main__":
    run_deterministic()
    if "--live" in sys.argv:
        run_live()
