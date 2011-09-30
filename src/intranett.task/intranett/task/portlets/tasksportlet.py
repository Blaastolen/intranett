from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from zope.interface import implements
from zope.component import getUtility, getMultiAdapter

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName, _checkPermission
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from intranett.task import TaskMessageFactory as _
from intranett.task.interfaces import ITaskManager
from intranett.task import permissions

class ITasksPortlet(IPortletDataProvider):
    """Add task portlet"""


class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(ITasksPortlet)

    title = _(u'Tasks')


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('tasksportlet.pt')

    def tasks(self):
        context = aq_inner(self.context)
        plone_view = getMultiAdapter((context, self.request), name=u'plone')

        user_id = self._getUserId()
        if user_id == 'Anonymous User':
            return []
        else:
            # Getting all tasks on content and sorting on due_date
            db = getUtility(ITaskManager)
            return db.tasksOnContent(context, self._getUserId())

    def _getUserId(self):
        membership = getToolByName(self.context, 'portal_membership', None)
        if membership is None:
            return None

        member = membership.getAuthenticatedMember()
        if not member:
            return None

        memberId = member.getId()
        if memberId is None:
            # Basic users such as the special Anonymous users have no
            # id, but we can use their username instead.
            try:
                memberId = member.getUserName()
            except AttributeError:
                pass

        if not memberId:
            return None

        return memberId

    @property
    def can_add_task(self):
        return _checkPermission(permissions.AssignTasksToUsers, self.context)

    @property
    def is_visible(self):
        user = self._getUserId()
        for task in self.tasks():
            if task.assigned_to == user or task.created_by == user:
                return True
        return False

    @property
    def items(self):
        context = aq_inner(self.context)
        plone_view = getMultiAdapter((context, self.request), name=u'plone')
        results = []
        for task in self.tasks():
            results.append(dict(
                task_id = task.id,
                description = task.description[:75],
                due_date = plone_view.toLocalizedTime(task.due_date),
                url = "%s/task-view?tid:int=%s" %(context.absolute_url(), task.id)
                ))

        return results


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()

