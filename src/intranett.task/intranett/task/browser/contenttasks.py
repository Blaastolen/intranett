from DateTime import DateTime
from zope.interface import implements, Interface
from zope.component import getUtility, getMultiAdapter
from Products.Five import BrowserView
from Products.CMFPlone import utils
from Products.CMFCore.utils import getToolByName, _checkPermission

from intranett.task.interfaces import ITaskManager
from intranett.task import permissions


class IContentTasksView(Interface):
    """
    Tasks on content view interface
    """


class ContentTasksView(BrowserView):
    """
    Tasks on content browser view
    """
    implements(IContentTasksView)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.plone_view = getMultiAdapter((self.context, self.request),
                                           name=u'plone')
        self.portal_membership = getToolByName(self.context,
                                               'portal_membership')

    @property
    def uniqueItemIndex(self):
        return utils.RealIndexIterator(pos=0)

    def current_date(self):
        return DateTime()

    def add_url(self):
        return "%s/@@add-task" % (self.context.absolute_url())

    def _userFullname(self, user_id):
        user = self.portal_membership.getMemberById(user_id)
        if not user:
            return user_id
        return user.getProperty('fullname') or user_id

    @property
    def has_items(self):
        return len(self.view_items)>0

    @property
    def view_items(self):
        toLocalizedTime = self.plone_view.toLocalizedTime

        results = []
        db = getUtility(ITaskManager)

        for item in db.tasksOnContent(self.context):
            due_date = toLocalizedTime(item.due_date)
            talk = item.messages != ''
            last_activity = toLocalizedTime(item.last_activity)
            created = toLocalizedTime(item.created, 1)
            created_by = self._userFullname(item.created_by)
            assigned_to = self._userFullname(item.assigned_to)
            view_url = "%s/task-view?tid:int=%s" %(self.context.absolute_url(),
                                                   item.id)

            results.append(dict(due_date = due_date,
                                description = item.description,
                                talk = talk,
                                last_activity = last_activity,
                                created = created,
                                created_by = created_by,
                                assigned_to = assigned_to,
                                done = item.done,
                                id = item.id,
                                view_url = view_url))

        return results

    @property
    def can_add_task(self):
        return _checkPermission(permissions.AssignTasksToUsers, self.context)

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
