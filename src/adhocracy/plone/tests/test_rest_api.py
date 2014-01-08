# -*- coding: utf-8 -*-
import unittest2 as unittest
from urllib2 import HTTPError
import json

from zope.component import getMultiAdapter
from zope.traversing.interfaces import BeforeTraverseEvent
from zope.event import notify

from plone.testing.z2 import Browser
from plone.app.testing import (
    setRoles,
    TEST_USER_ID,
    TEST_USER_NAME,
    TEST_USER_PASSWORD,
)
from adhocracy.plone.testing import (
    ADHOCRACY_PLONE_FUNCTIONAL_TESTING,
    ADHOCRACY_PLONE_INTEGRATION_TESTING,
)


class StaticPagesViewIntegrationTests(unittest.TestCase):

    layer = ADHOCRACY_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        request = self.layer['request']
        request.set('URL', self.portal.absolute_url() + '/staticpages')
        notify(BeforeTraverseEvent(self.portal, request))
        self.request = request
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_view_exists(self):
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages()
        response = view.request.response

        self.assertEqual(response.getHeader('content-type'),
                         'application/json;;charset="utf-8"')
        self.assertIn('errors', json.loads(response_body))

    def test_nonvalid_missing_lang(self):
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")
        response_body = view.staticpages()
        response = view.request.response
        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

    def test_nonvalid_wrong_lang(self):
        self.request["QUERY_STRING"] = 'lang=WRONG'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages()
        response = view.request.response

        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

    def test_valid_with_lang_no_children(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.request["QUERY_STRING"] = 'lang=de'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages()
        response = view.request.response

        wanted = {"title": "de uebersetzungen", "children": [], "name": "de"}
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(json.loads(response_body), wanted)

    def test_valid_wrong_lang_but_with_fallback_no_children(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.request["QUERY_STRING"] = 'lang=WRONG&lang=de'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages()
        response = view.request.response

        wanted = {"title": "de uebersetzungen", "children": [], "name": "de"}
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(json.loads(response_body), wanted)

    def test_valid_with_lang_and_children(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de übersetzungen")
        self.portal["de"].invokeFactory('Document', 'c1', title=u"content1",
                                        body=u"body content1")
        self.portal["de"].invokeFactory('Folder', 'p1', title=u"parent1")
        self.portal["de"]["p1"].invokeFactory('Document', 'c2',
                                              title=u"child2",
                                              body=u"body child2")

        self.request["QUERY_STRING"] = 'lang=de'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages()
        response = view.request.response

        wanted = {u'title': u'de übersetzungen', u'name': u'de',
                  u'children': [{u'title': u'content1', u'name': 'c1',
                                 u'children': []},
                                {u'title': u'parent1', u'name': u'p1',
                                 u'children': [{u'title': 'child2',
                                               u'name': 'c2',
                                               u'children': []}]}
                                ]}

        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(json.loads(response_body), wanted)

    def test_valid_with_lang_and_children_and_base(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.portal["de"].invokeFactory('Folder', 'parent1', title=u"parent1")
        self.portal["de"]["parent1"].invokeFactory('Document', 'child1',
                                                   title=u"child1",
                                                   body=u"body child1")

        self.request["QUERY_STRING"] = 'lang=de&base=parent1/child1'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages()
        response = view.request.response

        wanted = {u'title': 'child1', u'name': 'child1', u'children': []}
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(json.loads(response_body), wanted)

    def test_nonvalid_with_lang_and_children_and_wrong_base(self):
        self.portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        self.portal["de"].invokeFactory('Folder', 'parent1', title=u"parent1")
        self.portal["de"]["parent1"].invokeFactory('Document', 'child1',
                                                   title=u"child1",
                                                   body=u"body child1")

        self.request["QUERY_STRING"] = 'lang=de&base=WRONG'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages()
        response = view.request.response

        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))


class StaticPagesSingleViewIntegrationTests(unittest.TestCase):

    layer = ADHOCRACY_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        request = self.layer['request']
        portal = self.layer['portal']
        request.set('URL', portal.absolute_url() + '/staticpages')
        notify(BeforeTraverseEvent(portal, request))
        self.request = request
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('Folder', 'de', title=u"de uebersetzungen")
        portal["de"].invokeFactory('Folder', 'parent1', title=u"parent1")
        portal["de"]["parent1"].invokeFactory('Document', 'child1',
                                              title=u"child1",
                                              description=u"üdescription",
                                              body=u"body child1")
        self.portal = portal

    def test_view_exists(self):
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages_single()
        response = view.request.response

        self.assertEqual(response.getHeader('content-type'),
                         'application/json;;charset="utf-8"')
        self.assertIn('errors', json.loads(response_body))

    def test_nonvalid_missing_lang(self):
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")
        response_body = view.staticpages_single()
        response = view.request.response
        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

    def test_nonvalid_wrong_lang(self):
        self.request["QUERY_STRING"] = 'lang=WRONG'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages_single()
        response = view.request.response

        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

    def test_nonvalid_with_lang_but_missing_path(self):
        self.request["QUERY_STRING"] = 'lang=de'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages_single()
        response = view.request.response

        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

    def test_nonvalid_with_lang_but_wrong_path(self):
        self.request["QUERY_STRING"] = 'lang=de&path=WRONG'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages_single()
        response = view.request.response

        self.assertEqual(response.getStatus(), 400)
        self.assertIn("errors", json.loads(response_body))

    def test_valid_with_lang_and_path(self):
        self.request["QUERY_STRING"] = 'lang=de&path=parent1/child1'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view.staticpages_single()
        response = view.request.response

        self.assertEqual(response.getStatus(), 200)
        response_data = json.loads(response_body)
        self.assertTrue(response_data["body"].startswith(u'<div id="content"'))
        self.assertEqual(response_data["title"], u'child1')
        self.assertEqual(response_data["path"], u'parent1/child1')
        self.assertEqual(response_data["lang"], u'de')
        self.assertTrue(response_data["nav"].startswith(u'<ul'))
        self.assertEqual(response_data["description"], u'üdescription')
        self.assertEqual(response_data["private"], False)

    def test_valid_with_fallback_lang_and_path(self):
        self.request["QUERY_STRING"] = 'lang=WRONG&lang=de&path=parent1/child1'
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        view.staticpages_single()
        response = view.request.response

        self.assertEqual(response.getStatus(), 200)


class StaticPagesViewFunctionalTests(unittest.TestCase):

    layer = ADHOCRACY_PLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('Folder', 'de', title=u"de übersetzungen")
        portal["de"].invokeFactory('Folder', 'parent1', title=u"parent1")
        portal["de"]["parent1"].invokeFactory('Document', 'child1',
                                              title=u"child1",
                                              body=u"body child1")
        self.portal = portal
        self.portal_url = portal.absolute_url()
        import transaction
        transaction.commit()
        browser = Browser(self.app)
        browser.addHeader('Authorization',
                          'Basic %s:%s' % (TEST_USER_NAME,
                                           TEST_USER_PASSWORD,))
        self.browser = browser

    def test_staticpages_valid(self):
        self.browser.open(self.portal_url + "/staticpages?lang=de")
        response_data = json.loads(self.browser.contents)
        self.assertIn("name", response_data)

    def test_staticpages_nonvalid_missing_lang(self):
        try:
            self.browser.open(self.portal_url + "/staticpages")
        except HTTPError as e:
            self.assertEqual(e.getcode(), 400)

    def test_staticpagessingle_valid(self):
        url = "/staticpages/single?lang=de&path=parent1/child1"
        self.browser.open(self.portal_url + url)
        response_data = json.loads(self.browser.contents)
        self.assertIn("title", response_data)
