PROJECTNAME = 'intranett.policy'
ADD_PERMISSIONS = {'MembersFolder': '%s: Add MembersFolder' % PROJECTNAME,
                   'ProjectRoom': '%s: Add ProjectRoom' % PROJECTNAME,}
MEMBERS_FOLDER_ID = 'users'

from plutonian import Configurator

config = Configurator('intranett.policy')

# upgrade fails without default workflows installed
config.ignored_upgrade_profiles.append('Products.CMFPlacefulWorkflow:CMFPlacefulWorkflow')

# upgrade step is reinstall
config.ignored_upgrade_profiles.append('plonetheme.sunburst:default')
