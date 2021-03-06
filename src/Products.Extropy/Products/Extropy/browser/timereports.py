from itertools import groupby
from operator import attrgetter

from zope.app.publisher.browser.menu import getMenu
from Products.Archetypes.config import REFERENCE_CATALOG

from AccessControl import getSecurityManager
from Acquisition import aq_parent
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import transaction_note
from Products.Five import BrowserView
from ZTUtils import make_query

from Products.Extropy.permissions import MANAGE_FINANCES
from Products.Extropy.utils import safe_unicode, activity


class TimeReportQuery(object):
    """Mixin class for timereport queries"""
    _hours = None
    _sum = None

    def _query(self):
        self._hours = self.ettool.getHours(self.context, start=self.start,
                                           end=self.end, REQUEST=self.request)
        self._sum = self.ettool.countHours(self._hours)

    def _clearQuery(self):
        self._hours = self._sum = None

    @property
    def hours(self):
        if self._hours is None:
            self._query()
        return self._hours

    @property
    def sum(self):
        if self._sum is None:
            self._query()
        return self._sum

    def people(self):
        creators = self.ettool.uniqueValuesFor('Creator')
        mt = getToolByName(self.context, 'portal_membership')
        users = []
        for c in creators:
            member = mt.getMemberInfo(c)
            if member:
                users.append((0, member))
            else:
                users.append((1, c))
        users.sort()
        return [u[1] for u in users]

    @property
    def categories(self):
        return self.ettool.uniqueValuesFor('getBudgetCategory')

    @property
    def hours_by_category(self):
        hours = list(self.hours)
        category = attrgetter('getBudgetCategory')
        hours.sort(key=category)
        for category, hours in groupby(hours, category):
            yield dict(category=safe_unicode(category),
                       sum=self.ettool.countHours(hours))

    @property
    def hours_by_date(self):
        def earliestStart(hour):
            start = hour.start.earliestTime()
            # Ensure a clean date in the server timezone
            return DateTime(start.Date())
        hours = list(self.hours)
        hours.sort(key=earliestStart)
        by_date = dict((k, tuple(v))
                       for (k, v) in groupby(hours, earliestStart))
        for date, hours in groupby(hours, earliestStart):
            hours = tuple(hours)
            yield dict(date=date, hours=hours,
                       sum=self.ettool.countHours(hours))

    @property
    def hours_by_project(self):
        hours = list(self.hours)
        project = attrgetter('getProjectTitle')
        hours.sort(key=project)
        for project, hours in groupby(hours, project):
            hours = tuple(hours)
            sum = self.ettool.countHours(hours)
            yield dict(project=safe_unicode(project),
                       category=hours[0].getBudgetCategory, sum=sum)


class InvoicingError(ValueError):
    """Error invoicing hour objects"""


class TimeReports(BrowserView, TimeReportQuery):
    def __init__(self, context, request):
        super(TimeReports, self).__init__(context, request)

        self.ettool = getToolByName(self.context, 'extropy_timetracker_tool')

        start = self.request.get('startdate', None)
        if not start:
            now = DateTime()
            # Default to showing the current year. During January we still
            # include the last year, as we usually still write bills for that
            # period.
            if now.month() > 1:
                start = '%s-01-01' % now.year()
            else:
                start = '%s-01-01' % (now.year() - 1)

        start = DateTime(start)
        self.start = start.earliestTime()

        end = self.request.get('enddate', None)
        end = end and DateTime(end) or DateTime()
        self.end = end.latestTime()

        self.query_string = make_query(*(
            {key: self.request[key]}
            for key in ('Creator', 'getBudgetCategory', 'startdate', 'enddate')
            if key in self.request))
        self.query_string = self.query_string and '?' + self.query_string

    def __call__(self, *args, **kw):
        result = None
        if 'create_invoice' in self.request:
            result = self.create_invoice()
        if 'move_hours' in self.request:
            result = self.moveHours()
        if result:
            return self.request.response.redirect(result)
        return super(TimeReports, self).__call__(*args, **kw)

    @property
    def menu(self):
        for mitem in getMenu('timereport', self.context, self.request):
            if not mitem['selected']:
                # workaround for Zope bug #2288, don't include @@ in action
                mitem['action'] = mitem['action'].replace('@@', '')
                yield mitem

    @property
    def finance_access(self):
        """Does the current user have permission to manage finances"""
        # This needs to be a property, because PlonePAS cannot determine the
        # user yet at traversal time, which is when the view gets instantiated
        user = getSecurityManager().getUser()
        return user.has_permission(MANAGE_FINANCES, self.context)

    @property
    def invoice_states(self):
        return self.ettool.uniqueValuesFor('review_state')

    def invoice_numbers(self):
        strings = self.ettool.uniqueValuesFor('getInvoiceNumber')
        numbers = [0, ]
        for s in strings:
            try:
                n = int(s)
            except (ValueError, TypeError):
                pass
            else:
                numbers.append(n)
        return numbers

    def last_invoice_number(self):
        numbers = self.invoice_numbers()
        return str(max(numbers))

    @property
    def selected_hours(self):
        selected = self.request.get('hours', ())
        for hour in self.hours:
            if hour.getPath() in selected:
                if hour.getBudgetCategory != 'Billable':
                    raise InvoicingError('Selected hour is not billable')
                if hour.review_state != 'entered':
                    raise InvoicingError('Selected hour is already invoiced')
                yield hour.getObject()

    def can_invoice(self, hour):
        """Determine if the given hour report can be invoiced"""
        return (hour.getBudgetCategory == 'Billable' and
                hour.review_state == 'entered')

    def setMessage(self, message):
        tool = getToolByName(self.context, 'plone_utils')
        tool.addPortalMessage(message)
        transaction_note(message)

    def email_hours_report(self):
        result = []
        for data in self.hours_by_date:
            if data['hours']:
                result.append('-' * 20)
                result.append(data['date'].strftime('%A %d %b'))
                for hour in data['hours']:
                    result.append('%s to %s (%s hours)   : %s' % (
                        hour.start.TimeMinutes(), hour.end.TimeMinutes(),
                        hour.workedHours, hour.Title.ljust(25)))
                result.append("total: %s hours\n" % data['sum'])
        result.append('-' * 60)
        result.append('Total hours between %s and %s : %s' % (
            self.start.Date(), self.end.Date(), self.sum,))
        result.append('=' * 60)
        return '\n'.join(result)

    def csv_hours_report(self):
        result = []
        result.append('start,duration,activity,title')
        for hour in self.hours:
            start = hour.start.ISO()
            duration = hour.workedHours
            activity_ = activity(hour)
            if activity_ is None:
                activity_ = ''
            title = hour.Title
            result.append('%s,%s,%s,"%s"' % (start,duration,activity_,title))
        return '\n'.join(result)

    def mark_invoiced(self, number):
        """Mark the selected hours as invoiced"""
        wf_tool = getToolByName(self.context, 'portal_workflow')
        for hour in self.selected_hours:
            hour.setInvoiceNumber(number)
            wf_tool.doActionFor(hour, 'invoice')
            hour.reindexObject()
        self._clearQuery()

    def create_invoice(self):
        """Create an invoice from the selected hours"""
        nr = self.request.form.get('invoiceNumber', None)
        if not nr:
            self.setMessage('You need to specify a number.')
            return
        numbers = self.ettool.uniqueValuesFor('getInvoiceNumber')
        if nr in numbers:
            self.setMessage('This invoice number has already been used.')
            return

        self.mark_invoiced(nr)
        self.setMessage('Created invoice from marked hours.')
        return self.context.absolute_url() + '/@@invoice-hours?number=%s' % nr

    def moveHours(self):
        """Move the selected hours to a different package"""
        targetuid = self.request.get('targetuid',None)
        if not targetuid:
                raise AttributeError("Cannot move hours without a destination")
        referencetool = getToolByName(self.context, REFERENCE_CATALOG)
        destination = referencetool.lookupObject(targetuid)
        if destination is None:
            raise AttributeError("we are trying to move to a None-object from uid %s" % (targetuid))
        for obj in self.selected_hours:
            destination.hourglass.manage_pasteObjects(aq_parent(obj).manage_cutObjects(obj.getId()))
        return destination.absolute_url() + '/timereport'
