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


class PurgeAllPathsIntegrationTests(unittest.TestCase):

    layer = ADHOCRACY_PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        request = self.layer['request']
        portal = self.layer['portal']
        self.request = request
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.invokeFactory('Folder', 'de')
        self.portal = portal

    def test_view_exists(self):
        view = getMultiAdapter((self.portal, self.request),
                               name=u"staticpages")

        response_body = view['single']()
        response = view.request.response

        self.assertEqual(response.getHeader('content-type'),
                         'application/json;;charset="utf-8"')
        self.assertIn('errors', json.loads(response_body))
