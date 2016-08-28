import mock
import os
import unittest
from click import testing
from skipper import commands


USER_ID = 1000
GROUP_ID = 2000

REGISTRY = 'registry.io:5000'
IMAGE = 'image'
TAG = '1234567'
FQDN_IMAGE = REGISTRY + '/' + IMAGE + ':' + TAG

WORKDIR = '/home/adir/work'
PROJECT = 'proj'
PROJECT_DIR = os.path.join(WORKDIR, PROJECT)

ENV = ["KEY1=VAL1", "KEY2=VAL2"]


class TestCommands(unittest.TestCase):
    def setUp(self):
        self._runner = testing.CliRunner()

    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('skipper.docker.build', autospec=True)
    def test_build(self, skipper_docker_build_mock, *args):
        dockerfile = IMAGE + '.Dockerfile'
        self._invoke_cli_command('build')
        skipper_docker_build_mock.assert_called_once_with(PROJECT_DIR, dockerfile, FQDN_IMAGE)

    @mock.patch('os.getuid', autospec=True, return_value=USER_ID)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('skipper.docker.run', autospec=True)
    def test_run(self, skipper_docker_run_mock, getgrnam_mock, *args):
        command = ['ls', '-l']
        getgrnam_mock.return_value.gr_gid = GROUP_ID
        self._invoke_cli_command('run', *command)
        skipper_docker_run_mock.assert_called_once_with(
            WORKDIR,
            PROJECT,
            USER_ID,
            GROUP_ID,
            FQDN_IMAGE,
            [],
            command
        )

    @mock.patch('os.getuid', autospec=True, return_value=USER_ID)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('skipper.docker.run', autospec=True)
    def test_run_with_env(self, skipper_docker_run_mock, getgrnam_mock, *args):
        command = ['ls', '-l']
        getgrnam_mock.return_value.gr_gid = GROUP_ID
        self._invoke_cli_command('run', '-e', ENV[0], '-e', ENV[1], *command)
        skipper_docker_run_mock.assert_called_once_with(
            WORKDIR,
            PROJECT,
            USER_ID,
            GROUP_ID,
            FQDN_IMAGE,
            ENV,
            command
        )

    @mock.patch('os.getuid', autospec=True, return_value=USER_ID)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('skipper.docker.run', autospec=True)
    def test_run_without_command(self, skipper_docker_run_mock, getgrnam_mock, *args):
        getgrnam_mock.return_value.gr_gid = GROUP_ID
        self._invoke_cli_command('run')
        self.assertFalse(skipper_docker_run_mock.called)

    @mock.patch('os.getuid', autospec=True, return_value=USER_ID)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('skipper.docker.run', autospec=True)
    def test_make(self, skipper_docker_run_mock, getgrnam_mock, *args):
        makefile = 'Makefile'
        target = 'all'
        getgrnam_mock.return_value.gr_gid = GROUP_ID
        self._invoke_cli_command('make', makefile, target)
        skipper_docker_run_mock.assert_called_once_with(
            WORKDIR,
            PROJECT,
            USER_ID,
            GROUP_ID,
            FQDN_IMAGE,
            [],
            ['make', '-f', makefile, target]
        )

    def _invoke_cli_command(self, cmd, *params):
        subcommand = [cmd, '--registry', REGISTRY, '--image', IMAGE, '--tag', TAG] + list(params)
        self._runner.invoke(commands.cli, subcommand)
