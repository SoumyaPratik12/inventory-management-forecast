from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
import logging

scheduler = BackgroundScheduler()


def setup_scheduler():
    # Will be used in later days for daily automation
    logging.info("Scheduler initialized")
    return scheduler


def start_scheduler():
    scheduler.start()
    logging.info("Scheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logging.info("Scheduler stopped")
