import xmlrpclib

from django.core.urlresolvers import resolve, reverse
from django.test import Client, TestCase

from mock import *

from . import views

class HandlerTest(TestCase):
    def test_root(self):
        root_url = reverse("djangopypi2-root")
        self.assertEqual(resolve(root_url).func, views.index)

    def test_simple_index(self):
        simple_index_url = reverse("djangopypi2-simple-index")
        # Need to use func_name for class-based views
        self.assertEqual(resolve(simple_index_url).func.func_name, views.SimpleIndex.as_view().func_name)

    def test_simple_package_info(self):
        simple_package_info_url = reverse("djangopypi2-simple-package-info", kwargs = {"package_name": "testPackage"})
        self.assertEqual(resolve(simple_package_info_url).func, views.simple_details)

    def test_index(self):
        index_url = reverse("djangopypi2-pypi-index")
        self.assertEqual(resolve(index_url).func, views.index)

    def test_package_detail(self):
        package_detail_url = reverse("djangopypi2-pypi-package", kwargs = {"package_name": "testPackage"})
        self.assertEqual(resolve(package_detail_url).func, views.package_details)

    def test_package_doap(self):
        package_doap_url = reverse("djangopypi2-pypi-package-doap", kwargs = {"package_name": "testPackage"})
        self.assertEqual(resolve(package_doap_url).func, views.package_doap)

    def test_release_doap(self):
        release_doap_url = reverse("djangopypi2-pypi-release-doap", kwargs = {"package_name": "testPackage", "version": "0.0"})
        self.assertEqual(resolve(release_doap_url).func, views.release_doap)

class NormalViewTest(TestCase):
    fixtures = ["test_pypi_frontend"]

    def _get_and_basic_check(self, url, status_code):
        client = Client()
        response = client.get(url)
        self.assertEqual(response.status_code, status_code)
        return response

    def test_root(self):
        root_url = reverse("djangopypi2-root")
        self._get_and_basic_check(root_url, 302)

    def test_simple_index(self):
        simple_index_url = reverse("djangopypi2-simple-index")
        response = self._get_and_basic_check(simple_index_url, 200)
        self.assertContains(response, "testPackage1")
        self.assertContains(response, "testPackage2")

    def test_simple_package_info_exist(self):
        simple_package_info_url = reverse("djangopypi2-simple-package-info", kwargs = {"package_name": "testPackage1"})
        response = self._get_and_basic_check(simple_package_info_url, 200)
        self.assertContains(response, "testPackage1-1.0.0.tar.gz")
    def test_simple_package_info_not_exist(self):
        not_exist_url = reverse("djangopypi2-simple-package-info", kwargs = {"package_name": "notExistPackage"})
        self._get_and_basic_check(not_exist_url, 404)

    def test_index(self):
        index_url = reverse("djangopypi2-pypi-index")
        self._get_and_basic_check(index_url, 302)

    def test_package_detail_exist(self):
        package_detail_url = reverse("djangopypi2-pypi-package", kwargs = {"package_name": "testPackage1"})
        self._get_and_basic_check(package_detail_url, 302)
    def test_package_detail_not_exist(self):
        not_exist_url = reverse("djangopypi2-pypi-package", kwargs = {"package_name": "notExistPackage"})
        self._get_and_basic_check(not_exist_url, 404)

    def test_package_doap_exist(self):
        package_doap_url = reverse("djangopypi2-pypi-package-doap", kwargs = {"package_name": "testPackage1"})
        response = self._get_and_basic_check(package_doap_url, 200)
        self.assertEqual(response["Content-Type"], "text/xml")
    def test_package_doap_not_exist(self):
        not_exist_url = reverse("djangopypi2-pypi-package-doap", kwargs = {"package_name": "notExistPackage"})
        self._get_and_basic_check(not_exist_url, 404)

    def test_release_doap_exist(self):
        release_doap_url = reverse("djangopypi2-pypi-release-doap", kwargs = {"package_name": "testPackage1", "version": "1.0.0"})
        response = self._get_and_basic_check(release_doap_url, 200)
        self.assertEqual(response["Content-Type"], "text/xml")
    def test_release_doap_package_not_exist(self):
        package_not_exist_url = reverse("djangopypi2-pypi-release-doap", kwargs = {"package_name": "notExistPackage", "version": "0.0"})
        self._get_and_basic_check(package_not_exist_url, 404)
    def test_release_doap_version_not_exist(self):
        release_not_exist_url = reverse("djangopypi2-pypi-release-doap", kwargs = {"package_name": "testPackage1", "version": "9999"})
        self._get_and_basic_check(release_not_exist_url, 404)

class XmlRpcViewTest(TestCase):
    fixtures = ["test_pypi_frontend"]
    def _post_and_basic_check(self, param, func_name, status_code):
        client = Client()
        response = client.post(reverse("djangopypi2-pypi-index"), data = xmlrpclib.dumps(param, func_name), content_type = "text/xml")
        self.assertEqual(response["Content-Type"], "text/xml")
        self.assertEqual(response.status_code, status_code)
        return response

    def test_not_exist_function(self):
        client = Client()
        response = client.post(reverse("djangopypi2-pypi-index"), data = xmlrpclib.dumps((), "notExistFunction"), content_type = "text/xml")
        self.assertEqual(response.status_code, 405)

    # Test list_packages
    def test_list_packages(self):
        response = self._post_and_basic_check((), "list_packages", 200)
        packages = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(packages) > 0)

    # Test package_releases
    def test_package_releases(self):
        response = self._post_and_basic_check(("testPackage1",), "package_releases", 200)
        releases = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(releases) > 0)
    def test_package_releases_not_exist(self):
        response = self._post_and_basic_check(("notExistPackage",), "package_releases", 200)
        releases = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(releases) == 0)
    def test_package_releases_no_release(self):
        response = self._post_and_basic_check(("testPackageNoRelease",), "package_releases", 200)
        releases = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(releases) == 0)

    # Test release_urls
    def test_release_urls(self):
        # Mock os.path.getsize to return dummy size string.
        # Called internally by distribution.content.size.
        # Needed because the actual file is not there for unit tests.
        patcher = patch("os.path.getsize")
        self.mock_getsize = patcher.start()
        self.mock_getsize.return_value = "mockSize"

        response = self._post_and_basic_check(("testPackage1", "1.0.0"), "release_urls", 200)
        releases = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(releases) > 0)
        self.assertEqual(releases[0]["filename"], "testPackage1-1.0.0.tar.gz")
        self.assertEqual(releases[0]["size"], "mockSize")
    def test_release_urls_not_exist(self):
        response = self._post_and_basic_check(("notExistPackage", "1.0.0"), "release_urls", 200)
        releases = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(releases) == 0)
    def test_release_urls_version_not_exist(self):
        response = self._post_and_basic_check(("testPackage1", "9999"), "release_urls", 200)
        releases = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(releases) == 0)
    def test_release_urls_release_not_exist(self):
        response = self._post_and_basic_check(("testPackageNoRelease", "1.0.0"), "release_urls", 200)
        releases = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(releases) == 0)

    # Test release_data
    def test_release_data(self):
        response = self._post_and_basic_check(("testPackage1", "1.0.0"), "release_data", 200)
        release_data = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(any(val for val in release_data.values()))
    def test_release_data_not_exist(self):
        response = self._post_and_basic_check(("notExistPackage", "1.0.0"), "release_data", 200)
        release_data = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(not val for val in release_data.values())
    def test_release_data_version_not_exist(self):
        response = self._post_and_basic_check(("testPackage1", "9999"), "release_data", 200)
        release_data = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(not val for val in release_data.values())
    def test_release_data_release_not_exist(self):
        response = self._post_and_basic_check(("testPackageNoRelease", "1.0.0"), "release_data", 200)
        release_data = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(not val for val in release_data.values())

    # Test search
    def test_search(self):
        response = self._post_and_basic_check(({"name": "testPackage1"},), "search", 200)
        packages = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(packages) > 0)
    def test_search_not_exist(self):
        response = self._post_and_basic_check(({"name": "notExistPackage", "summary": "notExistPackage"},), "search", 200)
        packages = xmlrpclib.loads(response.content)[0][0]
        self.assertTrue(len(packages) == 0)
