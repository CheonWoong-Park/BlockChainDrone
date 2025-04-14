import requests
from config import DRONE_NODES
import time

def simulate_stealth_attack():
    attack_view = 101
    digest = None

    malicious_command = {
        "command": {
            "sender": "0x000000000000000000000000000000000000dead",  # 가짜 주소
            "operation": "malicious_cmd",
            "x": 999,
            "y": 999
        },
        "view": attack_view,
        "justify": None
    }


    print(f"💀 공격 시작: view={attack_view}, 리더는 {attack_view % len(DRONE_NODES)}번 드론")

    for nid, url in DRONE_NODES.items():
        try:
            print(f"📡 {url} 에게 malicious_cmd 제안 전송 중...")
            res = requests.post(f"{url}/propose", json=malicious_command)
            print(f"→ 응답: {res.status_code} {res.text}")
        except Exception as e:
            print(f"❌ {url} 전송 실패: {e}")

if __name__ == "__main__":
    simulate_stealth_attack()

