from zope.component import getUtility
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from zope.annotation.interfaces import IAnnotations
from zope.i18n import translate

from plone.portlets.interfaces import IPortletManager
from plone.app.portlets.browser.interfaces import IPortletAdding

from .database import Software77GeoDatabase


class Countries(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        portal = context.portal_url.getPortalObject()
        annotations = IAnnotations(portal)

        try:
            storage = annotations['geoportlet']
        except KeyError:
            terms = []
        else:
            database = Software77GeoDatabase(storage)
            terms = [
                SimpleTerm(code, code, name) for (code, name) in
                database.countries
                ]

        return SimpleVocabulary(terms)


class Portlets(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        assert IPortletAdding.providedBy(context)
        name = context.__parent__.__manager__
        manager = getUtility(IPortletManager, name=name)
        request = context.request
        return SimpleVocabulary([
            SimpleTerm(ptype.addview, ptype.addview, ptype.title)
            for ptype in sorted(
                manager.getAddablePortletTypes(),
                key=lambda ptype: translate(ptype.title, context=request))
            if ptype.addview != "collective.portlet.geo.GeoPortlet"
            ])


countries = Countries()
portlets = Portlets()
