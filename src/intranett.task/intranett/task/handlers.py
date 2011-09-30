from zope.component import queryUtility

from intranett.task.interfaces import ITaskManager


def remove_tasks_on_content(obj, event):
    db = queryUtility(ITaskManager)
    if db is not None:
        tasks = db.tasksOnContent(obj)
        for task in tasks:
            db.delTask(task)
