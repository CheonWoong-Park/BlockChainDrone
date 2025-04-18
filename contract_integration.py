from web3 import Web3
import json
from config import CONTRACT_ADDRESS

class ContractManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        with open('DroneConsensus.json') as f:
            contract_abi = json.load(f)['abi']
        self.contract = self.w3.eth.contract(
            address=CONTRACT_ADDRESS,
            abi=contract_abi
        )

    def commit_block_with_sig(self, blockView, operation, x, y, signature, signer_address):
        tx = self.contract.functions.commitBlockWithSig(
            blockView, operation, x, y, bytes.fromhex(signature.replace("0x", ""))
        ).transact({'from': signer_address})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx)
        return receipt



    def is_authorized(self, address):
        try:
            return self.contract.functions.isAuthorized(address).call()
        except Exception as e:
            print(f"[Contract] ❌ Failed to check authorization: {e}")
            return False
