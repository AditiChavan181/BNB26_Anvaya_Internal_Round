from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.artifact import Artifact
from app.services.blockchain_service import BLOCKCHAIN_ERROR, get_artifact, register_artifact
from app.services.hash_service import calculate_sha256
from app.services.provenance import analyze_provenance, compute_provenance_hash


router = APIRouter(
    prefix="/api/provenance",
    tags=["Provenance"],
)


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "25")) * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/avif",
    "video/mp4",
    "video/webm",
}


def _safe_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    allowed = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".mp4", ".webm"}
    return extension if extension in allowed else ""


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _payload_from_result(result: dict, *, sha256: str | None = None) -> dict:
    payload = {
        "status": result.get("status", "UNVERIFIABLE"),
        "model": result.get("model"),
        "model_identifier": result.get("model_identifier"),
        "model_type": result.get("model_type"),
        "tool": result.get("tool"),
        "issuer": result.get("issuer"),
        "validation_state": result.get("validation_state"),
        "validation_results": result.get("validation_results", []),
        "actions": result.get("actions", []),
        "ingredients": result.get("ingredients", []),
        "has_provenance_chain": bool(result.get("has_provenance_chain", False)),
        "error": result.get("error"),
    }
    if sha256:
        payload["sha256"] = sha256
    return payload


def _artifact_id_from_sha(sha256_hex: str) -> bytes:
    return hashlib.sha256(sha256_hex.encode("utf-8")).digest()


def _derive_verification_summary(artifact: Artifact) -> dict:
    validation_results = artifact.validation_results or []
    signature_valid = False
    if isinstance(validation_results, dict):
        active = validation_results.get("activeManifest", {})
        success = active.get("success", []) if isinstance(active, dict) else []
        codes = {item.get("code") for item in success if isinstance(item, dict)}
        signature_valid = "claimSignature.validated" in codes and "assertion.dataHash.match" in codes
    elif isinstance(validation_results, list):
        for result in validation_results:
            if isinstance(result, dict) and result.get("code") in {"claimSignature.validated", "assertion.dataHash.match"}:
                signature_valid = True

    return {
        "signature_valid": bool(signature_valid),
        "content_binding_valid": bool(signature_valid),
        "issuer_trusted": artifact.status == "TRUSTED",
        "blockchain_match": artifact.blockchain_status == "REGISTERED",
    }


async def _save_upload(file: UploadFile) -> tuple[Path, int]:
    extension = _safe_extension(file.filename or "")
    generated_name = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / generated_name
    total_size = 0

    try:
        with destination.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(413, detail=f"File exceeds the maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB.")
                output.write(chunk)
        return destination, total_size
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()


def _serialize_artifact(artifact: Artifact) -> dict:
    return {
        "id": artifact.id,
        "filename": artifact.filename,
        "content_type": artifact.content_type,
        "file_size": artifact.file_size,
        "sha256": artifact.sha256,
        "status": artifact.status,
        "model": artifact.model,
        "model_identifier": artifact.model_identifier,
        "model_type": artifact.model_type,
        "tool": artifact.tool,
        "issuer": artifact.issuer,
        "validation_state": artifact.validation_state,
        "c2pa_found": artifact.c2pa_found,
        "has_provenance_chain": artifact.has_provenance_chain,
        "actions": artifact.actions or [],
        "ingredients": artifact.ingredients or [],
        "validation_results": artifact.validation_results or [],
        "error": artifact.error,
        "blockchain": {
            "status": artifact.blockchain_status,
            "tx_hash": artifact.blockchain_tx_hash,
        },
        "verification": _derive_verification_summary(artifact),
        "created_at": artifact.created_at,
        "updated_at": artifact.updated_at,
    }


async def _persist_uploaded_artifact(
    db: Session,
    *,
    file: UploadFile,
    sha256: str,
    status: str,
    result: dict,
    blockchain_status: str = "NOT_ANCHORED",
    blockchain_tx_hash: str | None = None,
):
    artifact = Artifact(
        filename=Path(file.filename or "upload").name,
        content_type=file.content_type,
        file_size=0,
        sha256=sha256,
        status=status,
        model=result.get("model"),
        model_identifier=result.get("model_identifier"),
        model_type=result.get("model_type"),
        tool=result.get("tool"),
        issuer=result.get("issuer"),
        validation_state=result.get("validation_state"),
        c2pa_found=bool(result.get("c2pa_found")),
        has_provenance_chain=bool(result.get("has_provenance_chain", False)),
        actions=result.get("actions", []),
        ingredients=result.get("ingredients", []),
        validation_results=result.get("validation_results", []),
        error=result.get("error"),
        blockchain_status=blockchain_status,
        blockchain_tx_hash=blockchain_tx_hash,
    )

    db.add(artifact)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Artifact).filter(Artifact.sha256 == sha256).first()
        if existing:
            return existing, True
        raise
    db.refresh(artifact)
    return artifact, False


@router.post("/verify")
async def verify_provenance(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(400, detail="A filename is required.")

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES and not _safe_extension(file.filename or ""):
        raise HTTPException(415, detail="Unsupported content type. Supported images: JPEG, PNG, WEBP, AVIF. Supported video: MP4, WEBM.")

    destination: Path | None = None

    try:
        destination, file_size = await _save_upload(file)
        sha256 = calculate_sha256(str(destination))

        existing = db.query(Artifact).filter(Artifact.sha256 == sha256).first()
        if existing:
            return {"success": True, "duplicate": True, "artifact": _serialize_artifact(existing)}

        result = analyze_provenance(str(destination))
        result["blockchain"] = {"status": "NOT_ANCHORED", "tx_hash": None}

        artifact_id = _artifact_id_from_sha(sha256)
        provenance_hash = compute_provenance_hash(_payload_from_result(result, sha256=sha256))

        blockchain_result = {"status": "NOT_ANCHORED", "tx_hash": None, "blockchain_match": False}
        try:
            chain_entry = get_artifact(artifact_id)
            if chain_entry.get("exists"):
                chain_hash = bytes(chain_entry.get("artifact_hash", b""))
                current_hash = bytes.fromhex(sha256)
                blockchain_match = chain_hash == current_hash
                blockchain_result = {
                    "status": "REGISTERED",
                    "tx_hash": None,
                    "blockchain_match": bool(blockchain_match),
                }
                if blockchain_match:
                    result["status"] = "TRUSTED" if result.get("status") == "TRUSTED" else result.get("status", "TRUSTED")
                elif result.get("status") not in {"TAMPERED", "INCONSISTENT"}:
                    result["status"] = "TAMPERED"
        except Exception:
            blockchain_result = {"status": "BLOCKCHAIN_UNAVAILABLE", "tx_hash": None, "blockchain_match": False}
        if blockchain_result["status"] == "BLOCKCHAIN_UNAVAILABLE":
            result["status"] = result.get("status", "UNVERIFIABLE")

        result["verification"] = {
            "signature_valid": bool(result.get("verification", {}).get("signature_valid")),
            "content_binding_valid": bool(result.get("verification", {}).get("content_binding_valid")),
            "issuer_trusted": bool(result.get("verification", {}).get("issuer_trusted")),
            "blockchain_match": bool(blockchain_result.get("blockchain_match", False)),
        }

        artifact = Artifact(
            filename=Path(file.filename).name,
            content_type=file.content_type,
            file_size=file_size,
            sha256=sha256,
            status=result.get("status", "UNVERIFIABLE"),
            model=result.get("model"),
            model_identifier=result.get("model_identifier"),
            model_type=result.get("model_type"),
            tool=result.get("tool"),
            issuer=result.get("issuer"),
            validation_state=result.get("validation_state"),
            c2pa_found=bool(result.get("c2pa_found")),
            has_provenance_chain=bool(result.get("has_provenance_chain", False)),
            actions=result.get("actions", []),
            ingredients=result.get("ingredients", []),
            validation_results=result.get("validation_results", []),
            error=result.get("error"),
            blockchain_status=blockchain_result.get("status", "NOT_ANCHORED"),
            blockchain_tx_hash=blockchain_result.get("tx_hash"),
        )

        db.add(artifact)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.query(Artifact).filter(Artifact.sha256 == sha256).first()
            if existing:
                return {"success": True, "duplicate": True, "artifact": _serialize_artifact(existing)}
            raise
        db.refresh(artifact)
        return {"success": True, "duplicate": False, "artifact": _serialize_artifact(artifact), "provenance_hash": provenance_hash}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}") from exc
    finally:
        if destination is not None:
            destination.unlink(missing_ok=True)


@router.post("/register")
async def register_artifact_endpoint(
    file: UploadFile = File(...),
    model: str | None = Form(default=None),
    model_identifier: str | None = Form(default=None),
    model_type: str | None = Form(default=None),
    tool: str | None = Form(default=None),
    issuer: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(400, detail="A filename is required.")

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_CONTENT_TYPES and not _safe_extension(file.filename or ""):
        raise HTTPException(415, detail="Unsupported content type. Supported images: JPEG, PNG, WEBP, AVIF. Supported video: MP4, WEBM.")

    destination: Path | None = None

    try:
        destination, file_size = await _save_upload(file)
        sha256 = calculate_sha256(str(destination))

        existing = db.query(Artifact).filter(Artifact.sha256 == sha256).first()
        if existing:
            return {"success": True, "duplicate": True, "artifact": _serialize_artifact(existing)}

        result = analyze_provenance(str(destination))
        manual_values = {
            "model": _normalize_optional(model),
            "model_identifier": _normalize_optional(model_identifier),
            "model_type": _normalize_optional(model_type),
            "tool": _normalize_optional(tool),
            "issuer": _normalize_optional(issuer),
        }

        if not result.get("c2pa_found"):
            for key, value in manual_values.items():
                if value is None:
                    continue
                result[key] = value
            result["status"] = "SELF_ASSERTED"
            result["c2pa_found"] = False
        else:
            for key, value in manual_values.items():
                if value and result.get(key) is None:
                    result[key] = value

        if result.get("status") not in {"TRUSTED", "SELF_ASSERTED", "UNVERIFIABLE", "INCONSISTENT", "TAMPERED"}:
            result["status"] = "SELF_ASSERTED" if not result.get("c2pa_found") else result.get("status", "UNVERIFIABLE")

        provenance_hash = compute_provenance_hash(_payload_from_result(result, sha256=sha256))
        artifact_id = _artifact_id_from_sha(sha256)
        parent_id = bytes(32)
        blockchain_status = "NOT_ANCHORED"
        tx_hash = None

        try:
            if BLOCKCHAIN_ERROR:
                raise RuntimeError(BLOCKCHAIN_ERROR)
            existing_on_chain = get_artifact(artifact_id)
            if existing_on_chain.get("exists"):
                blockchain_status = "REGISTERED"
                tx_hash = None
            else:
                blockchain_response = register_artifact(artifact_id, bytes.fromhex(sha256), bytes.fromhex(provenance_hash), result.get("model") or "Unknown", result.get("issuer") or "Unknown", parent_id)
                blockchain_status = "REGISTERED"
                tx_hash = blockchain_response.get("transaction_hash")
        except Exception as exc:
            blockchain_status = "BLOCKCHAIN_UNAVAILABLE"
            result["error"] = str(exc) if not result.get("error") else result.get("error")

        artifact = Artifact(
            filename=Path(file.filename).name,
            content_type=file.content_type,
            file_size=file_size,
            sha256=sha256,
            status=result.get("status", "UNVERIFIABLE"),
            model=result.get("model"),
            model_identifier=result.get("model_identifier"),
            model_type=result.get("model_type"),
            tool=result.get("tool"),
            issuer=result.get("issuer"),
            validation_state=result.get("validation_state"),
            c2pa_found=bool(result.get("c2pa_found")),
            has_provenance_chain=bool(result.get("has_provenance_chain", False)),
            actions=result.get("actions", []),
            ingredients=result.get("ingredients", []),
            validation_results=result.get("validation_results", []),
            error=result.get("error"),
            blockchain_status=blockchain_status,
            blockchain_tx_hash=tx_hash,
        )

        db.add(artifact)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.query(Artifact).filter(Artifact.sha256 == sha256).first()
            if existing:
                return {"success": True, "duplicate": True, "artifact": _serialize_artifact(existing)}
            raise
        db.refresh(artifact)

        return {
            "success": True,
            "duplicate": False,
            "artifact": _serialize_artifact(artifact),
            "blockchain": {
                "status": blockchain_status,
                "tx_hash": tx_hash,
            },
            "provenance_hash": provenance_hash,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(500, detail=f"{type(exc).__name__}: {exc}") from exc
    finally:
        if destination is not None:
            destination.unlink(missing_ok=True)


@router.get("/history")
def history(
    limit: int = 20,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return list_provenance(limit=limit, status=status, db=db)


@router.get("/{artifact_id}")
def get_provenance(
    artifact_id: int,
    db: Session = Depends(get_db),
):
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if artifact is None:
        raise HTTPException(404, detail="Artifact not found.")
    return {"success": True, "artifact": _serialize_artifact(artifact)}


@router.get("")
def list_provenance(
    limit: int = 20,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    query = db.query(Artifact)
    if status:
        query = query.filter(Artifact.status == status.upper())
    artifacts = query.order_by(Artifact.created_at.desc()).limit(limit).all()
    return {
        "success": True,
        "count": len(artifacts),
        "items": [_serialize_artifact(artifact) for artifact in artifacts],
    }