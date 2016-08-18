import mock
import os
import unittest
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


class TestCommands(unittest.TestCase):
    @mock.patch('skipper.git.get_hash', autospec=True, return_value=TAG)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('skipper.docker.build', autospec=True)
    def test_build(self, skipper_docker_build_mock, *args):
        dockerfile = 'proj.Dockerfile'
        commands.build(REGISTRY, IMAGE, dockerfile)
        skipper_docker_build_mock.assert_called_once_with(PROJECT_DIR, dockerfile, FQDN_IMAGE)

    @mock.patch('os.getuid', autospec=True, return_value=USER_ID)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('skipper.docker.run', autospec=True)
    def test_run(self, skipper_docker_run_mock, getgrnam_mock, *args):
        command = ['ls', '-l']
        getgrnam_mock.return_value.gr_gid = GROUP_ID
        commands.run(REGISTRY, IMAGE, TAG,  command)
        skipper_docker_run_mock.assert_called_once_with(
            WORKDIR,
            PROJECT,
            USER_ID,
            GROUP_ID,
            FQDN_IMAGE,
            command
        )

    @mock.patch('os.getuid', autospec=True, return_value=USER_ID)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('skipper.docker.run', autospec=True)
    def test_run_with_no_command(self, skipper_docker_run_mock, getgrnam_mock, *args):
        getgrnam_mock.return_value.gr_gid = GROUP_ID
        commands.run(REGISTRY, IMAGE, TAG, [])
        self.assertFalse(skipper_docker_run_mock.called)

    @mock.patch('os.getuid', autospec=True, return_value=USER_ID)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('skipper.docker.run', autospec=True)
    def test_make(self, skipper_docker_run_mock, getgrnam_mock, *args):
        makefile = 'Makefile'
        target = 'all'
        getgrnam_mock.return_value.gr_gid = GROUP_ID
        commands.make(REGISTRY, IMAGE, TAG, makefile, target)
        skipper_docker_run_mock.assert_called_once_with(
            WORKDIR,
            PROJECT,
            USER_ID,
            GROUP_ID,
            FQDN_IMAGE,
            ['make', '-f', makefile, target]
        )

    @mock.patch('__builtin__.open', create=True)
    @mock.patch('os.getuid', autospec=True, return_value=USER_ID)
    @mock.patch('os.getcwd', autospec=True, return_value=PROJECT_DIR)
    @mock.patch('yaml.load', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True,)
    @mock.patch('skipper.docker.run', autospec=True)
    def test_depscheck(self, skipper_docker_run_mock, getgrnam_mock, yaml_load_mock, *args):
        getgrnam_mock.return_value.gr_gid = GROUP_ID
        installed_pips = [
            'pkg1===a43e12d',
            'pkg2===b360f75',
            'pkg3==0.0.1',
            '',
        ]
        manifesto = {
            'requirements': [
                dict(revision='b34a12b', pips=['pkg1']),
                dict(revision='b360f75', pips=['pkg2']),
                dict(revision='21e76c1', pips=None),
            ]
        }
        skipper_docker_run_mock.return_value = installed_pips
        yaml_load_mock.return_value = manifesto
        commands.depscheck(REGISTRY, IMAGE, TAG, '/tmp/manifesto.yaml')
