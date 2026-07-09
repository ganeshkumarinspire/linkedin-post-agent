"""
Scheduler: runs the post agent on Tue/Wed/Thu at 08:00 Paris time (Europe/Paris).
Run this file directly — it blocks and fires the job on schedule.
"""

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from agent import run_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PARIS_TZ = ZoneInfo("Europe/Paris")


def job():
    logger.info("Scheduler fired — starting agent run")
    try:
        run_agent()
    except Exception as e:
        logger.error(f"Agent run failed: {e}", exc_info=True)


def start():
    scheduler = BlockingScheduler(timezone=PARIS_TZ)

    # Tue=2, Wed=3, Thu=4 in APScheduler's cron day_of_week (0=Mon)
    trigger = CronTrigger(
        day_of_week="tue,wed,thu",
        hour=8,
        minute=0,
        timezone=PARIS_TZ,
    )
    scheduler.add_job(job, trigger, id="linkedin_post", name="LinkedIn Agile Post")
    logger.info("Scheduler started — posting Tue/Wed/Thu at 08:00 Paris time")
    scheduler.start()


if __name__ == "__main__":
    start()
