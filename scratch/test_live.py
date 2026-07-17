import urllib.request
import json
import time

print("Waiting 6 seconds for backend to settle...")
time.sleep(6)

payload = json.dumps({
    "query": "Explain about the LangGraph??",
    "conversation_id": "default",
    "user_id": "test-user"
}).encode("utf-8")

req = urllib.request.Request(
    "http://localhost:8000/api/v1/chat/query",
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    resp = urllib.request.urlopen(req, timeout=40)
    data = json.loads(resp.read().decode())
    response_text = data.get("data", {}).get("response", "NO RESPONSE")
    route = data.get("data", {}).get("router_decision", {}).get("route", "?")
    print(f"\n--- SUCCESS ---")
    print(f"Route: {route}")
    print(f"Response:\n{response_text}")
except Exception as e:
    print(f"Error calling API: {e}")
