"""A report of recently modified cinemas and films
"""
from DateTime import DateTime
from zope.component import getUtility, getMultiAdapter
from Products.Five.browser import BrowserView
from Products.statusmessages.interfaces import IStatusMessage

from intranett.task import TaskMessageFactory as _
from intranett.task.interfaces import ITaskManager


class AddTaskAction(BrowserView):
    """View for adding a new task on a content
    """

    def __call__(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                        name=u"plone_portal_state")

        content = self.context
        description = self.request.get('description')
        assigned_to = self.request.get('assigned_to')
        created_by = portal_state.member().getId()
        due_date = DateTime(self.request.get('due_date'))

        # Store task
        db = getUtility(ITaskManager)
        db.newTask(content, description, assigned_to, created_by, due_date)

        # Issue a status message
        confirm = _(u"Task added.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')

        return self.request.response.redirect(self.request['HTTP_REFERER'])


class EditTaskAction(BrowserView):
    """View for edit a task
    """

    def __call__(self):
        task_id = self.request.get('task_id')
        description = self.request.get('description')
        due_date = DateTime(self.request.get('due_date'))
        assigned_to = self.request.get('assigned_to')

        # Edit task
        db = getUtility(ITaskManager)
        task = db.getTask(task_id)
        task.edit(description, due_date, assigned_to)

        # Issue a status message
        confirm = _(u"Changes saved.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')

        return self.request.response.redirect(self.request['HTTP_REFERER'])


class DeleteTasksAction(BrowserView):
    """View for deleting tasks
    """

    def __call__(self):
        task_ids = self.request.get('task_ids', [])

        # Delete tasks
        db = getUtility(ITaskManager)
        for task_id in task_ids:
            task = db.getTask(task_id)
            db.delTask(task)

        # Issue a status message
        confirm = _(u"Tasks deleted.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')

        return self.request.response.redirect(self.request['HTTP_REFERER'])


class DeleteTaskAction(BrowserView):
    """View for deleting one task
    """

    def __call__(self):
        content = self.context
        task_id = self.request.get('task_id')

        # Delete task
        db = getUtility(ITaskManager)
        task = db.getTask(task_id)
        db.delTask(task)

        # Issue a status message
        confirm = _(u"Task deleted.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')

        # See if we have a came_from for this task.
        came_from = self.request.SESSION.get('intranett.task.came_from', {})
        url = came_from.get(task_id)
        if not url:
            url = content.absolute_url()+'/@@content-tasks'
        return self.request.response.redirect(url)


class AddTaskMessageAction(BrowserView):
    """View for adding a new task message
    """

    def __call__(self):
        portal_state = getMultiAdapter((self.context, self.request),
                                        name=u"plone_portal_state")

        task_id = self.request.get('task_id')
        message = self.request.get('message')
        created_by = portal_state.member().getId()

        # Get task from id and add the message
        db = getUtility(ITaskManager)
        task = db.listTasks().get(task_id)
        task.addMessage(message, created_by)

        # Issue a status message
        confirm = _(u"Message sent.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')
        targetpage = "%s/task-view?tid:int=%s" % (
            self.context.absolute_url(), task_id)
        return self.request.response.redirect(targetpage)


class MarkAsDone(BrowserView):
    """
    """

    def __call__(self):
        task_ids = self.request.get('task_ids', [])

        # Mark as done
        db = getUtility(ITaskManager)
        for task_id in task_ids:
            task = db.getTask(task_id)
            task.markAsDone()

        # Issue a status message
        confirm = _(u"The tasks have been marked as done.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')

        return self.request.response.redirect(self.request['HTTP_REFERER'])


class EditAssignedTasksAction(BrowserView):
    """View for batch editing assigned tasks
    """

    def __call__(self):
        tasks = self.request.get('tasks', [])
        db = getUtility(ITaskManager)

        for edit_data in tasks:
            assigned_to = edit_data.get('assigned_to')
            old_assigned = edit_data.get('old_assigned')
            task_id = edit_data.get('id')

            if assigned_to == old_assigned:
                continue

            # Edit tasks
            task = db.getTask(task_id)
            task.assigned_to = assigned_to

        # Issue a status message
        confirm = _(u"Changes saved.")
        IStatusMessage(self.request).addStatusMessage(confirm, type='info')

        return self.request.response.redirect(self.request['HTTP_REFERER'])
