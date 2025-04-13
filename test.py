import requests

COMMAND = {
    "sender": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
    "operation": "move_to",
    "x": 150,
    "y": 220
}

res = requests.post("http://localhost:6000/validate", json=COMMAND)
print("Result from Commander:", res.json())
