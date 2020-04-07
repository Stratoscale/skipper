import mock
import os
import unittest
from skipper import utils
from skipper import runner


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
