import unittest
import mock
from skipper import git


GIT_HASH_FULL = '00efe974e3cf18c3493f110f5aeda04ff78b125f'
GIT_HASH_SHORT = '00efe97'


class TestGit(unittest.TestCase):
    @mock.patch('subprocess.check_output', return_value=GIT_HASH_FULL)
    def test_get_hash_with_default_argument(self, check_output_mock):
        git_hash = git.get_hash()
        check_output_mock.assert_called_once_with(['git', 'rev-parse', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_FULL)

    @mock.patch('subprocess.check_output', return_value=GIT_HASH_FULL)
    def test_get_full_hash(self, check_output_mock):
        git_hash = git.get_hash(short=False)
        check_output_mock.assert_called_once_with(['git', 'rev-parse', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_FULL)

    @mock.patch('subprocess.check_output', return_value=GIT_HASH_SHORT)
    def test_get_short_hash(self, check_output_mock):
        git_hash = git.get_hash(short=True)
        check_output_mock.assert_called_once_with(['git', 'rev-parse', '--short', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_SHORT)
