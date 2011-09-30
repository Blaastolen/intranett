from DateTime import DateTime
from zope.interface import implements, Interface
from zope.component import getUtility, getMultiAdapter
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName, _checkPermission
from Products.CMFPlone import utils

from intranett.task.interfaces import ITaskManager
from intranett.task import permissions


class ITaskView(Interface):
    """
    Task view interface
    """


class TaskView(BrowserView):
    """
    Task browser view
    """
    implements(ITaskView)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.plone_view = getMultiAdapter((self.context, self.request),
                                           name=u'plone')
        self.portal_membership = getToolByName(self.context,
                                               'portal_membership')

        task_id = self.request.get('tid')
        db = getUtility(ITaskManager)
        self.task = db.listTasks().get(task_id)

        # Check if we come from the task_view. In that case, store the URL
        # for later redirect, if the task gets deleted.
        came_from = self.request.SESSION.get('intranett.task.came_from', {})
        if 'task-list' in self.request.get('HTTP_REFERER', ''):
            # Set the came_from to the task_view
            came_from[self.taskid] = self.request.get('HTTP_REFERER')
            self.request.SESSION['intrnaett.task.came_from'] = came_from

    def _userFullname(self, user_id):
        user = self.portal_membership.getMemberById(user_id)
        if not user:
            return user_id
        return user.getProperty('fullname') or user_id

    @property
    def description(self):
        return self.task.description

    def contentItem(self):
        db = getUtility(ITaskManager)
        return db.contentForTask(self.task)

    @property
    def due_date(self):
        return self.plone_view.toLocalizedTime(self.task.due_date)

    @property
    def created_by(self):
        return self._userFullname(self.task.created_by)

    @property
    def assigned_to(self):
        return self._userFullname(self.task.assigned_to)

    @property
    def created(self):
        return self.plone_view.toLocalizedTime(self.task.created)

    @property
    def messages(self):
        results = []
        for message in self.task.messages:
            results.append(dict(
                date = self.plone_view.toLocalizedTime(message['date']),
                created_by = message['created_by'],
                text = message['message']))

        return results

    @property
    def done(self):
        return self.task.done

    def current_date(self):
        return DateTime()

    @property
    def action_url(self):
        return "%s/@@add-task-message" %self.context.absolute_url()

    @property
    def delete_action_url(self):
        return "%s/@@delete-task" %self.context.absolute_url()

    @property
    def close_action_url(self):
        return "%s/@@mark-as-done" %self.context.absolute_url()

    @property
    def form_url(self):
        return "%s/@@edit-task" %self.context.absolute_url()

    @property
    def taskid(self):
        return self.request.get('tid')

    @property
    def uniqueItemIndex(self):
        return utils.RealIndexIterator(pos=0)

    @property
    def listUsers(self):
        self.pas = getToolByName(self.context, 'acl_users')
        users = []
        for user in self.pas.getUsers():
            user_id = user.getId()
            user_name = self._userFullname(user_id)
            users.append({'id': user_id,
                          'name': user_name})
        return sorted(users, key=lambda x: x['name'])

    @property
    def can_add_task(self):
        return _checkPermission(permissions.AssignTasksToUsers, self.context)

    @property
    def can_delete_task(self):
        return _checkPermission(permissions.AssignTasksToUsers, self.context)

    @property
    def can_close_task(self):
        user_id = self.portal_membership.getAuthenticatedMember().getId()
        return  user_id == self.task.assigned_to and not self.task.done
