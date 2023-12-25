import os
import unittest
import mock
from six.moves import http_client
import click
import six
from click import testing
from requests import HTTPError

from skipper import cli
from skipper import config, utils
from tests.consts import REGISTRY, SKIPPER_CONF_BUILD_CONTAINER_TAG, SKIPPER_CONF_MAKEFILE, SKIPPER_CONF_BUILD_CONTAINER_IMAGE, IMAGE, TAG

BUILD_CONTAINER_IMAGE = 'build-container-image'
BUILD_CONTAINER_TAG = 'build-container-tag'
BUILD_CONTAINER_FQDN_IMAGE = REGISTRY + '/' + BUILD_CONTAINER_IMAGE + ':' + BUILD_CONTAINER_TAG

ENV = ["KEY1=VAL1", "KEY2=VAL2"]
ENV_FILE_PATH = '/home/envfile.env'
ENV_FILES = ['/home/envfile1.env', '/home/envfile2.env']

SKIPPER_CONF_CONTAINER_CONTEXT = '/some/context'
SKIPPER_CONF_BUILD_CONTAINER_FQDN_IMAGE = REGISTRY + '/' + SKIPPER_CONF_BUILD_CONTAINER_IMAGE + ':' + SKIPPER_CONF_BUILD_CONTAINER_TAG
SKIPPER_CONF = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    }
}

SKIPPER_CONF_WITH_ENV_FILE = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'env_file': [ENV_FILE_PATH]
}
SKIPPER_CONF_ENV = {
    "KEY2": "NOT_VAL2",
    "KEY3": "VAL3",
}
SKIPPER_CONF_WITH_ENV = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'env': SKIPPER_CONF_ENV
}
SKIPPER_CONF_WITH_MULTIPLE_ENV_FILES = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'env_file': ENV_FILES
}
SKIPPER_CONF_WITH_ENV_LIST = {
    'registry': REGISTRY,
    'build-container-image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build-container-tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'env': ['key1=value1', 'key2']
}
SKIPPER_CONF_WITH_ENV_WRONG_TYPE = {
    'registry': REGISTRY,
    'build-container-image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build-container-tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'env': 'wrong-env-type',
}
SKIPPER_CONF_WITH_CONTAINERS = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'containers': {
        'image1': 'app1/Dockerfile',
        'image2': 'app2/Dockerfile',
    }
}
SKIPPER_CONF_WITH_VOLUMES = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'volumes': [
        'volume1',
        'volume2',
    ]
}

SKIPPER_CONF_WITH_WORKDIR = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'workdir': 'test-workdir'
}
SKIPPER_CONF_WITH_WORKSPACE = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'workspace': '/test/workspace'
}

SKIPPER_CONF_WITH_GIT_REV = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': 'git:revision',
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
}

SKIPPER_CONF_WITH_CONTEXT = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'build_container_tag': SKIPPER_CONF_BUILD_CONTAINER_TAG,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'container_context': SKIPPER_CONF_CONTAINER_CONTEXT
}

SKIPPER_CONF_WITH_CONTEXT_NO_TAG = {
    'registry': REGISTRY,
    'build_container_image': SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    'make': {
        'makefile': SKIPPER_CONF_MAKEFILE,
    },
    'container_context': SKIPPER_CONF_CONTAINER_CONTEXT
}


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.runtime = "docker"
        utils.CONTAINER_RUNTIME_COMMAND = self.runtime
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
            'push': [IMAGE],
            'run': ['ls' '-l'],
            'make': ['-f', 'Makefile', 'all'],
        }

        for subcmd, subcmd_params in six.iteritems(subcmd_params_map):
            result = self._invoke_cli(
                global_params=None,
                subcmd=subcmd,
                subcmd_params=subcmd_params,
            )
            self.assertIsInstance(result.exception, click.BadParameter)
            # since click testing module messes up exit code
            # we just verify if the exit code is not 0
            self.assertNotEqual(0, result.exit_code)

    @mock.patch('skipper.runner.run', autospec=True)
    def test_subcommand_without_subcommand_params(self, skipper_runner_run_mock):
        for subcmd in ('build', 'push', 'run', 'make'):
            result = self._invoke_cli(self.global_params, subcmd)
            self.assertNotEqual(result.exit_code, 0)
            self.assertFalse(skipper_runner_run_mock.called)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', mock.MagicMock(autospec=True,
                                                                            return_value={
                                                                                'image1': '/home/user/work/project/Dockerfile.image1',
                                                                                'image2': '/home/user/work/project/Dockerfile.image2'}))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_build_existing_image(self, skipper_runner_run_mock):
        build_params = ['image1']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'build',
            '--network=host',
            '--build-arg', 'TAG=1234567',
            '-f', '/home/user/work/project/Dockerfile.image1',
            '-t', 'image1:1234567',
            '/home/user/work/project'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', mock.MagicMock(autospec=True,
                                                                            return_value={
                                                                                'image1': '/home/user/work/project/Dockerfile.image1'}))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_build_existing_image_with_context(self, skipper_runner_run_mock):
        build_params = ['image1',
                        '--container-context',
                        '/home/user/work/project']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'build',
            '--network=host',
            '--build-arg', 'TAG=1234567',
            '-f', '/home/user/work/project/Dockerfile.image1',
            '-t', 'image1:1234567',
            '/home/user/work/project'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', mock.MagicMock(autospec=True,
                                                                            return_value={
                                                                                'image1': '/home/user/work/project/Dockerfile.image1',
                                                                                'image2': '/home/user/work/project/Dockerfile.image2'}))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_CONTEXT))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_build_with_context_from_config_file(self, skipper_runner_run_mock):
        build_params = ['image1']
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'build',
            '--network=host',
            '--build-arg', 'TAG=1234567',
            '-f', '/home/user/work/project/Dockerfile.image1',
            '-t', 'image1:1234567',
            SKIPPER_CONF_CONTAINER_CONTEXT
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_CONTEXT_NO_TAG))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value=''))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_make_without_build_container_tag_with_context(self, skipper_runner_run_mock):
        global_params = self.global_params[:-2]
        makefile = 'Makefile'
        target = 'all'
        make_params = ['-f', makefile, target]
        self._invoke_cli(
            defaults=config.load_defaults(),
            global_params=global_params,
            subcmd='make',
            subcmd_params=make_params
        )
        expected_commands = [
            mock.call(['build', '--network=host',
                       '-f', 'Dockerfile.build-container-image',
                       '-t', 'build-container-image',
                       SKIPPER_CONF_CONTAINER_CONTEXT],
                      stdout_to_stderr=True),
            mock.call(['make'] + make_params, fqdn_image='build-container-image', environment=[],
                      interactive=False, name=None, net=None, publish=(), volumes=None, workdir=None,
                      use_cache=False, workspace=None, env_file=()),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=False))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_build_non_existing_image(self, skipper_runner_run_mock):
        build_params = ['my_image']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        self.assertFalse(skipper_runner_run_mock.called)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', mock.MagicMock(autospec=True,
                                                                            return_value={
                                                                                'image1': '/home/user/work/project/Dockerfile.image1',
                                                                                'image2': '/home/user/work/project/Dockerfile.image2'}))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_build_multiple_images(self, skipper_runner_run_mock):
        skipper_runner_run_mock.return_value = 0
        build_params = ['image1', 'image2']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        expected_commands = [
            mock.call(['build', '--network=host', '--build-arg', 'TAG=1234567',
                       '-f', '/home/user/work/project/Dockerfile.image1', '-t',
                       'image1:1234567',
                       '/home/user/work/project']),
            mock.call(['build', '--network=host', '--build-arg', 'TAG=1234567',
                       '-f', '/home/user/work/project/Dockerfile.image2', '-t',
                       'image2:1234567',
                       '/home/user/work/project']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands, any_order=True)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', mock.MagicMock(autospec=True,
                                                                            return_value={
                                                                                'image1': '/home/user/work/project/Dockerfile.image1'}))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.runner.run', autospec=True, return_value=1)
    def test_build_multiple_images_with_invalid_image(self, skipper_runner_run_mock):
        build_params = ['image1', 'image2']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'build',
            '--network=host',
            '--build-arg', 'TAG=1234567',
            '-f', '/home/user/work/project/Dockerfile.image1',
            '-t', 'image1:1234567',
            '/home/user/work/project'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', mock.MagicMock(autospec=True,
                                                                            return_value={
                                                                                'image1': '/home/user/work/project/Dockerfile.image1',
                                                                                'image2': '/home/user/work/project/Dockerfile.image2'}))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('os.path.exists', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True, return_value=1)
    def test_build_multiple_images_with_non_existing_dockerfile(self, skipper_runner_run_mock, os_path_exists_mock):
        os_path_exists_mock.side_effect = lambda dockerfile: 'image1' in dockerfile
        build_params = ['image1', 'image2']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'build',
            '--network=host',
            '--build-arg', 'TAG=1234567',
            '-f', '/home/user/work/project/Dockerfile.image1',
            '-t', 'image1:1234567',
            '/home/user/work/project'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', mock.MagicMock(autospec=True,
                                                                            return_value={
                                                                                'image1': '/home/user/work/project/Dockerfile.image1',
                                                                                'image2': '/home/user/work/project/Dockerfile.image2'}))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_build_all_images(self, skipper_runner_run_mock):
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='build',
        )
        expected_commands = [
            mock.call(['build', '--network=host', '--build-arg', 'TAG=1234567',
                       '-f', '/home/user/work/project/Dockerfile.image1', '-t',
                       'image1:1234567',
                       '/home/user/work/project']),
            mock.call(['build', '--network=host', '--build-arg', 'TAG=1234567',
                       '-f', '/home/user/work/project/Dockerfile.image2', '-t',
                       'image2:1234567',
                       '/home/user/work/project']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands, any_order=True)

    @mock.patch('skipper.utils.get_images_from_dockerfiles', mock.MagicMock(autospec=True,
                                                                            return_value={
                                                                                'image1': '/home/user/work/project/Dockerfile.image1',
                                                                                'image2': '/home/user/work/project/Dockerfile.image2'}))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_build_with_defaults_from_config_file(self, skipper_runner_run_mock):
        build_params = ['image1']
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'build',
            '--network=host', '--build-arg', 'TAG=1234567',
            '-f', '/home/user/work/project/Dockerfile.image1',
            '-t', 'image1:1234567',
            '/home/user/work/project'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch('os.path.abspath',
                mock.MagicMock(autospec=True, return_value='/home/user/work/project/app1/Dockerfile'))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_CONTAINERS))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_build_with_defaults_from_config_file_including_containers(self, skipper_runner_run_mock):
        build_params = ['image1']
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='build',
            subcmd_params=build_params
        )
        expected_command = [
            'build',
            '--network=host', '--build-arg', 'TAG=1234567',
            '-f', '/home/user/work/project/app1/Dockerfile',
            '-t', 'image1:1234567',
            '/home/user/work/project/app1'
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_command)

    @mock.patch(
        "skipper.utils.get_images_from_dockerfiles",
        mock.MagicMock(
            autospec=True,
            return_value={"image1": "/home/user/work/project/Dockerfile.image1"},
        ),
    )
    @mock.patch("os.path.exists", mock.MagicMock(autospec=True, return_value=True))
    @mock.patch(
        "skipper.git.get_hash", mock.MagicMock(autospec=True, return_value="1234567")
    )
    @mock.patch("skipper.runner.run", autospec=True, return_value=0)
    def test_build_with_build_args(self, skipper_runner_run_mock):
        build_params = ["image1"]
        self._invoke_cli(
            global_params=self.global_params + ["--build-arg", "key1=value1", "--build-arg", "key2=value2"],
            subcmd="build",
            subcmd_params=build_params,
        )
        expected_commands = [
            "build",
            "--network=host",
            "--build-arg",
            "key1=value1",
            "--build-arg",
            "key2=value2",
            "--build-arg",
            "TAG=1234567",
            "-f",
            "/home/user/work/project/Dockerfile.image1",
            "-t",
            "image1:1234567",
            "/home/user/work/project",
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_commands)

    @mock.patch(
        "skipper.utils.get_images_from_dockerfiles",
        mock.MagicMock(
            autospec=True,
            return_value={"image1": "/home/user/work/project/Dockerfile.image1"},
        ),
    )
    @mock.patch("os.path.exists", mock.MagicMock(autospec=True, return_value=True))
    @mock.patch(
        "skipper.git.get_hash", mock.MagicMock(autospec=True, return_value="1234567")
    )
    @mock.patch("skipper.runner.run", autospec=True, return_value=0)
    def test_build_with_build_contexts(self, skipper_runner_run_mock):
        build_params = ["image1"]
        self._invoke_cli(
            global_params=self.global_params + ["--build-context", "context1=/path/to/context"],
            subcmd="build",
            subcmd_params=build_params,
        )
        expected_commands = [
            "build",
            "--network=host",
            "--build-arg", "TAG=1234567",
            "--build-context", "context1=/path/to/context",
            "-f", "/home/user/work/project/Dockerfile.image1",
            "-t", "image1:1234567",
            "/home/user/work/project",
        ]
        skipper_runner_run_mock.assert_called_once_with(expected_commands)

    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push(self, skipper_runner_run_mock, requests_get_mock):
        skipper_runner_run_mock.side_effect = [0, 0]
        push_params = ['my_image']
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
            }
            requests_get_mock.return_value = requests_response_mock

        self._invoke_cli(
            global_params=self.global_params,
            subcmd='push',
            subcmd_params=push_params
        )
        expected_commands = [
            mock.call(['tag', 'my_image:1234567', 'registry.io:5000/my_image:1234567']),
            mock.call(['push', 'registry.io:5000/my_image:1234567']),
            mock.call(['rmi', 'registry.io:5000/my_image:1234567']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push_already_in_registry(self, skipper_runner_run_mock, requests_get_mock):
        skipper_runner_run_mock.side_effect = [0, 0]
        push_params = ['my_image']
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb', "1234567"]
            }
            requests_get_mock.return_value = requests_response_mock

        self._invoke_cli(
            global_params=self.global_params,
            subcmd='push',
            subcmd_params=push_params
        )
        expected_commands = [
            mock.call(['tag', 'my_image:1234567', 'registry.io:5000/my_image:1234567']),
            mock.call(['rmi', 'registry.io:5000/my_image:1234567']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push_already_in_registry_with_force(self, skipper_runner_run_mock, requests_get_mock):
        skipper_runner_run_mock.side_effect = [0, 0]
        push_params = ['my_image', "--force"]
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
            }
            requests_get_mock.return_value = requests_response_mock

        self._invoke_cli(
            global_params=self.global_params,
            subcmd='push',
            subcmd_params=push_params
        )
        expected_commands = [
            mock.call(['tag', 'my_image:1234567', 'registry.io:5000/my_image:1234567']),
            mock.call(['push', 'registry.io:5000/my_image:1234567']),
            mock.call(['rmi', 'registry.io:5000/my_image:1234567']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push_fail(self, skipper_runner_run_mock, requests_get_mock):
        skipper_runner_run_mock.side_effect = [0, 1]
        push_params = ['my_image']
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
            }
            requests_get_mock.return_value = requests_response_mock

        result = self._invoke_cli(
            global_params=self.global_params,
            subcmd='push',
            subcmd_params=push_params
        )
        self.assertEqual(result.exit_code, 1)
        expected_commands = [
            mock.call(['tag', 'my_image:1234567', 'registry.io:5000/my_image:1234567']),
            mock.call(['push', 'registry.io:5000/my_image:1234567']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push_tag_fail(self, skipper_runner_run_mock):
        skipper_runner_run_mock.side_effect = [1]
        push_params = ['my_image']
        result = self._invoke_cli(
            global_params=self.global_params,
            subcmd='push',
            subcmd_params=push_params
        )
        self.assertEqual(result.exit_code, 1)
        expected_commands = [
            mock.call(['tag', 'my_image:1234567', 'registry.io:5000/my_image:1234567']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push_rmi_fail(self, skipper_runner_run_mock, requests_get_mock):
        skipper_runner_run_mock.side_effect = [0, 0, 1]
        push_params = ['my_image']
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
            }
            requests_get_mock.return_value = requests_response_mock

        result = self._invoke_cli(
            global_params=self.global_params,
            subcmd='push',
            subcmd_params=push_params
        )
        self.assertEqual(result.exit_code, 0)
        expected_commands = [
            mock.call(['tag', 'my_image:1234567', 'registry.io:5000/my_image:1234567']),
            mock.call(['push', 'registry.io:5000/my_image:1234567']),
            mock.call(['rmi', 'registry.io:5000/my_image:1234567']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push_to_namespace(self, skipper_runner_run_mock, requests_get_mock):
        skipper_runner_run_mock.side_effect = [0, 0]
        push_params = ['--namespace', 'my_namespace', 'my_image']
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
            }
            requests_get_mock.return_value = requests_response_mock

        self._invoke_cli(
            global_params=self.global_params,
            subcmd='push',
            subcmd_params=push_params
        )
        expected_commands = [
            mock.call(['tag', 'my_image:1234567', 'registry.io:5000/my_namespace/my_image:1234567']),
            mock.call(['push', 'registry.io:5000/my_namespace/my_image:1234567']),
            mock.call(['rmi', 'registry.io:5000/my_namespace/my_image:1234567']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF))
    @mock.patch('skipper.git.get_hash', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_push_with_defaults_from_config_file(self, skipper_runner_run_mock, requests_get_mock):
        skipper_runner_run_mock.side_effect = [0, 0]
        push_params = ['my_image']
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
            }
            requests_get_mock.return_value = requests_response_mock

        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='push',
            subcmd_params=push_params
        )
        expected_commands = [
            mock.call(['tag', 'my_image:1234567', 'registry.io:5000/my_image:1234567']),
            mock.call(['push', 'registry.io:5000/my_image:1234567']),
            mock.call(['rmi', 'registry.io:5000/my_image:1234567']),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.my_image']))
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True)
    def test_images_with_single_local_results(self, subprocess_check_output_mock, tabulate_mock):
        subprocess_check_output_mock.return_value = '{"name": "my_image", "tag": "1234567"}'
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='images',
            subcmd_params=[]
        )

        expected_command = [
            'docker',
            'images',
            '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
            'my_image'
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)
        tabulate_mock.assert_called_once_with([['none', 'my_image', '1234567']], headers=['REGISTRY', 'IMAGE', 'TAG'],
                                              tablefmt='grid')

    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.image1', 'Dockerfile.image2']))
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True)
    def test_images_with_multiple_local_results(self, subprocess_check_output_mock, tabulate_mock):
        subprocess_check_output_mock.side_effect = [
            '{"name": "image1", "tag": "aaaaaaa"}\n',
            '{"name": "image2", "tag": "bbbbbbb"}\n{"name": "image2", "tag": "ccccccc"}\n',
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
            mock.call(command_prefix + ['image1']),
            mock.call(command_prefix + ['image2']),
        ]
        subprocess_check_output_mock.assert_has_calls(expected_check_output_calls, any_order=True)
        expected_table = [
            ['none', 'image1', 'aaaaaaa'],
            ['none', 'image2', 'bbbbbbb'],
            ['none', 'image2', 'ccccccc'],
        ]
        tabulate_mock.assert_called_once_with(expected_table, headers=['REGISTRY', 'IMAGE', 'TAG'], tablefmt='grid')

    @mock.patch('skipper.utils.HttpBearerAuth', autospec=True)
    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.my_image']))
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True)
    def test_images_with_all_results(self, subprocess_check_output_mock, requests_get_mock, tabulate_mock,
                                     requests_bearer_auth_mock):
        subprocess_check_output_mock.return_value = '{"name": "my_image", "tag": "aaaaaaa"}'

        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
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
            'my_image',
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)

        expected_url = 'https://%(registry)s/v2/my_image/tags/list' % dict(registry=REGISTRY)
        requests_get_mock.assert_called_once_with(
            url=expected_url,
            auth=requests_bearer_auth_mock(),
            verify=False
        )

        expected_images_results = [
            ['none', 'my_image', 'aaaaaaa'],
            ['registry.io:5000', 'my_image', 'latest'],
            ['registry.io:5000', 'my_image', 'aaaaaaa'],
            ['registry.io:5000', 'my_image', 'bbbbbbb']
        ]
        tabulate_mock.assert_called_once_with(expected_images_results, headers=['REGISTRY', 'IMAGE', 'TAG'],
                                              tablefmt='grid')

    @mock.patch('skipper.utils.HttpBearerAuth', autospec=True)
    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.my_image']))
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True, return_value='')
    def test_images_with_remote_results_only(self, subprocess_check_output_mock, requests_get_mock, tabulate_mock,
                                             requests_bearer_auth_mock):
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.json.return_value = {
                'name': 'my_image',
                'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
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
            'my_image',
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)

        expected_url = 'https://%(registry)s/v2/my_image/tags/list' % dict(registry=REGISTRY)
        requests_get_mock.assert_called_once_with(
            url=expected_url,
            verify=False,
            auth=requests_bearer_auth_mock()
        )

        expected_images_results = [
            ['registry.io:5000', 'my_image', 'latest'],
            ['registry.io:5000', 'my_image', 'aaaaaaa'],
            ['registry.io:5000', 'my_image', 'bbbbbbb']
        ]
        tabulate_mock.assert_called_once_with(expected_images_results, headers=['REGISTRY', 'IMAGE', 'TAG'],
                                              tablefmt='grid')

    @mock.patch('skipper.utils.HttpBearerAuth', autospec=True)
    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.my_image']))
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True, return_value='')
    def test_images_with_missing_remote_results(self, subprocess_check_output_mock, requests_get_mock, tabulate_mock,
                                                requests_bearer_auth_mock):
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.ok = False
            requests_response_mock.json.return_value = {
                u'errors': [{u'message': u'repository name not known to registry', u'code': u'NAME_UNKNOWN',
                             u'detail': {u'name': u'my_image'}}]
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
            'my_image',
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)

        expected_url = 'https://%(registry)s/v2/my_image/tags/list' % dict(registry=REGISTRY)
        requests_get_mock.assert_called_once_with(
            url=expected_url,
            verify=False,
            auth=requests_bearer_auth_mock()
        )

        expected_images_results = []
        tabulate_mock.assert_called_once_with(expected_images_results, headers=['REGISTRY', 'IMAGE', 'TAG'],
                                              tablefmt='grid')

    @mock.patch('skipper.utils.HttpBearerAuth', autospec=True)
    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.my_image']))
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('requests.get', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True)
    def test_images_with_local_result_and_missing_remote_results(self, subprocess_check_output_mock, requests_get_mock,
                                                                 tabulate_mock, requests_bearer_auth_mock):
        subprocess_check_output_mock.return_value = '{"name": "my_image", "tag": "aaaaaaa"}'

        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.ok = False
            requests_response_mock.json.return_value = {
                u'errors': [{u'message': u'repository name not known to registry', u'code': u'NAME_UNKNOWN',
                             u'detail': {u'name': u'my_image'}}]
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
            'my_image',
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)

        expected_url = 'https://%(registry)s/v2/my_image/tags/list' % dict(registry=REGISTRY)
        requests_get_mock.assert_called_once_with(
            url=expected_url,
            verify=False,
            auth=requests_bearer_auth_mock()
        )

        expected_images_results = [
            ['none', 'my_image', 'aaaaaaa'],
        ]

        tabulate_mock.assert_called_once_with(expected_images_results, headers=['REGISTRY', 'IMAGE', 'TAG'],
                                              tablefmt='grid')

    @mock.patch('skipper.utils.HttpBearerAuth', autospec=True)
    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.my_image']))
    @mock.patch('tabulate.tabulate', mock.MagicMock(autospec=True))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True, return_value='')
    def test_images_with_with_remote_error(self, subprocess_check_output_mock, requests_get_mock,
                                           requests_bearer_auth_mock):
        with mock.patch('requests.Response', autospec=True) as requests_response_class_mock:
            requests_response_mock = requests_response_class_mock.return_value
            requests_response_mock.ok = False
            requests_response_mock.json.return_value = {
                u'errors': [{u'message': u'repository name not known to registry', u'code': u'UNKNOWN_ERROR',
                             u'detail': {u'name': u'my_image'}}]
            }
            requests_get_mock.return_value = requests_response_mock

        result = self._invoke_cli(
            global_params=self.global_params,
            subcmd='images',
            subcmd_params=['-r']
        )

        expected_command = [
            'docker',
            'images',
            '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
            'my_image',
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)

        expected_url = 'https://%(registry)s/v2/my_image/tags/list' % dict(registry=REGISTRY)
        requests_get_mock.assert_called_once_with(
            url=expected_url,
            verify=False,
            auth=requests_bearer_auth_mock()
        )

        self.assertIsInstance(result.exception, click.exceptions.ClickException)

    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.my_image']))
    @mock.patch('tabulate.tabulate', autospec=True)
    @mock.patch('subprocess.check_output', autospec=True, return_value='')
    def test_images_without_local_results(self, subprocess_check_output_mock, tabulate_mock):
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='images',
            subcmd_params=[]
        )

        expected_command = [
            'docker',
            'images',
            '--format', '{"name": "{{.Repository}}", "tag": "{{.Tag}}"}',
            'my_image',
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)
        tabulate_mock.assert_called_once_with([], headers=['REGISTRY', 'IMAGE', 'TAG'], tablefmt='grid')

    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.my_image']))
    @mock.patch('subprocess.check_output', autospec=True)
    def test_rmi_local(self, subprocess_check_output_mock):
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='rmi',
            subcmd_params=['my_image', '1234567']
        )

        expected_command = [
            'docker',
            'rmi',
            u'my_image:1234567'
        ]
        subprocess_check_output_mock.assert_called_once_with(expected_command)

    @mock.patch('skipper.utils.HttpBearerAuth', autospec=True)
    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.' + IMAGE]))
    @mock.patch('requests.delete', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_rmi_remote(self, requests_get_mock, requests_delete_mock, requests_bearer_auth_mock):
        requests_get_mock.side_effect = [mock.Mock(headers={'Docker-Content-Digest': 'digest'})]
        requests_delete_mock.side_effect = [mock.Mock(ok=True)]
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='rmi',
            subcmd_params=['-r', IMAGE, TAG]
        )

        url = 'https://%(registry)s/v2/%(image)s/manifests/%(reference)s' % dict(registry=REGISTRY, image=IMAGE,
                                                                                 reference=TAG)
        headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        requests_get_mock.assert_called_once_with(url=url, headers=headers, verify=False,
                                                  auth=requests_bearer_auth_mock())
        url = 'https://%(registry)s/v2/%(image)s/manifests/%(reference)s' % dict(registry=REGISTRY, image=IMAGE,
                                                                                 reference='digest')
        requests_delete_mock.assert_called_once_with(url=url, verify=False,
                                                     auth=requests_bearer_auth_mock())

    @mock.patch('skipper.utils.HttpBearerAuth', autospec=True)
    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.' + IMAGE]))
    @mock.patch('requests.delete', autospec=True)
    @mock.patch('requests.get', autospec=True)
    def test_rmi_remote_fail(self, requests_get_mock, requests_delete_mock, requests_bearer_auth_mock):
        requests_get_mock.side_effect = [mock.Mock(headers={'Docker-Content-Digest': 'digest'})]
        requests_delete_mock.side_effect = HTTPError()
        result = self._invoke_cli(
            global_params=self.global_params,
            subcmd='rmi',
            subcmd_params=['-r', IMAGE, TAG]
        )
        self.assertIsInstance(result.exception, Exception)

        url = 'https://%(registry)s/v2/%(image)s/manifests/%(reference)s' % dict(registry=REGISTRY, image=IMAGE,
                                                                                 reference=TAG)
        headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        requests_get_mock.assert_called_once_with(url=url, headers=headers, verify=False,
                                                  auth=requests_bearer_auth_mock())
        url = 'https://%(registry)s/v2/%(image)s/manifests/%(reference)s' % dict(registry=REGISTRY, image=IMAGE,
                                                                                 reference='digest')
        requests_delete_mock.assert_called_once_with(url=url, verify=False, auth=requests_bearer_auth_mock())

    @mock.patch('glob.glob', mock.MagicMock(autospec=True, return_value=['Dockerfile.' + IMAGE]))
    def test_validate_project_image(self):
        result = self._invoke_cli(
            global_params=self.global_params,
            subcmd='rmi',
            subcmd_params=['-r', 'non-project-image', TAG]
        )
        self.assertIsInstance(result.exception, click.BadParameter)

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_existing_local_build_container(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_image_name = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_image_name, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value=''))
    @mock.patch('requests.get', autospec=True)
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_existing_remote_build_container(self, skipper_runner_run_mock, requests_get_mock):
        requests_response_class_mock = mock.MagicMock(spec='requests.Response')
        requests_response_mock = requests_response_class_mock.return_value
        requests_response_mock.json.return_value = {
            'name': 'my_image',
            'tags': ['latest', 'aaaaaaa', 'bbbbbbb', 'build-container-tag']
        }
        requests_response_mock.status_code = http_client.OK
        requests_get_mock.return_value = requests_response_mock

        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_image_name = 'registry.io:5000/build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_image_name, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value=''))
    @mock.patch('skipper.runner.run', mock.MagicMock(autospec=True))
    @mock.patch('requests.get', autospec=True)
    def test_run_with_non_existing_build_container(self, requests_get_mock):
        requests_response_class_mock = mock.MagicMock(spec='requests.Response')
        requests_response_mock = requests_response_class_mock.return_value
        requests_response_mock.json.return_value = {
            'name': 'my_image',
            'tags': ['latest', 'aaaaaaa', 'bbbbbbb']
        }

        requests_get_mock.return_value = requests_response_mock
        command = ['ls', '-l']
        run_params = command
        ret = self._invoke_cli(
            global_params=self.global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        self.assertIsInstance(ret.exception, click.exceptions.ClickException)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_defaults_from_config_file(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_defaults_and_env_from_env_file(
            self,
            skipper_runner_run_mock
    ):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=SKIPPER_CONF_WITH_ENV_FILE,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command,
                                                        fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False,
                                                        name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None,
                                                        workspace=None,
                                                        use_cache=False,
                                                        env_file=(ENV_FILE_PATH,))

    @mock.patch('os.path.exists',
                mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('subprocess.check_output',
                mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_defaults_and_env_from_multiple_env_file(
            self,
            skipper_runner_run_mock
    ):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=SKIPPER_CONF_WITH_MULTIPLE_ENV_FILES,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command,
                                                        fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False,
                                                        name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None,
                                                        workspace=None,
                                                        use_cache=False,
                                                        env_file=tuple(ENV_FILES))

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_env_overriding_config_file(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = ['-e', ENV[0], '-e', ENV[1]] + command
        self._invoke_cli(
            defaults=SKIPPER_CONF_WITH_ENV,
            subcmd='run',
            subcmd_params=run_params
        )
        env = [f'{key}={value}' for key, value in six.iteritems(SKIPPER_CONF_ENV)] + ENV
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=env,
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('builtins.open', mock.MagicMock(create=True))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('os.environ', {})
    @mock.patch('yaml.safe_load', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_ENV_LIST))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_env_list(self, skipper_runner_run_mock):
        os.environ['VAL4'] = "val4-evaluation"
        command = ['ls', '-l']
        run_params = ['-e', ENV[0], '-e', ENV[1]] + command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        env = ['key1=value1'] + ENV
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=env,
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('builtins.open', mock.MagicMock(create=True))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('os.environ', {'key2': 'value2'})
    @mock.patch('yaml.safe_load', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_ENV_LIST))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_env_list_get_from_env(self, skipper_runner_run_mock):
        os.environ['VAL4'] = "val4-evaluation"
        command = ['ls', '-l']
        run_params = ['-e', ENV[0], '-e', ENV[1]] + command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        env = ['key1=value1', 'key2=value2'] + ENV
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=env,
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('builtins.open', mock.MagicMock(create=True))
    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('yaml.safe_load', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_ENV_WRONG_TYPE))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_env_wrong_type(self, skipper_runner_run_mock):
        os.environ['VAL4'] = "val4-evaluation"
        command = ['ls', '-l']
        run_params = ['-e', ENV[0], '-e', ENV[1]] + command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        self.assertEqual(len(skipper_runner_run_mock.mock_calls), 0)

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
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
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=ENV,
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_interactive_from_environment(self, skipper_runner_run_mock):
        os.environ['SKIPPER_INTERACTIVE'] = 'True'
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=True, name=None, net=None, publish=(), volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())
        del os.environ['SKIPPER_INTERACTIVE']

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_non_interactive_from_environment(self, skipper_runner_run_mock):
        os.environ['SKIPPER_INTERACTIVE'] = 'False'
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())
        del os.environ['SKIPPER_INTERACTIVE']

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_non_interactive(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = ['--interactive'] + command
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=True, name=None, net=None, publish=(), volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value=''))
    @mock.patch('skipper.utils.image_to_dockerfile', mock.MagicMock(autospec=True, side_effect=lambda x: 'Dockerfile.'+x))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_run_without_build_container_tag(self, skipper_runner_run_mock):
        global_params = self.global_params[:-2]
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            global_params=global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_commands = [
            mock.call(['build', '--network=host',
                       '-f', 'Dockerfile.build-container-image',
                       '-t', 'build-container-image', '.'],
                      stdout_to_stderr=True),
            mock.call(command, fqdn_image='build-container-image', environment=[],
                      interactive=False, name=None, net=None, publish=(), volumes=None, workdir=None, workspace=None,
                      use_cache=False, env_file=()),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value=''))
    @mock.patch('skipper.utils.image_to_dockerfile', mock.MagicMock(autospec=True, side_effect=lambda x: 'Dockerfile.'+x))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_run_without_build_container_tag_cached(self, skipper_runner_run_mock):
        global_params = self.global_params[:-2]
        command = ['ls', '-l']
        run_params = ['--cache'] + command
        self._invoke_cli(
            global_params=global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_commands = [
            mock.call(command, fqdn_image='build-container-image', environment=[],
                      interactive=False, name=None, net=None, publish=(), volumes=None, workdir=None, workspace=None,
                      use_cache=True, env_file=()),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_non_default_net(self, skipper_runner_run_mock):
        global_params = self.global_params
        global_params += ['--build-container-net', 'non-default-net']
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            global_params=global_params,
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=False, name=None, net='non-default-net',
                                                        publish=(), volumes=None, workdir=None, workspace=None,
                                                        use_cache=False, env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_publish_single_port(self, skipper_runner_run_mock):
        global_params = self.global_params
        global_params += ['--build-container-net', 'non-default-net']

        makefile = 'Makefile'
        target = 'all'
        make_params = ['-p', '123:123', '-f', makefile, target]

        self._invoke_cli(
            global_params=global_params,
            subcmd='make',
            subcmd_params=make_params
        )

        expected_command = ['make', '-f', makefile, target]

        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False, name=None, net=u'non-default-net',
                                                        publish=(u'123:123',), volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_publish_multiple_ports(self, skipper_runner_run_mock):
        global_params = self.global_params
        global_params += ['--build-container-net', 'non-default-net']

        makefile = 'Makefile'
        target = 'all'
        make_params = ['-p', '123:123', '-p', '12:12', '-f', makefile, target]

        self._invoke_cli(
            global_params=global_params,
            subcmd='make',
            subcmd_params=make_params
        )

        expected_command = ['make', '-f', makefile, target]

        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False, name=None, net=u'non-default-net',
                                                        publish=('123:123', '12:12'), volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_publish_port_range(self, skipper_runner_run_mock):
        global_params = self.global_params
        global_params += ['--build-container-net', 'non-default-net']

        makefile = 'Makefile'
        target = 'all'
        make_params = ['-p', '123:123', '-p', '12-13:12-13', '-f', makefile, target]

        self._invoke_cli(
            global_params=global_params,
            subcmd='make',
            subcmd_params=make_params
        )

        expected_command = ['make', '-f', makefile, target]

        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False, name=None, net=u'non-default-net',
                                                        publish=('123:123', '12-13:12-13'), volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    def test_run_with_publish_textual_port(self):
        global_params = self.global_params
        global_params += ['--build-container-net', 'non-default-net']

        makefile = 'Makefile'
        target = 'all'
        make_params = ['-p', '123:a1', '-p', '12:12', '-f', makefile, target]

        result = self._invoke_cli(global_params=global_params, subcmd='make', subcmd_params=make_params)
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual("Publish need to be in format port:port or port-port:port-port", result.exception.message)
        # since click testing module messes up exit code
        # we just verify if the exit code is not 0
        self.assertNotEqual(0, result.exit_code)

    def test_run_with_publish_textual_port_range(self):
        global_params = self.global_params
        global_params += ['--build-container-net', 'non-default-net']

        makefile = 'Makefile'
        target = 'all'
        make_params = ['-p', '123-1:1-a1', '-p', '12:12', '-f', makefile, target]

        result = self._invoke_cli(global_params=global_params, subcmd='make', subcmd_params=make_params)
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual("Publish need to be in format port:port or port-port:port-port", result.exception.message)
        # since click testing module messes up exit code
        # we just verify if the exit code is not 0
        self.assertNotEqual(0, result.exit_code)

    def test_run_with_invalid_port_range(self):
        global_params = self.global_params
        global_params += ['--build-container-net', 'non-default-net']

        makefile = 'Makefile'
        target = 'all'
        make_params = ['-p', '15-25:25-15', '-p', '12:12', '-f', makefile, target]

        result = self._invoke_cli(global_params=global_params, subcmd='make', subcmd_params=make_params)
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual("Invalid port range: 25 should be bigger than 15", result.exception.message)
        # since click testing module messes up exit code
        # we just verify if the exit code is not 0
        self.assertNotEqual(0, result.exit_code)

        make_params = ['-p', '25-15:15-25', '-p', '12:12', '-f', makefile, target]
        result = self._invoke_cli(global_params=global_params, subcmd='make', subcmd_params=make_params)
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual("Invalid port range: 25 should be bigger than 15", result.exception.message)
        # since click testing module messes up exit code
        # we just verify if the exit code is not 0
        self.assertNotEqual(0, result.exit_code)

    def test_run_with_publish_out_of_range_port(self):
        global_params = self.global_params
        global_params += ['--build-container-net', 'non-default-net']

        makefile = 'Makefile'
        target = 'all'
        make_params = ['-p', '123:1', '-p', '12:121111111', '-f', makefile, target]

        result = self._invoke_cli(global_params=global_params, subcmd='make', subcmd_params=make_params)
        self.assertIsInstance(result.exception, click.BadParameter)
        self.assertEqual("Invalid port number: port 121111111 is out of range", result.exception.message)
        # since click testing module messes up exit code
        # we just verify if the exit code is not 0
        self.assertNotEqual(0, result.exit_code)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_VOLUMES))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_defaults_from_config_file_including_volumes(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=['volume1', 'volume2'], workspace=None,
                                                        workdir=None, use_cache=False, env_file=())

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_WORKDIR))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_defaults_from_config_file_including_workdir(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir='test-workdir', workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_WORKSPACE))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_defaults_from_config_file_including_workspace(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace="/test/workspace", use_cache=False,
                                                        env_file=())

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_GIT_REV))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value=b'1234567\n'))
    @mock.patch('skipper.git.uncommitted_changes', mock.MagicMock(return_value=True))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_config_including_git_revision_with_uncommitted_changes(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'skipper-conf-build-container-image:1234567'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, use_cache=False, workspace=None,
                                                        env_file=())

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF_WITH_GIT_REV))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value=b'1234567\n'))
    @mock.patch('skipper.git.uncommitted_changes', mock.MagicMock(return_value=False))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_run_with_config_including_git_revision_without_uncommitted_changes(self, skipper_runner_run_mock):
        command = ['ls', '-l']
        run_params = command
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='run',
            subcmd_params=run_params
        )
        expected_fqdn_image = 'skipper-conf-build-container-image:1234567'
        skipper_runner_run_mock.assert_called_once_with(command, fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
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
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_make_with_default_params(self, skipper_runner_run_mock):
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='make',
        )
        expected_command = ['make', '-f', "Makefile"]
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_make_with_additional_make_params(self, skipper_runner_run_mock):
        target = 'all'
        make_params = ['-j', '4', target, 'OS=linux']
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='make',
            subcmd_params=make_params
        )
        expected_command = ['make', '-f', 'Makefile', '-j', '4', target, 'OS=linux']
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('skipper.config.load_defaults', mock.MagicMock(autospec=True, return_value=SKIPPER_CONF))
    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_make_with_defaults_from_config_file(self, skipper_runner_run_mock):
        makefile = 'Makefile'
        target = 'all'
        make_params = ['-f', makefile, target]
        self._invoke_cli(
            defaults=config.load_defaults(),
            subcmd='make',
            subcmd_params=make_params
        )
        expected_command = ['make', '-f', makefile, target]
        expected_fqdn_image = 'skipper-conf-build-container-image:skipper-conf-build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(expected_command, fqdn_image=expected_fqdn_image,
                                                        environment=[],
                                                        interactive=False, name=None, net=None, publish=(),
                                                        volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value=''))
    @mock.patch('skipper.utils.image_to_dockerfile', mock.MagicMock(autospec=True, side_effect=lambda x: 'Dockerfile.'+x))
    @mock.patch('skipper.runner.run', autospec=True, return_value=0)
    def test_make_without_build_container_tag(self, skipper_runner_run_mock):
        global_params = self.global_params[:-2]
        makefile = 'Makefile'
        target = 'all'
        make_params = ['-f', makefile, target]
        self._invoke_cli(
            global_params=global_params,
            subcmd='make',
            subcmd_params=make_params
        )
        expected_commands = [
            mock.call(['build', '--network=host', '-f', 'Dockerfile.build-container-image',
                      '-t', 'build-container-image', '.'],
                      stdout_to_stderr=True),
            mock.call(['make'] + make_params, fqdn_image='build-container-image', environment=[],
                      interactive=False, name=None, net=None, publish=(), volumes=None, workdir=None, workspace=None,
                      use_cache=False, env_file=()),
        ]
        skipper_runner_run_mock.assert_has_calls(expected_commands)

    @mock.patch('subprocess.check_output', mock.MagicMock(autospec=True, return_value='1234567\n'))
    @mock.patch('skipper.runner.run', autospec=True)
    def test_shell(self, skipper_runner_run_mock):
        self._invoke_cli(
            global_params=self.global_params,
            subcmd='shell',
        )
        expected_fqdn_image = 'build-container-image:build-container-tag'
        skipper_runner_run_mock.assert_called_once_with(['bash'], fqdn_image=expected_fqdn_image, environment=[],
                                                        interactive=True, name=None, net=None, publish=(), volumes=None,
                                                        workdir=None, workspace=None, use_cache=False,
                                                        env_file=())

    @mock.patch('click.echo', autospec=True)
    @mock.patch('skipper.cli.get_distribution', autospec=True)
    def test_version(self, get_dist_mock, echo_mock):
        expected_version = '1.2.3'
        get_dist_mock.return_value = mock.MagicMock()
        get_dist_mock.return_value.version = expected_version

        self._invoke_cli(
            subcmd='version',
        )
        echo_mock.assert_called_once_with(expected_version)

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
