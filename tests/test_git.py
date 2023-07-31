import unittest
import mock
from skipper import git


GIT_HASH_FULL = b'00efe974e3cf18c3493f110f5aeda04ff78b125f'
GIT_HASH_SHORT = b'00efe97'


class TestGit(unittest.TestCase):
    @mock.patch('subprocess.check_output', return_value=GIT_HASH_FULL)
    @mock.patch('os.path.exists', return_value=True)
    def test_get_hash_with_default_argument(self, exists_mock, check_output_mock):
        git_hash = git.get_hash()
        exists_mock.assert_called_once_with('.git')
        check_output_mock.assert_called_once_with(['git', 'rev-parse', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_FULL.decode('utf-8'))

    @mock.patch('subprocess.check_output', return_value=GIT_HASH_FULL)
    @mock.patch('os.path.exists', return_value=True)
    def test_get_full_hash(self, exists_mock, check_output_mock):
        git_hash = git.get_hash(short=False)
        exists_mock.assert_called_once_with('.git')
        check_output_mock.assert_called_once_with(['git', 'rev-parse', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_FULL.decode('utf-8'))

    @mock.patch('subprocess.check_output', return_value=GIT_HASH_SHORT)
    @mock.patch('os.path.exists', return_value=True)
    def test_get_short_hash(self, exists_mock, check_output_mock):
        git_hash = git.get_hash(short=True)
        exists_mock.assert_called_once_with('.git')
        check_output_mock.assert_called_once_with(['git', 'rev-parse', '--short', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_SHORT.decode('utf-8'))

    @mock.patch('subprocess.check_output')
    @mock.patch('os.path.exists', return_value=False)
    def test_not_in_git_project(self, exists_mock, check_output_mock):
        git_hash = git.get_hash()
        exists_mock.assert_called_once_with('.git')
        check_output_mock.assert_not_called()
        self.assertEqual(git_hash, 'none')
