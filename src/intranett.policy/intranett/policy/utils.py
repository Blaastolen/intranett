import logging
from urllib import quote

from Acquisition import aq_get
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from Products.PlonePAS.utils import cleanId
from zope.component import queryUtility

from intranett.policy.interfaces import IMembersFolderId

logger = logging.getLogger("intranett")


def get_fullname(context, userid):
    membership = getToolByName(context, 'portal_membership')
    member_info = membership.getMemberInfo(userid)
    # member_info is None if there's no Plone user object
    if member_info:
        fullname = member_info.get('fullname', '')
    else: # pragma: no cover
        fullname = None
    if fullname:
        return fullname
    return userid


def getMembersFolderId():
    """Helper function to retrieve the members folder id."""
    return queryUtility(IMembersFolderId, default='')


def get_users_folder_url(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    return portal.absolute_url() + '/' + quote(getMembersFolderId())


def get_user_profile_url(context, member_id):
    return get_users_folder_url(context) + '/' + quote(member_id)


def get_current_user_profile_url(context):
    mtool = getToolByName(context, "portal_membership")
    member = mtool.getAuthenticatedMember()
    userid = member.getId()
    return get_users_folder_url(context) + '/' + quote(userid)


def getMembersFolder(context):
    """Helper function to retrieve the members folder."""
    id = getMembersFolderId()
    if id:
        portal = getToolByName(context, 'portal_url').getPortalObject()
        return portal.get(id)


def quote_userid(user_id):
    if isinstance(user_id, unicode):
        user_id = user_id.encode('utf-8')
    return cleanId(user_id)







# Make functions available to scripts
from AccessControl import ModuleSecurityInfo
ModuleSecurityInfo('intranett.policy.utils').declarePublic('getMembersFolderId')
ModuleSecurityInfo('intranett.policy.utils').declarePublic('getMembersFolder')
ModuleSecurityInfo('intranett.policy.utils').declarePublic(
    'get_current_user_profile_url')
ModuleSecurityInfo('intranett.policy.utils').declarePublic(
    'get_user_profile_url')
