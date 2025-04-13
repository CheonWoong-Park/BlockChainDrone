from flask import Flask, jsonify, request
import requests
import threading
import time
from contract_integration import ContractManager
from config import DRONE_NODES

cm = ContractManager()
app = Flask(__name__)
current_view = 0  # 라운드로빈 방식으로 증가할 view 번호
last_qc = None   # 직전 라운드에서 생성된 QC

# 드론 핑 확인
def get_alive_drones():
    alive = []
    for nid, url in DRONE_NODES.items():
        try:
            res = requests.get(f"{url}/ping", timeout=1)
            if res.ok:
                data = res.json()
                alive.append((nid, url))
        except:
            continue
    return alive

# 라운드로빈 리더 선택
def select_leader():
    global current_view
    alive = get_alive_drones()
    if not alive:
        return None
    sorted_alive = sorted(alive, key=lambda x: x[0])
    leader_index = current_view % len(sorted_alive)
    return sorted_alive[leader_index][1]  # URL 반환

# 명령 전송
@app.route('/validate', methods=['POST'])
def validate():
    global current_view, last_qc
    command = request.json
    print(f"[명령서버] ⏳ 명령 검증 중: {command['operation']} from {command['sender']}")

    is_valid = cm.validate_command(command['sender'], command['operation'])
    if not is_valid:
        print("[명령서버] ❌ 명령이 거부됨 (스마트 컨트랙트 검증 실패)")
        return jsonify({"valid": False})

    leader_url = select_leader()
    if not leader_url:
        print("[명령서버] ❌ 활성화된 리더 없음")
        return jsonify({"valid": False})

    print(f"[명령서버] ✅ 명령 유효. 리더 노드({leader_url})에게 제안 전송")

    propose = {
        "view": current_view,
        "command": command,
        "justify": last_qc  # 직전 라운드 QC 포함
    }

    try:
        res = requests.post(f"{leader_url}/propose", json=propose)
        response_data = res.json()
        print(f"[명령서버] 📤 제안 전송 완료 → {leader_url} 응답: {response_data}")

        # 커밋된 경우 QC 저장
        if 'qc' in response_data:
            last_qc = response_data['qc']
            print(f"[명령서버] 🔐 QC 저장됨: view={last_qc['view']} digest={last_qc['digest']}")

        current_view += 1
    except Exception as e:
        print(f"[명령서버] ⚠️ 리더 전송 실패: {e}")
        return jsonify({"valid": False})

    return jsonify({"valid": True})

if __name__ == "__main__":
    app.run(port=6000)
