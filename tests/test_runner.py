import sys
import os
import unittest
import mock
from skipper import utils
from skipper import runner
from skipper.runner import get_default_net

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
ENV_FILE_PATH = '/home/envfile.env'
ENV_FILES = [ENV_FILE_PATH, ENV_FILE_PATH]


def get_volume_mapping(volume_mapping):
    if sys.platform == 'darwin':
        if volume_mapping.startswith('/etc/') or volume_mapping.startswith('/var/lib/'):
            return '/private' + volume_mapping

    return volume_mapping


class TestRunner(unittest.TestCase):

    NET_LS = 'NETWORK ID          NAME                DRIVER              SCOPE\n' \
             '8c954c27cf41        host                host                local\n'
    NET_NOT_EXISTS = 'NETWORK ID          NAME                DRIVER              SCOPE\n'

    def setUp(self):
        self.runtime = "docker"
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

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_simple_command_nested_network_exist(self, resource_filename_mock, check_output_mock,
                                                     popen_mock, grp_getgrnam_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_LS, '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE)
        expected_nested_command = [
            'docker', 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker:%(homedir)s/.docker:rw' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_simple_command_nested_network_not_exist(self, resource_filename_mock,
                                                         check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_NOT_EXISTS, 'new-net-hash', '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE)
        expected_nested_command = [
            'docker', 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker:%(homedir)s/.docker:rw' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_simple_command_nested_with_env(self, resource_filename_mock, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_LS, '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE, ENV)
        expected_docker_command = [
            'docker', 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'KEY1=VAL1',
            '-e', 'KEY2=VAL2',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker:%(homedir)s/.docker:rw' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_docker_command)

    @mock.patch('os.path.exists',
                mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('getpass.getuser',
                mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd',
                mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser',
                mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_simple_command_nested_with_env_file(
            self, resource_filename_mock, check_output_mock, popen_mock,
            grp_getgrnam_mock, os_getuid_mock
    ):
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_LS, '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb',
                                                               'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE, env_file=[ENV_FILE_PATH])
        expected_docker_command = [
            'docker', 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', get_default_net(),
            '--env-file', ENV_FILE_PATH,
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(
                homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(
                homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker:%(homedir)s/.docker:rw' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_docker_command)

    @mock.patch('os.path.exists',
                mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('getpass.getuser',
                mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd',
                mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser',
                mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_simple_command_nested_with_multiple_env_files(
            self, resource_filename_mock, check_output_mock, popen_mock,
            grp_getgrnam_mock, os_getuid_mock
    ):
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_LS, '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb',
                                                               'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE, env_file=ENV_FILES)
        expected_docker_command = [
            'docker', 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', 'host',
            '--env-file', ENV_FILE_PATH,
            '--env-file', ENV_FILE_PATH,
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(
                homedir=HOME_DIR),
            '-v', '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(
                homedir=HOME_DIR),
            '-v', get_volume_mapping('%(homedir)s/.docker:%(homedir)s/.docker:rw' % dict(
                homedir=HOME_DIR)),
            '-v', '/etc/docker:/etc/docker:ro',
            '-v', '%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR),
            '-v', '/var/run/docker.sock:/var/run/docker.sock:rw',
            '-v', 'entrypoint.sh:/opt/skipper/skipper-entrypoint.sh',
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw',
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_docker_command)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_simple_command_nested_interactive(self, resource_filename_mock,
                                                   check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_LS, '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE, interactive=True)

        expected_nested_command = [
            'docker', 'run',
            '-i',
            '-e', 'SKIPPER_INTERACTIVE=True',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker:%(homedir)s/.docker:rw' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_complex_command_nested(self, resource_filename_mock, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_LS, '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['ls', '-l']
        runner.run(command, FQDN_IMAGE)
        expected_nested_command = [
            'docker', 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker:%(homedir)s/.docker:rw' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            ' '.join(command)
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('os.path.exists', mock.MagicMock(autospec=True, return_value=True))
    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_complex_command_nested_with_env(self, resource_filename_mock, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_LS, '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['ls', '-l']
        runner.run(command, FQDN_IMAGE, ENV, name="test")
        expected_nested_command = [
            'docker', 'run',
            '--name',
            'test',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'KEY1=VAL1',
            '-e', 'KEY2=VAL2',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', get_volume_mapping('%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('%(homedir)s/.docker:%(homedir)s/.docker:rw' % dict(homedir=HOME_DIR)),
            '-v', get_volume_mapping('/etc/docker:/etc/docker:ro'),
            '-v', get_volume_mapping('%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR)),
            '-v', get_volume_mapping('/var/run/docker.sock:/var/run/docker.sock:rw'),
            '-v', get_volume_mapping('entrypoint.sh:/opt/skipper/skipper-entrypoint.sh'),
            '-v', get_volume_mapping('/var/lib/osmosis:/var/lib/osmosis:rw'),
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            ' '.join(command)
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('skipper.runner.utils.create_path_and_add_data', autospec=True)
    @mock.patch('os.path.exists', autospec=True)
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    @mock.patch('pkg_resources.resource_filename', autospec=False)
    def test_run_complex_command_nested_with_special_case_verification(self, resource_filename_mock, check_output_mock,
                                                                       popen_mock, grp_getgrnam_mock, os_getuid_mock,
                                                                       path_exists_mock, create_path_and_add_data_mock):

        path_exists_mock.return_value = False
        resource_filename_mock.return_value = "entrypoint.sh"
        check_output_mock.side_effect = [self.NET_LS, '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['ls', '-l']
        volumes = []
        runner.run(command, FQDN_IMAGE, ENV, name="test", volumes=volumes)
        expected_nested_command = [
            'docker', 'run',
            '--name',
            'test',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--ulimit', 'nofile=65536:65536',
            '--privileged',
            '--net', get_default_net(),
            '-e', 'KEY1=VAL1',
            '-e', 'KEY2=VAL2',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'CONTAINER_RUNTIME_COMMAND=%(runtime_command)s' % dict(runtime_command=utils.get_runtime_command()),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR),
            '-v', '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR),
            '-v', '%(workdir)s:%(workdir)s:rw' % dict(workdir=WORKDIR),
            '-v', '/var/run/docker.sock:/var/run/docker.sock:rw',
            '-v', 'entrypoint.sh:/opt/skipper/skipper-entrypoint.sh',
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            ' '.join(command)
        ]
        calls = [
            mock.call(full_path="/home/adir/.gitconfig", data="", is_file=True)
        ]
        create_path_and_add_data_mock.assert_has_calls(calls, any_order=True)
        popen_mock.assert_called_once_with(expected_nested_command)

    def test_handle_volumes_bind_mount_with_bad_volume_mount(self):
        docker_cmd = ['docker', 'run']
        volumes = ['bad volume mount']
        with self.assertRaises(ValueError):
            runner.handle_volumes_bind_mount(docker_cmd, HOME_DIR, volumes, WORKDIR)
