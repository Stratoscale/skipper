import json
import os
from shutil import which
from unittest import TestCase, mock

from skipper import config
from tests.consts import (
    REGISTRY,
    SKIPPER_CONF_BUILD_CONTAINER_TAG,
    SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
    SKIPPER_CONF_MAKEFILE,
)

ENV_FILE_PATH = "/home/envfile.env"
CONFIG_ENV = {"KEY2": "NOT_VAL2", "KEY3": "VAL3", "KEY4": "$VAL4", "KEY5": "$$VAL5"}

CONFIG_ENV_EVALUATION = {
    "KEY2": "NOT_VAL2",
    "KEY3": "VAL3",
    "KEY4": "val4-evaluation",
    "KEY5": "$VAL5",
}

SKIPPER_CONF_WITH_ENV = json.dumps(
    {
        "registry": REGISTRY,
        "build-container-image": SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
        "build-container-tag": SKIPPER_CONF_BUILD_CONTAINER_TAG,
        "make": {
            "makefile": SKIPPER_CONF_MAKEFILE,
        },
        "env": CONFIG_ENV,
    }
)

SKIPPER_CONF_WITH_ENV_FILE = json.dumps(
    {
        "registry": REGISTRY,
        "build-container-image": SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
        "build-container-tag": SKIPPER_CONF_BUILD_CONTAINER_TAG,
        "make": {
            "makefile": SKIPPER_CONF_MAKEFILE,
        },
        "env_file": [ENV_FILE_PATH],
    }
)

SKIPPER_CONF_WITH_SHELL_INTERPOLATION = json.dumps(
    {
        "registry": REGISTRY,
        "build-container-image": SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
        "build-container-tag": SKIPPER_CONF_BUILD_CONTAINER_TAG,
        "make": {
            "makefile": SKIPPER_CONF_MAKEFILE,
        },
        "volumes": [
            "$(which cat):/cat",
        ],
        "env": ["KEY=$(expr ${MY_NUMBER:-5} + 5)"],
    }
)

SKIPPER_CONF_WITH_INVALID_SHELL_INTERPOLATION = json.dumps(
    {
        "registry": REGISTRY,
        "build_container_image": SKIPPER_CONF_BUILD_CONTAINER_IMAGE,
        "build_container_tag": SKIPPER_CONF_BUILD_CONTAINER_TAG,
        "make": {
            "makefile": SKIPPER_CONF_MAKEFILE,
        },
        "volumes": [
            "$(bla bla):/cat",
        ],
    }
)


class TestConfig(TestCase):
    @mock.patch(
        "builtins.open",
        mock.MagicMock(side_effect=mock.mock_open(read_data=SKIPPER_CONF_WITH_ENV)),
    )
    @mock.patch("os.path.exists", mock.MagicMock(autospec=True, return_value=True))
    def test_config_with_env_eval(self):
        os.environ["VAL4"] = "val4-evaluation"
        defaults = config.load_defaults()

        self.assertEqual(CONFIG_ENV_EVALUATION, defaults.get("env"))
        self.assertEqual(
            defaults.get("build_container_image"), SKIPPER_CONF_BUILD_CONTAINER_IMAGE
        )
        self.assertEqual(
            defaults.get("build_container_tag"), SKIPPER_CONF_BUILD_CONTAINER_TAG
        )

    @mock.patch(
        "builtins.open",
        mock.MagicMock(
            side_effect=mock.mock_open(read_data=SKIPPER_CONF_WITH_SHELL_INTERPOLATION)
        ),
    )
    @mock.patch("os.path.exists", mock.MagicMock(autospec=True, return_value=True))
    def test_config_with_interpolation(self):
        defaults = config.load_defaults()

        self.assertEqual(defaults.get("env"), ["KEY=10"])
        self.assertEqual(defaults.get("volumes"), [f'{which("cat")}:/cat'])

    @mock.patch(
        "builtins.open",
        mock.MagicMock(
            side_effect=mock.mock_open(
                read_data=SKIPPER_CONF_WITH_INVALID_SHELL_INTERPOLATION
            )
        ),
    )
    @mock.patch("os.path.exists", mock.MagicMock(autospec=True, return_value=True))
    def test_config_with_wrong_interpolation(self):
        with self.assertRaises(ValueError):
            config.load_defaults()
