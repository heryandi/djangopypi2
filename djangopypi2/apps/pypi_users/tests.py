from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.urlresolvers import resolve, reverse
from django.test import Client, TestCase

from . import views

class ListViewTest(TestCase):
    fixtures = ["test_pypi_users"]
    list_user_url = reverse("djangopypi2-users")

    def test_handler(self):
        self.assertEqual(resolve(self.list_user_url).func.func_name, views.Index.as_view().func_name)

    def test_list(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(self.list_user_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("user1", response.content)
        self.assertIn("user2", response.content)

    def test_list_not_logged_in(self):
        client = Client()
        response = client.get(self.list_user_url)
        self.assertEqual(response.status_code, 302)

class UserDetailTest(TestCase):
    fixtures = ["test_pypi_users"]
    def test_handler(self):
        user_profile_url = reverse("djangopypi2-user-profile", kwargs = {"username": "anyUser"})
        self.assertEqual(resolve(user_profile_url).func.func_name, views.UserDetails.as_view().func_name)

    def test_user_detail(self):
        user_profile_url = reverse("djangopypi2-user-profile", kwargs = {"username": "user2"})
        client = Client()
        result = client.login(username="user1", password="password")
        response = client.get(user_profile_url, follow = True)
        self.assertEqual(response.status_code, 200)
        # Make sure user2's details are shown, not user1's
        self.assertIn("user2@user.com", response.content)
        self.assertNotIn("user1@user.com", response.content)

    def test_user_detail_user_not_exist(self):
        user_profile_url = reverse("djangopypi2-user-profile", kwargs = {"username": "notExistUser"})
        client = Client()
        result = client.login(username="user1", password="password")
        response = client.get(user_profile_url, follow = True)
        self.assertEqual(response.status_code, 404)

    def test_user_detail_not_logged_in(self):
        user_profile_url = reverse("djangopypi2-user-profile", kwargs = {"username": "user2"})
        client = Client()
        response = client.get(user_profile_url)
        self.assertEqual(response.status_code, 302)
