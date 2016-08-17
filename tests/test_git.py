import unittest
import mock
from skipper import git


class TestGit(unittest.TestCase):
    @mock.patch('subprocess.check_output')
    def test_get_short_hash(self, check_output_mock):
        hash = git.get_hash(short=True)
        check_output_mock.assert_called_once_with(['git', 'rev-parse', '--short', 'HEAD'])
