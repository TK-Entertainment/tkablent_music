import asyncio

class TaskStopper():
    def stop(self, task: asyncio.Task):
        if task is not None:
            task.cancel()
            task._timer = None

task_stopper = TaskStopper