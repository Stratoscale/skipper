import mock
import os
import unittest
import click
from click import testing
from skipper import cli


REGISTRY = 'registry.io:5000'
IMAGE = 'image'
TAG = '1234567'
FQDN_IMAGE = REGISTRY + '/' + IMAGE + ':' + TAG

BUILD_CONTAINER_IMAGE = 'build-container-image'
BUILD_CONTAINER_TAG = 'build-container-tag'
BUILD_CONTAINER_FQDN_IMAGE = REGISTRY + '/' + BUILD_CONTAINER_IMAGE + ':' + BUILD_CONTAINER_TAG

ENV = ["KEY1=VAL1", "KEY2=VAL2"]


class TestCLI(unittest.TestCase):
    def setUp(self):
        self._runner = testing.CliRunner()
        self.global_params = [
            '--registry', REGISTRY,
            '--build-container-image', BUILD_CONTAINER_IMAGE,
            '--build-container-tag', BUILD_CONTAINER_TAG
        ]

    def test_cli_without_params(self):
        result = self._invoke_cli()
        self.assertEqual(result.exit_code, 0)

    def test_help(self):
        result = self._invoke_cli(['--help'])
        self.assertEqual(result.exit_code, 0)

        for subcmd in ('build', 'push', 'make', 'run'):
            result = self._invoke_cli(None, subcmd, ['--help'])
            self.assertEqual(result.exit_code, 0)

    def test_nested_mode_without_global_parameters(self):
        result = self._invoke_cli(None, 'build', [IMAGE])
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual(result.exit_code, -1)

        result = self._invoke_cli(None, 'push', [IMAGE])
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual(result.exit_code, -1)

        result = self._invoke_cli(None, 'run', ['ls', '-l'])
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual(result.exit_code, -1)

        result = self._invoke_cli(None, 'make', ['-f', 'Makefile', 'all'])
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual(result.exit_code, -1)

    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_build(self, skipper_runner_run_mock, *args):
        dockerfile = IMAGE + '.Dockerfile'
        build_params = [IMAGE]
        self._invoke_cli(self.global_params, 'build', build_params)
        expected_command = [
            'docker',
            'build',
            '-f', dockerfile,
            '-t', FQDN_IMAGE,
            '.'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=BUILD_CONTAINER_FQDN_IMAGE)

    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push(self, skipper_runner_run_mock, *args):
        dockerfile = IMAGE + '.Dockerfile'
        push_params = [IMAGE]
        self._invoke_cli(self.global_params, 'push', push_params)
        expected_command = [
            'docker',
            'push',
            FQDN_IMAGE
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=BUILD_CONTAINER_FQDN_IMAGE)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_without_command(self, skipper_runner_run_mock):
        result = self._invoke_cli(self.global_params, 'run')
        self.assertNotEqual(result.exit_code, 0)
        self.assertFalse(skipper_runner_run_mock.called)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_run(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(self.global_params, 'run', run_params)
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=BUILD_CONTAINER_FQDN_IMAGE, environment=[])

    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_env(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = ['-e', ENV[0], '-e', ENV[1]] + command
        self._invoke_cli(self.global_params, 'run', run_params)
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=BUILD_CONTAINER_FQDN_IMAGE, environment=ENV)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_make(self, skipper_runner_run_mock):
        makefile = 'Makefile'
        target = 'all'
        make_params = ['-f', makefile, target]
        self._invoke_cli(self.global_params, 'make', make_params)
        expected_command = ['make', '-f', makefile, target]
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=BUILD_CONTAINER_FQDN_IMAGE, environment=[])

    def _invoke_cli(self, global_params=None, subcmd=None, subcmd_params=None):
        self.assertFalse(subcmd is None and subcmd_params is not None, 'No sub-command was provided!')

        cli_params = []
        if global_params is not None:
            cli_params += global_params

        if subcmd is not None:
            cli_params += [subcmd]

        if subcmd_params is not None:
            cli_params += subcmd_params

        return self._runner.invoke(cli.cli, cli_params, obj={}, standalone_mode=False)
