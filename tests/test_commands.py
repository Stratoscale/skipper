import mock
import os
import unittest
from click import testing
from skipper import commands


REGISTRY = 'registry.io:5000'
IMAGE = 'image'
TAG = '1234567'
FQDN_IMAGE = REGISTRY + '/' + IMAGE + ':' + TAG

ENV = ["KEY1=VAL1", "KEY2=VAL2"]


class TestCommands(unittest.TestCase):
    def setUp(self):
        self._runner = testing.CliRunner()

    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_build(self, skipper_runner_run_mock, *args):
        dockerfile = IMAGE + '.Dockerfile'
        self._invoke_cli_command('build', IMAGE)
        expected_command = [
            'docker',
            'build',
            '-f', dockerfile,
            '-t', FQDN_IMAGE,
            '.'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=FQDN_IMAGE)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_run(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        self._invoke_cli_command('run', *command)
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=FQDN_IMAGE, environment=[])

    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_env(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        self._invoke_cli_command('run', '-e', ENV[0], '-e', ENV[1], *command)
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=FQDN_IMAGE, environment=ENV)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_without_command(self, skipper_runner_run_mock):
        self._invoke_cli_command('run')
        self.assertFalse(skipper_runner_run_mock.called)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_make(self, skipper_runner_run_mock):
        makefile = 'Makefile'
        target = 'all'
        self._invoke_cli_command('make', '-f', makefile, target)
        expected_command = ['make', '-f', makefile, target]
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=FQDN_IMAGE, environment=[])

    def _invoke_cli_command(self, cmd, *params):
        global_opts = ['--registry', REGISTRY, '--image', IMAGE, '--tag', TAG]
        subcommand = [cmd] + list(params)
        self._runner.invoke(commands.cli, global_opts + subcommand, obj={})
