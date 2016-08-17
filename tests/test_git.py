import unittest
import mock
from skipper import git


@mock.patch('subprocess.check_output')
class TestGit(unittest.TestCase):
    def test_get_short_hash(self, check_output_mock):
        hash = git.get_hash(short=True)
        check_output_mock.assert_called_once_with(['git', 'rev-parse', '--short', 'HEAD'])

    def test_get_full_hash(self, check_output_mock):
        hash = git.get_hash(short=False)
        check_output_mock.assert_called_once_with(['git', 'rev-parse', 'HEAD'])

