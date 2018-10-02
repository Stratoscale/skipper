import mock
import os
import unittest
from skipper import runner


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


class TestRunner(unittest.TestCase):

    def setUp(self):
        os.environ['KEEP_CONTAINERS'] = 'True'

    @mock.patch('subprocess.Popen', autospec=False)
    def test_run_simple_command_not_nested(self, popen_mock):
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        command = ['pwd']
        runner.run(command)
        popen_mock.assert_called_once_with(command)

    @mock.patch('subprocess.Popen', autospec=False)
    def test_run_complex_command_not_nested(self, popen_mock):
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        command = ['ls -l']
        runner.run(command)
        popen_mock.assert_called_once_with(command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    def test_run_simple_command_nested_network_exist(self, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        check_output_mock.side_effect = ['d3be68b723d3\n', '']
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
            '--privileged',
            '--net', 'host',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', '%(workdir)s:%(workdir)s:rw,Z' % dict(workdir=WORKDIR),
            '-v', '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR),
            '-v', '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-v', '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    def test_run_simple_command_nested_network_not_exist(self, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        check_output_mock.side_effect = ['', 'new-net-hash', '']
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
            '--privileged',
            '--net', 'host',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', '%(workdir)s:%(workdir)s:rw,Z' % dict(workdir=WORKDIR),
            '-v', '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR),
            '-v', '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-v', '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    def test_run_simple_command_nested_with_env(self, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        check_output_mock.side_effect = ['d3be68b723d3\n', '']
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
            '--privileged',
            '--net', 'host',
            '-e', 'KEY1=VAL1',
            '-e', 'KEY2=VAL2',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', '%(workdir)s:%(workdir)s:rw,Z' % dict(workdir=WORKDIR),
            '-v', '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR),
            '-v', '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-v', '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_docker_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    def test_run_simple_command_nested_interactive(self, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        check_output_mock.side_effect = ['d3be68b723d3\n', '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['pwd']
        runner.run(command, FQDN_IMAGE, interactive=True)
        expected_nested_command = [
            'docker', 'run',
            '-i',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--privileged',
            '--net', 'host',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', '%(workdir)s:%(workdir)s:rw,Z' % dict(workdir=WORKDIR),
            '-v', '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR),
            '-v', '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-v', '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            command[0]
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    def test_run_complex_command_nested(self, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        check_output_mock.side_effect = ['d3be68b723d3\n', '']
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
            '--privileged',
            '--net', 'host',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', '%(workdir)s:%(workdir)s:rw,Z' % dict(workdir=WORKDIR),
            '-v', '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR),
            '-v', '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-v', '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            ' '.join(command)
        ]
        popen_mock.assert_called_once_with(expected_nested_command)

    @mock.patch('getpass.getuser', mock.MagicMock(autospec=True, return_value='testuser'))
    @mock.patch('os.getcwd', mock.MagicMock(autospec=True, return_value=PROJECT_DIR))
    @mock.patch('os.path.expanduser', mock.MagicMock(autospec=True, return_value=HOME_DIR))
    @mock.patch('os.getuid', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('subprocess.Popen', autospec=False)
    @mock.patch('subprocess.check_output', autospec=False)
    def test_run_complex_command_nested_with_env(self, check_output_mock, popen_mock, grp_getgrnam_mock, os_getuid_mock):
        check_output_mock.side_effect = ['d3be68b723d3\n', '']
        popen_mock.return_value.stdout.readline.side_effect = ['aaa', 'bbb', 'ccc', '']
        popen_mock.return_value.poll.return_value = -1
        grp_getgrnam_mock.return_value.gr_gid = 978
        os_getuid_mock.return_value = USER_ID
        command = ['ls', '-l']
        runner.run(command, FQDN_IMAGE, ENV)
        expected_nested_command = [
            'docker', 'run',
            '-t',
            '-e', 'KEEP_CONTAINERS=True',
            '--privileged',
            '--net', 'host',
            '-e', 'KEY1=VAL1',
            '-e', 'KEY2=VAL2',
            '-e', 'SKIPPER_USERNAME=testuser',
            '-e', 'SKIPPER_UID=%(user_uid)s' % dict(user_uid=USER_ID),
            '-e', 'HOME=%(homedir)s' % dict(homedir=HOME_DIR),
            '-e', 'SKIPPER_DOCKER_GID=978',
            '-v', '%(workdir)s:%(workdir)s:rw,Z' % dict(workdir=WORKDIR),
            '-v', '%(homedir)s/.netrc:%(homedir)s/.netrc:ro' % dict(homedir=HOME_DIR),
            '-v', '%(homedir)s/.gitconfig:%(homedir)s/.gitconfig:ro' % dict(homedir=HOME_DIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-v', '/opt/skipper/skipper-entrypoint.sh:/opt/skipper/skipper-entrypoint.sh:Z',
            '-w', PROJECT_DIR,
            '--entrypoint', '/opt/skipper/skipper-entrypoint.sh',
            FQDN_IMAGE,
            ' '.join(command)
        ]
        popen_mock.assert_called_once_with(expected_nested_command)
