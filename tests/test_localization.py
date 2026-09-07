import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


localization = load('localization')
upstream = load('sync_upstream')


class LocalizationTests(unittest.TestCase):
    def test_catalog_and_generated_resource_match(self):
        self.assertEqual(localization.render(localization.read_catalog()), localization.RESOURCE.read_text())

    def test_duplicate_keys_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"a":"甲","a":"乙"}', object_pairs_hook=localization.unique_pairs)

    def test_missing_placeholder_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            catalog = Path(temp) / 'catalog.json'
            catalog.write_text('{"Version %@":"版本"}')
            with patch.object(localization, 'CATALOG', catalog), self.assertRaises(ValueError):
                localization.read_catalog()

    def test_missing_build_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as temp, self.assertRaises(ValueError):
            localization.audit(Path(temp), {})

    def test_escaped_quotes_and_newlines(self):
        result = localization.render({'"%@"\n': '“%@”\n'})
        self.assertIn('\\"', result)
        self.assertIn('\\n', result)


class UpstreamTests(unittest.TestCase):
    def release(self, tag, date, draft=False):
        return {'tag_name': tag, 'published_at': date, 'draft': draft, 'prerelease': '-dev' in tag}

    def test_latest_published_includes_beta_ignores_drafts(self):
        releases = [self.release('0.11.12', '2024-10-29'),
                    self.release('0.11.13-dev.2', '2025-09-16'),
                    self.release('0.12.0', '2026-01-01', True)]
        self.assertEqual(upstream.select_release(releases)['tag_name'], '0.11.13-dev.2')

    def test_empty_releases_rejected(self):
        with self.assertRaises(ValueError):
            upstream.select_release([])

    def test_invalid_tag_rejected(self):
        with self.assertRaises(ValueError):
            upstream.select_release([self.release('$(echo bad)', '2026-01-01')])

    def test_same_release_is_noop(self):
        state = json.loads(upstream.STATE.read_text())
        with patch.object(upstream, 'run') as command:
            self.assertFalse(upstream.sync(self.release(state['tag'], state['published_at'])))
            command.assert_not_called()

    def test_merge_conflict_aborts_without_push(self):
        import subprocess
        release = self.release('0.12.0', '2099-01-01')
        commands = []

        def fake_run(*args):
            commands.append(args)
            if args[:3] == ('git', 'merge', '--no-edit'):
                raise subprocess.CalledProcessError(1, args)
            if args[:2] == ('git', 'diff'):
                return 'Ice/Main/Updates.swift'
            return 'a' * 40

        with patch.object(upstream, 'run', side_effect=fake_run), self.assertRaises(RuntimeError):
            upstream.sync(release)
        self.assertIn(('git', 'merge', '--abort'), commands)
        self.assertFalse(any(c[:2] == ('git', 'push') for c in commands))

    def test_old_release_does_not_roll_back(self):
        with patch.object(upstream, 'run') as command, self.assertRaises(ValueError):
            upstream.sync(self.release('0.1.0', '2000-01-01'))
        command.assert_not_called()


if __name__ == '__main__':
    unittest.main()
