from zope.interface import implements
from zope.interface import alsoProvides
from zope.interface import Interface
from zope import schema
from zope.formlib import form

from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component import ComponentLookupError
from zope.component import adapts
from zope.component.hooks import getSite

from zope.annotation.interfaces import IAnnotations
from zope.publisher.interfaces.http import IHTTPRequest
from zope.schema.interfaces import IVocabularyFactory
from zope.security.interfaces import IPermission
from zope.security import checkPermission
from zope.traversing.interfaces import ITraversable

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from plone.app.portlets.interfaces import IPortletPermissionChecker
from plone.app.portlets.browser.adding import PortletAdding
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletRenderer

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zExceptions import Unauthorized
from Acquisition import Implicit
from Acquisition import ImplicitAcquisitionWrapper

from .i18n import MessageFactory as _
from .database import Software77GeoDatabase


class IEditAssignmentView(Interface):
    """Marker interface for the assignment edit view."""


class IGeoPortlet(IPortletDataProvider):
    countries = schema.Tuple(
        title=_(u"Countries"),
        description=_(u"Portlets allows visitors only from the "
                      u"selected countries. The IP-address of the visitor "
                      u"is matched against a geolocation database."),
        required=False,
        value_type=schema.Choice(
            vocabulary="collective.portlet.geo.vocabularies.Countries",
            ),
        )

    languages = schema.Tuple(
        title=_(u"Languages"),
        description=_(u"Show portlet also if the HTTP request contains "
                      u"a language accept string that matches the selected "
                      u"languages."),
        required=False,
        value_type=schema.Choice(
            vocabulary="plone.app.vocabularies.AvailableContentLanguages")
        )


class GeoPortletPermissionChecker(object):
    implements(IPortletPermissionChecker)
    adapts(IGeoPortlet)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        checker = IPortletPermissionChecker(self.context.__parent__)
        checker()


class GeoPortletAssignment(base.Assignment):
    implements(IGeoPortlet)

    def __init__(self, assignment, countries, languages):
        self.assignment = assignment
        self.countries = countries
        self.languages = languages

    @property
    def available(self):
        return self.assignment.available

    @property
    def title(self):
        factory = getUtility(
            IVocabularyFactory,
            name="collective.portlet.geo.vocabularies.Countries"
            )

        # The portlet assignment is not acquisition-wrapped; we use
        # the site hook to get to the portal object.
        site = getSite()

        try:
            vocabulary = factory(site)
        except AttributeError:
            return _(u"Geoportlet: ${title}", mapping={
                'title': self.assignment.title})

        return _(u"Geoportlet: ${title} (${countries}; \"${languages}\")",
                 mapping={
                     'countries': ', '.join(
                         vocabulary.getTerm(country).title.\
                         split('(', 1)[0].strip()
                         for country in self.countries) or '-',
                     'languages': ', '.join(self.languages) or '-',
                     'title': self.assignment.title,
                     })


class GeoPortletRenderer(base.Renderer):
    _no_cache_headers = (
        ('Expires', 'Mon, 26 Jul 1997 05:00:00 GMT'),
        ('Cache-Control', 'no-store, no-cache, must-revalidate'),
        ('Pragma', 'no-cache')
        )

    render = ViewPageTemplateFile('wrapper.pt')

    def __init__(self, *args):
        super(GeoPortletRenderer, self).__init__(*args)

        self.renderer = getMultiAdapter(
            (self.context, self.request, self.__parent__,
             self.manager, self.data.assignment),
            IPortletRenderer)

        for name, value in self._no_cache_headers:
            self.request.response.setHeader(name, value)

    @property
    def available(self):
        languages = set(
            unicode(spec.split(';')[0].strip()) for spec in
            self.request.get('HTTP_ACCEPT_LANGUAGE', '').split(',')
            )

        if languages & set(self.data.languages):
            return self.renderer.available

        remote_addr = self.request.get('HTTP_X_FORWARDED_FOR') or \
                      self.request.get('REMOTE_ADDR')

        if not remote_addr:
            return False

        portal = self.context.portal_url.getPortalObject()
        annotations = IAnnotations(portal)

        try:
            storage = annotations['geoportlet']
        except KeyError:
            return False

        database = Software77GeoDatabase(storage)
        result = database.lookup(remote_addr)
        if result is not None:
            return result[0] in self.data.countries and \
                   self.renderer.available

        return False

    def update(self):
        self.renderer.update()


class GeoPortletAddForm(base.AddForm):
    label = _(u"Add Geoportlet")
    form_fields = form.Fields(IGeoPortlet) + \
                  form.Fields(schema.Choice(
        __name__="factory",
        title=_(u"Portlet type"),
        description=_(u"Select the portlet type to create."),
        vocabulary="collective.portlet.geo.vocabularies.Portlets",
        required=True,
        ))

    def createAndAdd(self, data):
        adding_url = self.context.aq_parent.absolute_url()

        self.request.response.redirect(
            "%s/++geoportlet++%s;%s/%s" % (
                adding_url,
                ",".join(data['countries']),
                ",".join(data['languages']),
                data['factory'],
                ),
            lock=1)


class GeoPortletEditForm(base.EditForm):
    form_fields = form.Fields(IGeoPortlet)

    @property
    def label(self):
        return _(
            u"Edit country and languages settings for \"${title}\" portlet",
            mapping={'title': self.context.assignment.title}
            )


class GeoPortletEditAssignmentForm(GeoPortletEditForm):
    def __call__(self):
        try:
            form = self.context.assignment.restrictedTraverse('@@edit')
        except AttributeError:
            return super(GeoPortletEditAssignmentForm, self).__call__()

        alsoProvides(form, IEditAssignmentView)
        return form()


class GeoPortletAddingTraverser(object):
    implements(ITraversable)
    adapts(IPortletAssignmentMapping, IHTTPRequest)

    def __init__(self, context, request=None):
        self.context = context
        self.request = request

    def traverse(self, name, ignore):
        return GeoPortletAdding(self.context, self.request, name)


class GeoPortletAdding(PortletAdding):
    permission = "plone.app.portlets.ManagePortlets"

    def __init__(self, context, request, name):
        self.id = "++geoportlet++%s" % name
        countries, languages = name.split(';')
        self.countries = filter(None, countries.split(','))
        self.languages = filter(None, languages.split(','))
        BrowserView.__init__(self, context, request)

    def add(self, content):
        if not checkPermission(self.permission, self.context):
            permission = getUtility(IPermission, name=self.permission).title
            raise Unauthorized("Must have permission: '%s'." % permission)

        content = GeoPortletAssignment(content, self.countries, self.languages)
        super(GeoPortletAdding, self).add(content)
