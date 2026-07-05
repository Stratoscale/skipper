import logging
import os
import unittest
from unittest import mock

from skipper import utils

utils.configure_logging("skipper-test", logging.WARNING)


class TestUtils(unittest.TestCase):
    @mock.patch("skipper.utils.which", autospec=False)
    def test_get_runtime_command(self, find_executable_mock):
        utils.CONTAINER_RUNTIME_COMMAND = None
        find_executable_mock.side_effect = "done"
        res = utils.get_runtime_command()
        self.assertEqual(res, utils.DOCKER)
        find_executable_mock.side_effect = [None, "done"]
        utils.CONTAINER_RUNTIME_COMMAND = None
        res = utils.get_runtime_command()
        self.assertEqual(res, utils.PODMAN)
        with self.assertRaises(Exception):
            find_executable_mock.side_effect = [None, None]
            utils.CONTAINER_RUNTIME_COMMAND = None
            utils.get_runtime_command()
        utils.CONTAINER_RUNTIME_COMMAND = utils.DOCKER
        res = utils.get_runtime_command()
        self.assertEqual(res, utils.DOCKER)

    @mock.patch("skipper.utils.open", autospec=False)
    @mock.patch("skipper.utils.os.makedirs", autospec=True)
    @mock.patch("skipper.utils.os.path.exists", autospec=True)
    def test_create_path_and_add_data(self, path_exists_mock, makedir_mock, open_mock):
        test_dir = "/home/test"
        test_file = os.path.join(test_dir, "test_file.txt")
        path_exists_mock.return_value = False
        utils.create_path_and_add_data(test_file, "", False)
        makedir_mock.assert_called_once_with(test_dir)
        open_mock.assert_not_called()

        makedir_mock.reset_mock()
        test_file = os.path.join(test_dir, "test_file.txt")
        path_exists_mock.return_value = True
        utils.create_path_and_add_data(test_file, "", False)
        makedir_mock.assert_not_called()
        open_mock.assert_not_called()

        test_file = os.path.join(test_dir, "test_file.txt")
        path_exists_mock.return_value = True
        utils.create_path_and_add_data(test_file, "", True)
        makedir_mock.assert_not_called()
        open_mock.assert_called_once_with(test_file, "w")

    @mock.patch("skipper.utils.get_image_digest", autospec=True, return_value="sha256:abc")
    @mock.patch("skipper.utils.requests", autospec=True)
    def test_delete_image_from_registry_fetches_token_with_get(self, requests_mock, _digest_mock):
        challenge = (
            'Bearer realm="https://registry/service/token",'
            'service="harbor-registry",scope="repository:foo/bar:pull,delete"'
        )
        unauthorized = mock.Mock(status_code=401, headers={"WWW-Authenticate": challenge})
        accepted = mock.Mock(status_code=202)
        requests_mock.delete.side_effect = [unauthorized, accepted]
        token_response = mock.Mock(status_code=200)
        token_response.json.return_value = {"token": "TKN"}
        requests_mock.get.return_value = token_response

        utils.delete_image_from_registry("registry", "foo/bar", "t1", "user", "password")

        # Token fetched via GET against the realm, never via DELETE.
        token_call = requests_mock.get.call_args
        self.assertEqual(token_call.kwargs["url"], "https://registry/service/token")
        # Final manifest DELETE carries the bearer token obtained above.
        final_delete = requests_mock.delete.call_args
        self.assertEqual(final_delete.kwargs["headers"]["Authorization"], "Bearer TKN")

    @mock.patch("skipper.utils.requests", autospec=True)
    def test_get_image_digest_accepts_oci_manifests(self, requests_mock):
        response = mock.Mock(status_code=200, headers={"Docker-Content-Digest": "sha256:abc"})
        requests_mock.get.return_value = response

        digest = utils.get_image_digest("registry", "foo/bar", "t1", "user", "password")

        self.assertEqual(digest, "sha256:abc")
        accept = requests_mock.get.call_args.kwargs["headers"]["Accept"]
        self.assertIn("application/vnd.oci.image.manifest.v1+json", accept)
        self.assertIn("application/vnd.docker.distribution.manifest.v2+json", accept)

    @mock.patch("skipper.utils.requests", autospec=True)
    def test_get_remote_image_info_tolerates_harbor_bad_request(self, requests_mock):
        response = mock.Mock(ok=False)
        response.json.return_value = {"errors": [{"code": "BAD_REQUEST", "message": "invalid repository name"}]}
        requests_mock.get.return_value = response

        self.assertEqual(utils.get_remote_image_info("bare-name", "registry", "user", "password"), [])

    @mock.patch("skipper.utils.requests", autospec=True)
    def test_get_remote_image_info_raises_on_unknown_error(self, requests_mock):
        response = mock.Mock(ok=False)
        response.json.return_value = {"errors": [{"code": "INTERNAL", "message": "boom"}]}
        requests_mock.get.return_value = response

        with self.assertRaises(RuntimeError):
            utils.get_remote_image_info("foo/bar", "registry", "user", "password")
