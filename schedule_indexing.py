import schedule
import time
from index_messages import index_messages
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_indexing.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def job():
    """Wrapper function for the indexing job with logging."""
    try:
        logger.info("Starting weekly indexing job")
        index_messages()
        logger.info("Completed weekly indexing job")
    except Exception as e:
        logger.error(f"Error in indexing job: {str(e)}", exc_info=True)

def main():
    """Main function to schedule and run the indexing job."""
    # Schedule the job to run every Monday at 00:00
    schedule.every().monday.at("00:00").do(job)
    
    logger.info("Scheduler started. Will run indexing every Monday at midnight.")
    
    # Run the job immediately once
    job()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute instead of every second

if __name__ == "__main__":
    main() 