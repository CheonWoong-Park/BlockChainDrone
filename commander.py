from flask import Flask, jsonify, request
import requests
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
from config import DRONE_NODES
from contract_integration import ContractManager  # 🔑 추가

app = Flask(__name__)
current_view = 0
last_qc = None
cm = ContractManager()  # 🔑 스마트컨트랙트 연동 인스턴스

# --- 드론 상태 확인 ---
def get_alive_drones():
    alive = []
    for nid, url in DRONE_NODES.items():
        try:
            res = requests.get(f"{url}/ping", timeout=1)
            if res.ok:
                alive.append((nid, url))
        except:
            continue
    return alive

# --- 라운드로빈 리더 선택 ---
def select_leader():
    global current_view
    alive = get_alive_drones()
    if not alive:
        return None
    sorted_alive = sorted(alive, key=lambda x: x[0])
    leader_index = current_view % len(sorted_alive)
    return sorted_alive[leader_index][1]

# --- 서명 생성 ---
def sign_command(view, operation, x, y, private_key):
    hash = Web3.solidityKeccak(["uint256", "string", "uint256", "uint256"], [view, operation, x, y])
    signed = Account.sign_message(encode_defunct(hash), private_key=private_key)
    return signed.signature.hex()

# --- 명령 수신 및 제안 전송 ---
@app.route("/validate", methods=["POST"])
def validate():
    global current_view, last_qc
    data = request.json

    # 명령 정보 추출
    private_key = data["private_key"]
    operation = data["operation"]
    x = data.get("x", 0)
    y = data.get("y", 0)

    # 계정 정보 복구
    account = Account.from_key(private_key)
    sender = account.address

    # 서명 생성
    signature = sign_command(current_view, operation, x, y, private_key)

    # proposal 생성
    proposal = {
        "view": current_view,
        "command": {
            "operation": operation,
            "x": x,
            "y": y
        },
        "sender": sender,
        "signature": signature,
        "justify": last_qc
    }

    # 리더 선택
    leader_url = select_leader()
    if not leader_url:
        print("[Commander] ❌ 활성화된 리더 없음")
        return jsonify({"valid": False})

    # 제안 전송
    try:
        res = requests.post(f"{leader_url}/propose", json=proposal)
        response_data = res.json()
        print(f"[Commander] 📤 제안 전송 완료 → {leader_url}, 응답: {response_data}")

        if 'qc' in response_data:
            last_qc = response_data['qc']
            print(f"[Commander] 🔐 QC 저장됨: view={last_qc['view']}")

        current_view += 1
        return jsonify({"valid": True})
    except Exception as e:
        print(f"[Commander] ⚠️ 제안 전송 실패: {e}")
        return jsonify({"valid": False})

# --- 블록체인 커밋 처리 엔드포인트 ---
@app.route('/commitBlockWithSig', methods=['POST'])
def commit_block_with_sig():
    data = request.json
    try:
        receipt = cm.commit_block_with_sig(
            data["blockView"],
            data["operation"],
            data["x"],
            data["y"],
            data["signature"],
            data["sender"]
        )
        print(f"[Commander] ✅ 블록체인 커밋 완료 → 블록 번호: {receipt.blockNumber}")
        return jsonify({"status": "success", "block": receipt.blockNumber})
    except Exception as e:
        print(f"[Commander] ❌ 블록체인 커밋 실패: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(port=6000)
