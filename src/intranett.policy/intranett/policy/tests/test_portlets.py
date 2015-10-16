from DateTime import DateTime
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletRenderer
from plone.portlets.interfaces import IPortletType
from Products.CMFCore.utils import getToolByName
import transaction
from zope.component import getUtility, getMultiAdapter

from intranett.policy.browser.portlets import eventhighlight
from intranett.policy.browser.portlets import newshighlight
from intranett.policy.browser.portlets import projectroominfo
from intranett.policy.browser.sources import DocumentSourceBinder
from intranett.policy.tests.base import get_browser
from intranett.policy.tests.base import IntranettFunctionalTestCase
from intranett.policy.tests.base import IntranettTestCase


class TestPortlets(IntranettTestCase):

    def test_navigation_portlet(self):
        portal = self.layer['portal']
        leftcolumn = '++contextportlets++plone.leftcolumn'
        mapping = portal.restrictedTraverse(leftcolumn)
        self.assert_(u'navigation' in mapping.keys())
        nav = mapping[u'navigation']
        self.assertEquals(nav.topLevel, 1)
        self.assertEquals(nav.currentFolderOnly, True)


class TestNewsHighlightPortlet(IntranettTestCase):

    def renderer(self, context=None, request=None, view=None, manager=None,
                 assignment=None):
        context = context or self.layer['portal']
        request = request or context.REQUEST
        view = view or context.restrictedTraverse('@@plone')
        manager = manager or getUtility(
            IPortletManager, name='plone.rightcolumn', context=context)
        assignment = assignment or newshighlight.Assignment()
        return getMultiAdapter((context, request, view, manager, assignment),
                               IPortletRenderer)

    def test_news_items(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        wt = getToolByName(portal, 'portal_workflow')

        # No news items
        assignment = newshighlight.Assignment(
            portletTitle='News',
            source='last')
        r = self.renderer(assignment=assignment)
        r = r.__of__(portal)
        r.update()
        self.assertEqual(r.item(), None)
        output = r.render()
        self.assertTrue('News' not in output)

        yesterday = DateTime() - 1
        day_before_yesterday = yesterday - 1

        # One news item.
        portal.invokeFactory('News Item', 'wedding',
                             title='A wedding')
        portal['wedding'].setEffectiveDate(day_before_yesterday)
        wt.doActionFor(portal['wedding'], 'publish')

        # We want the one before last, which does not exist.
        assignment = newshighlight.Assignment(
            portletTitle="News",
            source='before-last')
        r = self.renderer(assignment=assignment)
        r = r.__of__(portal)
        r.update()
        self.assertEqual(r.item(), None)
        output = r.render()
        self.assertTrue('News' not in output)

        # Two news items.
        portal.invokeFactory('News Item', 'funeral',
                             title='A funeral')
        portal['funeral'].setEffectiveDate(yesterday)
        wt.doActionFor(portal['funeral'], 'publish')

        # Show the last
        assignment = newshighlight.Assignment(
            portletTitle='News',
            source='last')
        r = self.renderer(assignment=assignment)
        r = r.__of__(portal)
        r.update()
        self.assertEqual(r.item().Title, 'A funeral')
        output = r.render()
        self.assertTrue('News' in output)
        self.assertTrue('A funeral' in output)

        # Show the one before last.
        assignment = newshighlight.Assignment(
            portletTitle="News",
            source='before-last')
        r = self.renderer(assignment=assignment)
        r = r.__of__(portal)
        r.update()
        self.assertEqual(r.item().Title, 'A wedding')
        output = r.render()
        self.assertTrue('News' in output)
        self.assertTrue('A wedding' in output)

    def DISABLED_test_invoke_add_view(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portlet = getUtility(IPortletType,
            name='intranett.policy.portlets.NewsHighlight')
        mapping = portal.restrictedTraverse(
            '++contextportlets++plone.rightcolumn')
        addview = mapping.restrictedTraverse('+/' + portlet.addview)
        initial = len(mapping)
        addview.createAndAdd(
            data={'portletTitle': 'News Highlight', 'source': 'last'})
        self.assertEquals(len(mapping), 1+initial)
        assignment_types = set(assignment.__class__ for assignment in
            mapping.values())
        self.assertIn(newshighlight.Assignment, assignment_types)


class TestEventHighlightPortlet(IntranettTestCase):

    def renderer(self, context=None, request=None, view=None, manager=None,
                 assignment=None):
        context = context or self.layer['portal']
        request = request or context.REQUEST
        view = view or context.restrictedTraverse('@@plone')
        manager = manager or getUtility(
            IPortletManager, name='plone.rightcolumn', context=context)
        assignment = assignment or eventhighlight.Assignment()
        return getMultiAdapter((context, request, view, manager, assignment),
                               IPortletRenderer)

    def test_upcoming_event(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        wt = getToolByName(portal, 'portal_workflow')

        # No event
        assignment = eventhighlight.Assignment(
            portletTitle="Event")
        r = self.renderer(assignment=assignment)
        r = r.__of__(portal)
        r.update()
        self.assertEqual(r.item(), None)
        output = r.render()
        self.assertTrue('Event' not in output)

        # Add two events, show the last.
        tomorrow = DateTime() + 1
        in_a_month = tomorrow + 30
        portal.invokeFactory('Event', 'wedding',
                             title='A wedding',
                             startDate=tomorrow, endDate=tomorrow + 1)
        wt.doActionFor(portal['wedding'], 'publish')
        portal.invokeFactory('Event', 'funeral',
                             title='A funeral',
                             startDate=in_a_month, endDate=in_a_month + 1)
        wt.doActionFor(portal['funeral'], 'publish')

        assignment = eventhighlight.Assignment(
            portletTitle="Event")
        r = self.renderer(assignment=assignment)
        r = r.__of__(portal)
        r.update()
        self.assertEqual(r.item().Title, 'A wedding')
        output = r.render()
        self.assertTrue('Event' in output)
        self.assertTrue('A wedding' in output)

    def DISABLED_test_invoke_add_view(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portlet = getUtility(IPortletType,
            name='intranett.policy.portlets.EventHighlight')
        mapping = portal.restrictedTraverse(
            '++contextportlets++plone.rightcolumn')
        addview = mapping.restrictedTraverse('+/' + portlet.addview)
        initial = len(mapping)
        addview.createAndAdd(
            data={'portletTitle': 'Event Highlight'})
        self.assertEquals(len(mapping), 1+initial)
        assignment_types = set(assignment.__class__ for assignment in
            mapping.values())
        self.assertIn(eventhighlight.Assignment, assignment_types)




class TestProjectRoomStatePortlet(IntranettTestCase):

    def renderer(self, context=None, request=None, view=None, manager=None,
                 assignment=None):
        context = context or self.layer['portal']
        request = request or context.REQUEST
        view = view or context.restrictedTraverse('@@plone')
        manager = manager or getUtility(
            IPortletManager, name='plone.rightcolumn', context=context)
        return getMultiAdapter((context, request, view, manager, assignment),
                               IPortletRenderer)

    def test_private_space(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        projectroom_id = portal.invokeFactory('ProjectRoom', 'projectroom',
                             title='First Space')
        projectroom = portal[projectroom_id]

        assignment = projectroominfo.Assignment()
        r = self.renderer(context=projectroom, assignment=assignment)
        r = r.__of__(projectroom)
        r.update()

        self.assertEqual(r.state, 'private')
        self.assertEqual(r.participants, [{
            'name': 'test_user_1_',
            'title': 'test_user_1_',
            'url': 'http://nohost/plone/users/test_user_1_'}])

    def test_public_space(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        wt = getToolByName(portal, 'portal_workflow')
        projectroom_id = portal.invokeFactory('ProjectRoom', 'projectroom',
                             title='First Space')
        projectroom = portal[projectroom_id]
        wt.doActionFor(projectroom, "publish")

        assignment = projectroominfo.Assignment()
        r = self.renderer(context=projectroom, assignment=assignment)
        r = r.__of__(projectroom)
        r.update()

        self.assertEqual(r.state, 'published')
        self.assertEqual(r.participants, [{
            'name': 'test_user_1_',
            'title': 'test_user_1_',
            'url': 'http://nohost/plone/users/test_user_1_'}])

    def test_member_fullname_shown(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        wt = getToolByName(portal, 'portal_workflow')
        projectroom_id = portal.invokeFactory('ProjectRoom', 'projectroom',
                             title='First Space')
        projectroom = portal[projectroom_id]
        projectroom.members = (TEST_USER_ID, )
        wt.doActionFor(projectroom, "publish")

        assignment = projectroominfo.Assignment()
        r = self.renderer(context=projectroom, assignment=assignment)
        r = r.__of__(projectroom)
        r.update()

        self.assertEqual(r.state, 'published')
        self.assertEqual(r.participants, [{
            'name': 'test_user_1_',
            'title': 'test_user_1_',
            'url': 'http://nohost/plone/users/test_user_1_'}])

    def test_outside_projectroom_no_portlet_rendered(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])

        assignment = projectroominfo.Assignment()
        r = self.renderer(context=portal, assignment=assignment)
        r = r.__of__(portal)
        r.update()

        self.assertFalse(r.available)
        output = r.render()
        self.assertEqual(output.strip(), "")
