from persistent import Persistent
from zope.app.container.contained import Contained
from zope.interface import implements

from DateTime import DateTime

from intranett.task.interfaces import ITask


class Task(Persistent, Contained):
    """simple task implementation
    """
    meta_type = 'Task'
    implements(ITask)

    def __init__(self, description='', assigned_to='',
                 created_by='', due_date=None):
        """
        """
        self.description = description
        self.assigned_to = assigned_to
        self.created_by = created_by
        self.created = DateTime()
        self.due_date = due_date
        self.last_activity = DateTime()
        self.done = False
        self.messages = []
        self.id = None
        self.content_uid = None

    def markAsDone(self):
        """
        """
        self.done = True

    def markAsNotDone(self):
        """
        """
        self.done = False

    def addMessage(self, message, created_by):
        """
        """
        msg ={'date': DateTime(),
              'created_by': created_by,
              'message': message.strip()}
        self.messages.append(msg)
        self.last_activity = DateTime()

    def edit(self, description, due_date, assigned_to):
        """
        """
        self.description = description
        self.due_date = due_date
        self.assigned_to = assigned_to
