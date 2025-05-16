#!/usr/bin/env python
"""
Script to refresh the Planfix data cache periodically.
This can be scheduled via cron to run every hour:

# Example crontab entry (runs every hour)
# 0 * * * * /path/to/your/venv/bin/python /path/to/your/project/refresh_planfix_cache.py >> /path/to/your/project/logs/cache_refresh.log 2>&1
"""

import os
import sys
import logging
import time
from datetime import datetime

# Configure paths and add project to PYTHONPATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'claude_chat.settings')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(BASE_DIR, 'logs', 'cache_refresh.log'))
    ]
)
logger = logging.getLogger("planfix_cache_refresh")

# Ensure logs directory exists
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Initialize Django
import django
django.setup()

# Import required modules
from chat.planfix_service import update_tasks_cache
from chat.planfix_cache_service import planfix_cache

def refresh_cache():
    """Refresh the Planfix data cache"""
    logger.info("Starting Planfix cache refresh")
    
    start_time = time.time()
    
    try:
        # Update the main cache from Planfix API
        logger.info("Updating main tasks cache")
        all_tasks = update_tasks_cache(force=True)
        logger.info(f"Main tasks cache updated, {len(all_tasks)} tasks loaded")
        
        # Refresh derived caches
        logger.info("Refreshing derived caches")
        planfix_cache.refresh_all_caches()
        logger.info("All derived caches refreshed")
        
        # Get updated stats
        stats = planfix_cache.get_stats()
        
        # Log cache stats
        logger.info("Cache refresh complete")
        logger.info(f"Total tasks: {stats.get('total_tasks', 0)}")
        logger.info(f"Active tasks: {stats.get('active_tasks', 0)}")
        logger.info(f"Completed tasks: {stats.get('completed_tasks', 0)}")
        logger.info(f"Overdue tasks: {stats.get('overdue_tasks', 0)}")
        logger.info(f"Due this week: {stats.get('tasks_due_this_week', 0)}")
        logger.info(f"Total projects: {stats.get('total_projects', 0)}")
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        logger.info(f"Cache refresh completed in {elapsed_time:.2f} seconds")
        
        return True
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info(f"Running cache refresh at {datetime.now().isoformat()}")
    success = refresh_cache()
    
    if success:
        logger.info("Cache refresh completed successfully")
        sys.exit(0)
    else:
        logger.error("Cache refresh failed")
        sys.exit(1)