import requests
import json

COMMAND = { 
    "private_key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "operation": "move_to",
    "x": 100,
    "y": 200
}

res = requests.post("http://localhost:6000/validate", json=COMMAND)
print("[TEST] Commander 전송:", json.dumps(COMMAND, indent=2))
print("[TEST] Commander 응답:", res.json())
