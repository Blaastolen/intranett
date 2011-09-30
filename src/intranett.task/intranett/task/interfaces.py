from zope.interface import Interface, Attribute
from zope.schema import Text


class ITask(Interface):
    """Store information about a task.
    """

    description = Text(
        title=u"Description",
        description=u"Description of the recipe",
        required=True)

    assigned_to = Text(
        title=u"Assigned to",
        description=u"The user selected to accomplish the task",
        required=True)

    created_by = Attribute('the creator of the task')
    created = Attribute('the creation date of the task')
    messages = Attribute('the messages the users exchange')
    due_date = Attribute('due date of the task')

    def addMessage(message, created_by):
        """Simple messaging system"""


class ITaskManager(Interface):
    """The task container
    """
    tasks = Attribute('btree containg the tasks')

    def newTask(content, description, assigned_to, created_by):
        """ create a new task
        """

    def delTask(task_id):
        """ delete a new task
        """

    def listTasks():
        """ list all tasks
        """

    def tasksCreatedBy(user):
        """ list all task created by a user
        """

    def tasksAssignedTo(user):
        """ list all task assigned to a user
        """

    def tasksOnContent(content):
        """ list all task on a content
        """

    def contentForTask(task):
        """return the content item a given task is defined for"""
