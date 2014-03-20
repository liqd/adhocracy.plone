"""behaviors."""
from adhocracy.plone import _
from adhocracy.plone.interfaces import IAdhocracyStaticPagesRootRegistry
from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IDublinCore
from zope.component import getUtility
from zope import interface
from zope import schema
from zope.component import adapts

import plone.api


class IAdhocracyStaticPagesRoot(interface.Interface):

    """StaticPages behavior.

    Navigation root for adhocracy static pages backends.
    Providing this interfaces implies to have a VHM pointing
    to this object.

    """

    adhocracy_url = schema.URI(
        title=_(u"Adhocracy URL"),
        readonly=True,
    )


class IAdhocracyStaticPagesRootMarker(INavigationRoot):

    """ StaticPage behavior marker interface. """


class AdhocracyStaticPagesRoot(object):

    """StaticPages behavior class."""

    interface.implements(IAdhocracyStaticPagesRoot)
    adapts(IDublinCore)

    def __init__(self, context):
        self.context = context

    @property
    def adhocracy_url(self):
        reg = getUtility(IRegistry)
        reg_roots = reg.forInterface(IAdhocracyStaticPagesRootRegistry)
        roots = filter(lambda x: '|' in x, reg_roots.roots or [])
        roots_dict = dict(map(lambda x: x.split('|'), roots))
        context_path = self.context.absolute_url_path()
        portal = plone.api.portal.get()
        portal_path = portal.absolute_url_path()
        root_path = context_path.replace(portal_path, '', 1).lstrip('/')
        url = roots_dict.get(root_path, u'')
        return url.rstrip('/')
