import os
import unittest
import mock
from skipper import utils
from skipper import runner
from skipper.runner import get_default_net
from tests.test_runner import get_volume_mapping

USER_ID = 1000
GROUP_ID = 2000

REGISTRY = 'registry.io:5000'
IMAGE = 'image'
TAG = '1234567'
FQDN_IMAGE = REGISTRY + '/' + IMAGE + ':' + TAG

WORKDIR = '/home/adir/work'
HOME_DIR = '/home/adir'
PROJECT = 'proj'
PROJECT_DIR = os.path.join(WORKDIR, PROJECT)

ENV = ["KEY1=VAL1", "KEY2=VAL2"]


@mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
class TestRunnerPodman(unittest.TestCase):

    def setUp(self):
        self.runtime = "podman"
        utils.CONTAINER_RUNTIME_COMMAND = self.runtime
        os.environ['KEEP_CONTAINERS'] = 'True'

    @mock.patch('subprocess.Popen', autospec=False)
    def test_run_simple_command_not_nested(self, popen_mock):
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        command = ['pwd']
        runner.run(command)
        popen_mock.assert_called_once_with([self.runtime] + command)

    @mock.patch('subprocess.Popen', autospec=False)
    def test_run_complex_command_not_nested(self, popen_mock):
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        command = ['ls -l']
        runner.run(command)
        popen_mock.assert_called_once_with([self.runtime] + command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_simple_command_nested_network_exist(self, resource_filename_mock, check_output_mock, popen_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE)
        expected_nested_command = [
            self.runtime, 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker/config.json:%(homedir)s/.docker/config.json:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw,shared' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:rw'),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        assert not check_output_mock.called
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=True)
    def test_run_simple_command_nested_network_not_exist(self, resource_filename_mock, check_output_mock, popen_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE)
        expected_nested_command = [
            self.runtime, 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker/config.json:%(homedir)s/.docker/config.json:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw,shared' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:rw'),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        assert not check_output_mock.called
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_complex_command_nested(self, resource_filename_mock, check_output_mock, popen_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        os_getuid_mock.return_value = USER_ID
        command = ['ls', '-l']
        runner.run(command, FQDN_IMAGE)
        expected_nested_command = [
            self.runtime, 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker/config.json:%(homedir)s/.docker/config.json:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw,shared' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:rw'),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            ' '.join(command)
        ]
        assert not check_output_mock.called
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_complex_command_nested_with_env(self, resource_filename_mock, check_output_mock, popen_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        os_getuid_mock.return_value = USER_ID
        command = ['ls', '-l']
        runner.run(command, FQDN_IMAGE, ENV)
        expected_nested_command = [
            self.runtime, 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'KEY1=VAL1',
            '-e', 'KEY2=VAL2',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker/config.json:%(homedir)s/.docker/config.json:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw,shared' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:rw'),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            ' '.join(command)
        ]
        assert not check_output_mock.called
        popen_mock.assert_called_once_with(expected_nested_command)
