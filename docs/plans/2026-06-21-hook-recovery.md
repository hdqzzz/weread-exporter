# WeRead Hook Recovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make chapter export recover automatically when the Canvas hook is missing after navigation.

**Architecture:** Register `hook.js` for every new browser document, then validate the hook after navigation. Convert unrecoverable hook and Markdown failures into the exporter’s existing retry signal so the browser can relaunch while completed chapter files remain cached.

**Tech Stack:** Python 3.12, asyncio, pyppeteer, unittest.

---

### Task 1: Register Hook for Every New Document

**Files:**
- Modify: `weread_exporter/webpage.py`
- Create: `tests/test_webpage.py`

**Step 1: Write the failing test**

Add an async unit test with a fake page. Call a new `_install_hook_on_new_document()` helper and assert that `hook.js` content is passed to `evaluateOnNewDocument`.

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_webpage.WebPageHookTests.test_installs_hook_for_new_documents -v`

Expected: FAIL because `_install_hook_on_new_document` does not exist.

**Step 3: Write minimal implementation**

Add `_load_hook_script()` and `_install_hook_on_new_document()` helpers. Invoke the installer immediately after page creation in `launch()`.

**Step 4: Run test to verify it passes**

Run the same test and expect PASS.

### Task 2: Detect and Recover Missing Hook

**Files:**
- Modify: `weread_exporter/webpage.py`
- Modify: `tests/test_webpage.py`

**Step 1: Write the failing tests**

Test that `_ensure_hook_available()` returns immediately when the hook exists, and that it registers the hook and reloads once when it is absent.

**Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m unittest tests.test_webpage.WebPageHookTests -v`

Expected: FAIL because `_ensure_hook_available` does not exist.

**Step 3: Write minimal implementation**

Add `_has_canvas_hook()` and `_ensure_hook_available()`. Call the latter after `goto()` and before pagination reads Canvas state. If validation still fails, raise `LoadChapterFailedError`.

**Step 4: Run tests to verify they pass**

Run the hook test class and expect PASS.

### Task 3: Normalize Markdown Recovery Errors

**Files:**
- Modify: `weread_exporter/webpage.py`
- Modify: `tests/test_webpage.py`

**Step 1: Write the failing tests**

Test that `get_markdown()` raises `LoadChapterFailedError` when the hook is missing or Markdown remains empty after update.

**Step 2: Run tests to verify they fail**

Run the new test methods and expect the current `ElementHandleError` or `RuntimeError`.

**Step 3: Write minimal implementation**

Validate the hook before evaluation and replace the generic Markdown timeout with `LoadChapterFailedError`.

**Step 4: Run tests to verify they pass**

Run the hook test class and expect PASS.

### Task 4: Full Verification

**Files:**
- Verify: `weread_exporter/webpage.py`
- Verify: `tests/test_webpage.py`

**Step 1: Run all tests**

Run: `.venv/bin/python -m unittest discover -v`

Expected: all tests PASS.

**Step 2: Compile source**

Run: `.venv/bin/python -m compileall -q weread_exporter tests`

Expected: exit code 0.

**Step 3: Run a cached export smoke test**

Run the exporter against book `3b832eb0813ababafg010d36`; all 14 cached chapters should be accepted and the existing EPUB should remain valid.

**Step 4: Inspect the diff**

Run: `git diff --check && git status --short`.
