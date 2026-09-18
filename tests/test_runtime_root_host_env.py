import os
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

from scripts.runtime_root import RuntimeRootError
from scripts.runtime_root import resolve_runtime_root_with_source


class RuntimeRootHostEnvironmentTests(unittest.TestCase):
    def _without_host_runtime_environment(self):
        names = ("JDIPT_RUNTIME_ROOT", "CLAUDE_PLUGIN_DATA", "PLUGIN_DATA", "CODEX_HOME")
        previous = {name: os.environ.pop(name, None) for name in names}
        return names, previous

    def _restore_host_runtime_environment(self, names, previous):
        os.environ.update(
            {
                name: value
                for name, value in previous.items()
                if value is not None
            }
        )

    def test_runtime_root_uses_host_plugin_data_when_codex_home_is_absent(self):
        names, previous = self._without_host_runtime_environment()
        with tempfile.TemporaryDirectory() as temporary:
            os.environ["CLAUDE_PLUGIN_DATA"] = temporary
            try:
                resolved = resolve_runtime_root_with_source()
            finally:
                os.environ.pop("CLAUDE_PLUGIN_DATA", None)
                self._restore_host_runtime_environment(names, previous)

        self.assertEqual(resolved.root, Path(temporary))
        self.assertEqual(resolved.source, "CLAUDE_PLUGIN_DATA")

    def test_runtime_root_derives_data_root_from_official_plugin_cache_cwd(self):
        names, previous = self._without_host_runtime_environment()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                plugin_root = (
                    Path(temporary)
                    / ".codex"
                    / "plugins"
                    / "cache"
                    / "sage1993"
                    / "jdipt"
                    / "0.2.6"
                )
                plugin_root.mkdir(parents=True)
                with patch("scripts.runtime_root.Path.cwd", return_value=plugin_root):
                    resolved = resolve_runtime_root_with_source()
                expected = (
                    Path(temporary)
                    / ".codex"
                    / "plugins"
                    / "data"
                    / "jdipt-sage1993"
                )
                self.assertEqual(resolved.root, expected)
                self.assertEqual(resolved.source, "PLUGIN_CWD")
        finally:
            self._restore_host_runtime_environment(names, previous)

    def test_unrelated_cwd_cannot_invent_a_runtime_root(self):
        names, previous = self._without_host_runtime_environment()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                with patch("scripts.runtime_root.Path.cwd", return_value=Path(temporary)):
                    with self.assertRaisesRegex(
                        RuntimeRootError,
                        "RUNTIME_ROOT_REQUIRED",
                    ):
                        resolve_runtime_root_with_source()
        finally:
            self._restore_host_runtime_environment(names, previous)
