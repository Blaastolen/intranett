from Products.CMFCore.interfaces import ISiteRoot
from Products.PluggableAuthService.interfaces.events import (
    IPrincipalCreatedEvent, IPrincipalDeletedEvent)
from zope.component import adapter
from zope.component import getUtility

from intranett.policy.utils import quote_userid


@adapter(IPrincipalCreatedEvent)
def onPrincipalCreation(event):
    """
    Setup user's "personal" folder.
    """
    pass

@adapter(IPrincipalDeletedEvent)
def onPrincipalDeletion(event):
    """
    Delete person folder of member.
    """
    pass
