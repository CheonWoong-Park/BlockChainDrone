import os

# 드론별 private key 리스트 (hex 형식, '0x' 접두어 제거)
private_keys = [
    "59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",  # drone0
    "5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",  # drone1
    "7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6"   # drone2
]

# 저장할 디렉토리
os.makedirs("keys", exist_ok=True)

for i, key in enumerate(private_keys):
    path = f"keys/drone{i}.hsm"
    with open(path, "wb") as f:
        f.write(bytes.fromhex(key))
    print(f"✅ Saved drone{i} private key to {path}")
