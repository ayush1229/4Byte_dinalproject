import os
import json
from web3 import Web3
from .config import Config

# Get the directory of this file (blockchain.py)
basedir = os.path.dirname(os.path.abspath(__file__))

# Compute the ABI path assuming the ABI file is in the same folder as blockchain.py
abi_path = os.path.join(basedir, "PerfectVotingSystemABI.json")

print("ABI path:", abi_path)  # For debugging; remove this in production

# Connect to Ethereum via Infura using the URL from Config
w3 = Web3(Web3.HTTPProvider(Config.INFURA_URL))

# Load the contract ABI from the computed path
with open(abi_path, "r") as f:
    data = json.load(f)
    contract_abi = data["abi"] if "abi" in data else data

# Create the contract instance with the address and ABI from Config
contract = w3.eth.contract(address=Config.CONTRACT_ADDRESS, abi=contract_abi)

# Set up the admin account using the private key from Config
account = w3.eth.account.from_key(Config.PRIVATE_KEY)
