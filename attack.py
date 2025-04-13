import requests
import time

ATTACK_COMMAND = {
    "view": 0,
    "seq": int(time.time()),
    "command": {
        "sender": "0xBADBADBAD",
        "operation": "self_destruct"
    }
}

TARGET_DRONES = [
    "http://localhost:5000",  # Drone 0
    "http://localhost:5001"   # Drone 1
]

def send_fake_pre_prepare():
    print("💀 [Compromised Drone] Sending fake pre-prepare to other drones...")
    for target in TARGET_DRONES:
        try:
            res = requests.post(f"{target}/pre-prepare", json=ATTACK_COMMAND)
            print(f"→ Sent to {target}, got: {res.json()}")
        except Exception as e:
            print(f"❌ Failed to send to {target}: {e}")

if __name__ == "__main__":
    send_fake_pre_prepare()