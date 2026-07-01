import uuid

from sqlalchemy.orm import Session

from app.db.models import Activity, User


def log_activity(
    db: Session,
    user: User | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | str | None = None,
    metadata: dict | None = None,
) -> Activity:
    row = Activity(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        metadata_json=metadata,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
