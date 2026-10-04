import { network } from "hardhat";

async function main() {
  const { ethers } = await network.connect();

  const ModelLedger = await ethers.getContractFactory("ModelLedger");

  const modelLedger = await ModelLedger.deploy();

  await modelLedger.waitForDeployment();

  console.log(
    "ModelLedger deployed to:",
    await modelLedger.getAddress()
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});