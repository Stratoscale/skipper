import logging
from unittest import TestCase, mock

from skipper import builder
from skipper.builder import BuildOptions, Image


class TestBuilder(TestCase):
    def test_build_basic_usage(self):
        """Testing the basic usage of the 'build' function."""

        runner = mock.MagicMock()
        runner.run.return_value = 0

        options = BuildOptions(
            image=Image(
                name="test",
                tag="test",
                dockerfile="test",
            ),
            container_context=(),
        )
        expected_cmd = [
            "build",
            "--network=host",
            "-f",
            options.image.dockerfile,
            "-t",
            options.image.local,
            ".",
        ]

        result = builder.build(options, runner.run, logging.getLogger())
        self.assertEqual(0, result)
        runner.run.assert_called_once_with(expected_cmd)

    def test_build_with_build_args(self):
        """Testing the 'build' function with build args."""

        runner = mock.MagicMock()
        runner.run.return_value = 0

        options = BuildOptions(
            image=Image(
                name="test",
                tag="test",
                dockerfile="test",
            ),
            container_context=(),
            build_args=["test1", "test2"],
        )
        expected_cmd = [
            "build",
            "--network=host",
            "--build-arg",
            "test1",
            "--build-arg",
            "test2",
            "-f",
            options.image.dockerfile,
            "-t",
            options.image.local,
            ".",
        ]

        result = builder.build(options, runner.run, logging.getLogger())
        self.assertEqual(0, result)
        runner.run.assert_called_once_with(expected_cmd)

    def test_build_with_build_contexts(self):
        """Testing the 'build' function with build contexts."""

        runner = mock.MagicMock()
        runner.run.return_value = 0

        options = BuildOptions(
            image=Image(
                name="test",
                tag="test",
                dockerfile="test",
            ),
            container_context=(),
            build_contexts=["test1", "test2"],
        )
        expected_cmd = [
            "build",
            "--network=host",
            "--build-context",
            "test1",
            "--build-context",
            "test2",
            "-f",
            options.image.dockerfile,
            "-t",
            options.image.local,
            ".",
        ]

        result = builder.build(options, runner.run, logging.getLogger())
        self.assertEqual(0, result)
        runner.run.assert_called_once_with(expected_cmd)

    def test_build_with_use_cache(self):
        """Testing the 'build' function with use cache."""

        runner = mock.MagicMock()
        runner.run.return_value = 0

        options = BuildOptions(
            image=Image(
                name="test",
                tag="test",
                dockerfile="test",
            ),
            container_context=(),
            use_cache=True,
        )
        expected_cmds = [
            mock.call(
                [
                    "build",
                    "--network=host",
                    "--cache-from",
                    options.image.cache_fqdn,
                    "-f",
                    options.image.dockerfile,
                    "-t",
                    options.image.local,
                    ".",
                ]
            ),
            mock.call(["pull", options.image.cache_fqdn]),
            mock.call(["tag", options.image.name, options.image.cache_fqdn]),
        ]

        result = builder.build(options, runner.run, logging.getLogger())
        self.assertEqual(0, result)
        runner.run.has_calls(expected_cmds)

    def test_build_with_options_from_context(self):
        """Testing the 'build' function with options from context."""

        runner = mock.MagicMock()
        runner.run.return_value = 0

        ctx_obj = {
            "build_container_image": "test",
            "build_container_tag": "test",
            "container_context": (),
            "build_contexts": ["test1", "test2"],
            "build_args": ["test1", "test2"],
            "use_cache": True,
        }
        expected_cmds = [
            mock.call(
                [
                    "build",
                    "--network=host",
                    "--cache-from",
                    "test:test",
                    "--build-arg",
                    "test1",
                    "--build-arg",
                    "test2",
                    "--build-context",
                    "test1",
                    "--build-context",
                    "test2",
                    "-f",
                    "test",
                    "-t",
                    "test:test",
                    ".",
                ]
            ),
            mock.call(["pull", "test:test"]),
            mock.call(["tag", "test", "test:test"]),
        ]

        result = builder.build(
            BuildOptions.from_context_obj(ctx_obj), runner.run, logging.getLogger()
        )
        self.assertEqual(0, result)
        runner.run.has_calls(expected_cmds)

    def test_build_fail(self):
        """Testing the 'build' function when the build fails."""

        runner = mock.MagicMock()
        runner.run.return_value = 1

        options = BuildOptions(
            image=Image(
                name="test",
                tag="test",
                dockerfile="test",
            ),
            container_context=(),
        )

        result = builder.build(options, runner.run, logging.getLogger())
        self.assertEqual(1, result)
        runner.run.assert_called_once()

    def test_build_fail_without_image_name(self):
        """Testing the 'build' function when the image name is not specified."""

        ctx_obj = {
            "build_container_tag": "test",
            "container_context": (),
            "build_contexts": ["test1", "test2"],
            "build_args": ["test1", "test2"],
            "use_cache": True,
        }

        self.assertRaises(ValueError, BuildOptions.from_context_obj, ctx_obj)
