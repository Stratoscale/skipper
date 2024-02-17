import subprocess
import unittest
import mock
from skipper import git


GIT_HASH_FULL = b'00efe974e3cf18c3493f110f5aeda04ff78b125f'
GIT_HASH_SHORT = b'00efe97'


class TestGit(unittest.TestCase):
    @mock.patch('subprocess.check_output', return_value=GIT_HASH_FULL)
    @mock.patch('skipper.git.is_git_repository', return_value=True)
    def test_get_hash_with_default_argument(self, is_git_repository_mock, check_output_mock):
        git_hash = git.get_hash()
        is_git_repository_mock.assert_called_once()
        check_output_mock.assert_called_once_with(['git', 'rev-parse', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_FULL.decode('utf-8'))

    @mock.patch('subprocess.check_output', return_value=GIT_HASH_FULL)
    @mock.patch('skipper.git.is_git_repository', return_value=True)
    def test_get_full_hash(self, is_git_repository_mock, check_output_mock):
        git_hash = git.get_hash(short=False)
        is_git_repository_mock.assert_called_once()
        check_output_mock.assert_called_once_with(['git', 'rev-parse', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_FULL.decode('utf-8'))

    @mock.patch('subprocess.check_output', return_value=GIT_HASH_SHORT)
    @mock.patch('skipper.git.is_git_repository', return_value=True)
    def test_get_short_hash(self, is_git_repository_mock, check_output_mock):
        git_hash = git.get_hash(short=True)
        is_git_repository_mock.assert_called_once()
        check_output_mock.assert_called_once_with(['git', 'rev-parse', '--short', 'HEAD'])
        self.assertEqual(git_hash, GIT_HASH_SHORT.decode('utf-8'))

    @mock.patch('skipper.git.is_git_repository', return_value=False)
    def test_not_in_git_project(self, is_git_repository_mock):
        self.assertEqual(git.get_hash(), 'none')
        is_git_repository_mock.assert_called_once()

    @mock.patch('os.path.exists', return_value=True)
    def test_should_be_in_git_project_os_path(self, exists_mock):
        self.assertTrue(git.is_git_repository())
        exists_mock.assert_called_once_with('.git')

    @mock.patch('subprocess.call', return_value=0)
    @mock.patch('os.path.exists', return_value=False)
    def test_should_be_in_git_project_git(self, exists_mock, call_mock):
        self.assertTrue(git.is_git_repository())
        exists_mock.assert_called_once_with('.git')
        call_mock.assert_called_once_with(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @mock.patch('subprocess.call', return_value=1)
    @mock.patch('os.path.exists', return_value=False)
    def test_should_not_be_in_git_project(self, exists_mock, call_mock):
        self.assertFalse(git.is_git_repository())
        exists_mock.assert_called_once_with('.git')
        call_mock.assert_called_once_with(['git', 'rev-parse', '--is-inside-work-tree'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
