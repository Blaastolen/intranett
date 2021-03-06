from zope.interface import implements

from AccessControl import ClassSecurityInfo

from Products.Archetypes.public import *

from Products.CMFCore.utils import getToolByName

from Products.Extropy.config import *
from Products.Extropy.interfaces import IExtropyBase
from Products.Extropy.interfaces import IExtropyTracking
from Products.Extropy.content.ExtropyBase import TimeSchema
from Products.Extropy.content.ExtropyBase import BudgetSchema
from Products.Extropy.content.ExtropyBase import ExtropyBase
from Products.Extropy.content.ExtropyBase import ExtropyBaseSchema
from Products.Extropy.content.ExtropyTracking import ExtropyTracking


ExtropyProjectSchema = ExtropyBaseSchema.copy() + Schema((

    LinesField(
        name='participants',
        vocabulary='getAvailableParticipants',
        multiValued=1,
        widget=InAndOutWidget(
            label='Participants',
            description='',
            label_msgid='label_participants',
            description_msgid='help_participants',
            i18n_domain='extropy',
        ),
    ),

    StringField(
        name='projectManager',
        vocabulary='getAvailableParticipants',
        widget=SelectionWidget(
            label='Project Manager',
            description='The project manager get a copy of all mail generated in the project.',
            label_msgid='label_project_manager',
            description_msgid='help_project_manager',
            i18n_domain='extropy',
        ),
    ),

    StringField(
        name='projectStatus',
        widget=StringWidget(
            label='Project Status',
            description='The current projetct status.',
            label_msgid='label_project_status',
            description_msgid='help_project_status',
            i18n_domain='extropy',
            size='60',
        ),
    ),

)) +  TimeSchema.copy() + BudgetSchema.copy()


class ExtropyProject(ExtropyTracking, ExtropyBase, OrderedBaseFolder):
    """An Extropy Project contains all the information needed to manage a project."""
    implements(IExtropyTracking, IExtropyBase)

    schema = ExtropyProjectSchema

    security = ClassSecurityInfo()
    _at_rename_after_creation = True

    security.declareProtected('View','getPhases')
    def getPhases(self):
        """Gets the list of phases."""
        return self.objectValues(['ExtropyPhase'])

    security.declareProtected('View','getActivePhases')
    def getActivePhases(self):
        """Gets the active phases. we can have more than one."""
        extropytool = getToolByName(self, TOOLNAME)
        res = extropytool.localQuery(node=self, portal_type='ExtropyPhase', review_state='active')
        return [i.getObject() for i in res]

    security.declareProtected('View','getAvailableParticipants')
    def getAvailableParticipants(self):
        """Lists the users."""
        membertool   = getToolByName(self, 'portal_membership')
        user_list    = membertool.listMemberIds()
        return user_list


registerType(ExtropyProject, PROJECTNAME)
