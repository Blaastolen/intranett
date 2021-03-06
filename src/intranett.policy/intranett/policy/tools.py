from cStringIO import StringIO

from App.class_init import InitializeClass
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from AccessControl import ClassSecurityInfo
from AccessControl.requestmethod import postonly
from OFS.Image import Image
from PIL import Image as PILImage
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ManageUsers
from Products.CMFPlone.utils import safe_hasattr
from Products.PlonePAS.tools.membership import MembershipTool as \
    BaseMembershipTool
from Products.PlonePAS.tools.memberdata import MemberDataTool as \
    BaseMemberDataTool
from Products.PlonePAS.tools.memberdata import MemberData as BaseMemberData
from Products.PlonePAS.tools.membership import default_portrait
from Products.PlonePAS.utils import scale_image
from zope.component import getUtility

from intranett.policy.utils import getMembersFolderId

PORTRAIT_SIZE = (300, 300, )
PORTRAIT_THUMBNAIL_SIZE = (100, 100, )


def crop_and_scale_image(image_file,
                         max_size=PORTRAIT_THUMBNAIL_SIZE,
                         default_format='PNG'):
    """Crop the image from the center so that the horizontal and vertical
    dimensions are the same, then rescale.
    """
    size = (int(max_size[0]), int(max_size[1]))
    image = PILImage.open(image_file)
    format = image.format
    mimetype = 'image/%s' % format.lower()
    cur_size = image.size

    # Preserve palletted mode.
    original_mode = image.mode
    if original_mode == '1': # pragma: no cover
        image = image.convert('L')
    elif original_mode == 'P':
        image = image.convert('RGBA')

    # Do we need cropping?
    if cur_size[0] != cur_size[1]:
        min_size = min(cur_size[0], cur_size[1])
        max_size = max(cur_size[0], cur_size[1])

        # Let's always do modulo 2 arithmetic to keep things simple;)
        if (max_size - min_size) % 2 != 0:
            max_size = max_size - 1

        margin = (max_size - min_size) / 2
        box = (0, 0, min_size, min_size)

        if min_size == cur_size[1]:
            box = (margin, 0, max_size - margin, min_size)
        else: # pragma: no cover
            box = (0, margin, min_size, max_size - margin)
        image = image.crop(box)

    # Now scale....
    image.thumbnail(size, resample=PILImage.ANTIALIAS)

    # Again go back to palleted mode if necessary.
    if original_mode == 'P' and format in ('GIF', 'PNG'):
        image = image.convert('P')

    new_file = StringIO()
    image.save(new_file, format, quality=88)
    new_file.seek(0)
    return new_file, mimetype


def safe_transform(context, text, mt='text/x-html-safe'):
    """Use the safe_html transform to protect text output. This also
    ensures that resolve UID links are transformed into real links.
    """
    # Portal transforms needs encoded strings, and getProperty returns them
    transformer = getToolByName(context, 'portal_transforms')
    data = transformer.convertTo(mt, text,
                                 context=context, mimetype='text/html')
    result = data.getData()
    return result


class Portrait(Image):
    """Custom Portrait class to be able to add specific cache headers.
    """
    security = ClassSecurityInfo()

InitializeClass(Portrait)


class MemberData(BaseMemberData):
    """This is a catalog-aware MemberData. We add functions to allow the
    catalog to index member data.
    """
    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    # This is to make Plone's search machinery happy
    meta_type = portal_type = 'MemberData'

    # The default view
    def __browser_default__(self, request):
        return (self, ('memberdata_view', ))

    security.declarePrivate('notifyModified')
    def notifyModified(self):
        super(MemberData, self).notifyModified()
        plone = getUtility(ISiteRoot)
        ct = getToolByName(plone, 'portal_catalog')
        ct.reindexObject(self)

    security.declarePublic('getId')
    def getId(self):
        return self.id

    security.declarePublic('getMemberId')
    def getMemberId(self):
        return self.id

    security.declarePublic('getUser')
    def getUser(self):
        bcontext = aq_base(aq_parent(self))
        bcontainer = aq_base(aq_parent(aq_inner(self)))
        if bcontext is bcontainer:
            # XXX: Our acquisition context is fouled up.
            # XXX: Work around by re-getting the user from PAS.
            plone = getUtility(ISiteRoot)
            mt = getToolByName(plone, 'portal_membership')
            return mt._huntUser(self.id, plone)
        if not safe_hasattr(bcontext, 'getUserName'): # pragma: no cover
            raise ValueError("Cannot find user: %s" % self.id)
        # Return the user object, which is our context.
        return aq_parent(self)

    security.declarePublic('getPhysicalPath')
    def getPhysicalPath(self):
        plone = getUtility(ISiteRoot)
        return plone.getPhysicalPath() + (getMembersFolderId(), self.id)

    security.declareProtected(View, 'Type')
    def Type(self):
        return self.portal_type

    security.declareProtected(View, 'Title')
    def Title(self):
        return self.getProperty('fullname')

    security.declareProtected(View, 'Description')
    def Description(self):
        position = self.getProperty('position') or ''
        department = self.getProperty('department') or ''
        if position and department:
            return "%s, %s" % (position, department)
        else:
            return "%s%s" % (position, department)

    security.declareProtected(View, 'SearchableText')
    def SearchableText(self):
        description = safe_transform(
            self, self.getProperty('description') or '', 'text/plain')
        return ' '.join([self.getProperty('fullname') or '',
                         self.getProperty('email') or '',
                         self.getProperty('position') or '',
                         self.getProperty('department') or '',
                         self.getProperty('location') or '',
                         self.getProperty('phone') or '',
                         self.getProperty('mobile') or '',
                         description or ''])

InitializeClass(MemberData)


class MemberDataTool(BaseMemberDataTool):

    def __init__(self):
        super(MemberDataTool, self).__init__()
        self.thumbnails = BTreeFolder2(id='thumbnails')

    def _getPortrait(self, member_id, thumbnail=False):
        "return member_id's portrait if you can "
        if thumbnail:
            return self.thumbnails.get(member_id, None)
        return super(MemberDataTool, self)._getPortrait(member_id)

    def _setPortrait(self, portrait, member_id, thumbnail=False):
        " store portrait which must be a raw image in _portrais "
        if thumbnail:
            if member_id in self.thumbnails:
                self.thumbnails._delObject(member_id)
            self.thumbnails._setObject(id=member_id, object=portrait)
        else:
            super(MemberDataTool, self)._setPortrait(portrait, member_id)

    def _deletePortrait(self, member_id):
        " remove member_id's portrait "
        super(MemberDataTool, self)._deletePortrait(member_id)
        if member_id in self.thumbnails:
            self.thumbnails._delObject(member_id)

    @postonly
    def deleteMemberData(self, member_id, REQUEST=None):
        """ Delete member data of specified member.
        """
        members = self._members
        # Uncatalog
        if member_id in members:
            catalog = getToolByName(self, 'portal_catalog')
            catalog.unindexObject(members[member_id])
        # Remove portrait
        self._deletePortrait(member_id)
        return super(MemberDataTool, self).deleteMemberData(member_id)

    def wrapUser(self, u):
        """ Override wrapUser to use our MemberData
        """
        id = u.getId()
        if isinstance(id, unicode):
            id = id.encode('utf-8')
        members = self._members
        if id not in members:
            base = aq_base(self)
            members[id] = MemberData(base, id)
        return members[id].__of__(self).__of__(u)


class MembershipTool(BaseMembershipTool):

    security = ClassSecurityInfo()

    def getMemberInfo(self, memberId=None):
        memberinfo = super(MembershipTool, self).getMemberInfo(memberId)
        if memberinfo is None:
            return None
        if not memberId:
            member = self.getAuthenticatedMember()
        else:
            member = self.getMemberById(memberId)
        memberinfo['email'] = member.getProperty('email')
        memberinfo['phone'] = member.getProperty('phone')
        memberinfo['mobile'] = member.getProperty('mobile')
        memberinfo['position'] = member.getProperty('position')
        memberinfo['department'] = member.getProperty('department')
        memberinfo['birth_date'] = member.getProperty('birth_date')
        memberinfo['description'] = safe_transform(
            self, member.getProperty('description') or '')
        memberinfo['userid'] = member.getId()
        return memberinfo

    def changeMemberPortrait(self, portrait, id=None):
        """update the portait of a member.

        Modified from CMFPlone version to URL-quote the member id.
        """
        safe_id = self._getSafeMemberId(id)
        if not safe_id:
            safe_id = self.getAuthenticatedMember().getId()

        membertool = getToolByName(self, 'portal_memberdata')
        membership = getToolByName(self, 'portal_membership')
        if portrait and portrait.filename:
            scaled, mimetype = scale_image(portrait,
                                           max_size=PORTRAIT_SIZE)
            image = Portrait(id=safe_id, file=scaled, title='')
            image.manage_permission('View', ['Authenticated', 'Manager'],
                acquire=False)
            membertool._setPortrait(image, safe_id)
            # Now for thumbnails
            portrait.seek(0)
            scaled, mimetype = crop_and_scale_image(portrait)
            image = Portrait(id=safe_id, file=scaled, title='')
            image.manage_permission('View', ['Authenticated', 'Manager'],
                acquire=False)
            membertool._setPortrait(image, safe_id, thumbnail=True)
            # Reindex
            memberdata = membership.getMemberById(safe_id)
            if memberdata is not None:
                memberdata.notifyModified()

    def getPersonalPortrait(self, id=None, thumbnail=True):
        """Return a members personal portait.

        Modified to make it possible to return the thumbnail portrait.
        """
        safe_id = self._getSafeMemberId(id)
        if not safe_id:
            safe_id = self.getAuthenticatedMember().getId()

        membertool = getToolByName(self, 'portal_memberdata')
        portrait = membertool._getPortrait(safe_id, thumbnail=thumbnail)

        if portrait is None:
            portal = getToolByName(self, 'portal_url').getPortalObject()
            portrait = getattr(portal, default_portrait, None)

        return portrait

    def deletePersonalPortrait(self, id=None):
        """deletes the Portait of a member.

        Modified to reindex after deleting a portrait.
        """
        safe_id = self._getSafeMemberId(id)
        if not safe_id: # pragma: no cover
            safe_id = self.getAuthenticatedMember().getId()

        membership = getToolByName(self, 'portal_membership')
        super(MembershipTool, self).deletePersonalPortrait(safe_id)

        # Reindex
        memberdata = membership.getMemberById(safe_id)
        if memberdata is not None:
            memberdata.notifyModified()

    security.declareProtected(ManageUsers, 'getMemberByLogin')
    def getMemberByLogin(self, login):
        """Retrieve a Member object by login name."""
        acl_users = getToolByName(self, 'acl_users')
        users = acl_users.searchUsers(login=login, exact_match=True)
        users = [x.get('userid') for x in users if x.get('userid')]
        if not users:
            return None
        if len(users) > 1:
            raise ValueError('Multiple users found with the same login name')
        return self.getMemberById(users[0])

InitializeClass(MembershipTool)
