import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import time

logger = logging.getLogger(__name__)

class TradingScheduler:
    def __init__(self, pipeline, interval_minutes: int = 15):
        self.pipeline = pipeline
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        
    def start(self):
        """Start the scheduler loop every N minutes to run pipeline."""
        logger.info(f"Starting scheduler, running pipeline every {self.interval_minutes} minutes.")
        self.scheduler.add_job(
            func=self.pipeline.run,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id='trading_pipeline_job',
            name='Trading Pipeline',
            replace_existing=True
        )
        self.scheduler.start()
        
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.stop()
            
    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping scheduler...")
        self.scheduler.shutdown()
