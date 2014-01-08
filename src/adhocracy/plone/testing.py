from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from plone.testing import z2

from zope.configuration import xmlconfig


class AdhocracyploneLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import adhocracy.plone
        xmlconfig.file(
            'configure.zcml',
            adhocracy.plone,
            context=configurationContext
        )

        # Install products that use an old-style initialize() function
        #z2.installProduct(app, 'Products.PloneFormGen')

#    def tearDownZope(self, app):
#        # Uninstall products installed above
#        z2.uninstallProduct(app, 'Products.PloneFormGen')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'adhocracy.plone:default')

ADHOCRACY_PLONE_FIXTURE = AdhocracyploneLayer()
ADHOCRACY_PLONE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(ADHOCRACY_PLONE_FIXTURE,),
    name="AdhocracyploneLayer:Integration"
)
ADHOCRACY_PLONE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(ADHOCRACY_PLONE_FIXTURE, z2.ZSERVER_FIXTURE),
    name="AdhocracyploneLayer:Functional"
)
