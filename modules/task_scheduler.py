import time
import threading
import queue
import logging
from typing import Callable, Any, Dict, Optional

logger = logging.getLogger("GENESIS_KERNEL")

class Task:
    """
    Represents a discrete unit of work within the Genesis OS.
    """
    def __init__(self, func: Callable, args: tuple = (), kwargs: Dict = None, priority: int = 0, task_id: str = None):
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.priority = priority
        self.task_id = task_id or f"task_{int(time.time() * 1000)}_{threading.get_ident()}"
        self.status = "pending"
        self.result = None
        self.exception = None
        self.created_at = time.time()
        self.estimated_runtime = 0  # Seconds

    def execute(self) -> Any:
        """Executes the function bound to this task."""
        self.status = "running"
        try:
            logger.debug(f"Executing task {self.task_id} with priority {self.priority}")
            self.result = self.func(*self.args, **self.kwargs)
            self.status = "completed"
            return self.result
        except Exception as e:
            self.exception = e
            self.status = "failed"
            logger.error(f"Task {self.task_id} failed: {e}")
            raise

class TaskScheduler:
    """
    The Kernel's Process Management Unit.
    Responsible for queuing, prioritizing, and dispatching tasks to the Executor.
    """
    def __init__(self):
        self.pending_queue = queue.PriorityQueue()
        self.running_tasks = []
        self.completed_tasks = []
        self._lock = threading.Lock()
        self._shutdown = False
        self._worker_threads = []
        
        # Configuration
        self.max_workers = 4  # Default concurrency level
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

    def submit_task(self, func: Callable, *args, priority: int = 0, **kwargs) -> Task:
        """
        Submits a new task to the scheduler.
        Returns immediately; task execution happens asynchronously.
        """
        task = Task(func, args=args, kwargs=kwargs, priority=priority)
        with self._lock:
            self.pending_queue.put((priority, task))
        return task

    def schedule_periodic(self, func: Callable, interval: float, *args, priority: int = 0, **kwargs) -> Task:
        """
        Schedules a task to run repeatedly at fixed intervals.
        """
        def wrapper():
            while not self._shutdown:
                func(*args, **kwargs)
                time.sleep(interval)
        
        task = Task(wrapper, priority=priority)
        return self.submit_task(wrapper, priority=priority)

    def _scheduler_loop(self):
        """Internal loop that dispatches tasks to worker threads."""
        while not self._shutdown:
            try:
                # Get task with highest priority (lowest number)
                priority, task = self.pending_queue.get(timeout=0.1)
                
                with self._lock:
                    self.running_tasks.append(task)
                
                # Dispatch to worker pool
                worker = threading.Thread(target=self._worker, args=(task,))
                worker.start()
                self._worker_threads.append(worker)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Scheduler error: {e}")

    def _worker(self, task: Task):
        """Worker thread function to execute a single task."""
        try:
            task.execute()
        finally:
            with self._lock:
                if task in self.running_tasks:
                    self.running_tasks.remove(task)
                self.completed_tasks.append(task)
            
            # Cleanup worker thread reference
            if self._worker_threads:
                self._worker_threads = [w for w in self._worker_threads if w.is_alive()]

    def get_status(self) -> Dict:
        """Returns current system status."""
        return {
            "pending": self.pending_queue.qsize(),
            "running": len(self.running_tasks),
            "completed": len(self.completed_tasks),
            "active_workers": len(self._worker_threads)
        }

    def shutdown(self):
        """Gracefully shuts down the scheduler."""
        self._shutdown = True
        self.scheduler_thread.join()
        logger.info("Task Scheduler shutdown complete.")