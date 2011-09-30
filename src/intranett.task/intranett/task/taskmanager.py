import logging

from zope.interface import implements
from Acquisition import aq_base
from BTrees.IOBTree import IOBTree
from BTrees.Length import Length
from OFS.ObjectManager import ObjectManager
from Products.CMFCore.utils import getToolByName

from intranett.task.interfaces import ITaskManager
from intranett.task.task import Task


RELATIONNAME = u'tasks'


logger = logging.getLogger('intranett.task')


class TaskManager(ObjectManager):
    """The default implementation of the task container
    """

    implements(ITaskManager)

    __name__ = 'taskmanager'
    __parent__ = None

    def __init__(self):
        # This is a mapping of task id to task object. The relation to a
        # content item is just a content_uid attribute on each task. This
        # makes most lookup tasks ineffecient as they require a full traversal
        # of all tasks. As long as there's just 50 tasks in total, we don't
        # care though.
        self._tasks = IOBTree()
        # The counter is used to generate new unique task ids
        self._counter = Length()

    def newTask(self, content, description, assigned_to,
                created_by, due_date=''):
        task = Task(description, assigned_to, created_by, due_date)
        self._counter.change(1)
        tid = self._counter()
        self._tasks[tid] = task
        task.id = tid
        task.content_uid = content.UID()
        return task

    def delTask(self, task):
        return self._tasks.pop(int(task.id), None)

    def listTasks(self):
        return self._tasks

    def getTask(self, tid):
        return self._tasks[int(tid)]

    def tasksCreatedBy(self, userid):
        """ list all task created by a user
        """
        return [t for t in self.listTasks().values() if t.created_by == userid]

    def tasksAssignedTo(self, userid):
        """ list all task assigned to a user
        """
        return [t for t in self.listTasks().values() if t.assigned_to == userid]

    def tasksOnContent(self, content, userid=None):
        """ list all task on a content
        """
        uid = getattr(aq_base(content), 'UID', None)
        if not uid:
            return []

        uid = content.UID()
        if userid != None:
            return [t for t in self.tasksAssignedTo(userid)
                      if t.content_uid == uid]
        else:
            return [t for t in self.listTasks().values()
                      if t.content_uid == uid]

    def contentForTask(self, task):
        """ return the content item a given task is defined for
        """
        catalog = getToolByName(self, 'portal_catalog')
        query = {'UID': task.content_uid}
        result = catalog(query)
        content = None
        if len(result) != 1:
            logger.error('something is fuzzy with the relation here. '
                         'task: %s ; %r' % (task.__dict__, result))
            content = None
        else:
            content = result[0].getObject()
        return content

    def _content_rel(self, task):
        # XXX only used in migration
        from plone.app.relations.interfaces import IRelationshipTarget
        target = IRelationshipTarget(task)
        contents = [t for t in target.getSources(relation='tasks')]
        if len(contents) != 1:
            logger.info('something is fuzzy with the relation here. '
                        'task: %s ; %r' % (task.__dict__, contents))
            contents = None
        else:
            contents = contents[0]
        return contents
