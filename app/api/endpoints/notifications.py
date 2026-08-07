"""
Notifications API — derives real-time notifications from training jobs,
uploads, and batch predictions. No separate DB table required.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.training_job import TrainingJob, JobStatus

logger = logging.getLogger(__name__)
router = APIRouter()


def _fmt_model(raw: str) -> str:
    """Convert snake_case model name to Title Case."""
    MAP = {
        "stacking_ensemble": "Stacking Ensemble",
        "xgboost":           "XGBoost",
        "lightgbm":          "LightGBM",
        "catboost":          "CatBoost",
        "random_forest":     "Random Forest",
        "logistic_regression": "Logistic Regression",
        "svm":               "SVM",
        "neural_network":    "Neural Network",
        "mlp":               "Neural Network",
        "base_model":        "Base Model",
        "ensemble":          "Ensemble",
        "dataset_generation":"Dataset Preparation",
        "feature_selection": "Feature Selection",
        "full_pipeline":     "Full Pipeline",
    }
    key = (raw or "").lower()
    return MAP.get(key) or raw.replace("_", " ").title()


@router.get("")
async def get_notifications(
    limit: int = Query(default=30, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Return recent notifications derived from:
      - ML training jobs (completed / failed / running)
      - Dataset uploads
      - Batch prediction results in MinIO
    """
    notifications = []
    cutoff = datetime.utcnow() - timedelta(days=14)

    # ── 1. Training jobs ─────────────────────────────────────────────────────
    try:
        jobs = (
            db.query(TrainingJob)
            .filter(
                TrainingJob.user_id == current_user.id,
                TrainingJob.created_at >= cutoff,
            )
            .order_by(TrainingJob.created_at.desc())
            .limit(30)
            .all()
        )

        for job in jobs:
            model = _fmt_model(job.model_name or job.job_type.value)
            ts = (job.completed_at or job.started_at or job.created_at).isoformat()

            if job.status == JobStatus.COMPLETED:
                auc_tag = f" · AUC {job.oof_auc:.2f}" if job.oof_auc else ""
                notifications.append({
                    "id":       f"job_{job.job_id}",
                    "type":     "training_complete",
                    "title":    "Training Complete",
                    "message":  f"{model} finished successfully{auc_tag}",
                    "timestamp": ts,
                    "link":     "/training",
                    "severity": "success",
                })

            elif job.status == JobStatus.FAILED:
                err = (job.error or "Unknown error")[:100]
                notifications.append({
                    "id":       f"job_{job.job_id}",
                    "type":     "training_failed",
                    "title":    "Training Failed",
                    "message":  f"{model} · {err}",
                    "timestamp": ts,
                    "link":     "/training",
                    "severity": "error",
                })

            elif job.status in (JobStatus.RUNNING, JobStatus.PENDING):
                label = "running" if job.status == JobStatus.RUNNING else "queued"
                notifications.append({
                    "id":       f"job_{job.job_id}",
                    "type":     "training_running",
                    "title":    "Training In Progress",
                    "message":  f"{model} is currently {label}…",
                    "timestamp": ts,
                    "link":     "/training",
                    "severity": "info",
                })

    except Exception as exc:
        logger.warning(f"[Notifications] training jobs error: {exc}")

    # ── 2. Recent dataset uploads ─────────────────────────────────────────────
    try:
        from app.models.flexible_schema import FlexibleDatasetWide
        from sqlalchemy import func

        rows = (
            db.query(
                FlexibleDatasetWide.import_batch_id,
                func.count(FlexibleDatasetWide.id).label("record_count"),
                func.max(FlexibleDatasetWide.created_at).label("uploaded_at"),
            )
            .filter(
                FlexibleDatasetWide.uploaded_by == current_user.id,
                FlexibleDatasetWide.created_at >= cutoff,
            )
            .group_by(FlexibleDatasetWide.import_batch_id)
            .order_by(func.max(FlexibleDatasetWide.created_at).desc())
            .limit(10)
            .all()
        )

        for row in rows:
            notifications.append({
                "id":       f"upload_{row.import_batch_id}",
                "type":     "upload",
                "title":    "Dataset Uploaded",
                "message":  f"{row.record_count} patient records added to registry",
                "timestamp": row.uploaded_at.isoformat(),
                "link":     "/data-preparation",
                "severity": "info",
            })

    except Exception as exc:
        logger.warning(f"[Notifications] uploads error: {exc}")

    # ── 3. Batch prediction results from MinIO ────────────────────────────────
    try:
        from app.services.minio_service import get_minio_service
        import json

        minio = get_minio_service()
        bucket = "predictions"

        if minio.client.bucket_exists(bucket):
            all_objs = list(minio.client.list_objects(bucket, recursive=True))
            meta_objs = [o for o in all_objs if o.object_name.endswith("_metadata.json")]
            meta_objs.sort(key=lambda x: x.last_modified, reverse=True)

            for obj in meta_objs[:10]:
                try:
                    raw = minio.client.get_object(bucket, obj.object_name)
                    meta = json.loads(raw.read().decode("utf-8"))
                    ts_str = meta.get("predicted_at", obj.last_modified.isoformat())
                    # Normalize timezone
                    ts_cmp = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
                    if ts_cmp < cutoff:
                        continue
                    n = meta.get("total_predictions", 0)
                    mdl = _fmt_model(meta.get("model_name", "Model"))
                    notifications.append({
                        "id":       f"pred_{str(obj.object_name)[:48]}",
                        "type":     "prediction",
                        "title":    "Batch Prediction Done",
                        "message":  f"{mdl} · {n} patients scored",
                        "timestamp": ts_str,
                        "link":     "/predictions",
                        "severity": "success",
                    })
                except Exception:
                    continue

    except Exception as exc:
        logger.warning(f"[Notifications] predictions error: {exc}")

    # ── Sort newest first, cap at limit ──────────────────────────────────────
    notifications.sort(key=lambda n: n.get("timestamp", ""), reverse=True)
    trimmed = notifications[:limit]

    return {"notifications": trimmed, "total": len(trimmed)}
