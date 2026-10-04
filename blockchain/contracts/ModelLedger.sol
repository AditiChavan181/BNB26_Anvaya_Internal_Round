// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract ModelLedger {

    struct Artifact {
        bytes32 artifactHash;
        bytes32 provenanceHash;
        string model;
        string issuer;
        uint256 timestamp;
        bytes32 parentId;
        bool exists;
    }

    mapping(bytes32 => Artifact) private artifacts;

    event ArtifactRegistered(
        bytes32 indexed artifactId,
        bytes32 artifactHash,
        bytes32 provenanceHash,
        string model,
        string issuer,
        uint256 timestamp,
        bytes32 parentId
    );

    event TransformationAdded(
        bytes32 indexed childId,
        bytes32 indexed parentId
    );

    function registerArtifact(
        bytes32 artifactId,
        bytes32 artifactHash,
        bytes32 provenanceHash,
        string calldata model,
        string calldata issuer,
        bytes32 parentId
    ) external {
        require(
            !artifacts[artifactId].exists,
            "Artifact already exists"
        );

        artifacts[artifactId] = Artifact({
            artifactHash: artifactHash,
            provenanceHash: provenanceHash,
            model: model,
            issuer: issuer,
            timestamp: block.timestamp,
            parentId: parentId,
            exists: true
        });

        emit ArtifactRegistered(
            artifactId,
            artifactHash,
            provenanceHash,
            model,
            issuer,
            block.timestamp,
            parentId
        );
    }

    function getArtifact(bytes32 artifactId)
        external
        view
        returns (
            bytes32 artifactHash,
            bytes32 provenanceHash,
            string memory model,
            string memory issuer,
            uint256 timestamp,
            bytes32 parentId,
            bool exists
        )
    {
        Artifact memory artifact = artifacts[artifactId];

        return (
            artifact.artifactHash,
            artifact.provenanceHash,
            artifact.model,
            artifact.issuer,
            artifact.timestamp,
            artifact.parentId,
            artifact.exists
        );
    }

    function verifyArtifact(
        bytes32 artifactId,
        bytes32 artifactHash,
        bytes32 provenanceHash
    )
        external
        view
        returns (bool)
    {
        Artifact memory artifact = artifacts[artifactId];

        if (!artifact.exists) {
            return false;
        }

        return (
            artifact.artifactHash == artifactHash &&
            artifact.provenanceHash == provenanceHash
        );
    }

    function addTransformation(
        bytes32 childId,
        bytes32 parentId
    ) external {
        require(
            artifacts[parentId].exists,
            "Parent does not exist"
        );

        require(
            artifacts[childId].exists,
            "Child does not exist"
        );

        artifacts[childId].parentId = parentId;

        emit TransformationAdded(
            childId,
            parentId
        );
    }
}