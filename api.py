from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from backend import workflow
import logging
import time


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Marketing Campaign API")

LAST_TRIGGER = {}
COOLDOWN_SECONDS = 30


class CampaignRequest(BaseModel):
    user_id: str
    description: str


def run_workflow(user_id: str, description: str):
    logger.info("🚀 Workflow started")

    event = {
        "event_type": "user_interest",
        "event_value": description,
        "timestamp": datetime.utcnow().isoformat()
    }

    workflow.invoke(
        {
            "user_id": user_id,
            "event": event
        },
        config={
            "configurable": {
                "thread_id": user_id
            }
        }
    )

    logger.info("✅ Workflow finished")


@app.post("/trigger-campaign")
def trigger_campaign(
    req: CampaignRequest,
    background_tasks: BackgroundTasks
):
    now = time.time()
    last = LAST_TRIGGER.get(req.user_id, 0)

    if now - last < COOLDOWN_SECONDS:
        logger.warning("⏳ Cooldown active")
        return {"status": "ignored", "message": "Cooldown active"}

    LAST_TRIGGER[req.user_id] = now

    background_tasks.add_task(
        run_workflow,
        req.user_id,
        req.description
    )

    logger.info("📨 Campaign accepted")
    return {
        "status": "accepted",
        "message": "Campaign processing started"
    }
