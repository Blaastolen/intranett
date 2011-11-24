from plone.app.portlets.interfaces import IColumn
from plone.theme.interfaces import IDefaultPloneLayer
from zope.viewlet.interfaces import IViewletManager


class IThemeSpecific(IDefaultPloneLayer):
    """Marker interface that defines a Zope browser layer.
    """


class IAboveColumns(IViewletManager):
    """A viewlet manager that sits above the columns
    """


class IAboveContent(IViewletManager):
    """A viewlet manager that sits between content and portal header
    """


class ITopBar(IViewletManager):
    """A viewlet manager that sits on top of everything
       else in the site and is rendered as the bar across the
       screen at the top
    """


class ITopBarWrapper(IViewletManager):
    """A viewlet manager that directly contains the top bar items
    """


class IFrontpagePortletManagers(IColumn):
    """ General interface for portlet managers on the Frontpage View.
    """
