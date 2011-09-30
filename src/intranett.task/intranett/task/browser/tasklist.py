from zope.interface import implements, Interface
from zope.component import getUtility, getMultiAdapter
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName

from intranett.task.interfaces import ITaskManager


class ITaskListView(Interface):
    """
    Tasks assigned to a user
    """


class TaskListView(BrowserView):
    """
    Tasks for a user browser view
    """
    implements(ITaskListView)

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.plone_view = getMultiAdapter((self.context, self.request),
                                          name=u'plone')
        self.portal_membership = getToolByName(self.context,
                                               'portal_membership')

    def _userFullname(self, user_id):
        user = self.portal_membership.getMemberById(user_id)
        if not user:
            return user_id
        return user.getProperty('fullname') or user_id

    @property
    def assigned_items(self):
        toLocalizedTime = self.plone_view.toLocalizedTime

        results = []
        db = getUtility(ITaskManager)
        username = self.portal_membership.getAuthenticatedMember().getId()
        for item in db.tasksAssignedTo(username):
            tid = item.id
            due_date = toLocalizedTime(item.due_date)
            talk = False
            if item.messages != []:
                last_message = item.messages[-1]
                if last_message['created_by'] != username:
                    talk = True
            last_activity = toLocalizedTime(item.last_activity)
            created = toLocalizedTime(item.created, 1)
            created_by = self._userFullname(item.created_by)
            target = db.contentForTask(item)
            if target is not None:
                content_url = target.absolute_url()
                view_url = "%s/task-view?tid:int=%s" % (content_url, item.id)
                title = target.Title()
            else:
                view_url = "%s/task-view?tid:int=%s" % (
                    self.context.absolute_url(), item.id)
                content_url=None
                title=None

            done = item.done
            results.append(dict(due_date=due_date,
                                done=done,
                                tid=tid,
                                description=item.description,
                                talk=talk,
                                last_activity=last_activity,
                                created=created,
                                created_by=created_by,
                                view_url=view_url,
                                content_url=content_url,
                                title=title))

        return results

    @property
    def created_items(self):
        toLocalizedTime = self.plone_view.toLocalizedTime

        results = []
        db = getUtility(ITaskManager)
        username = self.portal_membership.getAuthenticatedMember().getId()
        for item in db.tasksCreatedBy(username):
            tid = item.id
            due_date = toLocalizedTime(item.due_date)
            talk = False
            if item.messages != []:
                last_message = item.messages[-1]
                if last_message['created_by'] != username:
                    talk = True
            last_activity = toLocalizedTime(item.last_activity)
            created = toLocalizedTime(item.created, 1)
            assigned_to = self._userFullname(item.assigned_to)
            target = db.contentForTask(item)
            if target is not None:
                content_url = target.absolute_url()
                view_url = "%s/task-view?tid:int=%s" % (content_url, item.id)
                title = target.Title()
            else:
                view_url = None
                content_url=None
                title = None

            done = item.done
            results.append(dict(tid=tid,
                                due_date=due_date,
                                done=done,
                                description=item.description,
                                talk=talk,
                                last_activity=last_activity,
                                created=created,
                                assigned_to=assigned_to,
                                assigned_to_user_id=item.assigned_to,
                                view_url=view_url,
                                content_url=content_url,
                                title=title))

        return results

    @property
    def delete_url(self):
        return "%s/@@delete-tasks" % (self.context.absolute_url())

    @property
    def edit_tasks_url(self):
        if self.is_batch_editing:
            return "%s/@@edit-assigned-tasks" % (self.context.absolute_url())
        else:
            return "%s/@@delete-tasks" % (self.context.absolute_url())

    @property
    def mark_as_done_url(self):
        return "%s/@@mark-as-done" % (self.context.absolute_url())

    @property
    def batch_edit_url(self):
        return "%s?batchedit=1" %self.request.get('ACTUAL_URL')

    @property
    def is_batch_editing(self):
        return 'batchedit' in self.request

    @property
    def listUsers(self):
        pas = getToolByName(self.context, 'acl_users')
        users = []
        for user in pas.getUsers():
            user_id = user.getId()
            user_name = self._userFullname(user_id)
            users.append({'id': user_id,
                          'name': user_name})
        return sorted(users, key=lambda x: x['name'])
