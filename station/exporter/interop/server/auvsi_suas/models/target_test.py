"""Tests for the target module."""

import os.path
from auvsi_suas.models.gps_position import GpsPosition
from auvsi_suas.models.mission_clock_event import MissionClockEvent
from auvsi_suas.models.takeoff_or_landing_event import TakeoffOrLandingEvent
from auvsi_suas.models.target import Color
from auvsi_suas.models.target import Target
from auvsi_suas.models.target import TargetEvaluator
from auvsi_suas.models.target import TargetType
from auvsi_suas.models.target import Shape
from auvsi_suas.models.target import Orientation
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone


class TestTarget(TestCase):
    """Tests for the Target model."""

    def setUp(self):
        """Sets up the tests."""
        super(TestTarget, self).setUp()
        self.user = User.objects.create_user('user', 'email@example.com',
                                             'pass')

    def test_valid(self):
        """Test creating a valid target."""
        with open(os.path.join(settings.BASE_DIR,
                               'auvsi_suas/fixtures/testdata/S.jpg')) as f:
            thumb = SimpleUploadedFile('thumb.jpg', f.read())

        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user,
                   target_type=TargetType.standard,
                   location=l,
                   orientation=Orientation.s,
                   shape=Shape.square,
                   background_color=Color.white,
                   alphanumeric='ABC',
                   alphanumeric_color=Color.black,
                   description='Test target',
                   thumbnail=thumb)
        t.save()

    def test_unicode(self):
        """Test unicode conversion."""
        with open(os.path.join(settings.BASE_DIR,
                               'auvsi_suas/fixtures/testdata/S.jpg')) as f:
            thumb = SimpleUploadedFile('thumb.jpg', f.read())

        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user,
                   target_type=TargetType.standard,
                   location=l,
                   orientation=Orientation.s,
                   shape=Shape.square,
                   background_color=Color.white,
                   alphanumeric='ABC',
                   alphanumeric_color=Color.black,
                   description='Test target',
                   thumbnail=thumb)
        t.save()

        self.assertTrue(t.__unicode__())

    def test_minimal_unicode(self):
        """Unicode with only user and target."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        self.assertTrue(t.__unicode__())

    def test_null_fields(self):
        """Only user and target type."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

    def test_creation_time(self):
        """Creation time is set on creation and doesn't change on update."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        orig = t.creation_time
        self.assertIsNotNone(orig)

        t.alphanumeric = 'A'
        t.save()

        self.assertEqual(orig, t.creation_time)

    def test_last_modified_time(self):
        """Last modified time is set on creation and changes every update."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        orig = t.last_modified_time
        self.assertIsNotNone(orig)

        t.alphanumeric = 'A'
        t.save()

        self.assertGreater(t.last_modified_time, orig)

    def test_json(self):
        """Test target JSON."""
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()

        t = Target(user=self.user,
                   target_type=TargetType.standard,
                   location=l,
                   orientation=Orientation.s,
                   shape=Shape.square,
                   background_color=Color.white,
                   alphanumeric='ABC',
                   alphanumeric_color=Color.black,
                   description='Test target',
                   autonomous=True)
        t.save()

        d = t.json()

        self.assertIn('id', d)
        self.assertEqual(self.user.pk, d['user'])
        self.assertEqual('standard', d['type'])
        self.assertEqual(38, d['latitude'])
        self.assertEqual(-76, d['longitude'])
        self.assertEqual('s', d['orientation'])
        self.assertEqual('square', d['shape'])
        self.assertEqual('white', d['background_color'])
        self.assertEqual('ABC', d['alphanumeric'])
        self.assertEqual('black', d['alphanumeric_color'])
        self.assertEqual('Test target', d['description'])
        self.assertEqual(True, d['autonomous'])
        self.assertNotIn('thumbnail_approved', d)

        d = t.json(is_superuser=True)
        self.assertIn('thumbnail_approved', d)

        t.thumbnail_approved = True
        t.save()
        d = t.json(is_superuser=True)
        self.assertEqual(None, d['thumbnail'])
        self.assertEqual(True, d['thumbnail_approved'])

    def test_minimal_json(self):
        """Test target JSON with minimal data."""
        t = Target(user=self.user, target_type=TargetType.standard)
        t.save()

        d = t.json()

        self.assertIn('id', d)
        self.assertEqual(self.user.pk, d['user'])
        self.assertEqual('standard', d['type'])
        self.assertEqual(None, d['latitude'])
        self.assertEqual(None, d['longitude'])
        self.assertEqual(None, d['orientation'])
        self.assertEqual(None, d['shape'])
        self.assertEqual(None, d['background_color'])
        self.assertEqual(None, d['alphanumeric'])
        self.assertEqual(None, d['alphanumeric_color'])
        self.assertEqual(None, d['description'])
        self.assertEqual(False, d['autonomous'])

    def test_similar_classifications(self):
        """Tests similar classification counts are computed correctly."""
        # Test equal standard targets.
        l = GpsPosition(latitude=38, longitude=-76)
        l.save()
        t1 = Target(user=self.user,
                    target_type=TargetType.standard,
                    location=l,
                    orientation=Orientation.s,
                    shape=Shape.square,
                    background_color=Color.white,
                    alphanumeric='ABC',
                    alphanumeric_color=Color.black,
                    description='Test target',
                    autonomous=True)
        t1.save()
        t2 = Target(user=self.user,
                    target_type=TargetType.standard,
                    location=l,
                    orientation=Orientation.s,
                    shape=Shape.square,
                    background_color=Color.white,
                    alphanumeric='ABC',
                    alphanumeric_color=Color.black,
                    description='Test other target',
                    autonomous=True)
        t2.save()
        self.assertAlmostEqual(1.0, t1.similar_classifications(t2))

        # Test unequal standard targets.
        t1.alphanumeric = 'DEF'
        t1.alphanumeric_color = Color.blue
        t1.save()
        self.assertAlmostEqual(3.0 / 5.0, t1.similar_classifications(t2))
        t1.shape = Shape.circle
        t1.background_color = Color.orange
        t1.save()
        self.assertAlmostEqual(1.0 / 5.0, t1.similar_classifications(t2))

        # Test different types.
        t1.target_type = TargetType.off_axis
        t1.save()
        self.assertAlmostEqual(0, t1.similar_classifications(t2))

        # Test off_axis is same as standard.
        t2.target_type = TargetType.off_axis
        t2.alphanumeric = 'DEF'
        t2.save()
        self.assertAlmostEqual(2.0 / 5.0, t1.similar_classifications(t2))

        # Test emergent type is always 1.
        t1.target_type = TargetType.emergent
        t1.save()
        t2.target_type = TargetType.emergent
        t2.save()
        self.assertAlmostEqual(1.0, t1.similar_classifications(t2))

    def test_actionable_submission(self):
        """Tests actionable_submission correctly filters submissions."""
        # t1 created and updated before take off.
        t1 = Target(user=self.user, target_type=TargetType.standard)
        t1.save()
        t1.alphanumeric = 'A'
        t1.save()

        # t2 created before take off and updated in flight.
        t2 = Target(user=self.user, target_type=TargetType.standard)
        t2.save()

        event = TakeoffOrLandingEvent(user=self.user, uas_in_air=True)
        event.save()

        t2.alphanumeric = 'A'
        t2.save()

        # t3 created and updated in flight.
        t3 = Target(user=self.user, target_type=TargetType.standard)
        t3.save()
        t3.alphanumeric = 'A'
        t3.save()

        # t4 created in flight and updated after landing.
        t4 = Target(user=self.user, target_type=TargetType.standard)
        t4.save()

        event = TakeoffOrLandingEvent(user=self.user, uas_in_air=False)
        event.save()

        t4.alphanumeric = 'A'
        t4.save()

        # t5 created and updated after landing.
        t5 = Target(user=self.user, target_type=TargetType.standard)
        t5.save()
        t5.alphanumeric = 'A'
        t5.save()

        # t6 created and updated in second flight.
        event = TakeoffOrLandingEvent(user=self.user, uas_in_air=True)
        event.save()
        t6 = Target(user=self.user, target_type=TargetType.standard)
        t6.save()
        t6.alphanumeric = 'A'
        t6.save()
        event = TakeoffOrLandingEvent(user=self.user, uas_in_air=False)
        event.save()

        self.assertFalse(t1.actionable_submission())
        self.assertFalse(t2.actionable_submission())
        self.assertTrue(t3.actionable_submission())
        self.assertFalse(t4.actionable_submission())
        self.assertFalse(t5.actionable_submission())
        self.assertFalse(t6.actionable_submission())

    def test_interop_submission(self):
        """Tests interop_submission correctly filters submissions."""
        # t1 created and updated before mission time starts.
        t1 = Target(user=self.user, target_type=TargetType.standard)
        t1.save()
        t1.alphanumeric = 'A'
        t1.save()

        # t2 created before mission time starts and updated once it does.
        t2 = Target(user=self.user, target_type=TargetType.standard)
        t2.save()

        # Mission time starts.
        event = MissionClockEvent(user=self.user,
                                  team_on_clock=True,
                                  team_on_timeout=False)
        event.save()

        t2.alphanumeric = 'A'
        t2.save()

        # t3 created and updated during mission time.
        t3 = Target(user=self.user, target_type=TargetType.standard)
        t3.save()
        t3.alphanumeric = 'A'
        t3.save()

        # t4 created in in mission time and updated during timeout.
        t4 = Target(user=self.user, target_type=TargetType.standard)
        t4.save()

        # Team takes timeout. Mission time stops.
        event = MissionClockEvent(user=self.user,
                                  team_on_clock=False,
                                  team_on_timeout=True)
        event.save()

        t4.alphanumeric = 'A'
        t4.save()

        # t5 created and updated during timeout.
        t5 = Target(user=self.user, target_type=TargetType.standard)
        t5.save()
        t5.alphanumeric = 'A'
        t5.save()

        # t6 created and updated once mission time resumes.
        event = MissionClockEvent(user=self.user,
                                  team_on_clock=True,
                                  team_on_timeout=False)
        event.save()
        t6 = Target(user=self.user, target_type=TargetType.standard)
        t6.save()
        t6.alphanumeric = 'A'
        t6.save()
        event = MissionClockEvent(user=self.user,
                                  team_on_clock=False,
                                  team_on_timeout=False)
        event.save()

        self.assertFalse(t1.interop_submission())
        self.assertFalse(t2.interop_submission())
        self.assertTrue(t3.interop_submission())
        self.assertFalse(t4.interop_submission())
        self.assertFalse(t5.interop_submission())
        self.assertTrue(t6.interop_submission())


class TestTargetEvaluator(TestCase):
    """Tests for the TargetEvaluator."""

    def setUp(self):
        """Setup the test case."""
        super(TestTargetEvaluator, self).setUp()
        self.maxDiff = None
        self.user = User.objects.create_user('user', 'email@example.com',
                                             'pass')

        l1 = GpsPosition(latitude=38, longitude=-76)
        l1.save()
        l2 = GpsPosition(latitude=38.0003, longitude=-76)
        l2.save()
        l3 = GpsPosition(latitude=-38, longitude=76)
        l3.save()

        event = MissionClockEvent(user=self.user,
                                  team_on_clock=True,
                                  team_on_timeout=False)
        event.save()

        event = TakeoffOrLandingEvent(user=self.user, uas_in_air=True)
        event.save()

        # A target worth full points.
        self.submit1 = Target(user=self.user,
                              target_type=TargetType.standard,
                              location=l1,
                              orientation=Orientation.s,
                              shape=Shape.square,
                              background_color=Color.white,
                              alphanumeric='ABC',
                              alphanumeric_color=Color.black,
                              description='Submit test target 1',
                              autonomous=True,
                              thumbnail_approved=True)
        self.submit1.save()
        self.real1 = Target(user=self.user,
                            target_type=TargetType.standard,
                            location=l1,
                            orientation=Orientation.s,
                            shape=Shape.square,
                            background_color=Color.white,
                            alphanumeric='ABC',
                            alphanumeric_color=Color.black,
                            description='Real target 1')
        self.real1.save()

        event = MissionClockEvent(user=self.user,
                                  team_on_clock=False,
                                  team_on_timeout=False)
        event.save()

        # A target worth less than full points.
        self.submit2 = Target(user=self.user,
                              target_type=TargetType.standard,
                              location=l1,
                              orientation=Orientation.n,
                              shape=Shape.circle,
                              background_color=Color.white,
                              # alphanumeric set below
                              alphanumeric_color=Color.black,
                              description='Submit test target 2',
                              autonomous=False,
                              thumbnail_approved=True)
        self.submit2.save()
        self.real2 = Target(user=self.user,
                            target_type=TargetType.standard,
                            location=l2,
                            orientation=Orientation.s,
                            shape=Shape.triangle,
                            background_color=Color.white,
                            alphanumeric='ABC',
                            alphanumeric_color=Color.black,
                            description='Real test target 2')
        self.real2.save()

        # A target worth no points, so unmatched.
        self.submit3 = Target(user=self.user,
                              target_type=TargetType.standard,
                              location=l1,
                              orientation=Orientation.nw,
                              shape=Shape.pentagon,
                              background_color=Color.gray,
                              alphanumeric='XYZ',
                              alphanumeric_color=Color.orange,
                              description='Incorrect description',
                              autonomous=False,
                              thumbnail_approved=True)
        self.submit3.save()
        self.real3 = Target(user=self.user,
                            target_type=TargetType.standard,
                            orientation=Orientation.e,
                            shape=Shape.semicircle,
                            background_color=Color.yellow,
                            alphanumeric='LMN',
                            # alphanumeric_color set below
                            location=l3,
                            description='Test target 3')
        self.real3.save()

        # Targets without approved image may still match.
        self.submit4 = Target(user=self.user,
                              target_type=TargetType.emergent,
                              location=l1,
                              description='Test target 4',
                              autonomous=False,
                              thumbnail_approved=False)
        self.submit4.save()
        self.real4 = Target(user=self.user,
                            target_type=TargetType.emergent,
                            location=l1,
                            description='Test target 4')
        self.real4.save()

        # A target without location worth fewer points.
        self.submit5 = Target(user=self.user,
                              target_type=TargetType.standard,
                              orientation=Orientation.n,
                              shape=Shape.trapezoid,
                              background_color=Color.purple,
                              alphanumeric='PQR',
                              alphanumeric_color=Color.blue,
                              description='Test target 5',
                              autonomous=False,
                              thumbnail_approved=True)
        self.submit5.save()
        self.real5 = Target(user=self.user,
                            target_type=TargetType.standard,
                            location=l1,
                            orientation=Orientation.n,
                            shape=Shape.trapezoid,
                            background_color=Color.purple,
                            alphanumeric='PQR',
                            alphanumeric_color=Color.blue,
                            description='Test target 5')
        self.real5.save()

        event = TakeoffOrLandingEvent(user=self.user, uas_in_air=False)
        event.save()

        # submit2 updated after landing.
        self.submit2.alphanumeric = 'ABC'
        self.submit2.save()

        self.submit3.alphanumeric_color = Color.yellow
        self.submit3.save()

        self.submitted_targets = [self.submit5, self.submit4, self.submit3,
                                  self.submit2, self.submit1]
        self.real_targets = [self.real1, self.real2, self.real3, self.real4,
                             self.real5]
        self.real_matched_targets = [self.real1, self.real2, self.real4,
                                     self.real5]

    def test_match_value(self):
        """Tests the match value for two targets."""
        e = TargetEvaluator(self.submitted_targets, self.real_targets)
        self.assertAlmostEqual(1,
                               e.match_value(self.submit1, self.real1),
                               places=3)
        self.assertAlmostEqual(0.174,
                               e.match_value(self.submit2, self.real2),
                               places=3)
        self.assertAlmostEqual(0.0,
                               e.match_value(self.submit3, self.real3),
                               places=3)
        self.assertAlmostEqual(0.5,
                               e.match_value(self.submit4, self.real4),
                               places=3)
        self.assertAlmostEqual(0.3,
                               e.match_value(self.submit5, self.real5),
                               places=3)

        self.assertAlmostEqual(0.814,
                               e.match_value(self.submit1, self.real2),
                               places=3)
        self.assertAlmostEqual(0.32,
                               e.match_value(self.submit2, self.real1),
                               places=3)

    def test_match_targets(self):
        """Tests that matching targets produce maximal matches."""
        e = TargetEvaluator(self.submitted_targets, self.real_targets)
        self.assertEqual(
            {
                self.submit1: self.real1,
                self.submit2: self.real2,
                self.submit4: self.real4,
                self.submit5: self.real5,
                self.real1: self.submit1,
                self.real2: self.submit2,
                self.real4: self.submit4,
                self.real5: self.submit5,
            }, e.match_targets(self.submitted_targets, self.real_targets))

    def test_evaluation_dict(self):
        """Tests that the evaluation dictionary is generated correctly."""
        e = TargetEvaluator(self.submitted_targets, self.real_targets)
        d = e.evaluation_dict()

        self.assertIn('matched_target_value', d)
        self.assertIn('unmatched_target_count', d)
        self.assertIn('targets', d)
        for t in d['targets'].values():
            keys = ['match_value', 'image_approved', 'classifications',
                    'location_accuracy', 'actionable', 'interop_submission']
            for key in keys:
                self.assertIn(key, t)
        for s in self.real_targets:
            self.assertIn(s.pk, d['targets'].keys())

        self.assertAlmostEqual(1.974, d['matched_target_value'], places=3)
        self.assertEqual(1, d['unmatched_target_count'])
        self.assertEqual(self.submit1.pk,
                         d['targets'][self.real1.pk]['submitted_target'])
        self.assertAlmostEqual(1.0,
                               d['targets'][self.real1.pk]['match_value'],
                               places=3)
        self.assertEqual(True, d['targets'][self.real1.pk]['image_approved'])
        self.assertEqual(1.0, d['targets'][self.real1.pk]['classifications'])
        self.assertEqual(0.0, d['targets'][self.real1.pk]['location_accuracy'])
        self.assertEqual(True, d['targets'][self.real1.pk]['actionable'])
        self.assertEqual(True,
                         d['targets'][self.real1.pk]['interop_submission'])

        self.assertEqual(False, d['targets'][self.real2.pk]['actionable'])
        self.assertEqual(False,
                         d['targets'][self.real2.pk]['interop_submission'])

    def test_evaluation_dict_no_submitted_targets(self):
        """Tests that evaluation_dict works with no submitted targets."""
        e = TargetEvaluator([], self.real_targets)
        d = e.evaluation_dict()

        self.assertEqual(0, d['matched_target_value'])
        self.assertEqual(0, d['unmatched_target_count'])
        for td in d['targets'].values():
            for v in td.values():
                self.assertEqual('', v)

    def test_evaluation_dict_no_real_targets(self):
        """Tests that evaluation_dict works with no real targets."""
        e = TargetEvaluator(self.submitted_targets, [])
        d = e.evaluation_dict()

        self.assertEqual(0, d['matched_target_value'])
        self.assertEqual(5, d['unmatched_target_count'])
        self.assertEqual({}, d['targets'])
