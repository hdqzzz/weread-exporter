import unittest
from unittest.mock import patch

from weread_exporter import utils
from weread_exporter.webpage import WeReadWebPage


class FakePage:
    def __init__(self, hook_states=None, markdown="content"):
        self.hook_states = list(hook_states or [True])
        self.markdown = markdown
        self.installed_scripts = []
        self.reload_count = 0
        self.update_count = 0

    async def evaluateOnNewDocument(self, script):
        self.installed_scripts.append(script)

    async def reload(self):
        self.reload_count += 1

    async def evaluate(self, script):
        if script == "typeof canvasContextHandler !== 'undefined';":
            if len(self.hook_states) > 1:
                return self.hook_states.pop(0)
            return self.hook_states[0]
        if script == "canvasContextHandler.data.complete;":
            return True
        if script == "canvasContextHandler.data.markdown;":
            return self.markdown
        if script == "canvasContextHandler.updateMarkdown();":
            self.update_count += 1
            return None
        raise AssertionError("unexpected script: %s" % script)


class WebPageHookTests(unittest.IsolatedAsyncioTestCase):
    def make_webpage(self, page):
        webpage = WeReadWebPage("book-id")
        webpage._page = page
        return webpage

    async def test_installs_hook_for_new_documents(self):
        page = FakePage()
        webpage = self.make_webpage(page)

        await webpage._install_hook_on_new_document()

        self.assertEqual(len(page.installed_scripts), 1)
        installed_script = page.installed_scripts[0]
        self.assertTrue(installed_script.lstrip().startswith("() => {"))
        self.assertIn("if (window.__wereadExporterHookInstalled)", installed_script)
        self.assertIn("window.canvasContextHandler = {", installed_script)
        self.assertIn("window.__wereadExporterHookInstalled = true", installed_script)

    async def test_missing_hook_is_installed_and_page_reloaded_once(self):
        page = FakePage(hook_states=[False, True])
        webpage = self.make_webpage(page)

        await webpage._ensure_hook_available()

        self.assertEqual(len(page.installed_scripts), 1)
        self.assertEqual(page.reload_count, 1)

    async def test_persistently_missing_hook_raises_retryable_error(self):
        page = FakePage(hook_states=[False, False])
        webpage = self.make_webpage(page)

        with self.assertRaises(utils.LoadChapterFailedError):
            await webpage._ensure_hook_available()

    async def test_preload_does_not_add_legacy_response_hook_injection(self):
        page = FakePage()
        webpage = self.make_webpage(page)
        captured_rules = []

        class FakeProxy:
            def __init__(self, _, rules):
                captured_rules.extend(rules)

            async def setup_interception(self):
                return None

        with patch("weread_exporter.webpage.webproxy.WebProxy", FakeProxy):
            await webpage.pre_load_page()

        self.assertFalse(
            any(rule.stage == "response" for rule in captured_rules)
        )
        self.assertFalse(
            any(rule._resource_type == "Script" for rule in captured_rules)
        )

    async def test_get_markdown_with_missing_hook_raises_retryable_error(self):
        page = FakePage(hook_states=[False])
        webpage = self.make_webpage(page)

        with self.assertRaises(utils.LoadChapterFailedError):
            await webpage.get_markdown()

    async def test_empty_markdown_raises_retryable_error(self):
        page = FakePage(hook_states=[True], markdown="")
        webpage = self.make_webpage(page)

        with self.assertRaises(utils.LoadChapterFailedError):
            await webpage.get_markdown()

        self.assertEqual(page.update_count, 1)


if __name__ == "__main__":
    unittest.main()
