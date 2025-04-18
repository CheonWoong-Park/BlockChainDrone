# BlockChainDrone

## HotStuff 합의 알고리즘이 적용된 프라이빗 블록체인 기반 군집 드론 제어 시스템

### 목적
분산된 드론들이 명령을 제안하고, HotStuff 합의를 통해 블록체인 상에 기록함으로써 자율성과 보안성을 동시에 확보하는 시스템 시연

---

### 시스템 개요
본 시스템은 Commander와 다수의 드론 노드가 참여하는 탈중앙 합의 기반 분산 제어 구조이다.
- HotStuff 3단계 합의 알고리즘
- ECDSA 서명 기반 검증
- 프라이빗 블록체인 기록

각 드론은 명령을 제안하고, 검증하고, 투표 및 커밋하는 역할을 수행합니다.

---

### 합의 프로세스 요약
#### 단계 1: Proposal (Pre-prepare)
- 리더 노드(또는 Commander)가 명령 블록을 제안
- 포함 정보: 명령, 뷰 번호(view), 제안자의 서명

#### 단계 2: Pre-commit (Prepare)
- 다른 드론들은 제안의 유효성(서명 + 명령 검증)을 확인
- 블록체인에 등록된 명령인지 validateCommand()로 검증
- 유효한 경우 투표 전송
- 2f+1개의 유효 투표 수신 시 prepareQC 생성

#### 단계 3: Commit
- prepareQC에 기반해 pre-commit 메시지를 전파
- 드론들이 다시 투표 → commitQC 생성
- 블록 확정 및 로컬 커밋
- 리더 노드는 최종 블록을 스마트컨트랙트에 기록

---

### 서명 기반 명령 검증
- 각 드론은 명령 제안 시 자신의 private key로 서명
- 스마트컨트랙트는 ecrecover()를 통해 서명자 주소를 복구
- 복구된 주소가 실제 트랜잭션 전송자와 일치해야 블록 커밋 허용
- 명령 위조 및 스푸핑 공격 방지

---

### 보안: HSM 기반 개인키 보호
- 드론의 서명 키는 HSM(하드웨어 보안모듈)에 저장
- 외부 접근 불가, 서명만 가능
- 드론이 노획되어도 개인키 추출 불가 → 보안성 유지

---

### 자율성과 탈중앙성
- Commander 없이도 드론 간 자체 명령 제안 가능
- 제안된 명령이 검증 및 합의를 통과하면 블록에 커밋
- 특정 노드에 의존하지 않는 완전한 탈중앙 시스템 구현

---

### 이상 노드 대응 - 신뢰 점수 기반 퇴출 (추후 구현 가능)
- 각 드론의 응답률, 서명 유효성, 트랜잭션 패턴 분석
- 악성 행위 반복 시 신뢰 점수 감소
- 임계치 이하 시 블록체인에서 자동 퇴출
- 탈중앙 환경에서도 자가 치유(autonomous healing) 가능

---

### 블록체인 세팅
1. Solidity 스마트컨트랙트 준비: `contracts/DroneConsensus.sol`
2. 하드햇 컴파일:
```bash
npx hardhat compile
cp artifacts/contracts/DroneConsensus.sol/DroneConsensus.json .
```
3. 로컬 블록체인 실행:
```bash
npx hardhat node
```
4. 스마트컨트랙트 배포:
```bash
npx hardhat run scripts/deploy.js --network localhost
```
→ 배포된 컨트랙트 주소를 `config.py` 내 `CONTRACT_ADDRESS`로 설정

---

### 실행 순서
1. 드론 노드 실행:
```bash
python3 drone_node.py
```
2. 커맨더 서버 실행:
```bash
python3 commander.py
```
3. 테스트 명령 전송:
```bash
python3 test.py
```

---

### 전체 명령 흐름
- 사용자는 `test.py`를 통해 명령을 커맨더에게 전송
- 커맨더는 서명 및 명령 구조 생성 후 리더에게 전달
- 리더 드론은 proposal 전송
- 팔로워 드론은 블록체인을 통해 해당 명령이 서명되어 있는지 확인하고 투표
- 합의가 성립되면 리더는 커밋을 요청
- 각 드론은 로컬 커밋, 리더는 블록체인에 최종 기록

---

### 보안 시나리오 예시: 드론 노획 공격
- 드론 2번이 노획되어 악성 명령을 리더인 척 제안
- 다른 드론들은 명령의 서명자 주소를 복구
- validateCommand() 호출로 명령 검증 여부 확인
- 미검증 명령은 투표 거절 → 합의 실패 → 공격 무력화

---

### 주요 구성 파일
| 파일명 | 설명 |
|--------|------|
| DroneConsensus.sol | 스마트컨트랙트: 서명 검증 및 블록 커밋 |
| commander.py | 명령 서명 및 제안 중계 |
| drone_node.py | 드론 노드 |
| contract_integration.py | Python ↔ Solidity 연동 모듈 |
| test.py | 테스트용 명령 실행 |
| config.py | 주소 및 노드 정보 설정 |

