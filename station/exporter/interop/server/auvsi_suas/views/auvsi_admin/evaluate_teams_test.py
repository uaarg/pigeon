"""Tests for the evaluate_teams module."""

import json
import logging
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client


class TestEvaluateTeams(TestCase):
    """Tests the evaluate_teams view."""

    fixtures = ['testdata/sample_mission.json']

    def setUp(self):
        """Sets up the tests."""
        # Create nonadmin user
        self.nonadmin_user = User.objects.create_user(
            'testuser', 'testemail@x.com', 'testpass')
        self.nonadmin_user.save()
        self.nonadmin_client = Client()
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            'testuser2', 'testemail@x.com', 'testpass')
        self.admin_user.save()
        self.admin_client = Client()
        # Create URLs for testing
        self.login_url = reverse('auvsi_suas:login')
        self.eval_url = reverse('auvsi_suas:evaluate_teams')
        self.eval_url_csv = reverse('auvsi_suas:evaluate_teams_csv')

    def test_evaluate_teams_nonadmin(self):
        """Tests that you can only access data as admin."""
        self.client.post(self.login_url, {'username': 'testuser',
                                          'password': 'testpass'})
        response = self.client.get(self.eval_url)
        self.assertEqual(403, response.status_code)

    def test_invalid_mission(self):
        """Tests that an invalid mission ID results in error."""
        self.client.post(self.login_url, {'username': 'testuser',
                                          'password': 'testpass'})

        response = self.client.get(self.eval_url, {'mission': 100000})
        self.assertGreaterEqual(response.status_code, 400)

    def test_evaluate_teams(self):
        """Tests the eval Json method."""
        self.client.post(self.login_url, {'username': 'testuser2',
                                          'password': 'testpass'})
        response = self.client.get(self.eval_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 3)
        self.assertIn('user0', data)
        self.assertIn('user1', data)
        self.assertIn('uas_telem_times', data['user0'])

    def test_evaluate_teams_specific_team(self):
        """Tests the eval Json method on a specific team."""
        self.client.post(self.login_url, {'username': 'testuser2',
                                          'password': 'testpass'})
        response = self.client.get(self.eval_url, {'team': 53})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertIn('user0', data)
        self.assertNotIn('user1', data)

    def test_evaluate_teams_csv(self):
        """Tests the CSV method."""
        self.client.post(self.login_url, {'username': 'testuser2',
                                          'password': 'testpass'})
        response = self.client.get(self.eval_url_csv)
        self.assertEqual(response.status_code, 200)
        csv_data = response.content
        self.assertEqual(len(csv_data.split('\n')), 5)
        self.assertIn('username', csv_data)
        self.assertIn('uas_telem_times.max', csv_data)
        self.assertIn('user0', csv_data)
        self.assertIn('user1', csv_data)
