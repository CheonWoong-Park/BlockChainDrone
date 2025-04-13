from web3 import Web3
import json
from config import CONTRACT_ADDRESS

class ContractManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))  # 로컬 블록체인 노드
        with open('DroneConsensus.json') as f:
            contract_abi = json.load(f)['abi']
        self.contract = self.w3.eth.contract(
            address=CONTRACT_ADDRESS,
            abi=contract_abi
        )
        self.default_account = self.w3.eth.accounts[0]
        self.w3.eth.default_account = self.default_account

    def validate_command(self, sender, operation):
        tx = self.contract.functions.validateCommand(sender, operation).transact()
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        return receipt.status == 1

    def commit_block(self, view, digest, operation, x, y):
        tx = self.contract.functions.commitBlock(
            view,
            digest,
            operation,
            x,
            y
        ).transact({'from': self.default_account})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        return receipt