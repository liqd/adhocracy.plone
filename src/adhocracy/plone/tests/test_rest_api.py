import unittest2 as unittest
import json

from zope.component import getMultiAdapter
from zope.traversing.interfaces import BeforeTraverseEvent
from zope.event import notify

from plone.testing.z2 import Browser
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from adhocracy.plone.testing import \
    ADHOCRACY_PLONE_FUNCTIONAL_TESTING


class StaticPagesRESTAPIFunctionalTests(unittest.TestCase):

    layer = ADHOCRACY_PLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.browser = Browser(self.app)
        request = self.layer['request']
        request.set('URL', self.portal.absolute_url() + '/staticpages')
        notify(BeforeTraverseEvent(self.portal, request))
        self.request = request
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_staticpages_view_exists(self):
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view()
        response = view.request.response

        self.assertEqual(response.getHeader('content-type'),
                         'application/json;;charset="utf-8"')
        self.assertIn('errors', json.loads(response_body))

    def test_staticpages_nonvalid_missing_lang(self):
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")
        response_body = view()
        response = view.request.response
        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

    def test_staticpages_nonvalid_wrong_lang(self):
        self.request["QUERY_STRING"] = 'lang=WRONG'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view()
        response = view.request.response

        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

    def test_staticpages_valid_with_lang_no_children(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.request["QUERY_STRING"] = 'lang=de'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view()
        response = view.request.response

        wanted = {"title": "de uebersetzungen", "children": [], "name": "de"}
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(json.loads(response_body), wanted)

    def test_staticpages_valid_wrong_lang_but_with_fallback_no_children(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.request["QUERY_STRING"] = 'lang=WRONG&lang=de'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view()
        response = view.request.response

        wanted = {"title": "de uebersetzungen", "children": [], "name": "de"}
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(json.loads(response_body), wanted)

    def test_staticpages_valid_with_lang_and_children(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.portal["de"].invokeFactory('Document', 'c1', title=u"content1",
                                        body=u"body content1")
        self.portal["de"].invokeFactory('Folder', 'p1', title=u"parent1")
        self.portal["de"]["p1"].invokeFactory('Document', 'c2',
                                                   title=u"child2",
                                                   body=u"body child2")

        self.request["QUERY_STRING"] = 'lang=de'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view()
        response = view.request.response

        wanted = {u'title': u'de uebersetzungen', u'name': u'de',
                  u'children': [{u'title': u'content1', u'name': 'c1',
                                 u'children': []},
                                {u'title': u'parent1', u'name': u'p1',
                                 u'children': [{u'title': 'child2',
                                               u'name': 'c2',
                                               u'children': []}]}
                                ]}
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(json.loads(response_body), wanted)

    def test_staticpages_valid_with_lang_and_children_and_base(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.portal["de"].invokeFactory('Folder', 'parent1', title=u"parent1")
        self.portal["de"]["parent1"].invokeFactory('Document', 'child1',
                                                   title=u"child1",
                                                   body=u"body child1")

        self.request["QUERY_STRING"] = 'lang=de&base=parent1/child1'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view()
        response = view.request.response

        wanted = {u'title': 'child1', u'name': 'child1', u'children': []}
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(json.loads(response_body), wanted)

    def test_staticpages_nonvalid_with_lang_and_children_and_wrong_base(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.portal["de"].invokeFactory('Folder', 'parent1', title=u"parent1")
        self.portal["de"]["parent1"].invokeFactory('Document', 'child1',
                                                   title=u"child1",
                                                   body=u"body child1")

        self.request["QUERY_STRING"] = 'lang=de&base=WRONG'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view()
        response = view.request.response

        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

