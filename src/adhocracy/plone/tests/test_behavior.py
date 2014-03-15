# -*- coding: utf-8 -*-
import unittest2 as unittest

from zope.traversing.interfaces import BeforeTraverseEvent
from zope.event import notify

from plone.app.testing import (
    setRoles,
    TEST_USER_ID,
)
from adhocracy.plone.testing import (
    ADHOCRACY_PLONE_INTEGRATION_TESTING,
)


class AdhocracyStaticPagesRootIntegrationTests(unittest.TestCase):

    layer = ADHOCRACY_PLONE_INTEGRATION_TESTING

    def _setup_test_content_type(self, name):
        from plone.dexterity.fti import DexterityFTI
        fti = DexterityFTI(name)
        fti.behaviors = ('plone.app.dexterity.behaviors.metadata.IDublinCore',
                         'adhocracy.plone.behavior.IAdhocracyStaticPagesRoot')
        fti.klass = 'plone.dexterity.content.Container'
        fti.filter_content_types = False
        self.portal.portal_types._setObject(name, fti)
        fti.lookupSchema()

    def tearDown(self):
        if 'test_folder' in self.portal.portal_types:
            del self.portal.portal_types['test_folder']

    def setUp(self):
        self.app = self.layer['app']
        request = self.layer['request']
        portal = self.layer['portal']
        request.set('URL', portal.absolute_url() + '/staticpages')
        notify(BeforeTraverseEvent(portal, request))
        self.request = request
        setRoles(portal, TEST_USER_ID, ['Manager'])
        self.portal = portal
        self._setup_test_content_type('test_folder')

    def test_registry(self):
        from adhocracy.plone.interfaces import\
            IAdhocracyStaticPagesRootRegistry
        from zope.component import getUtility
        from plone.registry.interfaces import IRegistry
        reg = getUtility(IRegistry)
        reg_roots = reg.forInterface(IAdhocracyStaticPagesRootRegistry)
        roots = reg_roots.roots
        self.assertIn('adhocracy|https://adhocracy.de/static/', roots)

    def test_create(self):
        from adhocracy.plone.behavior import IAdhocracyStaticPagesRoot
        from adhocracy.plone.behavior import IAdhocracyStaticPagesRootMarker
        self.portal.invokeFactory('test_folder', 'adhocracy',
                                  title=u"Staticpages For adhocracy.de")
        folder = self.portal['adhocracy']
        self.assertTrue(IAdhocracyStaticPagesRootMarker.providedBy(folder))
        IAdhocracyStaticPagesRoot(folder)

    def test_get_adhocracy_url(self):
        from adhocracy.plone.behavior import IAdhocracyStaticPagesRoot
        from adhocracy.plone.interfaces import\
            IAdhocracyStaticPagesRootRegistry
        from zope.component import getUtility
        from plone.registry.interfaces import IRegistry
        reg = getUtility(IRegistry)
        reg_roots = reg.forInterface(IAdhocracyStaticPagesRootRegistry)
        self.portal.invokeFactory('test_folder', 'adhocracy',
                                  title=u"Staticpages For adhocracy.de")
        folder = self.portal['adhocracy']
        adhocracyroot = IAdhocracyStaticPagesRoot(folder)

        reg_roots.roots = [u"adhocracy|https://adhocracy.de"]
        self.assertEqual(adhocracyroot.adhocracy_url, u"https://adhocracy.de")
        reg_roots.roots = [u"adhocracy|https://adhocracy.de/"]
        self.assertEqual(adhocracyroot.adhocracy_url, u"https://adhocracy.de")
        reg_roots.roots = [u"adhocracy|"]
        self.assertEqual(adhocracyroot.adhocracy_url, u"")
        reg_roots.roots = None
        self.assertEqual(adhocracyroot.adhocracy_url, u"")
        reg_roots.roots = [u""]
        self.assertEqual(adhocracyroot.adhocracy_url, u"")

