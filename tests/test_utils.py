import os
import unittest

import mock

from skipper import utils


class TestUtils(unittest.TestCase):

    @mock.patch('skipper.utils.find_executable', autospec=False)
    def test_get_runtime_command(self, find_executable_mock):
        utils.CONTAINER_RUNTIME_COMMAND = None
        find_executable_mock.side_effect = "done"
        res = utils.get_runtime_command()
        self.assertEquals(res, utils.DOCKER)
        find_executable_mock.side_effect = [None, "done"]
        utils.CONTAINER_RUNTIME_COMMAND = None
        res = utils.get_runtime_command()
        self.assertEquals(res, utils.PODMAN)
        with self.assertRaises(Exception):
            find_executable_mock.side_effect = [None, None]
            utils.CONTAINER_RUNTIME_COMMAND = None
            utils.get_runtime_command()
        utils.CONTAINER_RUNTIME_COMMAND = utils.DOCKER
        res = utils.get_runtime_command()
        self.assertEquals(res, utils.DOCKER)

    @mock.patch('skipper.utils.open', autospec=False)
    @mock.patch('skipper.utils.os.makedirs', autospec=True)
    @mock.patch('skipper.utils.os.path.exists', autospec=True)
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
