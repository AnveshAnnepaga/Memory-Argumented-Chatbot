import asyncio
import os
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test():
    from app.ai.llm.groq_client import GroqProvider
    from app.core.config import settings

    # Confirm settings paths are correct now
    print(f"groq.temperature = {settings.ai.groq.temperature}")
    print(f"groq.max_tokens  = {settings.ai.groq.max_tokens}")
    print(f"groq.timeout     = {settings.ai.groq.timeout_seconds}")
    print(f"chat_model       = {settings.ai.models.chat_model}")

    p = GroqProvider()
    ok = await p.initialize()
    print(f"\nGroq initialized: {ok} | stub_mode: {p.stub_mode}")

    if not p.stub_mode:
        res = await p.generate(
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond in Markdown."},
                {"role": "user", "content": "In 2 bullet points, explain what LangGraph is."}
            ],
            temperature=0.5,
            max_tokens=200
        )
        print(f"\n=== GROQ RESPONSE ===\n{res.get('content', '')}")
    else:
        print("\nERROR: Groq is still in stub mode — API key issue")

    await p.close()

asyncio.run(test())
