from Acquisition import aq_get
from plutonian.gs import import_step
from Products.CMFCore.utils import getToolByName
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.i18n import translate
from zope.interface import alsoProvides

from intranett.policy.config import config


def set_profile_version(site):
    setup = getToolByName(site, 'portal_setup')
    setup.setLastVersionForProfile(
        config.policy_profile, config.last_upgrade_to())


def setup_locale(site):
    request = aq_get(site, 'REQUEST', None)
    language = 'no'
    if request is not None:
        language = request.form.get('language', 'no')
    site.setLanguage(language)
    tool = getToolByName(site, "portal_languages")
    tool.manage_setLanguageSettings(language,
        [language],
        setUseCombinedLanguageCodes=False,
        startNeutral=False)

    calendar = getToolByName(site, "portal_calendar")
    calendar.firstweekday = 0


def disable_contentrules(site):
    from plone.contentrules.engine.interfaces import IRuleStorage
    rule = queryUtility(IRuleStorage)
    if rule is not None:
        rule.active = False


def disallow_sendto(site):
    perm_id = 'Allow sendto'
    site.manage_permission(perm_id, roles=['Manager'], acquire=0)


def disable_collections(site):
    # Once collections are usable or we have a SiteAdmin role this should be
    # changed (both depend on Plone 4.1)
    perm_id = 'Add portal topics'
    site.manage_permission(perm_id, roles=[], acquire=0)
    perm_id = 'plone.portlet.collection: Add collection portlet'
    site.manage_permission(perm_id, roles=[], acquire=0)


def disable_portlets(site):
    from plone.portlets.interfaces import IPortletType
    from zope.component import getUtilitiesFor

    disabled = ['portlets.Calendar', 'portlets.Classic', 'portlets.Login',
                'portlets.Review', 'plone.portlet.collection.Collection']

    for info in getUtilitiesFor(IPortletType):
        if info[0] in disabled:
            p = info[1]
            # We remove the IColumn specification here, which makes the
            # portlets not addable for anything
            p.for_ = []
            p._p_changed = True


def setup_default_groups(site):
    gtool = getToolByName(site, 'portal_groups')
    # We could add more groups like this:
    # gtool.addGroup('Users', title='Users', roles=['Member'])
    gtool.removeGroups(['Administrators', 'Reviewers', 'Site Administrators'])


def setup_reject_anonymous(site):
    from iw.rejectanonymous import IPrivateSite
    # Used both as a setup and upgrade handler
    portal = getToolByName(site, 'portal_url').getPortalObject()
    alsoProvides(portal, IPrivateSite)


def setup_members_folder(site):
    from Products.CMFPlone.utils import _createObjectByType
    from intranett.policy.config import MEMBERS_FOLDER_ID
    fti = getToolByName(site, 'portal_types')['MembersFolder']
    title = translate(fti.Title(), target_language=site.Language())
    portal = getToolByName(site, 'portal_url').getPortalObject()
    _createObjectByType('MembersFolder', portal, id=MEMBERS_FOLDER_ID,
        title=title)
    portal[MEMBERS_FOLDER_ID].processForm() # Fire events
    workflow = getToolByName(portal, 'portal_workflow')
    workflow.doActionFor(portal[MEMBERS_FOLDER_ID], 'publish')


def setup_personal_folder(site):
    from plone.portlets.interfaces import ILocalPortletAssignmentManager
    from plone.portlets.interfaces import IPortletManager
    from Products.CMFPlone.utils import _createObjectByType
    from intranett.policy.config import PERSONAL_FOLDER_ID
    from intranett.policy import IntranettMessageFactory as _
    personal_folder_title = _(u'Personal folders')
    title = translate(personal_folder_title, target_language=site.Language())
    portal = getToolByName(site, 'portal_url').getPortalObject()
    _createObjectByType('Folder', portal, id=PERSONAL_FOLDER_ID,
        title=title)
    folder = portal[PERSONAL_FOLDER_ID]
    folder.setExcludeFromNav(True)
    folder.processForm() # Fire events
    workflow = getToolByName(portal, 'portal_workflow')
    workflow.doActionFor(folder, 'publish')
    # Block all portlets
    for manager_name in ('plone.leftcolumn', 'plone.rightcolumn'):
        manager = queryUtility(IPortletManager, name=manager_name)
        if manager is not None:
            assignable = queryMultiAdapter((folder, manager),
                ILocalPortletAssignmentManager)
            assignable.setBlacklistStatus('context', True)
            assignable.setBlacklistStatus('group', True)
            assignable.setBlacklistStatus('content_type', True)


def setup_default_content(site):
    from Testing import makerequest
    wrapped = makerequest.makerequest(site)
    from intranett.policy.browser.defaultcontent import DefaultContent
    view = DefaultContent(wrapped, wrapped.REQUEST)
    view()


def enable_secure_cookies(context):
    acl = aq_get(context, 'acl_users')
    acl.session._updateProperty('secure', True)
    acl.session._updateProperty('timeout', 172800)
    acl.session._updateProperty('refresh_interval', 7200)
    acl.session._updateProperty('cookie_lifetime', 7)


def ignore_link_integrity_exceptions(site):
    error_log = aq_get(site, 'error_log')
    props = error_log.getProperties()
    exceptions = props['ignored_exceptions']
    exceptions = exceptions + ('LinkIntegrityNotificationException', )
    error_log.setProperties(props['keep_entries'],
        ignored_exceptions=tuple(sorted(set(exceptions))))


def enable_link_by_uid(site):
    from plone.outputfilters.setuphandlers import \
        install_mimetype_and_transforms
    tiny = getToolByName(site, 'portal_tinymce')
    tiny.link_using_uids = True
    install_mimetype_and_transforms(site)


def open_ext_links_in_new_window(site):
    jstool = getToolByName(site, 'portal_javascripts')
    jstool.getResource('mark_special_links.js').setEnabled(True)
    jstool.cookResources()


def restrict_siteadmin(site):
    perm_ids = (
        'Content rules: Manage rules',
        'FTP access',
        'Plone Site Setup: Overview',
        'Plone Site Setup: Calendar',
        'Plone Site Setup: Editing',
        'Plone Site Setup: Filtering',
        'Plone Site Setup: Imaging',
        'Plone Site Setup: Language',
        'Plone Site Setup: Mail',
        'Plone Site Setup: Markup',
        'Plone Site Setup: Navigation',
        'Plone Site Setup: Search',
        'Plone Site Setup: Security',
        'Plone Site Setup: Site',
        'Plone Site Setup: Themes',
        'Plone Site Setup: TinyMCE',
        'Plone Site Setup: Types',
        'Sharing page: Delegate Reviewer role',
        'Undo changes',
        'Use Database Methods',
        'Use external editor',
        'View management screens',
        'WebDAV access',
        )
    for perm_id in perm_ids:
        site.manage_permission(perm_id, roles=['Manager'], acquire=0)


@import_step()
def various(context):
    if context.readDataFile('intranett-policy-various.txt') is None:
        return
    site = context.getSite()
    set_profile_version(site)
    setup_locale(site)
    disable_contentrules(site)
    disallow_sendto(site)
    disable_collections(site)
    disable_portlets(site)
    setup_default_groups(site)
    setup_reject_anonymous(site)
    ignore_link_integrity_exceptions(site)
    enable_link_by_uid(site)
    setup_members_folder(site)
    setup_personal_folder(site)
    enable_secure_cookies(site)
    open_ext_links_in_new_window(site)
    restrict_siteadmin(site)


def content(context):
    if context.readDataFile('intranett-policy-content.txt') is None:
        return
    site = context.getSite()
    setup_default_content(site)


import logging

from plone.app.upgrade.v40.alphas import migrateFolders
from plone.app.upgrade.v40.alphas import updateLargeFolderType
from plone.app.upgrade.v40.betas import convertToBlobs

from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import safe_callable
from Products.Archetypes.utils import getRelURL
from Products.Archetypes.ReferenceEngine import Reference
from Products.ATContentTypes.criteria.base import ATBaseCriterion

logger = logging.getLogger('karmoy.contentimport')


def fixOwnership(portal):
    """Repair owner tuples to contain the right user folder path.
    """
    logger.info('Fixing executable ownership...')

    def fixOwnerTuple(obj, path):
        old = obj.getOwnerTuple()
        if old:
            if old[1] in ('admin', 'jarn', 'manager', 'redpilladmin', 'tog'):
                if old[0] != ['acl_users']:
                    new = (['acl_users'], old[1])
                    logger.info('Fixing %s %r -> %r', path, old, new)
                    obj._owner = new
            else:
                if old[0] != ['Plone', 'acl_users']:
                    new = (['Plone', 'acl_users'], old[1])
                    logger.info('Fixing %s %r -> %r', path, old, new)
                    obj._owner = new

    portal.ZopeFindAndApply(portal, search_sub=True, apply_func=fixOwnerTuple)


def rebuildPortalCatalog(portal):
    """Empties catalog, then finds all contentish objects (i.e. objects
       with an indexObject method), and reindexes them.
       This may take a long time.
    """
    logger.info('Rebuilding portal catalog...')
    portal.portal_catalog.clearFindAndRebuild()


def rebuildUIDCatalog(portal):
    logger.info('Rebuilding UID catalog...')

    def indexObject(obj, path):
        if (base_hasattr(obj, 'indexObject') and
            safe_callable(obj.indexObject)):

            if isinstance(obj, ATBaseCriterion): return
            url = getRelURL(portal, obj.getPhysicalPath())
            portal.uid_catalog.catalog_object(obj, url)

    portal.uid_catalog.manage_catalogClear()
    portal.ZopeFindAndApply(portal, search_sub=True, apply_func=indexObject)


def rebuildRefCatalog(portal):
    logger.info('Rebuilding reference catalog...')
    portal.reference_catalog.manage_catalogClear()
    brains = portal.portal_catalog.unrestrictedSearchResults()
    for brain in brains:
        obj = brain.getObject()
        if base_hasattr(obj, 'at_references'):
            for ref in obj.at_references.objectValues():
                if not isinstance(ref, Reference):
                    continue
                url = getRelURL(portal, ref.getPhysicalPath())
                portal.reference_catalog.catalog_object(ref, url)


def importZexp(context, zexp_name, set_owner=True):
    """Import zexp file into context."""
    logger.info('Importing %s...', zexp_name)
    if zexp_name in context:
        context.manage_delObjects(zexp_name)
    zexp_file = zexp_name + '.zexp'
    context.manage_importObject(zexp_file, set_owner=set_owner)

@import_step()
def importContent(context):
    """Import old Karmoy content
    """
    if context.readDataFile('intranett-policy-contentimport.txt') is None:
        return
    portal = context.getSite()

    zexps = ('source_users',)
    for zexp_name in zexps:
        importZexp(portal.acl_users, zexp_name)
    #'portal_memberdata',
    zexps = ('avdelinger', 'sandkasse', 'bilder', 'hurtiglenker', 
             'studietur-til-voss-kulturhus-med-bibliotek', 'kalender', 
             'telefonliste', 'news', 'vaktlister', 'personal-og-hms', 
             'vekeplan-for-moterom', 'prosjekter', 'viktig-informasjon',)
    for zexp_name in zexps:
        importZexp(portal, zexp_name)

    migrateFolders(portal)
    rebuildPortalCatalog(portal)
    updateLargeFolderType(portal)
    fixOwnership(portal)
    rebuildPortalCatalog(portal)
    rebuildUIDCatalog(portal)
    rebuildRefCatalog(portal)
    convertToBlobs(portal)

    logger.info('done')


