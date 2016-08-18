import mock
import subprocess
import unittest
from skipper import docker


@mock.patch('subprocess.Popen', autospec=False)
class TestDocker(unittest.TestCase):
    def test_build_with_default_tag(self, popen_mock):
        popen_mock.return_value.poll.side_effect = [
            None,
            None,
            None,
            True,
        ]
        docker.build('/home/adir/proj', 'proj.Dockerfile')
        popen_mock.assert_called_once_with(
            ['docker', 'build', '-f', 'proj.Dockerfile', '-t', 'latest', '/home/adir/proj'],
            stdout=subprocess.PIPE
        )

    def test_build_with_custom_tag(self, popen_mock):
        docker.build('/home/adir/proj', 'proj.Dockerfile', 'some_tag')
        popen_mock.assert_called_once_with(
            ['docker', 'build', '-f', 'proj.Dockerfile', '-t', 'some_tag', '/home/adir/proj'],
            stdout=subprocess.PIPE
        )

    def test_run_simple_command(self, popen_mock):
        docker.run('/home/adir/workspace', 'proj', 1000, 2000, 'registry.io:5000/image', ['pwd'])
        popen_mock.assert_called_once_with(
            ['docker', 'run', '--rm', '--net', 'host',
             '-v', '/home/adir/workspace:/workspace:rw,Z', '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
             '-v', '/var/run/docker.sock:/var/run/docker.sock:Z', '-u', '1000:2000', '-w', '/workspace/proj',
             '--entrypoint', 'pwd', 'registry.io:5000/image'],
            stdout=subprocess.PIPE
        )

    def test_run_complex_command(self, popen_mock):
        docker.run('/home/adir/workspace', 'proj', 1000, 2000, 'registry.io:5000/image', ['ls', '-l'])
        popen_mock.assert_called_once_with(
            ['docker', 'run', '--rm', '--net', 'host',
             '-v', '/home/adir/workspace:/workspace:rw,Z', '-v', '/var/lib/osmosis:/var/lib/osmosis:rw,Z',
             '-v', '/var/run/docker.sock:/var/run/docker.sock:Z', '-u', '1000:2000', '-w', '/workspace/proj',
             '--entrypoint', 'ls', 'registry.io:5000/image', '-l'],
            stdout=subprocess.PIPE
        )
