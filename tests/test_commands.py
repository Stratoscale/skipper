import mock
import unittest
from skipper import commands


class TestCommands(unittest.TestCase):
    @mock.patch('skipper.docker.build', autospec=True)
    @mock.patch('skipper.git.get_hash', autospec=True, return_value='1234567')
    @mock.patch('os.getcwd', autospec=True, return_value='/home/adir/proj')
    def test_build(self, *args):
        commands.build('registry.io:5000', 'image', 'proj.Dockerfile')
        args[2].assert_called_once_with('/home/adir/proj', 'proj.Dockerfile', 'registry.io:5000/image:1234567')

    @mock.patch('skipper.docker.run', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('pwd.getpwnam', autospec=True)
    @mock.patch('os.getcwd', autospec=True, return_value='/home/adir/work/proj')
    def test_run(self, *args):
        args[1].return_value.pw_uid = 1000
        args[2].return_value.gr_gid = 2000
        commands.run('registry.io:5000', 'image', '1234567', ['ls', '-l'])
        args[3].assert_called_once_with(
            '/home/adir/work',
            'proj',
            1000,
            2000,
            'registry.io:5000/image:1234567',
            ['ls', '-l']
        )

    @mock.patch('skipper.docker.run', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('pwd.getpwnam', autospec=True)
    @mock.patch('os.getcwd', autospec=True, return_value='/home/adir/work/proj')
    def test_run_with_no_command(self, *args):
        args[1].return_value.pw_uid = 1000
        args[2].return_value.gr_gid = 2000
        commands.run('registry.io:5000', 'image', '1234567', [])
        self.assertFalse(args[3].called)

    @mock.patch('skipper.docker.run', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('pwd.getpwnam', autospec=True)
    @mock.patch('os.getcwd', autospec=True, return_value='/home/adir/work/proj')
    def test_make(self, *args):
        args[1].return_value.pw_uid = 1000
        args[2].return_value.gr_gid = 2000
        commands.make('registry.io:5000', 'image', '1234567', 'Makefile', 'all')
        args[3].assert_called_once_with(
            '/home/adir/work',
            'proj',
            1000,
            2000,
            'registry.io:5000/image:1234567',
            ['make', '-f', 'Makefile', 'all']
        )

    @mock.patch('logging.error')
    @mock.patch('__builtin__.open', create=True)
    @mock.patch('yaml.load', autospec=True)
    @mock.patch('skipper.docker.run', autospec=True)
    @mock.patch('grp.getgrnam', autospec=True)
    @mock.patch('pwd.getpwnam', autospec=True)
    @mock.patch('os.getcwd', autospec=True, return_value='/home/adir/work/proj')
    def test_depscheck(self, *args):
        args[1].return_value.pw_uid = 1000
        args[2].return_value.gr_gid = 2000
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
        args[3].return_value = installed_pips
        args[4].return_value = manifesto
        commands.depscheck('registry.io:5000', 'image', '1234567', '/tmp/manifesto.yaml')
