from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.artifact import Artifact
from app.services.hash_service import calculate_sha256
from app.services.provenance_engine import analyze_provenance


router = APIRouter(
    prefix="/api/provenance",
    tags=["Provenance"],
)


BASE_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = (
    BASE_DIR
    / os.getenv("UPLOAD_DIR", "uploads")
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


MAX_FILE_SIZE = (
    int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    * 1024
    * 1024
)


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

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".avif",
        ".mp4",
        ".webm",
    }

    if extension not in allowed_extensions:
        return ""

    return extension


async def _save_upload(file: UploadFile) -> tuple[Path, int]:
    """
    Stream upload to disk while enforcing size limits.
    """

    extension = _safe_extension(
        file.filename or ""
    )

    generated_name = (
        f"{uuid.uuid4().hex}{extension}"
    )

    destination = UPLOAD_DIR / generated_name

    total_size = 0

    try:
        with destination.open("wb") as output:

            while True:
                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "File exceeds the maximum "
                            f"allowed size of "
                            f"{MAX_FILE_SIZE // (1024 * 1024)} MB."
                        ),
                    )

                output.write(chunk)

        return destination, total_size

    except Exception:
        destination.unlink(
            missing_ok=True
        )
        raise

    finally:
        await file.close()


def _serialize_artifact(
    artifact: Artifact,
) -> dict:
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
        "has_provenance_chain": (
            artifact.has_provenance_chain
        ),
        "actions": artifact.actions or [],
        "ingredients": artifact.ingredients or [],
        "validation_results": (
            artifact.validation_results or []
        ),
        "error": artifact.error,
        "blockchain": {
            "status": artifact.blockchain_status,
            "tx_hash": artifact.blockchain_tx_hash,
        },
        "created_at": artifact.created_at,
        "updated_at": artifact.updated_at,
    }


@router.post("/verify")
async def verify_provenance(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Verify AI provenance for an uploaded asset.

    Pipeline:

    Upload
      -> SHA-256
      -> C2PA validation
      -> provenance classification
      -> MySQL persistence
      -> JSON response
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="A filename is required.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported content type. "
                "Supported images: JPEG, PNG, WEBP, AVIF. "
                "Supported video: MP4, WEBM."
            ),
        )

    destination: Path | None = None

    try:
        destination, file_size = await _save_upload(
            file
        )

        sha256 = calculate_sha256(
            str(destination)
        )

        # Fast deduplication by cryptographic fingerprint.
        existing = (
            db.query(Artifact)
            .filter(
                Artifact.sha256 == sha256
            )
            .first()
        )

        if existing:
            destination.unlink(
                missing_ok=True
            )

            return {
                "success": True,
                "duplicate": True,
                "artifact": _serialize_artifact(
                    existing
                ),
            }

        # Core C2PA provenance analysis.
        result = analyze_provenance(
            str(destination)
        )

        artifact = Artifact(
            filename=Path(
                file.filename
            ).name,

            content_type=file.content_type,

            file_size=file_size,

            sha256=sha256,

            status=result.get(
                "status",
                "UNVERIFIABLE",
            ),

            model=result.get("model"),

            model_identifier=result.get(
                "model_identifier"
            ),

            model_type=result.get(
                "model_type"
            ),

            tool=result.get("tool"),

            issuer=result.get("issuer"),

            validation_state=result.get(
                "validation_state"
            ),

            c2pa_found=bool(
                result.get("c2pa_found")
            ),

            has_provenance_chain=bool(
                result.get(
                    "has_provenance_chain"
                )
            ),

            actions=result.get(
                "actions",
                [],
            ),

            ingredients=result.get(
                "ingredients",
                [],
            ),

            validation_results=result.get(
                "validation_results",
                [],
            ),

            error=result.get("error"),

            blockchain_status="NOT_ANCHORED",
        )

        db.add(artifact)

        try:
            db.commit()

        except IntegrityError:
            db.rollback()

            existing = (
                db.query(Artifact)
                .filter(
                    Artifact.sha256 == sha256
                )
                .first()
            )

            if existing:
                return {
                    "success": True,
                    "duplicate": True,
                    "artifact": _serialize_artifact(
                        existing
                    ),
                }

            raise

        db.refresh(artifact)

        return {
            "success": True,
            "duplicate": False,
            "artifact": _serialize_artifact(
                artifact
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        ) from exc

    finally:
        # We only need the asset temporarily for verification.
        if destination is not None:
            destination.unlink(
                missing_ok=True
            )


@router.get("/{artifact_id}")
def get_provenance(
    artifact_id: int,
    db: Session = Depends(get_db),
):
    artifact = (
        db.query(Artifact)
        .filter(
            Artifact.id == artifact_id
        )
        .first()
    )

    if artifact is None:
        raise HTTPException(
            status_code=404,
            detail="Artifact not found.",
        )

    return {
        "success": True,
        "artifact": _serialize_artifact(
            artifact
        ),
    }


@router.get("")
def list_provenance(
    limit: int = 20,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Query verification history.

    Optional:
        ?limit=20
        ?status=TRUSTED
        ?status=UNVERIFIABLE
    """

    limit = max(
        1,
        min(limit, 100),
    )

    query = db.query(Artifact)

    if status:
        query = query.filter(
            Artifact.status == status.upper()
        )

    artifacts = (
        query
        .order_by(
            Artifact.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    return {
        "success": True,
        "count": len(artifacts),
        "items": [
            _serialize_artifact(
                artifact
            )
            for artifact in artifacts
        ],
    }