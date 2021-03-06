#
# ExtropyTrackingTestCase Skeleton
#

from Testing import ZopeTestCase
from Products.Extropy.tests import ExtropyTrackingTestCase

from Products.CMFPlone.utils import _createObjectByType

from Products.Extropy.browser.reports import ReportView, iteratorFactory, ReportIterator, ReportKey, TableView, CSVView


class Dummyhours:
    """fake worked hours"""
    def __init__(self, hours):
        self.workedHours = hours


class TestReportViews(ExtropyTrackingTestCase.ExtropyTrackingTestCase):

    def afterSetUp(self):
        self.tool = self.portal.extropy_timetracker_tool
        self.request = self.app.REQUEST

    def testReportKeyUnicodeRendering(self):
        key = ReportKey(2001)
        unicode(key)
        key = ReportKey('\xc3\x98ks')
        unicode(key)

    def testInstantiateView(self):
        view = ReportView(self.portal, self.request)
        attributes = ('portal_membership', 'extropy_tracking_tool',
                      'extropy_timetracker_tool', 'getReportData')
        for attribute in attributes:
            self.failUnless(hasattr(view, attribute))

    def testQueryMinMax(self):
        view = ReportView(self.portal, self.request)
        self.folder.invokeFactory('Folder', 'extropy')
        folder = self.folder.extropy
        _createObjectByType('ExtropyHourGlass',folder, 'hourglass')
        folder.hourglass.invokeFactory('ExtropyHours','test1', startDate='2001/01/01', endDate='2001/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test2', startDate='2002/01/01', endDate='2002/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test3', startDate='2002/02/01', endDate='2002/02/02')
        res = view.getReportData2(group_by='getBudgetCategory')
        self.failUnlessEqual(res['total'], 24*3)
        res = view.getReportData2(group_by='start/year')
        self.failUnlessEqual(res['total'], 24*3)
        self.failUnlessEqual(res['2001']['total'], 24)
        self.failUnlessEqual(res['2002']['total'], 24*2)

    def testGetReportData2(self):
        view = ReportView(self.portal, self.request)
        self.folder.invokeFactory('Folder', 'extropy')
        folder = self.folder.extropy
        _createObjectByType('ExtropyHourGlass',folder, 'hourglass')
        folder.hourglass.invokeFactory('ExtropyHours','test1', startDate='2001/01/01', endDate='2001/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test2', startDate='2002/01/01', endDate='2002/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test3', startDate='2002/02/01', endDate='2002/02/02')
        res = view.getReportData(group_by='getBudgetCategory')
        self.failUnlessEqual(res.getValue(), 24*3)
        res = view.getReportData(group_by='start/year')
        self.failUnlessEqual(res.getValue(), 24*3)
        self.failUnlessEqual(res[ReportKey(2001)].getValue(), 24)
        self.failUnlessEqual(res[2001].getValue(), 24)
        self.failUnlessEqual(res[2002].getValue(), 24*2)

    def testGetReportDataActivity(self):
        view = CSVView(self.portal, self.request)
        self.folder.invokeFactory('Folder', 'extropy')
        folder = self.folder.extropy
        _createObjectByType('ExtropyHourGlass',folder, 'hourglass')
        folder.hourglass.invokeFactory('ExtropyHours','test1', title='Project management', startDate='2001/01/01', endDate='2001/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test2', title='#456 work', startDate='2002/01/01', endDate='2002/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test3', title='#456 more work', startDate='2002/02/01', endDate='2002/02/02')
        self.request.set('group_by', 'activity:getBudgetCategory')
        out = view()
        self.failUnlessEqual(out, 'activity,Billable\n'\
                                  '456,48.0\n'\
                                  'Project mgmt,24.0'
                                  )

        folder.hourglass.invokeFactory('ExtropyHours','test4', title='#457 even more work', startDate='2002/02/01', endDate='2002/02/02',budgetCategory='Administration')
        out = view()
        self.failUnlessEqual(out, 'activity,Administration,Billable\n'\
                                  '456,0,48.0\n'\
                                  '457,24.0,0\n'\
                                  'Project mgmt,0,24.0'\
                                  )

    def testGetReportMultiGrouping(self):
        view = CSVView(self.portal, self.request)
        self.folder.invokeFactory('Folder', 'extropy')
        folder = self.folder.extropy
        _createObjectByType('ExtropyHourGlass',folder, 'hourglass')
        folder.hourglass.invokeFactory('ExtropyHours','test1', title='Project management', startDate='2001/01/01', endDate='2001/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test2', title='#456 work', startDate='2002/01/01', endDate='2002/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test3', title='#456 more work', startDate='2002/02/01', endDate='2002/02/02')
        self.request.set('group_by', 'activity:getBudgetCategory:start/month')
        out = view()
        self.failUnlessEqual(out, 'activity,getBudgetCategory,January,February\n'\
                                  '456,Billable,24.0,24.0\n'\
                                  'Project mgmt,Billable,24.0,0'\
                                  )

        folder.hourglass.invokeFactory('ExtropyHours','test4', title='#457 even more work', startDate='2002/02/01', endDate='2002/02/02',budgetCategory='Administration')
        out = view()
        self.failUnlessEqual(out, 
                            'activity,getBudgetCategory,January,February\n'\
                            '456,Billable,24.0,24.0\n'\
                            '457,Administration,0,24.0\n'\
                            'Project mgmt,Billable,24.0,0'
                            )


    def testIteratorFactory(self):
        iterator = iteratorFactory(None)
        self.failUnless(isinstance(iterator, ReportIterator))

    def testReportIterator(self):
        iterator = ReportIterator(None)
        iterator['a'] = 'A'
        iterator['c'] = 'C'
        iterator['b'] = 'B'
        firstrun = [x for x in iterator]
        self.failUnless(firstrun)
        self.failUnlessEqual(firstrun, ['A', 'B', 'C'])
        secondrun = [x for x in iterator]
        self.failUnless(secondrun)
        self.failUnlessEqual(firstrun, secondrun)

    def testBreadCrumbs(self):
        iterator = ReportIterator(None)
        self.failUnlessEqual(iterator.getBreadCrumb(), '')

    def testReportKey(self):
        key1 = ReportKey(2001)
        key2 = ReportKey(2001)
        self.failUnlessEqual(key1, key2)

    def testReportKeyProject(self):
        class K(object):
            def __init__(self, title):
                self.Title = title
        k = ReportKey('activity', K('#456 worked hour'))
        self.failUnlessEqual(str(k), '456')
        k = ReportKey('activity', K('456 worked hour'))
        self.failUnlessEqual(str(k), '456')
        k = ReportKey('activity', K('Worked #456 hour'))
        self.failUnlessEqual(str(k), '456')

        k = ReportKey('activity', K('Planning meeting'))
        self.failUnlessEqual(str(k), 'Communication')
        k = ReportKey('activity', K('Discussed setup'))
        self.failUnlessEqual(str(k), 'Communication')

        k = ReportKey('activity', K('Project management'))
        self.failUnlessEqual(str(k), 'Project mgmt')
        k = ReportKey('activity', K('Project mgmt'))
        self.failUnlessEqual(str(k), 'Project mgmt')
        k = ReportKey('activity', K('Managed project'))
        self.failUnlessEqual(str(k), 'Project mgmt')

        k = ReportKey('activity', K('Tested ticket'))
        self.failUnlessEqual(str(k), 'Testing')

        k = ReportKey('activity', K('Nothing specific...'))
        self.failUnlessEqual(str(k), 'Other')

class TestTableViews(ExtropyTrackingTestCase.ExtropyTrackingTestCase):

    def afterSetUp(self):
        self.tool = self.portal.extropy_timetracker_tool
        self.request = self.app.REQUEST

    def testInstantiateView(self):
        view = TableView(self.portal, self.request)
        attributes = ('portal_membership', 'extropy_tracking_tool',
                      'extropy_timetracker_tool', 'getReportData')
        for attribute in attributes:
            self.failUnless(hasattr(view, attribute))

    def testQueryMinMax(self):
        view = TableView(self.portal, self.request)
        self.folder.invokeFactory('Folder', 'extropy')
        folder = self.folder.extropy
        _createObjectByType('ExtropyHourGlass',folder, 'hourglass')
        folder.hourglass.invokeFactory('ExtropyHours','test1', startDate='2001/01/01', endDate='2001/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test2', startDate='2002/01/01', endDate='2002/01/02')
        folder.hourglass.invokeFactory('ExtropyHours','test3', startDate='2002/02/01', endDate='2002/02/02')
        res = view.getReportData(group_by='getBudgetCategory:Creator')
        for row in res.rows():
            for col in row:
                self.failUnlessEqual(col, 72.0)
        res = view.getReportData2(group_by='start/year:getBudgetCategory')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTableViews))
    suite.addTest(makeSuite(TestReportViews))
    return suite
