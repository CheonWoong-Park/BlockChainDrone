from flask import Flask, jsonify, request
import requests
import hashlib
import json
import threading
import time
from config import *
from contract_integration import ContractManager
cm = ContractManager()

app = Flask(__name__)
node_id = None
my_node_url = None
log = []
chain = []  # 🔗 실제 블록체인 체인 구조
locked_qc = None
last_voted_view = -1

# --- 유틸 함수 ---
def is_leader(view):
    return node_id == (view % len(DRONE_NODES))

def get_digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

# --- QC 관련 ---
def make_qc(digest, view):
    votes = [entry for entry in log if entry.get('type') == 'vote' and entry.get('digest') == digest and entry.get('view') == view]
    quorum_size = max((len(DRONE_NODES) * 2) // 3, 1)
    if len(votes) >= quorum_size:
        return {"view": view, "digest": digest, "signatures": ["sig" for _ in votes]}  # 서명은 간략화
    return None

# --- 메시지 카운트 ---
def vote_count(digest, view):
    seen = set()
    count = 0
    for entry in log:
        if entry.get('type') == 'vote' and entry.get('digest') == digest and entry.get('view') == view:
            sender = entry.get('sender')
            if sender and sender not in seen:
                seen.add(sender)
                count += 1
    return count

# --- 핸들러 ---
@app.route('/propose', methods=['POST'])
def handle_propose():
    data = request.json
    qc = data.get("justify")
    view = data.get("view")
    command = data.get("command")
    digest = get_digest(command)

    global locked_qc
    if locked_qc and qc and qc.get('view', -1) < locked_qc.get('view', -1):
        print(f"[드론 {node_id}] 🔒 QC Lock 위반, 블록 거절! (view={view})")
        return jsonify({"status": "locked_reject"})

    # 🔐 블록체인에서 실제 유효성 검증 이벤트가 존재하는지 확인
    if not cm.is_command_logged(command['sender'], command['operation']):
        print(f"[드론 {node_id}] ❌ 체인에 기록되지 않은 명령, vote 거절!")
        return jsonify({"status": "unverified_command"})

    print(f"[드론 {node_id}] 📨 블록 제안 수락됨, view={view}, digest={digest}")
    log.append({"type": "propose", "digest": digest, "view": view, "command": command, "justify": qc})

    if not is_leader(view):
        print(f"[드론 {node_id}] 🕊️ vote 준비 중... (view={view})")
        threading.Thread(target=send_vote, args=(digest, view)).start()
    else:
        print(f"[드론 {node_id}] 👑 나는 리더다 (view={view}), propose 브로드캐스트 중...")
        threading.Thread(target=broadcast_propose, args=(data,)).start()

    return jsonify({"status": "propose_received"})


@app.route('/vote', methods=['POST'])
def handle_vote():
    data = request.json
    if 'sender' not in data:
        data['sender'] = request.remote_addr or f"drone_{node_id}"
    return process_vote(data, external=True)

def process_vote(data, external=False):
    digest = data['digest']
    view = data['view']
    sender = data.get('sender', f"drone_{node_id}")
    log.append({"type": "vote", "digest": digest, "view": view, "sender": sender})
    count = vote_count(digest, view)
    quorum_size = max((len(DRONE_NODES) * 2) // 3, 1)
    print(f"[드론 {node_id}] 🗳️ {digest} (view={view}) ← {sender} | 총 투표 수: {count}")
    if is_leader(view) and count >= quorum_size:
        qc = make_qc(digest, view)
        print(f"[드론 {node_id}] ✅ QC 생성 완료! digest={digest}, view={view}")
        threading.Thread(target=broadcast_commit, args=(digest, qc, view)).start()
    if external:
        return jsonify({"status": "vote_received"})

@app.route('/commit', methods=['POST'])
def handle_commit():
    data = request.json
    digest = data.get('digest')
    qc = data.get('qc') or {}
    view = qc.get('view', -1)
    global locked_qc
    locked_qc = qc

    command = None
    for entry in log:
        if entry["digest"] == digest and entry["view"] == view and entry["type"] == "propose":
            command = entry.get("command")
            break

    block = {
        "view": view,
        "digest": digest,
        "qc": qc,
        "command": command  # 🔥 실제 명령 포함
    }
    chain.append(block)

    print(f"[드론 {node_id}] 🔥 블록 커밋됨! digest={digest}, view={view} → 체인 길이: {len(chain)})")
    return jsonify({"status": "commit_received", "qc": locked_qc})

@app.route('/chain', methods=['GET'])
def get_chain():
    return jsonify(chain)

# --- propose 브로드캐스트 ---
def broadcast_propose(propose_data):
    for nid, url in DRONE_NODES.items():
        if url != my_node_url:
            try:
                print(f"[드론 {node_id}] 📡 propose 전송 중 → {url}")
                requests.post(f"{url}/propose", json=propose_data)
            except Exception as e:
                print(f"[드론 {node_id}] ❌ propose 전송 실패: {url}, 에러: {e}")

# --- vote 전송 ---
def send_vote(digest, view):
    vote = {
        "view": view,
        "digest": digest,
        "sender": f"drone_{node_id}"
    }
    leader_id = view % len(DRONE_NODES)
    leader_url = DRONE_NODES[leader_id]
    try:
        print(f"[드론 {node_id}] 📬 리더에게 vote 전송 중 → {leader_url} (view={view})")
        response = requests.post(f"{leader_url}/vote", json=vote)
        print(f"[드론 {node_id}] ✅ vote 전송 성공 → {response.status_code} {response.text}")
    except Exception as e:
        print(f"[드론 {node_id}] ❌ vote 전송 실패: {e}")

# --- 커밋 전송 ---
def broadcast_commit(digest, qc, view):
    commit_msg = {"digest": digest, "qc": qc}
    for nid, url in DRONE_NODES.items():
        try:
            requests.post(f"{url}/commit", json=commit_msg)
        except Exception as e:
            print(f"[드론 {node_id}] ❌ commit 전송 실패: {url}, 에러: {e}")

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive", "node_id": node_id})

if __name__ == "__main__":
    node_id = int(input("드론 ID를 입력하세요 (0-2): "))
    my_node_url = DRONE_NODES[node_id]
    print(f"[드론 {node_id}] 🛫 준비 완료. 리더는 view % {len(DRONE_NODES)} 기준으로 동적으로 결정됨.")
    app.run(port=5000 + node_id, threaded=True)
