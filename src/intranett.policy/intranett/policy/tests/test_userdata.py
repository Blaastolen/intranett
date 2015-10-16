# -*- coding:utf-8 -*-
import os
import transaction

from Acquisition import aq_get
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from zope.component import queryUtility
from intranett.policy.utils import getMembersFolder
from intranett.policy.utils import getMembersFolderId

from plone.app.testing import setRoles
from intranett.policy.tests.base import get_browser
from intranett.policy.tests.base import IntranettTestCase
from intranett.policy.tests.base import IntranettFunctionalTestCase
from intranett.policy.tests.utils import make_file_upload

TEST_IMAGES = os.path.join(os.path.dirname(__file__), 'images')


class TestMemberTools(IntranettTestCase):

    def test_membership_tool_registered(self):
        # Check we can get the tool by name
        from ..tools import MembershipTool
        portal = self.layer['portal']
        tool = getToolByName(portal, 'portal_membership')
        self.failUnless(isinstance(tool, MembershipTool))

    def test_memberdata_tool_registered(self):
        # Check we can get the tool by name
        from ..tools import MemberDataTool
        portal = self.layer['portal']
        tool = getToolByName(portal, 'portal_memberdata')
        self.failUnless(isinstance(tool, MemberDataTool))
        from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
        self.failUnless(isinstance(tool.thumbnails, BTreeFolder2))


class TestGetMember(IntranettTestCase):

    def test_get_by_id(self):
        portal = self.layer['portal']
        tool = getToolByName(portal, 'portal_membership')
        self.assertNotEqual(tool.getMemberById('test_user_1_'), None)

    def test_get_by_id_returns_None(self):
        portal = self.layer['portal']
        tool = getToolByName(portal, 'portal_membership')
        self.assertEqual(tool.getMemberById('test-user'), None)

    def test_get_by_login(self):
        portal = self.layer['portal']
        tool = getToolByName(portal, 'portal_membership')
        self.assertNotEqual(tool.getMemberByLogin('test-user'), None)

    def test_get_by_login_returns_None(self):
        portal = self.layer['portal']
        tool = getToolByName(portal, 'portal_membership')
        self.assertEqual(tool.getMemberByLogin('test_user_1_'), None)


class TestUserdataSchema(IntranettTestCase):

    def test_no_homepage(self):
        from ..userdataschema import ICustomUserDataSchema
        self.assert_('home_page' not in ICustomUserDataSchema.names())

    def test_custom_schema(self):
        from ..userdataschema import ICustomUserDataSchema
        from plone.app.users.userdataschema import IUserDataSchemaProvider
        util = queryUtility(IUserDataSchemaProvider)
        schema = util.getSchema()
        self.assertEquals(schema, ICustomUserDataSchema)

    def test_memberdatafields(self):
        from plone.app.users.userdataschema import IUserDataSchemaProvider
        util = queryUtility(IUserDataSchemaProvider)
        schema = util.getSchema()
        self.failUnless('position' in schema)
        self.failUnless('department' in schema)
        self.failUnless('phone' in schema)
        self.failUnless('mobile' in schema)

    def test_memberinfo(self):
        from DateTime import DateTime
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'phone': '12345',
                                    'mobile': '67890',
                                    'position': 'Øngønør',
                                    'department': 'it',
                                    'email': 'info@jarn.com',
                                    'birth_date': DateTime('23/11/2008'),
                                    'description': "<p>Kjære Python!</p>"})

        info = mt.getMemberInfo()
        self.assertEquals(info['phone'], '12345')
        self.assertEquals(info['mobile'], '67890')
        self.assertEquals(info['position'], 'Øngønør')
        self.assertEquals(info['department'], 'it')
        self.assertEquals(info['email'], 'info@jarn.com')
        self.assertEquals(info['birth_date'], DateTime('23/11/2008'))
        self.assertEquals(info['description'], "<p>Kjære Python!</p>")

    def test_userid_in_memberinfo(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        info = mt.getMemberInfo()
        self.assertEquals(info['userid'], TEST_USER_ID)

    def test_bad_memberinfo(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        info = mt.getMemberInfo(memberId='foo')
        self.failUnless(info is None)

    def test_safe_transform_description(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'description': """
            <script> document.load(something) </script>
            <object> some object </object>
            <span>This is ok</span>
        """})
        info = mt.getMemberInfo()
        self.assertEquals(info['description'].strip(), "<span>This is ok</span>")

    def test_personal_information_widget(self):
        from zope.component import getMultiAdapter
        from plone.app.form.widgets.wysiwygwidget import WYSIWYGWidget
        portal = self.layer['portal']
        request = self.layer['request']
        view = getMultiAdapter((portal, request), name='personal-information')
        self.assertEquals(view.form_fields['description'].custom_widget,
                          WYSIWYGWidget)

    def test_user_information_widget(self):
        from zope.component import getMultiAdapter
        from plone.app.form.widgets.wysiwygwidget import WYSIWYGWidget
        portal = self.layer['portal']
        request = self.layer['request']
        view = getMultiAdapter((portal, request), name='user-information')
        self.assertEquals(view.form_fields['description'].custom_widget,
                        WYSIWYGWidget)

    def test_userpanel(self):
        from ..userdataschema import ICustomUserDataSchema
        portal = self.layer['portal']
        panel = ICustomUserDataSchema(portal)

        self.assertEquals(panel.fullname, u'')
        panel.fullname = u'Geir Bœkholly'
        self.assertEquals(panel.fullname, u'Geir Bœkholly')

        self.assertEquals(panel.position, u'')
        panel.position = u'Øngønør'
        self.assertEquals(panel.position, u'Øngønør')

        self.assertEquals(panel.department, u'')
        panel.department = u'IT Tønsberg'
        self.assertEquals(panel.department, u'IT Tønsberg')

        self.assertEquals(panel.location, u'')
        panel.location = u'Tønsberg'
        self.assertEquals(panel.location, u'Tønsberg')

        self.assertEquals(panel.phone, '')
        panel.phone = '+47 55533'
        self.assertEquals(panel.phone, '+47 55533')

        self.assertEquals(panel.mobile, '')
        panel.mobile = '+47 55533'
        self.assertEquals(panel.mobile, '+47 55533')


class TestUserPortraits(IntranettTestCase):

    def test_set_portraits(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        mdt = getToolByName(portal, 'portal_memberdata')
        path = os.path.join(TEST_IMAGES, 'test.jpg')
        image_jpg = make_file_upload(path, 'image/jpeg', 'myportrait.jpg')
        mt.changeMemberPortrait(image_jpg)
        self.failUnless(TEST_USER_ID in mdt.portraits)
        self.failUnless(TEST_USER_ID in mdt.thumbnails)

        portrait_thumb = mt.getPersonalPortrait()
        from ..tools import PORTRAIT_SIZE, PORTRAIT_THUMBNAIL_SIZE
        self.assertEquals(portrait_thumb.width, PORTRAIT_THUMBNAIL_SIZE[0])
        self.assertEquals(portrait_thumb.height, PORTRAIT_THUMBNAIL_SIZE[1])
        portrait = mt.getPersonalPortrait(thumbnail=False)
        self.assertEquals(portrait.width, PORTRAIT_SIZE[0])
        self.assertEquals(portrait.height, PORTRAIT_SIZE[1])

    def test_change_portraits(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        path = os.path.join(TEST_IMAGES, 'test.jpg')
        image_jpg = make_file_upload(path, 'image/jpeg', 'myportrait.jpg')
        mt.changeMemberPortrait(image_jpg)
        portrait = mt.getPersonalPortrait(thumbnail=False)
        old_portrait_size = portrait.get_size()
        portrait = mt.getPersonalPortrait(thumbnail=True)
        old_thumbnail_size = portrait.get_size()

        # Now change the portraits
        path = os.path.join(TEST_IMAGES, 'test.gif')
        image_gif = make_file_upload(path, 'image/gif', 'myportrait.gif')
        mt.changeMemberPortrait(image_gif)
        portrait = mt.getPersonalPortrait(thumbnail=False)
        self.assertNotEqual(old_portrait_size, portrait.get_size())
        portrait = mt.getPersonalPortrait(thumbnail=True)
        self.assertNotEqual(old_thumbnail_size, portrait.get_size())

    def test_delete_portraits(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        mdt = getToolByName(portal, 'portal_memberdata')
        path = os.path.join(TEST_IMAGES, 'test.jpg')
        image_jpg = make_file_upload(path, 'image/jpeg', 'myportrait.jpg')
        mt.changeMemberPortrait(image_jpg)
        # Now delete the portraits
        mt.deletePersonalPortrait()
        self.failIf(TEST_USER_ID in mdt.portraits)
        self.failIf(TEST_USER_ID in mdt.thumbnails)

    def test_funky_ids(self):
        # Well, let's admit we really do this for the coverage.
        # There is this retarded check in changeMemberPortrait
        # that we copied and have to cover.
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        mt.getPersonalPortrait(id='')
        path = os.path.join(TEST_IMAGES, 'test.gif')
        image_gif = make_file_upload(path, 'image/gif', 'myportrait.gif')
        mt.changeMemberPortrait(image_gif, id='')

    def test_change_portrait_recatalogs(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        path = os.path.join(TEST_IMAGES, 'test.jpg')
        image_jpg = make_file_upload(path, 'image/jpeg', 'myportrait.jpg')
        catalog = getToolByName(portal, 'portal_catalog')
        before = catalog.getCounter()
        mt.changeMemberPortrait(image_jpg)
        self.assertEqual(catalog.getCounter(), before + 1)

    def test_delete_portrait_recatalogs(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        path = os.path.join(TEST_IMAGES, 'test.jpg')
        image_jpg = make_file_upload(path, 'image/jpeg', 'myportrait.jpg')
        catalog = getToolByName(portal, 'portal_catalog')
        mt.changeMemberPortrait(image_jpg)
        before = catalog.getCounter()
        mt.deletePersonalPortrait()
        self.assertEqual(catalog.getCounter(), before + 1)

    def test_delete_member_purges_portrait(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        mdt = getToolByName(portal, 'portal_memberdata')
        path = os.path.join(TEST_IMAGES, 'test.jpg')
        image_jpg = make_file_upload(path, 'image/jpeg', 'myportrait.jpg')
        mt.changeMemberPortrait(image_jpg)
        # Now delete the member
        setRoles(portal, TEST_USER_ID, ['Manager'])
        mt.deleteMembers([TEST_USER_ID])
        self.failIf(TEST_USER_ID in mdt.portraits)
        self.failIf(TEST_USER_ID in mdt.thumbnails)


class TestImageCropping(IntranettTestCase):

    def test_image_crop(self):
        from intranett.policy.tools import crop_and_scale_image
        from PIL import Image as PILImage
        path = os.path.join(TEST_IMAGES, 'idiot.jpg')
        old_image = open(path)
        new_image_data, mimetype = crop_and_scale_image(old_image)
        new_image = PILImage.open(new_image_data)
        self.assertEqual(new_image.size, (100, 100))


class TestUserSearch(IntranettTestCase):

    def test_type(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        self.assertEqual(member.meta_type, 'MemberData')
        self.assertEqual(member.portal_type, 'MemberData')
        self.assertEqual(member.Type(), 'MemberData')

    def test_title(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'fullname': 'John Døe'})
        self.assertEqual(member.Title(), 'John Døe')

    def test_description(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'position': '', 'department': ''})
        self.assertEqual(member.Description(), '')
        member.setMemberProperties({'position': '', 'department': 'Øl'})
        self.assertEqual(member.Description(), 'Øl')
        member.setMemberProperties({'position': 'Tørst', 'department': ''})
        self.assertEqual(member.Description(), 'Tørst')
        member.setMemberProperties({'position': 'Tørst', 'department': 'Øl'})
        self.assertEqual(member.Description(), 'Tørst, Øl')

    def test_update_member_and_search(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'fullname': 'John Døe',
                                    'phone': '12345',
                                    'mobile': '67890',
                                    'position': 'Øngønør',
                                    'department': 'Tøst',
                                    'location': 'Tønsberg',
                                    'email': 'info@jarn.com',
                                    'description': '<p>Kjære Python!</p>'})
        catalog = getToolByName(portal, 'portal_catalog')
        results = catalog.searchResults(Title='Døe')
        self.assertEquals(len(results), 1)
        john_brain = results[0]
        self.assertEquals(john_brain.getPath(), '/plone/users/test_user_1_')
        self.assertEquals(john_brain.Title, 'John Døe')
        self.assertEquals(john_brain.Description, 'Øngønør, Tøst')
        results = catalog.searchResults(SearchableText='12345')
        self.assertEquals(len(results), 1)
        john_brain = results[0]
        self.assertEquals(john_brain.getPath(), '/plone/users/test_user_1_')
        results = catalog.searchResults(SearchableText='67890')
        self.assertEquals(len(results), 1)
        john_brain = results[0]
        self.assertEquals(john_brain.getPath(), '/plone/users/test_user_1_')
        results = catalog.searchResults(SearchableText='Øngønør')
        self.assertEquals(len(results), 1)
        john_brain = results[0]
        self.assertEquals(john_brain.getPath(), '/plone/users/test_user_1_')
        results = catalog.searchResults(SearchableText='Tøst')
        self.assertEquals(len(results), 1)
        john_brain = results[0]
        self.assertEquals(john_brain.getPath(), '/plone/users/test_user_1_')
        results = catalog.searchResults(SearchableText='Tønsberg')
        self.assertEquals(len(results), 1)
        john_brain = results[0]
        self.assertEquals(john_brain.getPath(), '/plone/users/test_user_1_')
        results = catalog.searchResults(SearchableText='info@jarn.com')
        self.assertEquals(len(results), 1)
        john_brain = results[0]
        self.assertEquals(john_brain.getPath(), '/plone/users/test_user_1_')
        results = catalog.searchResults(SearchableText='Kjære')
        self.assertEquals(len(results), 1)
        john_brain = results[0]
        self.assertEquals(john_brain.getPath(), '/plone/users/test_user_1_')

    def test_safe_transform_searchable_text(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'description': '<p>Kjære Python!</p>'})
        self.assertEquals(member.SearchableText().strip(), 'Kjære Python!')

    def test_brain_getObject(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'fullname': 'John Døe'})
        catalog = getToolByName(portal, 'portal_catalog')
        results = catalog.searchResults(Title='Døe')
        self.assertEquals(len(results), 1)
        brain = results[0]
        obj = brain.getObject()
        self.assertEqual(obj.Title(), 'John Døe')
        self.assertEqual(obj.getPhysicalPath(),
            ('', 'plone', 'users', 'test_user_1_'))

    def test_refreshCatalog_does_not_lose_memberdata(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'fullname': 'John Døe'})
        catalog = getToolByName(portal, 'portal_catalog')
        results = catalog.searchResults(Title='Døe')
        self.assertEquals(len(results), 1)
        catalog.refreshCatalog()
        results = catalog.searchResults(Title='Døe')
        self.assertEquals(len(results), 1)


class TestFunctionalUserSearch(IntranettFunctionalTestCase):

    def test_ttw_editing(self):
        browser = get_browser(self.layer['app'])
        browser.handleErrors = False
        portal = self.layer['portal']
        browser.open(portal.absolute_url() + '/@@personal-information')
        browser.getControl(name='form.fullname').value = 'John Døe'
        browser.getControl(name='form.email').value = 'test@example.com'
        browser.getControl(name='form.description').value = '<p>Kjære Python!</p>'
        browser.getControl(name='form.location').value = 'Tønsberg'
        browser.getControl(name='form.position').value = 'Øngønør'
        browser.getControl(name='form.department').value = 'Tåst'
        browser.getControl(name='form.actions.save').click()
        self.assert_(browser.url.endswith('@@personal-information'))

    def test_ttw_search(self):
        browser = get_browser(self.layer['app'])
        browser.handleErrors = False
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'fullname': 'Bob Døe',
                                    'phone': '12345',
                                    'mobile': '67890',
                                    'position': 'Øngønør',
                                    'department': 'Tøst',
                                    'location': 'Tønsberg',
                                    'email': 'info@jarn.com'})
        transaction.commit()
        browser.open(portal.absolute_url())
        browser.getControl(name='SearchableText').value = 'Bob'
        # bbb the searchform is called name=searchform in our jbot version of the template
        # not sure why that is not picked up here
        browser.getForm(id='searchGadget_form').submit()
        self.failUnless('Bob Døe' in browser.contents)
        self.failUnless('Øngønør' in browser.contents)
        self.failUnless('Tøst' in browser.contents)
        self.failUnless('Øngønør, Tøst' in browser.contents)


class TestDashboard(IntranettTestCase):

    def test_default_dashboard(self):
        from plone.portlets.constants import USER_CATEGORY
        from plone.portlets.interfaces import IPortletManager

        portal = self.layer['portal']
        addUser = aq_get(portal, 'acl_users').userFolderAddUser
        addUser('member', 'secret', ['Member'], [])

        prefix = 'plone.dashboard'
        for i in range(1, 5):
            name = prefix + str(i)
            column = queryUtility(IPortletManager, name=name)
            category = column.get(USER_CATEGORY, None)
            manager = category.get('member', {})
            self.assert_(manager == {}, 'Found unexpected portlets in '
                         'dashboard column %s: %s' % (i, manager.keys()))


class TestMemberData(IntranettTestCase):

    def _make_one(self, request):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        member = mt.getAuthenticatedMember()
        member.setMemberProperties({'fullname': 'John Døe',
                                    'position': 'Øngønør',
                                    'department': 'Tøst'})
        return member

    def test_getAuthenticatedMember(self):
        request = self.layer['request']
        member = self._make_one(request)
        chain = member.aq_chain
        self.assertEqual(chain[0].__class__.__name__, 'MemberData')
        self.assertEqual(chain[1].__class__.__name__, 'PloneUser')
        self.assertEqual(chain[2].__class__.__name__, 'PluggableAuthService')
        self.assertEqual(chain[3].__class__.__name__, 'PloneSite')

    def test_getMemberById(self):
        request = self.layer['request']
        member = self._make_one(request)
        chain = member.aq_chain
        self.assertEqual(chain[0].__class__.__name__, 'MemberData')
        self.assertEqual(chain[1].__class__.__name__, 'PloneUser')
        self.assertEqual(chain[2].__class__.__name__, 'PluggableAuthService')
        self.assertEqual(chain[3].__class__.__name__, 'PloneSite')

    def test_getUser(self):
        request = self.layer['request']
        member = self._make_one(request)
        user = member.getUser()
        chain = user.aq_chain
        self.assertEqual(chain[0].__class__.__name__, 'PloneUser')
        self.assertEqual(chain[1].__class__.__name__, 'PluggableAuthService')
        self.assertEqual(chain[2].__class__.__name__, 'PloneSite')

    def test_getPhysicalPath(self):
        request = self.layer['request']
        member = self._make_one(request)
        self.assertEqual(member.getPhysicalPath(),
            ('', 'plone', 'users', 'test_user_1_'))

    def test_notifyModified(self):
        request = self.layer['request']
        portal = self.layer['portal']
        member = self._make_one(request)
        catalog = getToolByName(portal, 'portal_catalog')
        self.assertEqual(len(catalog(Title='Døe')), 1)
        catalog.unindexObject(member)
        self.assertEqual(len(catalog(Title='Døe')), 0)
        member.notifyModified()
        self.assertEqual(len(catalog(Title='Døe')), 1)

    def test_types(self):
        request = self.layer['request']
        member = self._make_one(request)
        self.assertEqual(member.Type(), 'MemberData')
        self.assertEqual(member.portal_type, 'MemberData')
        self.assertEqual(member.meta_type, 'MemberData')

    def test_title(self):
        request = self.layer['request']
        member = self._make_one(request)
        self.assertEqual(member.Title(), 'John Døe')

    def test_description(self):
        request = self.layer['request']
        member = self._make_one(request)
        self.assertEqual(member.Description(), 'Øngønør, Tøst')

    def test_unicode_getId(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        mt.addMember(u'måm', 'secret', ['Member'], [])
        member = mt.getMemberById(u'måm')
        self.assertEqual(member.getId(), 'måm')
        self.failIf(isinstance(member.getId(), unicode))
        self.assertEqual(member.getPhysicalPath(),
            ('', 'plone', 'users', 'måm'))

    def test_unicode_getMemberId(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        mt.addMember(u'måm', 'secret', ['Member'], [])
        member = mt.getMemberById(u'måm')
        self.assertEqual(member.getMemberId(), 'måm')
        self.failIf(isinstance(member.getMemberId(), unicode))
        self.assertEqual(member.getPhysicalPath(),
            ('', 'plone', 'users', 'måm'))

    def test_unicode_id(self):
        portal = self.layer['portal']
        mt = getToolByName(portal, 'portal_membership')
        mt.addMember(u'måm', 'secret', ['Member'], [])
        member = mt.getMemberById(u'måm')
        self.assertEqual(member.id, 'måm')
        self.failIf(isinstance(member.id, unicode))

    def test_delete_member_uncatalogs(self):
        request = self.layer['request']
        portal = self.layer['portal']
        member = self._make_one(request)
        member # pyflakes
        mt = getToolByName(portal, 'portal_membership')
        catalog = getToolByName(portal, 'portal_catalog')
        self.assertEqual(len(catalog(dict(Title='Døe'))), 1)
        # Now delete the member
        setRoles(portal, TEST_USER_ID, ['Manager'])
        mt.deleteMembers([TEST_USER_ID])
        self.assertEqual(len(catalog(dict(Title='Døe'))), 0)


class TestMembersFolder(IntranettTestCase):

    def _make_one(self):
        portal = self.layer['portal']
        # Remove the default members folder
        if 'users' in portal:
            portal._delObject('users')
        _createObjectByType('MembersFolder', portal, id='members', title='Members')
        portal['members'].processForm() # Fire events
        return portal['members']

    def test_create(self):
        folder = self._make_one()
        self.assertEqual(folder.portal_type, 'MembersFolder')
        self.assertEqual(folder.Title(), 'Members')

    def test_users_setuphandler(self):
        from intranett.policy.setuphandlers import setup_members_folder
        portal = self.layer['portal']
        request = self.layer['request']
        if 'users' in portal:
            portal._delObject('users')
        # simulate the effect of commands.py create_site
        request.form = {
            'extension_ids': ('intranett.policy:default', ),
            'form.submitted': True,
            'language': portal.Language(),
        }
        setup_members_folder(portal)
        folder = portal['users']
        self.assertEqual(folder.portal_type, 'MembersFolder')
        self.assertEqual(folder.Title(), 'Ansatte')
        self.assertEqual(folder.Language(), portal.Language())

    def test_get_member(self):
        folder = self._make_one()
        member = folder['test_user_1_']
        self.assertEqual(member.getId(), 'test_user_1_')

    def test_get_bad_member(self):
        folder = self._make_one()
        self.assertRaises(KeyError, folder.__getitem__, 'test_user_2_')

    def test_traverse(self):
        folder = self._make_one()
        member = folder.restrictedTraverse('test_user_1_')
        self.assertEqual(member.getId(), 'test_user_1_')
        self.assertEqual(member.getUserName(), 'test-user')

    def test_bad_traverse(self):
        folder = self._make_one()
        self.assertRaises(AttributeError, folder.restrictedTraverse, 'test_user_2_')

    def test_path_traverse(self):
        folder = self._make_one()
        member = folder.restrictedTraverse('test_user_1_')
        self.assertEqual(member.getId(), 'test_user_1_')
        self.assertEqual(member.getUserName(), 'test-user')

    def test_getMembersFolderId(self):
        portal = self.layer['portal']
        folder = self._make_one()
        id = getMembersFolderId()
        self.assertEqual(id, folder.getId())
        portal._delObject('members')
        self.assertEqual(getMembersFolderId(), '')

    def test_getMembersFolder(self):
        portal = self.layer['portal']
        folder = self._make_one()
        members = getMembersFolder(portal)
        self.assertNotEqual(members, None)
        self.assertEqual(members.getId(), folder.getId())
        self.assertEqual(members.absolute_url(), 'http://nohost/plone/members')
        portal._delObject('members')
        self.assertEqual(getMembersFolder(portal), None)

    def test_rename_members_folder(self):
        portal = self.layer['portal']
        folder = self._make_one()
        self.assertEqual(getMembersFolderId(), folder.getId())
        setRoles(portal, TEST_USER_ID, ['Manager'])
        transaction.savepoint(True) # Acquire a _p_oid
        portal.manage_renameObject('members', 'persons')
        self.assertEqual(getMembersFolderId(), 'persons')

    def test_override_members_folder(self):
        # There should only ever be one members folder in real life
        portal = self.layer['portal']
        folder = self._make_one()
        self.assertEqual(getMembersFolderId(), folder.getId())
        _createObjectByType('MembersFolder', portal, id='persons', title='Persons')
        portal['persons'].processForm() # Fire events
        self.assertEqual(getMembersFolderId(), 'persons')

    def test_delete_inactive_members_folder(self):
        # There should only ever be one members folder in real life
        portal = self.layer['portal']
        folder = self._make_one()
        _createObjectByType('MembersFolder', portal, id='persons', title='Persons')
        portal['persons'].processForm() # Fire events
        self.assertEqual(getMembersFolderId(), 'persons')
        # Deleting members keeps persons active
        portal._delObject(folder.getId())
        self.assertEqual(getMembersFolderId(), 'persons')
