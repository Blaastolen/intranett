import unittest

from zope.component import getUtility
from zope.interface.verify import verifyClass

from DateTime import DateTime
from Products.Five import zcml, fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from Testing import ZopeTestCase as ztc

import intranett.task
from intranett.task.interfaces import ITask, ITaskManager
from intranett.task.taskmanager import TaskManager
from intranett.task.task import Task


@onsetup
def setup_product():
    """ """
    fiveconfigure.debug_mode = True
    zcml.load_config('configure.zcml', intranett.task)
    fiveconfigure.debug_mode = False
    ztc.installPackage('intranett.task', quiet=1)

setup_product()
ptc.setupPloneSite(products=['intranett.task', ],
                   policy='intranett.task:default')


class TestCreation(ptc.PloneTestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.folder.invokeFactory('Document', 'doc')
        self.doc = self.folder.doc

    def testTask(self):
        self.failUnless(verifyClass(ITask, Task), True)
        date = DateTime()
        t = Task('description', 'axa', 'vds', date)
        self.failUnless(t.description == 'description')
        self.failUnless(t.assigned_to == 'axa')
        self.failUnless(t.created_by == 'vds')
        self.failUnless(t.due_date == date)

    def testTaskManager(self):
        self.failUnless(verifyClass(ITaskManager, TaskManager), True)
        tm = TaskManager()
        self.failUnless(tm.__name__ == 'taskmanager')


class TestRelations(ptc.PloneTestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.folder.invokeFactory('Document', 'doc')
        self.doc = self.folder.doc

    def testRelation(self):
        tm = getUtility(ITaskManager)
        task = tm.newTask(self.doc, 'description', 'axa', 'vds')
        self.assertEquals(task.content_uid, self.doc.UID())
        self.assertEquals(len(tm.listTasks()), 1)
        self.assertEqual(tm.contentForTask(task), self.doc)
        tid = task.id
        oldtask = tm.delTask(task)
        self.failUnless(oldtask.id == tid)
        self.failUnless(len(tm.listTasks()) == 0)

    def testTaskManagement(self):
        tm = getUtility(ITaskManager)
        t0 = tm.newTask(self.doc, 'description0', 'axa', 'vds')
        t1 = tm.newTask(self.doc, 'description1', 'vds', 'vds')
        t2 = tm.newTask(self.doc, 'description2', 'axa', 'lili')
        self.failIf(tm.tasksCreatedBy('vds') != [t0, t1])
        self.failIf(tm.tasksAssignedTo('axa') != [t0, t2])
        self.failIf(tm.tasksOnContent(self.doc) != [t0, t1, t2])


class TestEvents(ptc.PloneTestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.folder.invokeFactory('Document', 'doc')
        self.doc = self.folder.doc

    def testObjectRemovedEvent(self):
        tm = getUtility(ITaskManager)
        tm.newTask(self.doc, 'description0', 'axa', 'vds')
        self.failUnless(len(tm.tasksOnContent(self.doc)) == 1)
        self.folder._delObject('doc')
        self.failUnless(len(tm.tasksOnContent(self.doc)) == 0)


def test_suite():
    return unittest.TestSuite([
        unittest.makeSuite(TestCreation),
        unittest.makeSuite(TestRelations),
        unittest.makeSuite(TestEvents),
        ])
