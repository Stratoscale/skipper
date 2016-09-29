import mock
import os
import unittest
import click
from click import testing
from skipper import cli
from skipper import config


REGISTRY = 'registry.io:5000'
IMAGE = 'image'
TAG = '1234567'
FQDN_IMAGE = REGISTRY + '/' + IMAGE + ':' + TAG

BUILD_CONTAINER_IMAGE = 'build-container-image'
BUILD_CONTAINER_TAG = 'build-container-tag'
BUILD_CONTAINER_FQDN_IMAGE = REGISTRY + '/' + BUILD_CONTAINER_IMAGE + ':' + BUILD_CONTAINER_TAG

ENV = ["KEY1=VAL1", "KEY2=VAL2"]

SKIPPER_CONF_BUILD_CONTAINER_IMAGE = 'skipper-conf-build-container-image'
SKIPPER_CONF_BUILD_CONTAINER_TAG = 'skipper-conf-build-container-tag'
SKIPPER_CONF_BUILD_CONTAINER_FQDN_IMAGE = REGISTRY + '/' + SKIPPER_CONF_BUILD_CONTAINER_IMAGE + ':' + SKIPPER_CONF_BUILD_CONTAINER_TAG
SKIPPER_CONF_MAKEFILE = 'Makefile.skipper'
SKIPPER_CONF = {
    'registry': REGISTRY,
    'build-container-image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build-container-tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    }
}
CONFIG_ENV = {
    "KEY2": "NOT_VAL2",
    "KEY3": "VAL3",
    "KEY4": "$VAL4",
    "KEY5": "$$VAL5"
}
CONFIG_ENV_EVALUATION = {
    "KEY2": "NOT_VAL2",
    "KEY3": "VAL3",
    "KEY4": "val4-evaluation",
    "KEY5": "$VAL5"
}
SKIPPER_CONF_WITH_ENV = {
    'registry': REGISTRY,
    'build-container-image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build-container-tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'env': CONFIG_ENV
}


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

    def test_cli_help(self):
        result = self._invoke_cli(global_params=['--help'])
        self.assertEqual(result.exit_code, 0)

    def test_subcommand_help(self):
        for subcmd in ('build', 'push', 'make', 'run'):
            result = self._invoke_cli(
                global_params=None,
                subcmd=subcmd,
                subcmd_params=['--help']
            )
            self.assertEqual(result.exit_code, 0)

    def test_subcommand_without_global_params(self):
        subcmd_params_map = {
            'build': [IMAGE],
            'push': [IMAGE],
            'run': ['ls' '-l'],
            'make': ['-f', 'Makefile', 'all'],
        }

        for subcmd, subcmd_params in subcmd_params_map.iteritems():
            result = self._invoke_cli(
                global_params=None,
                subcmd=subcmd,
                subcmd_params=subcmd_params,
            )
            self.assertIsInstance(result.exception, click.BadParameter)
            self.assertEqual(result.exit_code, -1)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_subcommand_without_subcommand_params(self, skipper_runner_run_mock):
        for subcmd in ('build', 'push', 'run', 'make'):
            result = self._invoke_cli(self.global_params, subcmd)
            self.assertNotEqual(result.exit_code, 0)
            self.assertFalse(skipper_runner_run_mock.called)

    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_build_single_image(self, skipper_runner_run_mock, *args):
        skipper_runner_run_mock.return_value = 0
        dockerfile = 'Dockerfile.' + IMAGE
        build_params = [IMAGE]
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'docker',
            'build',
            '-f', dockerfile,
            '-t', FQDN_IMAGE,
            '.'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_build_multiple_images(self, skipper_runner_run_mock, *args):
        skipper_runner_run_mock.return_value = 0
        build_params = ['image1', 'image2']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        expected_commands = [
            mock.call(['docker', 'build', '-f', 'Dockerfile.image1', '-t', REGISTRY + '/' + 'image1' + ':' + TAG, '.']),
            mock.call(['docker', 'build', '-f', 'Dockerfile.image2', '-t', REGISTRY + '/' + 'image2' + ':' + TAG, '.']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_build_multiple_images_with_error(self, skipper_runner_run_mock, *args):
        skipper_runner_run_mock.return_value = 1
        build_params = ['image1', 'image2']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'docker',
            'build',
            '-f', 'Dockerfile.image1',
            '-t', REGISTRY + '/' + 'image1' + ':' + TAG,
            '.'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', autospec=True, return_value=['image1', 'image2'])
    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_build_all_images(self, skipper_runner_run_mock, *args):
        skipper_runner_run_mock.return_value = 0
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
        )
        expected_commands = [
            mock.call(['docker', 'build', '-f', 'Dockerfile.image1', '-t', REGISTRY + '/' + 'image1' + ':' + TAG, '.']),
            mock.call(['docker', 'build', '-f', 'Dockerfile.image2', '-t', REGISTRY + '/' + 'image2' + ':' + TAG, '.']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('os.path.exists', autospec=True, return_value=True)
    @mock.patch('yaml.load', autospec=True, return_value=SKIPPER_CONF)
    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_build_with_defaults_from_config_file(self, skipper_runner_run_mock, *args):
        skipper_runner_run_mock.return_value = 0
        dockerfile = 'Dockerfile.' + IMAGE
        build_params = [IMAGE]
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'docker',
            'build',
            '-f', dockerfile,
            '-t', FQDN_IMAGE,
            '.'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push(self, skipper_runner_run_mock, *args):
        push_params = [IMAGE]
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='push',
            subcmd_params=push_params
        )
        expected_command = [
            'docker',
            'push',
            FQDN_IMAGE
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('os.path.exists', autospec=True, return_value=True)
    @mock.patch('yaml.load', autospec=True, return_value=SKIPPER_CONF)
    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push_with_defaults_from_config_file(self, skipper_runner_run_mock, *args):
        push_params = [IMAGE]
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='push',
            subcmd_params=push_params
        )
        expected_command = [
            'docker',
            'push',
            FQDN_IMAGE
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('glob.glob', autospec=True, return_value=['Dockerfile.' + IMAGE])
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True)
    def test_images_with_single_local_results(self, subprocess_check_output_mock, tabulate_mock, *args):
        name = REGISTRY + '/' + IMAGE
        subprocess_check_output_mock.return_value = '{"name": "%(name)s", "tag": "%(tag)s"}' % dict(name=name, tag=TAG)
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='images',
            subcmd_params=[]
        )

        expected_command = [
            'docker',
            'images',
            '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
            name
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)
        tabulate_mock.assert_called_once_with([['LOCAL', name, TAG]], headers=['ORIGIN', 'IMAGE', 'TAG'], tablefmt='grid')

    @mock.patch('glob.glob', autospec=True, return_value=['Dockerfile.image1', 'Dockerfile.image2'])
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True)
    def test_images_with_multiple_local_results(self, subprocess_check_output_mock, tabulate_mock, *args):
        subprocess_check_output_mock.side_effect = [
            '{"name": "%(registry)s/image1", "tag": "tag1"}\n' % dict(registry=REGISTRY),
            '{"name": "%(registry)s/image2", "tag": "tag2"}\n{"name": "%(registry)s/image2", "tag": "tag3"}\n' % dict(registry=REGISTRY),
        ]
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='images',
            subcmd_params=[]
        )

        command_prefix = [
            'docker',
            'images',
            '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
        ]
        expected_check_output_calls = [
            mock.call(command_prefix + [REGISTRY + '/image1']),
            mock.call(command_prefix + [REGISTRY + '/image2']),
        ]
        subprocess_check_output_mock.assert_has_calls(expected_check_output_calls)
        expected_table = [
            ['LOCAL', REGISTRY + '/image1', 'tag1'],
            ['LOCAL', REGISTRY + '/image2', 'tag2'],
            ['LOCAL', REGISTRY + '/image2', 'tag3'],
        ]
        tabulate_mock.assert_called_once_with(expected_table, headers=['ORIGIN', 'IMAGE', 'TAG'], tablefmt='grid')

    @mock.patch('glob.glob', autospec=True, return_value=['Dockerfile.' + IMAGE])
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True)
    def test_images_with_all_results(self, subprocess_check_output_mock, requests_get_mock, tabulate_mock, *args):
        name = REGISTRY + '/' + IMAGE
        subprocess_check_output_mock.return_value = '{"name": "%(name)s", "tag": "%(tag)s"}' % dict(name=name, tag=TAG)

        requests_response_mock = None
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': name,
                'tags': ['latest', '85cd8cae14592a8f2086db5559fa90b334009028', '0f259966bee4d908636bcbee82dd89be5f274f9e']
            }
            requests_get_mock.return_value = requests_response_mock

        self._invoke_cli(
            global_params=self.global_params,
            subcmd='images',
            subcmd_params=['-r']
        )

        expected_command = [
            'docker',
            'images',
            '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
            name
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)

        expected_url = 'https://%(registry)s/v2/%(image)s/tags/list' % dict(registry=REGISTRY, image=IMAGE)
        requests_get_mock.assert_called_once_with(
            url=expected_url,
            verify=False
        )

        expected_images_results = [
            ['LOCAL', name, TAG],
            ['REMOTE', name, 'latest'],
            ['REMOTE', name, '85cd8cae14592a8f2086db5559fa90b334009028'],
            ['REMOTE', name, '0f259966bee4d908636bcbee82dd89be5f274f9e']
        ]
        tabulate_mock.assert_called_once_with(expected_images_results, headers=['ORIGIN', 'IMAGE', 'TAG'], tablefmt='grid')

    @mock.patch('glob.glob', autospec=True, return_value=['Dockerfile.' + IMAGE])
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True, return_value='')
    def test_images_without_results(self, subprocess_check_output_mock, tabulate_mock, *args):
        name = REGISTRY + '/' + IMAGE
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='images',
            subcmd_params=[]
        )

        expected_command = [
            'docker',
            'images',
            '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
            name
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)
        tabulate_mock.assert_called_once_with([], headers=['ORIGIN', 'IMAGE', 'TAG'], tablefmt='grid')

    @mock.patch('glob.glob', autospec=True, return_value=['Dockerfile.' + IMAGE])
    @mock.patch('subprocess.check_call', autospec=True)
    def test_rmi_local(self, subprocess_check_call_mock, *args):
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='rmi',
            subcmd_params=[IMAGE, TAG]
        )

        expected_command = [
            'docker',
            'rmi',
            FQDN_IMAGE
        ]
        subprocess_check_call_mock.assert_called_once_with(expected_command)

    @mock.patch('glob.glob', autospec=True, return_value=['Dockerfile.' + IMAGE])
    @mock.patch('requests.delete', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_rmi_remote(self, requests_get_mock, requests_delete_mock, *args):
        requests_get_mock.side_effect = [mock.Mock(headers={'Docker-Content-Digest': 'digest'})]
        requests_delete_mock.side_effect = [mock.Mock(ok=True)]
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='rmi',
            subcmd_params=['-r', IMAGE, TAG]
        )

        url = 'https://%(registry)s/v2/%(image)s/manifests/%(reference)s' % dict(registry=REGISTRY, image=IMAGE, reference=TAG)
        headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        requests_get_mock.assert_called_once_with(url=url, headers=headers, verify=False)
        url = 'https://%(registry)s/v2/%(image)s/manifests/%(reference)s' % dict(registry=REGISTRY, image=IMAGE, reference='digest')
        requests_delete_mock.assert_called_once_with(url=url, verify=False)

    @mock.patch('glob.glob', autospec=True, return_value=['Dockerfile.' + IMAGE])
    @mock.patch('requests.delete', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_rmi_remote_fail(self, requests_get_mock, requests_delete_mock, *args):
        requests_get_mock.side_effect = [mock.Mock(headers={'Docker-Content-Digest': 'digest'})]
        requests_delete_mock.side_effect = [mock.Mock(ok=False)]
        result = self._invoke_cli(
            global_params=self.global_params,
            subcmd='rmi',
            subcmd_params=['-r', IMAGE, TAG]
        )
        self.assertIsInstance(result.exception, Exception)

        url = 'https://%(registry)s/v2/%(image)s/manifests/%(reference)s' % dict(registry=REGISTRY, image=IMAGE, reference=TAG)
        headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        requests_get_mock.assert_called_once_with(url=url, headers=headers, verify=False)
        url = 'https://%(registry)s/v2/%(image)s/manifests/%(reference)s' % dict(registry=REGISTRY, image=IMAGE, reference='digest')
        requests_delete_mock.assert_called_once_with(url=url, verify=False)

    @mock.patch('glob.glob', autospec=True, return_value=['Dockerfile.' + IMAGE])
    def test_validate_project_image(self, *args):
        result = self._invoke_cli(
            global_params=self.global_params,
            subcmd='rmi',
            subcmd_params=['-r', 'non-project-image', TAG]
        )
        self.assertIsInstance(result.exception, click.BadParameter)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_run(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=BUILD_CONTAINER_FQDN_IMAGE, environment=[])

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('os.path.exists', autospec=True, return_value=True)
    @mock.patch('yaml.load', autospec=True, return_value=SKIPPER_CONF)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_defaults_from_config_file(self, skipper_runner_run_mock, *args):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=SKIPPER_CONF_BUILD_CONTAINER_FQDN_IMAGE, environment=[])

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('os.path.exists', autospec=True, return_value=True)
    @mock.patch('yaml.load', autospec=True, return_value=SKIPPER_CONF_WITH_ENV)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_defaults_and_env_from_config_file(self, skipper_runner_run_mock, *args):
        command = ['ls', '-l']
        run_params = command
        os.environ['VAL4'] = "val4-evaluation"
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        env = ["%s=%s" % (key, value) for key, value in CONFIG_ENV_EVALUATION.iteritems()]
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=SKIPPER_CONF_BUILD_CONTAINER_FQDN_IMAGE, environment=env)

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('os.path.exists', autospec=True, return_value=True)
    @mock.patch('yaml.load', autospec=True, return_value=SKIPPER_CONF_WITH_ENV)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_env_overriding_config_file(self, skipper_runner_run_mock, *args):
        command = ['ls', '-l']
        run_params = ['-e', ENV[0], '-e', ENV[1]] + command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        env = ["%s=%s" % (key, value) for key, value in CONFIG_ENV_EVALUATION.iteritems()] + ENV
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=SKIPPER_CONF_BUILD_CONTAINER_FQDN_IMAGE, environment=env)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_env(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        os.environ['VAL4'] = "val4-evaluation"
        run_params = ['-e', ENV[0], '-e', ENV[1]] + command
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=BUILD_CONTAINER_FQDN_IMAGE, environment=ENV)

    @mock.patch('subprocess.check_output', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_without_build_container_tag(self, skipper_runner_run_mock, subprocess_check_output_mock):
        build_container_sha256 = 'sha256:8f0396f5d47ebeaded68702e67c21bf13519efb00c9959a308615beb2e5a429f'
        subprocess_check_output_mock.return_value = build_container_sha256 + '\n'
        global_params = self.global_params[:-2]
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            global_params=global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=build_container_sha256, environment=[])

    @mock.patch('skipper.runner.run', autospec=True)
    def test_make(self, skipper_runner_run_mock):
        makefile = 'Makefile'
        target = 'all'
        make_params = ['-f', makefile, target]
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='make',
            subcmd_params=make_params
        )
        expected_command = ['make', '-f', makefile, target]
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=BUILD_CONTAINER_FQDN_IMAGE, environment=[])

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('os.path.exists', autospec=True, return_value=True)
    @mock.patch('yaml.load', autospec=True, return_value=SKIPPER_CONF)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_make_with_defaults_from_config_file(self, skipper_runner_run_mock, *args):
        makefile = 'Makefile'
        target = 'all'
        make_params = ['-f', makefile, target]
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='make',
            subcmd_params=make_params
        )
        expected_command = ['make', '-f', makefile, target]
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=SKIPPER_CONF_BUILD_CONTAINER_FQDN_IMAGE, environment=[])

    @mock.patch('subprocess.check_output', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_make_without_build_container_tag(self, skipper_runner_run_mock, subprocess_check_output_mock):
        build_container_sha256 = 'sha256:8f0396f5d47ebeaded68702e67c21bf13519efb00c9959a308615beb2e5a429f'
        subprocess_check_output_mock.return_value = build_container_sha256 + '\n'
        global_params = self.global_params[:-2]
        makefile = 'Makefile'
        target = 'all'
        make_params = ['-f', makefile, target]
        self._invoke_cli(
            global_params=global_params,
            subcmd='make',
            subcmd_params=make_params
        )
        expected_command = ['make', '-f', makefile, target]
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=build_container_sha256, environment=[])

    @mock.patch('skipper.runner.run', autospec=True)
    def test_shell(self, skipper_runner_run_mock):
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='shell',
        )
        skipper_runner_run_mock.assert_called_once_with(['bash'], fqdn_image=BUILD_CONTAINER_FQDN_IMAGE, environment=[], interactive=True)

    def _invoke_cli(self, defaults=None, global_params=None, subcmd=None, subcmd_params=None):
        self.assertFalse(subcmd is None and subcmd_params is not None, 'No sub-command was provided!')

        defaults = defaults or {}

        cli_params = []
        if global_params is not None:
            cli_params += global_params

        if subcmd is not None:
            cli_params += [subcmd]

        if subcmd_params is not None:
            cli_params += subcmd_params

        return self._runner.invoke(cli.cli, cli_params, default_map=defaults, obj={}, standalone_mode=False)
