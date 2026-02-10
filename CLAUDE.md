# Council of Elders — Claude Code Instructions

## Pre-Commit Audit Requirement

**IMPORTANT: Before creating any git commit, you MUST check whether a code audit should be run.**

### When an audit is REQUIRED (always prompt the user):
- Changes touch **3 or more files**
- A **new feature** was added
- A **significant refactor** was performed
- Any change to **orchestrator.py**, **app.py**, or **TTS pipeline** files
- It has been **more than 1 week** since the last audit (check AUDIT_REPORT.html modification date)

### When an audit can be SKIPPED:
- Single-file typo/comment fixes
- README or documentation-only changes
- Test-only changes

### How to prompt:
Before committing, say:
> "This commit touches N files including [key files]. The last audit was on [date]. I recommend running a fresh code audit before committing. Should I generate one now?"

If the user agrees, regenerate `AUDIT_REPORT.html` using the same comprehensive expert panel format (Architecture, Security, UX, Code Quality, Test Coverage).

### Audit report location:
- `AUDIT_REPORT.html` in the project root (do NOT commit this file)

## Pre-Commit Testing Checklist

**IMPORTANT: Before every commit, provide the user with a tailored testing checklist based on what changed. Always present this checklist and ask the user to confirm they've tested before proceeding with the commit.**

### How to generate the checklist:
1. Analyze all changed files
2. Map each change to a user-facing behavior that should be manually verified
3. Present the checklist in markdown with unchecked boxes
4. Include both **smoke tests** (does it launch?) and **feature tests** (does the new thing work?)

### Checklist template (adapt based on actual changes):

**Smoke Tests (always include):**
- [ ] App launches without errors (`cd desktop && npm start`)
- [ ] All unit tests pass (`source venv/bin/activate && pytest tests/ -v`)
- [ ] No console errors in Electron DevTools (Cmd+Opt+I)

**Feature Tests (include per changed area):**
- [ ] *[For sidebar changes]*: Mode selector works, elder checkboxes work, history loads
- [ ] *[For chat changes]*: Send a question, response streams correctly, cards render
- [ ] *[For orchestrator changes]*: Test each modified mode (panel/salon/rap/poetry)
- [ ] *[For TTS changes]*: Download podcast, verify audio plays
- [ ] *[For profile panel changes]*: Click elder name, tabs switch, content loads
- [ ] *[For commerce changes]*: Affiliate links open correct Amazon pages
- [ ] *[For Electron changes]*: Right-click spellcheck, window controls, app quit/relaunch
- [ ] *[For config changes]*: Switch providers, save API key, settings persist across restart

**Regression Tests (include when touching core files):**
- [ ] Existing panel discussion still works
- [ ] Elder nominations still appear
- [ ] Enrichment background tasks complete

### When to present:
- ALWAYS before committing, even if the user says "commit now" — present the checklist first and ask "Have you tested these? Or should I launch the app so you can verify?"

## Project Structure
- **Backend**: `council/` — Python Flask app with LLM orchestration, TTS, knowledge enrichment
- **Frontend**: `council/web/static/desktop/` — JS (IIFE components) + CSS
- **Desktop**: `desktop/` — Electron wrapper
- **Tests**: `tests/` — pytest unit tests (run with `source venv/bin/activate && pytest tests/ -v`)
- **Venv**: `venv/` (not `.venv`)

## Key Commands
- **Run tests**: `source venv/bin/activate && python -m pytest tests/ -v`
- **Launch app**: `cd desktop && npm start`
- **Python imports**: Always activate venv first: `source venv/bin/activate`
