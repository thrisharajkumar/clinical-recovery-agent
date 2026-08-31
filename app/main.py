import logging

from fastapi import FastAPI

from app.core import conversation, guardrails, llm_client
from app.models.schemas import ChatRequest, ChatResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recuro")

app = FastAPI(title="Recuro — Amy Recovery Coach", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # 1. INPUT guardrail — check before we ever call the LLM.
    red_flag = guardrails.check_red_flags(req.message)
    if red_flag.triggered:
        logger.warning(
            "escalation triggered session=%s terms=%s", req.session_id, red_flag.matched_terms
        )
        conversation.append_turn(req.session_id, "user", req.message)
        msg = guardrails.escalation_message()
        conversation.append_turn(req.session_id, "assistant", msg)
        return ChatResponse(
            session_id=req.session_id,
            reply=msg,
            escalated=True,
            escalation_reason=", ".join(red_flag.matched_terms),
        )

    # 2. Normal path — LLM + tool use.
    conversation.append_turn(req.session_id, "user", req.message)
    history = conversation.get_history(req.session_id)
    reply, used_engine, recommendation = llm_client.generate_reply(history)

    # 3a. Provenance check — did the reply actually reflect what the
    # recommendation engine returned, if it was called? A tool call
    # happening correctly does not guarantee the final text stayed
    # faithful to it.
    if used_engine and not guardrails.check_recommendation_provenance(reply, recommendation):
        logger.warning(
            "provenance check failed session=%s recommendation=%r reply=%r",
            req.session_id, recommendation, reply,
        )
        reply = (
            f"Here's what I'd suggest: {recommendation['exercise']}. "
            f"{recommendation['rationale']}"
        )

    # 3b. OUTPUT guardrail — check before returning to the patient.
    violation = guardrails.check_output_safety(reply)
    if violation:
        logger.warning(
            "output guardrail blocked session=%s pattern=%r", req.session_id, violation
        )
        reply = (
            "I want to be careful here — that's a question your care team should "
            "answer directly rather than me guessing. Would you like me to note "
            "this for them?"
        )

    conversation.append_turn(req.session_id, "assistant", reply)
    return ChatResponse(
        session_id=req.session_id,
        reply=reply,
        escalated=False,
        used_recommendation_engine=used_engine,
    )
