import { expect } from "chai";
import { network } from "hardhat";

describe("ModelLedger", function () {
  it("should register and verify an artifact", async function () {
    const { ethers } = await network.connect();

    const ModelLedger = await ethers.getContractFactory("ModelLedger");
    const ledger = await ModelLedger.deploy();

    await ledger.waitForDeployment();

    const artifactId = ethers.id("artifact-001");
    const artifactHash = ethers.id("video-file-001");
    const provenanceHash = ethers.id("c2pa-manifest-001");

    await ledger.registerArtifact(
      artifactId,
      artifactHash,
      provenanceHash,
      "Gemini",
      "Google",
      ethers.ZeroHash
    );

    const result = await ledger.verifyArtifact(
      artifactId,
      artifactHash,
      provenanceHash
    );

    expect(result).to.equal(true);
  });

  it("should link a child artifact to a parent artifact", async function () {
  const { ethers } = await network.connect();

  const ModelLedger = await ethers.getContractFactory("ModelLedger");
  const ledger = await ModelLedger.deploy();

  await ledger.waitForDeployment();

  const parentId = ethers.id("parent-001");
  const childId = ethers.id("child-001");

  const hash1 = ethers.id("original-file");
  const provenance1 = ethers.id("original-provenance");

  const hash2 = ethers.id("modified-file");
  const provenance2 = ethers.id("modified-provenance");

  await ledger.registerArtifact(
    parentId,
    hash1,
    provenance1,
    "Gemini",
    "Google",
    ethers.ZeroHash
  );

  await ledger.registerArtifact(
    childId,
    hash2,
    provenance2,
    "Gemini",
    "Google",
    ethers.ZeroHash
  );

  await ledger.addTransformation(childId, parentId);

  const artifact = await ledger.getArtifact(childId);

  expect(artifact.parentId).to.equal(parentId);
});
});
  