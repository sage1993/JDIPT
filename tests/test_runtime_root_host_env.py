import os
from pathlib import Path
import tempfile
import unittest

from scripts.runtime_root import resolve_runtime_root_with_source


class RuntimeRootHostEnvironmentTests(unittest.TestCase):
    def test_runtime_root_uses_host_plugin_data_when_codex_home_is_absent(self):
        names = ("JDIPT_RUNTIME_ROOT", "PLUGIN_DATA", "CODEX_HOME")
        previous = {name: os.environ.pop(name, None) for name in names}
        with tempfile.TemporaryDirectory() as temporary:
            os.environ["CLAUDE_PLUGIN_DATA"] = temporary
            try:
                resolved = resolve_runtime_root_with_source()
            finally:
                os.environ.pop("CLAUDE_PLUGIN_DATA", None)
                os.environ.update(
                    {
                        name: value
                        for name, value in previous.items()
                        if value is not None
                    }
                )

        self.assertEqual(resolved.root, Path(temporary))
        self.assertEqual(resolved.source, "CLAUDE_PLUGIN_DATA")
