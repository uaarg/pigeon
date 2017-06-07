import unittest

import features

class FeatureTestCase(unittest.TestCase):
    def testSerialization(self):
        """
        Checks that features can be serialized and deserialize to the same thing.
        """
        f = features.BaseFeature()
        old_id = f.id

        serialized = f.serialize()
        del f

        f2 = features.BaseFeature.deserialize(serialized)
        self.assertEqual(f2.id, old_id)

    def testSerializationPicklingSecurity(self):
        """
        Checks that unsafe pickled data isn't trusted.

        Note: this isn't a comprehensive security check. It doesn't guarantee
        that things are secure. It's just a unittest for the approach of
        whitelisting classes which is believed to be secure.
        """

        # First, preparing the exploit:
        import pickle
        import subprocess
        import base64

        class Exploit:
          def __reduce__(self):
            return (subprocess.call, (("echo", "pwned"),))

        payload = base64.b64encode(pickle.dumps(Exploit()))

        # Applying payload, asserting that an exception is raised:
        with self.assertRaises(features.FeatureDeserializeSecurityError):
            features.BaseFeature.deserialize(payload)
