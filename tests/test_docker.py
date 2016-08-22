import mock
import os
import subprocess
import unittest
from skipper import docker


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


@mock.patch('subprocess.Popen', autospec=False)
class TestDocker(unittest.TestCase):
    def test_build_with_default_tag(self, popen_mock):
        popen_mock.return_value.poll.side_effect = [None, None, None, True]
        dockerfile = 'proj.Dockerfile'
        docker.build(WORKDIR, dockerfile)
        expected_docker_command = ['docker', 'build', '-f', dockerfile, '-t', 'latest', WORKDIR]
        popen_mock.assert_called_once_with(
            expected_docker_command,
            stdout=subprocess.PIPE
        )

    def test_build_with_custom_tag(self, popen_mock):
        dockerfile = 'proj.Dockerfile'
        docker.build(PROJECT_DIR, dockerfile, TAG)
        popen_mock.assert_called_once_with(
            ['docker', 'build', '-f', dockerfile, '-t', TAG, PROJECT_DIR],
            stdout=subprocess.PIPE
        )

    def test_run_simple_command(self, popen_mock):
        command = ['pwd']
        docker.run(WORKDIR, PROJECT, USER_ID, GROUP_ID, FQDN_IMAGE, None, command)
        expected_docker_command = [
            'docker', 'run',
            '--rm',
            '--net', 'host',
            '-v', '%(workdir)s:/workspace:rw,Z' % dict(workdir=WORKDIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-u', '%(uid)s:%(gid)s' % dict(uid=USER_ID, gid=GROUP_ID),
            '-w', '/workspace/proj',
            '--entrypoint', command[0],
            FQDN_IMAGE
        ]
        popen_mock.assert_called_once_with(
            expected_docker_command,
            stdout=subprocess.PIPE
        )

    def test_run_simple_command_with_env(self, popen_mock):
        command = ['pwd']
        docker.run(WORKDIR, PROJECT, USER_ID, GROUP_ID, FQDN_IMAGE, ENV, command)
        expected_docker_command = [
            'docker', 'run',
            '--rm',
            '--net', 'host',
            '-e', 'KEY1=VAL1',
            '-e', 'KEY2=VAL2',
            '-v', '%(workdir)s:/workspace:rw,Z' % dict(workdir=WORKDIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-u', '%(uid)s:%(gid)s' % dict(uid=USER_ID, gid=GROUP_ID),
            '-w', '/workspace/proj',
            '--entrypoint', command[0],
            FQDN_IMAGE
        ]
        popen_mock.assert_called_once_with(
            expected_docker_command,
            stdout=subprocess.PIPE
        )

    def test_run_complex_command(self, popen_mock):
        command = ['ls', '-l']
        docker.run(WORKDIR, PROJECT, USER_ID, GROUP_ID, FQDN_IMAGE, None, command)
        expected_docker_command = [
            'docker', 'run',
            '--rm',
            '--net', 'host',
            '-v', '%(workdir)s:/workspace:rw,Z' % dict(workdir=WORKDIR),
            '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
            '-v', '/var/run/docker.sock:/var/run/docker.sock:Z',
            '-u', '%(uid)s:%(gid)s' % dict(uid=USER_ID, gid=GROUP_ID),
            '-w', '/workspace/proj',
            '--entrypoint', command[0],
            FQDN_IMAGE,
            command[1]
        ]
        popen_mock.assert_called_once_with(
            expected_docker_command,
            stdout=subprocess.PIPE
        )
