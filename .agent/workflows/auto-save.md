---
description: Auto-save code changes with version bump and git commit
---

# Auto-Save Workflow

This workflow automatically:
1. Runs deep code checks
2. Bumps the version number
3. Commits and pushes to git

## Steps

### 1. Run Deep Code Check
// turbo
```powershell
python scripts/deep_check.py --fix
```

If the check fails, the workflow stops here. Fix the issues first.

---

### 2. Bump Version (Patch)
// turbo
```powershell
python scripts/version_bump.py --patch
```

This increments the patch version: `2.0.5` → `2.0.6`

For feature additions, use `--minor`. For breaking changes, use `--major`.

---

### 3. Get Current Version
// turbo
```powershell
python scripts/version_bump.py --show
```

Save this version for the commit message.

---

### 4. Stage All Changes
// turbo
```powershell
git add -A
```

---

### 5. Commit with Version
```powershell
git commit -m "Release: v$(python scripts/version_bump.py --show) - [describe changes]"
```

Replace `[describe changes]` with a brief description of what changed.

---

### 6. Push to Remote
```powershell
git push origin master
```

---

## Quick Command (All-in-One)

For experienced users, run all steps in one command:

```powershell
python scripts/deep_check.py --fix && python scripts/version_bump.py --patch && git add -A && git commit -m "Release: v$(python scripts/version_bump.py --show)" && git push origin master
```

---

## Notes

- Always run `deep_check.py` before committing
- The pre-commit hooks will also run automatically on `git commit`
- If pre-commit fails, the commit is blocked
