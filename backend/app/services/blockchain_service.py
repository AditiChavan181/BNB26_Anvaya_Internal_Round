import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3


load_dotenv()

RPC_URL = os.getenv("RPC_URL", "http://127.0.0.1:8545")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

BASE_DIR = Path(__file__).resolve().parents[3]
ABI_PATH = (
    BASE_DIR
    / "blockchain"
    / "artifacts"
    / "contracts"
    / "ModelLedger.sol"
    / "ModelLedger.json"
)

CONTRACT_ABI = []
BLOCKCHAIN_ERROR = None
w3 = None
contract = None

if ABI_PATH.is_file():
    with open(ABI_PATH, "r", encoding="utf-8") as file:
        CONTRACT_ABI = json.load(file).get("abi", [])

if not RPC_URL:
    BLOCKCHAIN_ERROR = "RPC_URL is missing from .env"
elif not CONTRACT_ADDRESS:
    BLOCKCHAIN_ERROR = "CONTRACT_ADDRESS is missing from .env"
elif not PRIVATE_KEY:
    BLOCKCHAIN_ERROR = "PRIVATE_KEY is missing from .env"
elif not CONTRACT_ABI:
    BLOCKCHAIN_ERROR = "ModelLedger ABI could not be loaded"
else:
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            BLOCKCHAIN_ERROR = f"Could not connect to blockchain at {RPC_URL}"
        else:
            contract = w3.eth.contract(
                address=Web3.to_checksum_address(CONTRACT_ADDRESS),
                abi=CONTRACT_ABI,
            )
    except Exception as exc:  # pragma: no cover - environment dependent
        BLOCKCHAIN_ERROR = str(exc)


def _ensure_blockchain_ready():
    if w3 is None or contract is None:
        raise RuntimeError(BLOCKCHAIN_ERROR or "Blockchain is unavailable")


def register_artifact(
    artifact_id: bytes,
    artifact_hash: bytes,
    provenance_hash: bytes,
    model: str,
    issuer: str,
    parent_id: bytes,
) -> dict:
    _ensure_blockchain_ready()

    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address)

    transaction = contract.functions.registerArtifact(
        artifact_id,
        artifact_hash,
        provenance_hash,
        model,
        issuer,
        parent_id,
    ).build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "gas": 500000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    signed_transaction = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        "transaction_hash": tx_hash.hex(),
        "block_number": receipt.blockNumber,
    }


def verify_artifact(
    artifact_id: bytes,
    artifact_hash: bytes,
    provenance_hash: bytes,
) -> bool:
    _ensure_blockchain_ready()
    return contract.functions.verifyArtifact(
        artifact_id,
        artifact_hash,
        provenance_hash,
    ).call()


def get_artifact(
    artifact_id: bytes,
) -> dict:
    _ensure_blockchain_ready()
    result = contract.functions.getArtifact(artifact_id).call()

    return {
        "artifact_hash": result[0],
        "provenance_hash": result[1],
        "model": result[2],
        "issuer": result[3],
        "timestamp": result[4],
        "parent_id": result[5],
        "exists": result[6],
    }