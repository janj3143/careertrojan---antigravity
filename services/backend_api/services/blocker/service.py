
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from services.backend_api.db.models import ApplicationBlocker, BlockerImprovementPlan
import uuid
from datetime import datetime

class BlockerService:
    def __init__(self, db: Session):
        self.db = db

    def create_blocker(self, **kwargs) -> str:
        blocker = ApplicationBlocker(**kwargs)
        if not blocker.blocker_id:
            blocker.blocker_id = str(uuid.uuid4())
        self.db.add(blocker)
        self.db.commit()
        self.db.refresh(blocker)
        return blocker.blocker_id

    def get_user_blockers(self, user_id: int, status: str = "active") -> List[ApplicationBlocker]:
        return self.db.query(ApplicationBlocker).filter(
            ApplicationBlocker.user_id == user_id,
            ApplicationBlocker.status == status
        ).order_by(ApplicationBlocker.criticality_score.desc()).all()

    def create_improvement_plan(self, **kwargs) -> str:
        plan = BlockerImprovementPlan(**kwargs)
        if not plan.plan_id:
            plan.plan_id = str(uuid.uuid4())
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan.plan_id

    def get_improvement_plans(self, blocker_id: str) -> List[BlockerImprovementPlan]:
        return self.db.query(BlockerImprovementPlan).filter(
            BlockerImprovementPlan.blocker_id == blocker_id
        ).order_by(BlockerImprovementPlan.priority_rank).all()
