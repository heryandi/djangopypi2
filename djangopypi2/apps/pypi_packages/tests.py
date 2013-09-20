from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.files import File
from django.core.urlresolvers import resolve, reverse
from django.test import Client, TestCase

from mock import *

from . import package_views, release_views
from .models import *

class ListViewTest(TestCase):
    fixtures = ["test_pypi_package"]
    list_package_url = reverse("djangopypi2-packages-index")

    def test_handler(self):
        self.assertEqual(resolve(self.list_package_url).func.func_name, package_views.Index.as_view().func_name)

    def test_list(self):
        client = Client()
        response = client.get(self.list_package_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testPackage1")
        self.assertContains(response, "testPackage2")

    def test_search(self):
        client = Client()
        response = client.get(self.list_package_url, {"query": "package1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testPackage1")
        self.assertNotContains(response, "testPackage2")

    def test_search_not_exist(self):
        client = Client()
        response = client.get(self.list_package_url, {"query": "packageNotExist"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "testPackage1")
        self.assertNotContains(response, "testPackage2")

class AdvancedSearchTest(TestCase):
    fixtures = ["test_pypi_package"]
    search_package_url = reverse("djangopypi2-packages-search")

    def test_handler(self):
        self.assertEqual(resolve(self.search_package_url).func.func_name, package_views.advanced_search.func_name)

    def test_get(self):
        client = Client()
        response = client.get(self.search_package_url)
        self.assertEqual(response.status_code, 200)

    def test_advanced_search_name(self):
        client = Client()
        response = client.post(self.search_package_url, {"name": "testPackage1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "testPackage1")
        self.assertNotContains(response, "testPackage2")

    def test_advanced_search_name_not_exist(self):
        client = Client()
        response = client.post(self.search_package_url, {"name": "packageNotExist"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "testPackage1")
        self.assertNotContains(response, "testPackage2")

class PackageDetailTest(TestCase):
    fixtures = ["test_pypi_package"]

    def test_handler(self):
        package_url = reverse("djangopypi2-package", kwargs = {"package_name": "anyPackage"})
        self.assertEqual(resolve(package_url).func.func_name, package_views.PackageDetails.as_view().func_name)

    def test_get(self):
        package_url = reverse("djangopypi2-package", kwargs = {"package_name": "testPackage1"})
        client = Client()
        response = client.get(package_url)
        self.assertEqual(response.status_code, 200)

    def test_package_not_exist(self):
        package_url = reverse("djangopypi2-package", kwargs = {"package_name": "packageNotExist"})
        client = Client()
        response = client.get(package_url)
        self.assertEqual(response.status_code, 404)

class PackageDeleteTest(TestCase):
    fixtures = ["test_pypi_package"]

    def test_handler(self):
        package_url = reverse("djangopypi2-package-delete", kwargs = {"package_name": "anyPackage"})
        self.assertEqual(resolve(package_url).func.func_name, package_views.DeletePackage.as_view().func_name)

    def test_not_logged_in(self):
        delete_package_url = reverse("djangopypi2-package-delete", kwargs = {"package_name": "anyPackage"})
        client = Client()
        response = client.get(delete_package_url)
        self.assertEqual(response.status_code, 403)

    def test_not_owners(self):
        delete_package_url = reverse("djangopypi2-package-delete", kwargs = {"package_name": "testPackage1"})
        client = Client()
        client.login(username="user2", password="password")
        response = client.get(delete_package_url)
        self.assertEqual(response.status_code, 403)

    def test_package_not_exist(self):
        delete_package_url = reverse("djangopypi2-package-delete", kwargs = {"package_name": "packageNotExist"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(delete_package_url)
        # 403 because of user_owns_package implementation
        self.assertEqual(response.status_code, 403)

    def test_delete_success(self):
        # Need to mock os.remove because the package file doesn't actually exist
        patcher = patch("os.remove")
        self.addCleanup(patcher.stop)
        self.mock_remove = patcher.start()

        self.assertTrue(Package.objects.filter(name__exact = "testPackage1").exists())

        delete_package_url = reverse("djangopypi2-package-delete", kwargs = {"package_name": "testPackage1"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(delete_package_url)
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Package.objects.filter(name__exact = "testPackage1").exists())
        self.assertTrue(self.mock_remove.called)

class PackagePermissionTest(TestCase):
    fixtures = ["test_pypi_package"]
    package1_permission_url = reverse("djangopypi2-package-permission", kwargs = {"package_name": "testPackage1"})

    def test_handler(self):
        package_permission_url = reverse("djangopypi2-package-permission", kwargs = {"package_name": "anyPackage"})
        self.assertEqual(resolve(package_permission_url).func.func_name, package_views.PackagePermission.as_view().func_name)

    # Test add owner
    def test_add_owner_not_logged_in(self):
        client = Client()
        response = client.post(self.package1_permission_url, {"username": "user2", "action": "add", "relation": "owner"})
        self.assertEqual(response.status_code, 403)
    def test_add_owner_not_in_owners(self):
        client = Client()
        client.login(username="user2", password="password")
        response = client.post(self.package1_permission_url, {"username": "user2", "action": "add", "relation": "owner"})
        self.assertEqual(response.status_code, 403)
    def test_add_owner_user_not_exist(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "userNotExist", "action": "add", "relation": "owner"})
        self.assertEqual(response.status_code, 404)
    def test_add_owner_success(self):
        self.assertTrue(User.objects.get(username__exact="user2") not in Package.objects.get(name="testPackage1").owners.distinct())
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "user2", "action": "add", "relation": "owner"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(username__exact="user2") in Package.objects.get(name="testPackage1").owners.distinct())

    # Test delete owner, cannot delete last owner
    def test_delete_owner_last_owner(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "user1", "action": "delete", "relation": "owner"})
        self.assertEqual(response.status_code, 403)
    # Need at least 2 owners to be able to delete 1
    def _add_user2_to_owners(self):
        user2 = User.objects.get(username__exact="user2")
        p1 = Package.objects.get(name="testPackage1")
        p1.owners.add(user2)
        self.assertTrue(user2 in p1.owners.distinct())
    def test_delete_owner_not_logged_in(self):
        self._add_user2_to_owners()
        client = Client()
        response = client.post(self.package1_permission_url, {"username": "user1", "action": "delete", "relation": "owner"})
        self.assertEqual(response.status_code, 403)
    def test_delete_owner_not_in_owners(self):
        self._add_user2_to_owners()
        client = Client()
        client.login(username="user3", password="password")
        response = client.post(self.package1_permission_url, {"username": "user1", "action": "delete", "relation": "owner"})
        self.assertEqual(response.status_code, 403)
    def test_delete_owner_user_not_exist(self):
        self._add_user2_to_owners()
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "userNotExist", "action": "delete", "relation": "owner"})
        self.assertEqual(response.status_code, 404)
    def test_delete_owner_success(self):
        self._add_user2_to_owners()
        self.assertTrue(User.objects.get(username__exact="user2") in Package.objects.get(name="testPackage1").owners.distinct())
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "user2", "action": "delete", "relation": "owner"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(username__exact="user2") not in Package.objects.get(name="testPackage1").owners.distinct())

    # Test add maintainer
    def test_add_maintainer_not_logged_in(self):
        client = Client()
        response = client.post(self.package1_permission_url, {"username": "user3", "action": "add", "relation": "maintainer"})
        self.assertEqual(response.status_code, 403)
    def test_add_maintainer_not_in_owners(self):
        client = Client()
        client.login(username="user2", password="password")
        response = client.post(self.package1_permission_url, {"username": "user3", "action": "add", "relation": "maintainer"})
        self.assertEqual(response.status_code, 403)
    def test_add_maintainer_user_not_exist(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "userNotExist", "action": "add", "relation": "maintainer"})
        self.assertEqual(response.status_code, 404)
    def test_add_maintainer_success(self):
        self.assertTrue(User.objects.get(username__exact="user3") not in Package.objects.get(name="testPackage1").maintainers.distinct())
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "user3", "action": "add", "relation": "maintainer"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(username__exact="user3") in Package.objects.get(name="testPackage1").maintainers.distinct())

    # Test delete maintainer
    def test_delete_maintainer_not_logged_in(self):
        self._add_user2_to_owners()
        client = Client()
        response = client.post(self.package1_permission_url, {"username": "user2", "action": "delete", "relation": "maintainer"})
        self.assertEqual(response.status_code, 403)
    def test_delete_maintainer_not_in_owners(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.post(self.package1_permission_url, {"username": "user2", "action": "delete", "relation": "maintainer"})
        self.assertEqual(response.status_code, 403)
    def test_delete_maintainer_user_notExist(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "userNotExist", "action": "delete", "relation": "maintainer"})
        self.assertEqual(response.status_code, 404)
    def test_delete_maintainer_success(self):
        self.assertTrue(User.objects.get(username__exact="user2") in Package.objects.get(name="testPackage1").maintainers.distinct())
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.package1_permission_url, {"username": "user2", "action": "delete", "relation": "maintainer"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(username__exact="user2") not in Package.objects.get(name="testPackage1").maintainers.distinct())

class ReleaseDetailTest(TestCase):
    fixtures = ["test_pypi_package"]
    release_url = reverse("djangopypi2-release", kwargs = {"package_name": "testPackage1", "version": "1.0.0"})

    def test_handler(self):
        self.assertEqual(resolve(self.release_url).func.func_name, release_views.ReleaseDetails.as_view().func_name)

    def test_get(self):
        # Needed because the actual file is not there for unit tests.
        patcher = patch("os.path.getsize")
        self.addCleanup(patcher.stop)
        self.mock_getsize = patcher.start()
        self.mock_getsize.return_value = "mockSize"

        client = Client()
        response = client.get(self.release_url)
        self.assertEqual(response.status_code, 200)

    def test_package_not_exist(self):
        release_url = reverse("djangopypi2-release", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        response = client.get(release_url)
        self.assertEqual(response.status_code, 404)

    def test_release_not_exist(self):
        release_url = reverse("djangopypi2-release", kwargs = {"package_name": "packageNotExist", "version": "99.99.99"})
        client = Client()
        response = client.get(release_url)
        self.assertEqual(response.status_code, 404)

class ReleaseDeleteTest(TestCase):
    fixtures = ["test_pypi_package"]
    delete_release_url = reverse("djangopypi2-release-delete", kwargs = {"package_name": "testPackage1", "version": "1.0.0"})

    def test_handler(self):
        self.assertEqual(resolve(self.delete_release_url).func.func_name, release_views.DeleteRelease.as_view().func_name)

    def test_not_logged_in(self):
        client = Client()
        response = client.get(self.delete_release_url)
        self.assertEqual(response.status_code, 403)

    def test_not_owners(self):
        client = Client()
        client.login(username="user2", password="password")
        response = client.get(self.delete_release_url)
        self.assertEqual(response.status_code, 403)

    def test_package_not_exist(self):
        delete_release_url = reverse("djangopypi2-release-delete", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(delete_release_url)
        self.assertEqual(response.status_code, 403)

    def test_release_not_exist(self):
        delete_release_url = reverse("djangopypi2-release-delete", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(delete_release_url)
        self.assertEqual(response.status_code, 404)

    def test_delete_success(self):
        # Need to mock os.remove because the package file doesn't actually exist
        patcher = patch("os.remove")
        self.addCleanup(patcher.stop)
        self.mock_remove = patcher.start()

        self.assertTrue(Release.objects.filter(package__name__exact="testPackage1", version__exact="1.0.0").exists())

        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.delete_release_url)
        self.assertEqual(response.status_code, 302)

        self.assertFalse(Release.objects.filter(package__name__exact="testPackage1", version__exact="1.0.0").exists())
        self.assertTrue(self.mock_remove.called)

class ReleaseManageTest(TestCase):
    fixtures = ["test_pypi_package"]
    edit_details_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "testPackage1", "version": "1.0.0"})

    def test_handler(self):
        self.assertEqual(resolve(self.edit_details_url).func.func_name, release_views.ManageRelease.as_view().func_name)

    def test_get_not_logged_in(self):
        client = Client()
        response = client.get(self.edit_details_url)
        self.assertEquals(response.status_code, 403)
    def test_get_not_maintainers(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.get(self.edit_details_url)
        self.assertEquals(response.status_code, 403)
    def test_get_package_not_exist(self):
        edit_details_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(edit_details_url)
        self.assertEquals(response.status_code, 403)
    def test_get_release_not_exist(self):
        edit_details_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(edit_details_url)
        self.assertEquals(response.status_code, 404)
    def test_get_success(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(self.edit_details_url)
        self.assertEquals(response.status_code, 200)

    def test_post_not_logged_in(self):
        client = Client()
        response = client.post(self.edit_details_url)
        self.assertEquals(response.status_code, 403)
    def test_post_not_maintainers(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.post(self.edit_details_url, {"hidden": "1"})
        self.assertEquals(response.status_code, 403)
    def test_post_package_not_exist(self):
        edit_details_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(edit_details_url, {"hidden": "1"})
        self.assertEquals(response.status_code, 403)
    def test_post_release_not_exist(self):
        edit_details_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(edit_details_url, {"hidden": "1"})
        self.assertEquals(response.status_code, 404)
    def test_post_success(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(self.edit_details_url, {"metadata_version": "1.2"})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Release.objects.filter(package__name__exact="testPackage1", version__exact="1.0.0")[0].metadata_version, "1.2")

class ReleaseManageMetadata(TestCase):
    fixtures = ["test_pypi_package"]
    edit_metadata_url = reverse("djangopypi2-release-edit-metadata", kwargs = {"package_name": "testPackage1", "version": "1.0.0"})

    def test_handler(self):
        self.assertEqual(resolve(self.edit_metadata_url).func.func_name, release_views.manage_metadata.func_name)

    def test_get_not_logged_in(self):
        client = Client()
        response = client.get(self.edit_metadata_url)
        self.assertEquals(response.status_code, 403)
    def test_get_not_maintainers(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.get(self.edit_metadata_url)
        self.assertEquals(response.status_code, 403)
    def test_get_package_not_exist(self):
        edit_metadata_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(edit_metadata_url)
        self.assertEquals(response.status_code, 403)
    def test_get_release_not_exist(self):
        edit_metadata_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(edit_metadata_url)
        self.assertEquals(response.status_code, 404)
    def test_get_success(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(self.edit_metadata_url)
        self.assertEquals(response.status_code, 200)

    def test_post_not_logged_in(self):
        client = Client()
        response = client.post(self.edit_metadata_url)
        self.assertEquals(response.status_code, 403)
    def test_post_not_maintainers(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.post(self.edit_metadata_url)
        self.assertEquals(response.status_code, 403)
    def test_post_package_not_exist(self):
        edit_metadata_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(edit_metadata_url)
        self.assertEquals(response.status_code, 403)
    def test_post_release_not_exist(self):
        edit_metadata_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(edit_metadata_url)
        self.assertEquals(response.status_code, 404)
    def test_post_success(self):
        client = Client()
        client.login(username="user1", password="password")
        data = {
            "keywords": "test",
            "author_email": "user1@user.com",
            "license": "BSD",
            "summary": "test summary"
        }
        response = client.post(self.edit_metadata_url, data)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(Release.objects.filter(package__name__exact="testPackage1", version__exact="1.0.0")[0].summary, "test summary")

class ReleaseManageFile(TestCase):
    fixtures = ["test_pypi_package"]
    manage_file_url = reverse("djangopypi2-release-manage-files", kwargs = {"package_name": "testPackage1", "version": "1.0.0"})

    def test_handler(self):
        self.assertEqual(resolve(self.manage_file_url).func.func_name, release_views.manage_files.func_name)

    def test_get_not_logged_in(self):
        client = Client()
        response = client.get(self.manage_file_url)
        self.assertEquals(response.status_code, 403)
    def test_get_not_maintainers(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.get(self.manage_file_url)
        self.assertEquals(response.status_code, 403)
    def test_get_package_not_exist(self):
        manage_file_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(manage_file_url)
        self.assertEquals(response.status_code, 403)
    def test_get_release_not_exist(self):
        manage_file_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(manage_file_url)
        self.assertEquals(response.status_code, 404)
    def test_get_success(self):
        # Needed because the actual file is not there for unit tests.
        patcher = patch("os.path.getsize")
        self.addCleanup(patcher.stop)
        self.mock_getsize = patcher.start()
        self.mock_getsize.return_value = "mockSize"

        client = Client()
        client.login(username="user1", password="password")
        response = client.get(self.manage_file_url)
        self.assertEquals(response.status_code, 200)

    def test_post_not_logged_in(self):
        client = Client()
        response = client.post(self.manage_file_url)
        self.assertEquals(response.status_code, 403)
    def test_post_not_maintainers(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.post(self.manage_file_url)
        self.assertEquals(response.status_code, 403)
    def test_post_package_not_exist(self):
        manage_file_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(manage_file_url)
        self.assertEquals(response.status_code, 403)
    def test_post_release_not_exist(self):
        manage_file_url = reverse("djangopypi2-release-edit-details", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(manage_file_url)
        self.assertEquals(response.status_code, 404)
    def test_post_success(self):
        # Needed because the actual file is not there for unit tests.
        patcher = patch("os.path.getsize")
        self.addCleanup(patcher.stop)
        self.mock_getsize = patcher.start()
        self.mock_getsize.return_value = "mockSize"

        client = Client()
        client.login(username="user1", password="password")
        data = {
            "distributions-TOTAL_FORMS": 1,
            "distributions-INITIAL_FORMS": 1,
            "distributions-MAX_NUM_FORMS": 1000,
            "distributions-0-id": 1,
            "distributions-0-release": 1,
            "distributions-0-comment": "test comment"
        }
        response = client.post(self.manage_file_url, data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(Distribution.objects.get(id=1).comment, "test comment")

class ReleaseUploadFile(TestCase):
    fixtures = ["test_pypi_package"]
    upload_file_url = reverse("djangopypi2-release-upload-file", kwargs = {"package_name": "testPackage1", "version": "1.0.0"})

    def test_handler(self):
        self.assertEqual(resolve(self.upload_file_url).func.func_name, release_views.upload_file.func_name)

    def test_get_not_logged_in(self):
        client = Client()
        response = client.get(self.upload_file_url)
        self.assertEquals(response.status_code, 403)
    def test_get_not_maintainers(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.get(self.upload_file_url)
        self.assertEquals(response.status_code, 403)
    def test_get_package_not_exist(self):
        upload_file_url = reverse("djangopypi2-release-upload-file", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(upload_file_url)
        self.assertEquals(response.status_code, 403)
    def test_get_release_not_exist(self):
        upload_file_url = reverse("djangopypi2-release-upload-file", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(upload_file_url)
        self.assertEquals(response.status_code, 404)
    def test_get_success(self):
        client = Client()
        client.login(username="user1", password="password")
        response = client.get(self.upload_file_url)
        self.assertEquals(response.status_code, 200)

    def test_post_not_logged_in(self):
        client = Client()
        response = client.post(self.upload_file_url)
        self.assertEquals(response.status_code, 403)
    def test_post_not_maintainers(self):
        client = Client()
        client.login(username="user3", password="password")
        response = client.post(self.upload_file_url)
        self.assertEquals(response.status_code, 403)
    def test_post_package_not_exist(self):
        upload_file_url = reverse("djangopypi2-release-upload-file", kwargs = {"package_name": "packageNotExist", "version": "1.0.0"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(upload_file_url)
        self.assertEquals(response.status_code, 403)
    def test_post_release_not_exist(self):
        upload_file_url = reverse("djangopypi2-release-upload-file", kwargs = {"package_name": "testPackage1", "version": "99.99.99"})
        client = Client()
        client.login(username="user1", password="password")
        response = client.post(upload_file_url)
        self.assertEquals(response.status_code, 404)

    # Need to mock save() function so no file will actually get saved to disk
    @patch.object(Distribution, "save")
    def test_post_success(self, mock_save):
        client = Client()
        client.login(username="user1", password="password")

        # Hack to make the setting available on unit tests
        from django.conf import settings
        settings.DJANGOPYPI_ALLOW_VERSION_OVERWRITE = False

        # Create mock File
        mock_file = Mock(spec=File)
        mock_file.name = "mock object"
        mock_file.read.return_value = "fake file contents"
        data = {
            "content": mock_file,
            "comment": "test comment",
            "filetype": "sdist",
            "pyversion": 1
        }
        response = client.post(self.upload_file_url, data)
        self.assertEquals(response.status_code, 302)
