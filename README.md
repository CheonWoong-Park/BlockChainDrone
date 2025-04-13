# 🚁 BlockChainDrone

HotStuff 합의 알고리즘이 적용된 프라이빗 블록체인 기반 드론 

> 목적: 분산된 드론들이 합의 알고리즘을 통해 명령을 처리하고, 블록체인 상에 기록하는 과정 시연

---

##  블록체인 세팅

### 1. Solidity 스마트 컨트랙트 준비

- `./drone-blockchain/contracts/DroneConsensus.sol` 파일에 컨트랙트 코드 작성 또는 수정

### 2. 하드햇 컴파일

```bash
npx hardhat compile
```

- 컴파일 성공 시, ABI 파일 생성됨:
```bash
cp artifacts/contracts/DroneConsensus.sol/DroneConsensus.json .
```

### 3. 로컬 블록체인 노드 실행 (Hardhat RPC)

```bash
npx hardhat node
```

- 실행 시 여러 개의 테스트용 계정과 프라이빗 키가 출력됨
- 이 중 하나를 `test.py` 또는 `config.py`에 적용해 사용

### 4. 스마트 컨트랙트 배포

```bash
npx hardhat run scripts/deploy.js --network localhost
```

- 결과 예시:
```
DroneConsensus deployed to: 0xabc123...
```
- 이 주소를 `config.py`의 `CONTRACT_ADDRESS` 변수에 복사해 사용

---

## 노드 및 서버 실행

### 1. 드론 노드 실행
```bash
python3 drone_node.py
```
- 0~2의 ID를 입력해 각 드론 인스턴스를 실행

### 2. 커맨더 서버 실행
```bash
python3 commander.py
```
- 명령을 처리하는 중앙 통제 서버 역할

### 3. 명령 전송 (테스트)
```bash
python3 test.py
```
- 테스트용 명령을 커맨더 서버에 전송

---

## 전체 흐름 요약

1. 사용자는 `test.py`를 통해 커맨더 서버에 명령을 전송합니다.
   - 예: 특정 x, y 좌표로 이동, 공격, 구조 등의 명령

2. 커맨더는 이 명령을 스마트 컨트랙트를 통해 유효성 검증합니다.
   - `validateCommand()` 호출

3. 검증에 성공하면 커맨더는 현재 라운드의 리더 드론에게 명령을 제안합니다.
   - 리더는 `view % 3` 방식으로 라운드로빈으로 결정됨

4. 리더 드론은 다른 팔로워 드론들에게 명령에 대한 투표 요청을 브로드캐스트합니다.

5. 전체 드론 중 3분의 2 이상이 찬성하면 **HotStuff 합의가 성립**됩니다.
   - 리더는 QC(Quorum Certificate)을 생성
   - 블록 커밋 요청을 드론들에 전송

6. 드론들은 이 명령을 **로컬 체인에 커밋**하며, 리더 드론은 명령 내역을 **블록체인 스마트 컨트랙트에 기록**합니다.
   - `commitBlock(view, digest, operation, x, y)` 함수 호출

---

## 구성 파일 설명

| 파일명 | 설명 |
|--------|------|
| `DroneConsensus.sol` | 스마트 컨트랙트 코드 (명령 검증 + 블록 커밋) |
| `contract_integration.py` | Python ↔ Solidity 연동 관리 모듈 |
| `commander.py` | 명령 제안 및 리더에게 전달하는 서버 역할 |
| `drone_node.py` | 각 드론 인스턴스 / HotStuff 합의 수행 |
| `config.py` | 노드 주소 및 컨트랙트 주소 설정 |
| `test.py` | 테스트용 명령 전송 스크립트 |

---

