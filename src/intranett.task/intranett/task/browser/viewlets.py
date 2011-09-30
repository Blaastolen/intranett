from zope.component import getUtility
from zope.publisher.browser import BrowserView

from Acquisition import aq_inner
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName
from plone.memoize.instance import memoize
from plone.app.layout.viewlets import common

from intranett.task.interfaces import ITaskManager


class TaskInfoViewlet(common.ViewletBase):

    render = ViewPageTemplateFile("task_info_viewlet.pt")

    @memoize
    def task_count(self):
        # If we try this on Add Views, they get Intids, and then they get
        # pickled and that fails, and then intids are all messed up and try
        # to load things that doesn't exist. This happens when we have views
        # on views, which happens with add views. I don't know if we ever have
        # views on skin templates, but that would likely also fail.
        if isinstance(self.context, BrowserView):
            return 0
        context = aq_inner(self.context)
        user_id = self._getUserId()
        if user_id == 'Anonymous User':
            return 0
        else:
            # Getting all tasks on content
            db = getUtility(ITaskManager)
            tasks = db.tasksOnContent(context, self._getUserId())
            return len([x for x in tasks if not x.done])

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
