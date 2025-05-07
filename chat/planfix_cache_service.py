import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import os
from datetime import datetime, timedelta

from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = Path(settings.BASE_DIR) / 'chat' / 'cache'
TASKS_CACHE_FILE = CACHE_DIR / 'tasks_cache.json'
LAST_UPDATE_FILE = CACHE_DIR / 'last_update.txt'

# Additional cache files for structured data
ACTIVE_TASKS_CACHE = CACHE_DIR / 'active_tasks.json'
COMPLETED_TASKS_CACHE = CACHE_DIR / 'completed_tasks.json'
OVERDUE_TASKS_CACHE = CACHE_DIR / 'overdue_tasks.json'
PROJECTS_CACHE = CACHE_DIR / 'projects.json'
USERS_CACHE = CACHE_DIR / 'users.json'
STATS_CACHE = CACHE_DIR / 'stats.json'

# Task status IDs
COMPLETED_STATUS_ID = 3  # Using known completion status ID from Planfix

class PlanfixCacheService:
    """Enhanced service for Planfix data caching and retrieval"""
    
    def __init__(self):
        """Initialize cache service and ensure cache directory exists"""
        self._ensure_cache_directory()
    
    def _ensure_cache_directory(self):
        """Ensure cache directory and files exist"""
        if not CACHE_DIR.exists():
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created cache directory: {CACHE_DIR}")
    
    def is_cache_valid(self, max_age_minutes: int = 60) -> bool:
        """Check if cache is valid (not too old)"""
        if not LAST_UPDATE_FILE.exists():
            return False
        
        try:
            with open(LAST_UPDATE_FILE, 'r') as f:
                last_update_str = f.read().strip()
                last_update = float(last_update_str)
                # Check if cache is older than max_age_minutes
                return (time.time() - last_update) < (max_age_minutes * 60)
        except (ValueError, IOError) as e:
            logger.error(f"Error checking cache validity: {e}")
            return False
    
    def get_cache_age_minutes(self) -> Optional[float]:
        """Get cache age in minutes"""
        if not LAST_UPDATE_FILE.exists():
            return None
        
        try:
            with open(LAST_UPDATE_FILE, 'r') as f:
                last_update_str = f.read().strip()
                last_update = float(last_update_str)
                return (time.time() - last_update) / 60
        except (ValueError, IOError) as e:
            logger.error(f"Error getting cache age: {e}")
            return None
    
    def update_cache_timestamp(self):
        """Update the last cache update timestamp"""
        try:
            with open(LAST_UPDATE_FILE, 'w') as f:
                f.write(str(time.time()))
            logger.info("Updated cache timestamp")
        except IOError as e:
            logger.error(f"Error updating cache timestamp: {e}")
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks from cache"""
        if not TASKS_CACHE_FILE.exists():
            logger.warning("Tasks cache file does not exist")
            return []
        
        try:
            with open(TASKS_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading tasks cache: {e}")
            return []
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get active tasks from cache or generate if needed"""
        if ACTIVE_TASKS_CACHE.exists():
            try:
                with open(ACTIVE_TASKS_CACHE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass  # Fall back to regenerating
        
        # Generate active tasks cache
        return self._generate_active_tasks_cache()
    
    def _generate_active_tasks_cache(self) -> List[Dict[str, Any]]:
        """Generate active tasks cache from all tasks"""
        all_tasks = self.get_all_tasks()
        active_tasks = [
            task for task in all_tasks 
            if not self._is_task_completed(task)
        ]
        
        try:
            with open(ACTIVE_TASKS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(active_tasks, f, ensure_ascii=False, indent=2)
            logger.info(f"Generated active tasks cache with {len(active_tasks)} tasks")
        except IOError as e:
            logger.error(f"Error writing active tasks cache: {e}")
        
        return active_tasks
    
    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """Get completed tasks from cache or generate if needed"""
        if COMPLETED_TASKS_CACHE.exists():
            try:
                with open(COMPLETED_TASKS_CACHE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass  # Fall back to regenerating
        
        # Generate completed tasks cache
        return self._generate_completed_tasks_cache()
    
    def _generate_completed_tasks_cache(self) -> List[Dict[str, Any]]:
        """Generate completed tasks cache from all tasks"""
        all_tasks = self.get_all_tasks()
        completed_tasks = [
            task for task in all_tasks 
            if self._is_task_completed(task)
        ]
        
        try:
            with open(COMPLETED_TASKS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(completed_tasks, f, ensure_ascii=False, indent=2)
            logger.info(f"Generated completed tasks cache with {len(completed_tasks)} tasks")
        except IOError as e:
            logger.error(f"Error writing completed tasks cache: {e}")
        
        return completed_tasks
    
    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """Get overdue tasks from cache or generate if needed"""
        if OVERDUE_TASKS_CACHE.exists():
            try:
                with open(OVERDUE_TASKS_CACHE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass  # Fall back to regenerating
        
        # Generate overdue tasks cache
        return self._generate_overdue_tasks_cache()
    
    def _generate_overdue_tasks_cache(self) -> List[Dict[str, Any]]:
        """Generate overdue tasks cache from active tasks"""
        active_tasks = self.get_active_tasks()
        today = datetime.now().date().isoformat()
        
        overdue_tasks = []
        for task in active_tasks:
            # Check for endDateTime in various formats
            end_date = None
            if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
                if 'date' in task['endDateTime']:
                    end_date = task['endDateTime']['date']
                elif 'dateTo' in task['endDateTime']:
                    end_date = task['endDateTime']['dateTo']
            elif task.get('endDateTime') and isinstance(task['endDateTime'], str):
                end_date = task['endDateTime']
            elif task.get('dateEnd') and isinstance(task['dateEnd'], str):
                end_date = task['dateEnd']
            
            # If we found a valid end date and it's in the past
            if end_date and end_date < today:
                overdue_tasks.append(task)
        
        try:
            with open(OVERDUE_TASKS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(overdue_tasks, f, ensure_ascii=False, indent=2)
            logger.info(f"Generated overdue tasks cache with {len(overdue_tasks)} tasks")
        except IOError as e:
            logger.error(f"Error writing overdue tasks cache: {e}")
        
        return overdue_tasks
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get projects from cache or extract from tasks"""
        if PROJECTS_CACHE.exists():
            try:
                with open(PROJECTS_CACHE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass  # Fall back to regenerating
        
        # Generate projects cache from tasks
        return self._generate_projects_cache()
    
    def _generate_projects_cache(self) -> List[Dict[str, Any]]:
        """Generate projects cache from all tasks"""
        all_tasks = self.get_all_tasks()
        
        # Extract unique projects
        projects_map = {}
        for task in all_tasks:
            if task.get('project') and task['project'].get('id'):
                project_id = str(task['project']['id'])
                
                if project_id not in projects_map:
                    # Extract relevant project info
                    project_info = {
                        'id': task['project']['id'],
                        'name': task['project'].get('name', f"Project {project_id}"),
                        'task_count': 1,
                        'active_tasks': 0,
                        'completed_tasks': 0,
                        'overdue_tasks': 0
                    }
                    
                    # Count task status
                    if self._is_task_completed(task):
                        project_info['completed_tasks'] = 1
                    else:
                        project_info['active_tasks'] = 1
                        
                        # Check if overdue
                        today = datetime.now().date().isoformat()
                        end_date = None
                        if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
                            if 'date' in task['endDateTime']:
                                end_date = task['endDateTime']['date']
                            elif 'dateTo' in task['endDateTime']:
                                end_date = task['endDateTime']['dateTo']
                        elif task.get('endDateTime') and isinstance(task['endDateTime'], str):
                            end_date = task['endDateTime']
                        elif task.get('dateEnd') and isinstance(task['dateEnd'], str):
                            end_date = task['dateEnd']
                        
                        if end_date and end_date < today:
                            project_info['overdue_tasks'] = 1
                    
                    projects_map[project_id] = project_info
                else:
                    # Update existing project info
                    projects_map[project_id]['task_count'] += 1
                    
                    if self._is_task_completed(task):
                        projects_map[project_id]['completed_tasks'] += 1
                    else:
                        projects_map[project_id]['active_tasks'] += 1
                        
                        # Check if overdue
                        today = datetime.now().date().isoformat()
                        end_date = None
                        if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
                            if 'date' in task['endDateTime']:
                                end_date = task['endDateTime']['date']
                            elif 'dateTo' in task['endDateTime']:
                                end_date = task['endDateTime']['dateTo']
                        elif task.get('endDateTime') and isinstance(task['endDateTime'], str):
                            end_date = task['endDateTime']
                        elif task.get('dateEnd') and isinstance(task['dateEnd'], str):
                            end_date = task['dateEnd']
                        
                        if end_date and end_date < today:
                            projects_map[project_id]['overdue_tasks'] += 1
        
        # Convert map to list
        projects = list(projects_map.values())
        
        try:
            with open(PROJECTS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(projects, f, ensure_ascii=False, indent=2)
            logger.info(f"Generated projects cache with {len(projects)} projects")
        except IOError as e:
            logger.error(f"Error writing projects cache: {e}")
        
        return projects
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Get users from cache or extract from tasks"""
        if USERS_CACHE.exists():
            try:
                with open(USERS_CACHE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass  # Fall back to regenerating
        
        # Generate users cache from tasks
        return self._generate_users_cache()
    
    def _generate_users_cache(self) -> List[Dict[str, Any]]:
        """Generate users cache from all tasks"""
        all_tasks = self.get_all_tasks()
        
        # Extract unique users
        users_map = {}
        
        # Process assignees
        for task in all_tasks:
            # Process assignees
            if task.get('assignees'):
                if isinstance(task['assignees'], list):
                    assignees = task['assignees']
                elif isinstance(task['assignees'], dict) and task['assignees'].get('users'):
                    assignees = task['assignees']['users']
                else:
                    assignees = []
                
                for assignee in assignees:
                    if assignee.get('id'):
                        user_id = str(assignee['id'])
                        
                        if user_id not in users_map:
                            users_map[user_id] = {
                                'id': assignee['id'],
                                'name': assignee.get('name', f"User {user_id}"),
                                'email': assignee.get('email', ''),
                                'assigned_tasks': 1,
                                'assigned_active': 0,
                                'assigned_completed': 0,
                                'assigned_overdue': 0,
                                'created_tasks': 0,
                                'projects': set()
                            }
                        else:
                            users_map[user_id]['assigned_tasks'] += 1
                        
                        # Track status
                        if self._is_task_completed(task):
                            users_map[user_id]['assigned_completed'] += 1
                        else:
                            users_map[user_id]['assigned_active'] += 1
                            
                            # Check if overdue
                            today = datetime.now().date().isoformat()
                            end_date = None
                            if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
                                if 'date' in task['endDateTime']:
                                    end_date = task['endDateTime']['date']
                                elif 'dateTo' in task['endDateTime']:
                                    end_date = task['endDateTime']['dateTo']
                            elif task.get('endDateTime') and isinstance(task['endDateTime'], str):
                                end_date = task['endDateTime']
                            elif task.get('dateEnd') and isinstance(task['dateEnd'], str):
                                end_date = task['dateEnd']
                            
                            if end_date and end_date < today:
                                users_map[user_id]['assigned_overdue'] += 1
                        
                        # Track project
                        if task.get('project') and task['project'].get('id'):
                            users_map[user_id]['projects'].add(str(task['project']['id']))
            
            # Process assigner/creator
            if task.get('assigner') and task['assigner'].get('id'):
                assigner = task['assigner']
                user_id = str(assigner['id'])
                
                if user_id not in users_map:
                    users_map[user_id] = {
                        'id': assigner['id'],
                        'name': assigner.get('name', f"User {user_id}"),
                        'email': assigner.get('email', ''),
                        'assigned_tasks': 0,
                        'assigned_active': 0,
                        'assigned_completed': 0,
                        'assigned_overdue': 0,
                        'created_tasks': 1,
                        'projects': set()
                    }
                else:
                    users_map[user_id]['created_tasks'] += 1
                
                # Track project
                if task.get('project') and task['project'].get('id'):
                    users_map[user_id]['projects'].add(str(task['project']['id']))
        
        # Convert sets to lists for JSON serialization
        for user_id, user_data in users_map.items():
            user_data['projects'] = list(user_data['projects'])
        
        # Convert map to list
        users = list(users_map.values())
        
        try:
            with open(USERS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            logger.info(f"Generated users cache with {len(users)} users")
        except IOError as e:
            logger.error(f"Error writing users cache: {e}")
        
        return users
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from cache or generate if needed"""
        if STATS_CACHE.exists():
            try:
                with open(STATS_CACHE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass  # Fall back to regenerating
        
        # Generate stats cache
        return self._generate_stats_cache()
    
    def _generate_stats_cache(self) -> Dict[str, Any]:
        """Generate statistics cache from all data"""
        all_tasks = self.get_all_tasks()
        active_tasks = self.get_active_tasks()
        completed_tasks = self.get_completed_tasks()
        overdue_tasks = self.get_overdue_tasks()
        projects = self.get_projects()
        
        # Calculate deadlines this week
        today = datetime.now().date()
        week_end = (today + timedelta(days=7)).isoformat()
        
        tasks_due_this_week = []
        for task in active_tasks:
            end_date = None
            if task.get('endDateTime') and isinstance(task['endDateTime'], dict):
                if 'date' in task['endDateTime']:
                    end_date = task['endDateTime']['date']
                elif 'dateTo' in task['endDateTime']:
                    end_date = task['endDateTime']['dateTo']
            elif task.get('endDateTime') and isinstance(task['endDateTime'], str):
                end_date = task['endDateTime']
            elif task.get('dateEnd') and isinstance(task['dateEnd'], str):
                end_date = task['dateEnd']
            
            if end_date and end_date <= week_end:
                tasks_due_this_week.append(task)
        
        # Calculate tasks by status
        status_counts = {}
        for task in all_tasks:
            status = "Unknown"
            if task.get('status'):
                if task['status'].get('name'):
                    status = task['status']['name']
                elif task['status'].get('id'):
                    status = f"Status ID {task['status']['id']}"
            
            if status not in status_counts:
                status_counts[status] = 1
            else:
                status_counts[status] += 1
        
        # Calculate completion rate
        completion_rate = 0
        if all_tasks:
            completion_rate = (len(completed_tasks) / len(all_tasks)) * 100
        
        # Calculate average tasks per project
        avg_tasks_per_project = 0
        if projects:
            avg_tasks_per_project = len(all_tasks) / len(projects)
        
        # Compile stats
        stats = {
            'total_tasks': len(all_tasks),
            'active_tasks': len(active_tasks),
            'completed_tasks': len(completed_tasks),
            'overdue_tasks': len(overdue_tasks),
            'tasks_due_this_week': len(tasks_due_this_week),
            'completion_rate': round(completion_rate, 2),
            'total_projects': len(projects),
            'avg_tasks_per_project': round(avg_tasks_per_project, 2),
            'status_counts': status_counts,
            'cache_updated_at': datetime.now().isoformat(),
            'cache_age_minutes': self.get_cache_age_minutes() or 0
        }
        
        try:
            with open(STATS_CACHE, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            logger.info("Generated stats cache")
        except IOError as e:
            logger.error(f"Error writing stats cache: {e}")
        
        return stats
    
    def get_task_by_id(self, task_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """Get a specific task by ID"""
        task_id_str = str(task_id)
        
        all_tasks = self.get_all_tasks()
        for task in all_tasks:
            if str(task.get('id', '')) == task_id_str:
                return task
        
        return None
    
    def refresh_all_caches(self):
        """Refresh all derived caches from the main tasks cache"""
        logger.info("Refreshing all derived caches")
        
        self._generate_active_tasks_cache()
        self._generate_completed_tasks_cache()
        self._generate_overdue_tasks_cache()
        self._generate_projects_cache()
        self._generate_users_cache()
        self._generate_stats_cache()
        
        logger.info("All caches refreshed successfully")
    
    def _is_task_completed(self, task: Dict[str, Any]) -> bool:
        """Determine if a task is completed based on its status"""
        # Check by status ID first
        if task.get('status') and task['status'].get('id'):
            if task['status']['id'] == COMPLETED_STATUS_ID:
                return True
        
        # Check by status name if ID check fails
        if task.get('status') and task['status'].get('name'):
            status_name = task['status']['name'].lower()
            return ('завершен' in status_name or 
                    'completed' in status_name or 
                    'выполнен' in status_name)
        
        return False
    
    def search_tasks(self, query: str, include_completed: bool = False) -> List[Dict[str, Any]]:
        """Search tasks by name, description, status, etc."""
        query = query.lower()
        tasks_to_search = self.get_all_tasks() if include_completed else self.get_active_tasks()
        
        results = []
        for task in tasks_to_search:
            # Search in task name
            if task.get('name') and query in task['name'].lower():
                results.append(task)
                continue
            
            # Search in description
            if task.get('description') and query in task['description'].lower():
                results.append(task)
                continue
            
            # Search in status
            if task.get('status') and task['status'].get('name') and query in task['status']['name'].lower():
                results.append(task)
                continue
            
            # Search in project name
            if task.get('project') and task['project'].get('name') and query in task['project']['name'].lower():
                results.append(task)
                continue
        
        return results
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search projects by name"""
        query = query.lower()
        projects = self.get_projects()
        
        return [
            project for project in projects
            if project.get('name') and query in project['name'].lower()
        ]
    
    def search_users(self, query: str) -> List[Dict[str, Any]]:
        """Search users by name or email"""
        query = query.lower()
        users = self.get_users()
        
        results = []
        for user in users:
            # Search in name
            if user.get('name') and query in user['name'].lower():
                results.append(user)
                continue
            
            # Search in email
            if user.get('email') and query in user['email'].lower():
                results.append(user)
                continue
        
        return results

# Singleton instance
planfix_cache = PlanfixCacheService()