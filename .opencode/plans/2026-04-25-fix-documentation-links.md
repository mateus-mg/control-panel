# Fix Documentation Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct all GitHub repository links from `mateus/control-panel` to `mateus-mg/control-panel`. The Material for MkDocs theme automatically renders stars and forks badges in the header when `repo_url` points to a valid GitHub repository — no extra configuration needed.

**Architecture:** Update all hardcoded repository URLs across the project (README, MkDocs config, systemd service files, installation docs). The theme handles GitHub stats rendering natively.

**Tech Stack:** MkDocs, Material for MkDocs

---

## Task 1: Fix MkDocs Configuration

**Files:**
- Modify: `mkdocs.yml`

- [ ] **Step 1: Update repository and site URLs**

Replace all occurrences of `mateus/control-panel` with `mateus-mg/control-panel` in `mkdocs.yml`.

Current content (lines 4, 6-7, 58):
```yaml
site_url: https://mateus.github.io/control-panel
repo_name: mateus/control-panel
repo_url: https://github.com/mateus/control-panel
```

And in `extra.social`:
```yaml
    - icon: fontawesome/brands/github
      link: https://github.com/mateus
```

New content:
```yaml
site_url: https://mateus-mg.github.io/control-panel
repo_name: mateus-mg/control-panel
repo_url: https://github.com/mateus-mg/control-panel
```

And:
```yaml
    - icon: fontawesome/brands/github
      link: https://github.com/mateus-mg
```

- [ ] **Step 2: Verify mkdocs.yml syntax**

Run: `python -c "import yaml; yaml.safe_load(open('mkdocs.yml'))"`
Expected: No output (success)

- [ ] **Step 3: Commit**

```bash
git add mkdocs.yml
git commit -m "fix: correct GitHub repo links in MkDocs config"
```

---

## Task 2: Fix README.md Documentation Link

**Files:**
- Modify: `README.md:5`

- [ ] **Step 1: Update documentation link in README**

Replace line 5:
```markdown
> **Documentation:** Full documentation is now available at [https://mateus.github.io/control-panel](https://mateus.github.io/control-panel)
```

With:
```markdown
> **Documentation:** Full documentation is now available at [https://mateus-mg.github.io/control-panel](https://mateus-mg.github.io/control-panel)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "fix: correct documentation URL in README"
```

---

## Task 3: Fix Installation Guide Clone URL

**Files:**
- Modify: `docs/getting-started/installation.md:16`

- [ ] **Step 1: Update clone URL in installation guide**

Replace:
```bash
git clone https://github.com/mateus/control-panel.git
```

With:
```bash
git clone https://github.com/mateus-mg/control-panel.git
```

- [ ] **Step 2: Commit**

```bash
git add docs/getting-started/installation.md
git commit -m "fix: correct GitHub clone URL in installation guide"
```

---

## Task 4: Fix Systemd Service Documentation URLs

**Files:**
- Modify: `backup-daemon.service:3`
- Modify: `panel-keepalive.service:3`

- [ ] **Step 1: Update Documentation directive in backup-daemon.service**

Replace line 3:
```
Documentation=https://github.com/mateus/control-panel
```

With:
```
Documentation=https://github.com/mateus-mg/control-panel
```

- [ ] **Step 2: Update Documentation directive in panel-keepalive.service**

Replace line 3:
```
Documentation=https://github.com/mateus/control-panel
```

With:
```
Documentation=https://github.com/mateus-mg/control-panel
```

- [ ] **Step 3: Commit**

```bash
git add backup-daemon.service panel-keepalive.service
git commit -m "fix: correct GitHub URLs in systemd service files"
```

---

## Task 5: Test MkDocs Build and Verify GitHub Stats

**Files:**
- Test: Build validation

- [ ] **Step 1: Install MkDocs dependencies (if not installed)**

Run:
```bash
pip install mkdocs-material mkdocstrings-python mermaid2
```

- [ ] **Step 2: Build documentation**

Run:
```bash
mkdocs build --strict
```

Expected: Build succeeds with no errors. Output should end with `INFO  -  Documentation built in ...`

- [ ] **Step 3: Verify corrected repo URL in generated HTML**

Run:
```bash
grep -o 'github.com/mateus-mg/control-panel' site/*/index.html | head -1 || grep -o 'github.com/mateus-mg/control-panel' site/index.html | head -1
```

Expected: The corrected URL `github.com/mateus-mg/control-panel` is found.

- [ ] **Step 4: Verify stars/forks data is requested by the theme (optional visual check)**

The Material theme requests GitHub stats via JavaScript at runtime. Serve the site locally and visually confirm the header shows the repository name with stars and forks badges:

```bash
mkdocs serve &
sleep 3
# Open http://127.0.0.1:8000 in browser and check the top-right corner
# Expected: Repository name + stars count + forks count
kill %1
```

- [ ] **Step 5: Commit build artifacts (if site/ is tracked)**

Note: If `site/` is in `.gitignore`, skip this step. Run `cat .gitignore | grep site` to verify.

---

## Task 6: Final Verification and Cleanup

- [ ] **Step 1: Search for any remaining old URLs**

Run:
```bash
grep -r "github.com/mateus/control-panel" --include="*.md" --include="*.yml" --include="*.yaml" --include="*.service" --include="*.sh" . || echo "No old URLs found - good!"
```

Expected: `No old URLs found - good!`

- [ ] **Step 2: Search for any remaining old GitHub Pages URLs**

Run:
```bash
grep -r "mateus.github.io/control-panel" --include="*.md" --include="*.yml" --include="*.yaml" . || echo "No old URLs found - good!"
```

Expected: `No old URLs found - good!`

---

## Self-Review Checklist

**1. Spec coverage:**
- README documentation link fixed? → Task 2
- GitHub repo link in header (top-right) updated so stars/forks render automatically? → Task 1
- All internal references to old URL corrected? → Task 1, 3, 4, 6
- Installation guide clone URL fixed? → Task 3
- Systemd service documentation URLs fixed? → Task 4

**2. Placeholder scan:**
- No "TBD", "TODO", or "implement later" found.
- All code blocks contain actual content.
- All commands have expected output defined.

**3. Type consistency:**
- Repository name consistently uses `mateus-mg/control-panel`.
- File paths are exact and consistent.
