from flask import Flask, request, jsonify
import requests, json, hashlib, threading, datetime
from config import *
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

app = Flask(__name__)
node_id = None
my_node_url = None
log = []
chain = []
locked_qc = None
vote_pool = {}
DRONE_PRIVATE_KEY = None
DRONE_ACCOUNT = None

def log_event(message):
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] [드론 {node_id}] {message}", flush=True)

def is_leader(view):
    return node_id == (view % len(DRONE_NODES))

def quorum():
    return max((len(DRONE_NODES) * 2) // 3, 1)

def get_digest(command):
    return hashlib.sha256(json.dumps(command, sort_keys=True).encode()).hexdigest()

def record_vote(view, stage, sender):
    vote_pool.setdefault(view, {}).setdefault(stage, set()).add(sender)

def vote_count(view, stage):
    return len(vote_pool.get(view, {}).get(stage, set()))

def verify_signature(view, op, x, y, signature, sender):
    hash = Web3.solidityKeccak(["uint256", "string", "uint256", "uint256"], [view, op, x, y])
    eth_hash = encode_defunct(hash)
    try:
        recovered = Account.recover_message(eth_hash, signature=bytes.fromhex(signature.replace("0x", "")))
        return recovered == sender
    except Exception as e:
        log_event(f"⚠️ 서명 복구 실패: {e}")
        return False

def sign_command(view, op, x, y):
    hash = Web3.solidityKeccak(["uint256", "string", "uint256", "uint256"], [view, op, x, y])
    signed = Account.sign_message(encode_defunct(hash), private_key=DRONE_PRIVATE_KEY)
    return signed.signature.hex()

def send_to_blockchain(view, command):
    op = command["operation"]
    x = command.get("x", 0)
    y = command.get("y", 0)
    sig = sign_command(view, op, x, y)

    payload = {
        "blockView": view,
        "operation": op,
        "x": x,
        "y": y,
        "signature": sig,
        "sender": DRONE_ACCOUNT.address
    }

    try:
        res = requests.post(f"{COMMANDER_ADDR}/commitBlockWithSig", json=payload)
        log_event(f"🔗 블록체인 커밋 요청 완료 → {res.status_code}")
    except Exception as e:
        log_event(f"❌ 블록체인 커밋 실패: {e}")

@app.route("/propose", methods=["POST"])
def handle_propose():
    data = request.json
    view = data["view"]
    command = data["command"]
    sender = data["sender"]
    sig = data["signature"]
    digest = get_digest(command)

    log.append({
        "type": "propose",
        "view": view,
        "command": command,
        "sender": sender,
        "signature": sig,
        "digest": digest
    })
    log_event(f"📩 리더가 제안 수신 (view={view}) → pre-prepare 브로드캐스트")

    if is_leader(view):
        for url in DRONE_NODES.values():
            if url != my_node_url:
                try:
                    requests.post(f"{url}/pre-prepare", json=data)
                except Exception as e:
                    log_event(f"⚠️ pre-prepare 전송 실패 → {url}: {e}")
    return jsonify({"status": "propose_processed"})

@app.route("/pre-prepare", methods=["POST"])
def handle_preprepare():
    data = request.json
    view = data["view"]
    command = data["command"]
    sender = data["sender"]
    sig = data["signature"]
    digest = get_digest(command)

    log.append({
        "type": "pre-prepare",
        "view": view,
        "command": command,
        "sender": sender,
        "signature": sig,
        "digest": digest
    })

    if not is_leader(view):
        if verify_signature(view, command["operation"], command.get("x", 0), command.get("y", 0), sig, sender):
            log_event(f"✅ pre-prepare 서명 검증 성공 → vote 전송")
            vote = {"view": view, "digest": digest, "from": DRONE_ACCOUNT.address}
            leader_url = DRONE_NODES[view % len(DRONE_NODES)]
            requests.post(f"{leader_url}/vote/prepare", json=vote)
        else:
            log_event(f"❌ pre-prepare 서명 검증 실패")
    return jsonify({"status": "pre-prepare_processed"})

@app.route("/vote/prepare", methods=["POST"])
def handle_prepare_vote():
    vote = request.json
    view = vote["view"]
    sender = vote["from"]
    record_vote(view, "prepare", sender)

    log_event(f"🗳️ prepare 투표 수신 (view={view}) → {vote_count(view, 'prepare')}개")

    if is_leader(view) and vote_count(view, "prepare") >= quorum():
        log_event(f"✅ prepareQC 생성 완료 → pre-commit 전파")
        msg = {"view": view}
        for url in DRONE_NODES.values():
            requests.post(f"{url}/pre-commit", json=msg)
    return jsonify({"status": "prepare_vote_received"})

@app.route("/pre-commit", methods=["POST"])
def handle_precommit():
    data = request.json
    view = data["view"]

    if not is_leader(view):
        vote = {"view": view, "from": DRONE_ACCOUNT.address}
        leader_url = DRONE_NODES[view % len(DRONE_NODES)]
        requests.post(f"{leader_url}/vote/precommit", json=vote)
        log_event(f"📥 pre-commit 브로드캐스트 수신 (view={view})")
    return jsonify({"status": "precommit_received"})

@app.route("/vote/precommit", methods=["POST"])
def handle_precommit_vote():
    vote = request.json
    view = vote["view"]
    sender = vote["from"]
    record_vote(view, "precommit", sender)

    log_event(f"🗳️ precommit 투표 수신 (view={view}) → {vote_count(view, 'precommit')}개")

    if is_leader(view) and vote_count(view, "precommit") >= quorum():
        log_event(f"✅ commitQC 생성 완료 → commit 전파")
        msg = {"view": view}
        for url in DRONE_NODES.values():
            requests.post(f"{url}/commit", json=msg)
    return jsonify({"status": "precommit_vote_received"})

@app.route("/commit", methods=["POST"])
def handle_commit():
    data = request.json
    view = data["view"]
    global locked_qc
    locked_qc = {"view": view}

    block = None
    for entry in log:
        if entry["view"] == view and entry["type"] in ["propose", "pre-prepare"]:
            block = {
                "view": view,
                "digest": entry["digest"],
                "qc": locked_qc,
                "command": entry["command"]
            }
            break

    if block:
        chain.append(block)
        log_event(f"🔐 블록 커밋 완료! view={view}, digest={block['digest']}")
        if is_leader(view):
            send_to_blockchain(view, block["command"])
        return jsonify({"status": "commit_applied", "qc": locked_qc})
    else:
        log_event(f"⚠️ 커밋 실패: 블록 없음")
        return jsonify({"status": "commit_failed"})

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "alive", "id": node_id})

@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify(chain)

if __name__ == "__main__":
    node_id = int(input("드론 ID 입력 (0~2): "))
    my_node_url = DRONE_NODES[node_id]

    def load_key(id):
        with open(f"keys/drone{id}.hsm", "rb") as f:
            return f.read()

    DRONE_PRIVATE_KEY = load_key(node_id)
    DRONE_ACCOUNT = Account.from_key(DRONE_PRIVATE_KEY)
    log_event(f"계정 주소: {DRONE_ACCOUNT.address}")
    app.run(port=5000 + node_id)
