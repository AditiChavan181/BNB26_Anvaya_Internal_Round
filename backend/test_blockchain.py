from app.services.blockchain_service import w3, contract


print("Connected:", w3.is_connected())
print("Latest block:", w3.eth.block_number)
print("Contract:", contract.address)