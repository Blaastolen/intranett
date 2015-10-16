from plone.app.upgrade.utils import loadMigrationProfile
from plutonian.gs import upgrade_to


@upgrade_to(47)
def install_xmpp(context):
    from intranett.policy.setuphandlers import setup_xmpp
    loadMigrationProfile(context, 'profile-jarn.xmpp.core:default')
    loadMigrationProfile(context, 'profile-intranett.policy:default',
        steps=('cssregistry', 'jsregistry', 'kssregistry', 'plone.app.registry', ))
    loadMigrationProfile(context, 'profile-intranett.theme:default',
        steps=('viewlets', ))
    setup_xmpp(context)

@upgrade_to(48)
def plone_43(context):
    loadMigrationProfile(context, 'profile-plone.app.theming:default')
    loadMigrationProfile(context, 'profile-intranett.policy:default',
        steps=('jsregistry', 'factorytool'))
