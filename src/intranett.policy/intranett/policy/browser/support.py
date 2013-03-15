from AccessControl import getSecurityManager
from zope.interface import implements
from zope.publisher.browser import BrowserView
from zope.viewlet.interfaces import IViewlet


VIEWLET_TEXT = u"""
<script type="text/javascript"
  src="//asset0.zendesk.com/external/zenbox/v2.1/zenbox.js"></script>
<style type="text/css" media="screen, projection">
  @import url(//asset0.zendesk.com/external/zenbox/v2.1/zenbox.css);
</style>
<script type="text/javascript">
  if (typeof(Zenbox) !== "undefined") {
    Zenbox.init({
      dropboxID: "20021871",
      url: "https://blaastolen.zendesk.com",
      tabID: "support",
      hide_tab: true,
    });
    $('#supportLink').click(function() {
       window.Zenbox.show()
       });
  }
</script>
"""

class SupportViewlet(BrowserView):
    implements(IViewlet)

    def __init__(self, context, request, view, manager):
        super(SupportViewlet, self).__init__(context, request, view, manager)
        self.view = view
        self.manager = manager

    def update(self):
        pass

    def render(self):
        sm = getSecurityManager()
        can_manage_users = sm.checkPermission('Manage users', self.context)
        if can_manage_users:
            return VIEWLET_TEXT
        return u''
