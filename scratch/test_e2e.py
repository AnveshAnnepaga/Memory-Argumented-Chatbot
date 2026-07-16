import urllib.request, json

payload = json.dumps({"query": "Explain LangGraph in 2 bullet points", "conversation_id": "default", "user_id": "test-user"}).encode()
req = urllib.request.Request(
    "http://localhost:8000/api/v1/chat/query",
    data=payload,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())

response_text = data.get("data", {}).get("response", "NO RESPONSE FIELD FOUND")
route = data.get("data", {}).get("router_decision", {}).get("route", "?")
exec_ms = data.get("data", {}).get("metadata", {}).get("execution_time_ms", "?")

print(f"Route:   {route}")
print(f"Time:    {exec_ms}ms")
print(f"\n=== RESPONSE ===\n{response_text}")
