# Contributing to GB Power Market JJ

## Copilot-Enhanced Commit Workflow

### The "Stage → Sparkle → Edit → Sanity-check" Pattern

This workflow uses GitHub Copilot's smart actions to **draft** commit messages, which you then refine.

#### 1. Stage first, then generate

- **Stage only the changes** you want described in this specific commit.
- If you have multiple logical changes, commit them separately (better history, easier review).

#### 2. Use the sparkle action to draft

- In the **Source Control** view, look for the **sparkle icon** (✨) in the commit message box.
- Click it → **"Generate Commit Message"**.
- Copilot analyzes your staged changes and drafts a message.

#### 3. Edit the draft into our team's style

The AI draft is a **starting point**. Always edit it to answer:

- **What changed?** (specific, factual)
- **Why?** (context, motivation)
- **Any risk/impact?** (breaking changes, perf implications, migration needs)

**Conventional Commits style** (recommended):
```
<type>(optional scope): <subject>

Examples:
feat: add real-time IRIS pipeline for bmrs_fuelinst
fix(auth): refresh token handling in BigQuery client
chore: update dependencies and fix deprecation warnings
docs: add DNO lookup architecture guide
refactor(vlp): extract battery arbitrage logic to separate module
```

**Add issue keys** if your workflow requires them:
```
feat: add BESS cost analysis dashboard

Fixes #123
Related to JIRA-456
```

#### 4. Sanity-check for AI gotchas

Before committing, verify the message doesn't:

- Claim you **fixed/added something you didn't** (hallucination)
- Include **secrets, API keys, credentials, internal URLs**
- Include **customer names, sensitive details, or proprietary info**
- Overstate the change ("completely rewrote X" when you changed 3 lines)
- Describe unrelated/unstaged changes

**When in doubt, be conservative.** A boring, accurate commit message is better than a creative, incorrect one.

---

## Pull Request Workflow

### Using Copilot Smart Actions for PRs

If you use the **GitHub Pull Requests** extension, you can draft PR descriptions similarly:

1. **Create your branch** with well-scoped changes.
2. **Push and open a PR** (or use the extension's "Create Pull Request" command).
3. **Use the sparkle action** to draft the PR title and description.
4. **Edit into the template structure** (see below).

### PR Template Structure

Our PR template expects these sections (auto-populated in `.github/pull_request_template.md`):

```markdown
## Summary
Brief description of what this PR does.

## Motivation / context
Why are we making this change? What problem does it solve?
Link to relevant issues, discussions, or docs.

## Testing
- [ ] Unit tests pass (make test)
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing performed: <describe what you tested>
- [ ] No new errors in BigQuery queries
- [ ] Dashboard/Sheets updates verified (if applicable)

## Screenshots / evidence (optional)
For UI changes, dashboard updates, or visual verification.

## Rollout / risk
- **Breaking changes?** (API changes, schema changes, config changes)
- **Performance impact?** (query cost, runtime)
- **Migration needed?** (data backfill, manual steps)
- **Rollback plan?** (can we revert safely?)
```

---

## When NOT to Use AI-Generated Commits/PRs

**Skip the AI draft** and write manually for:

- **Security-sensitive changes** (auth, keys, permissions, secrets management, infra)
- **Large refactors** where a human-written narrative matters (architectural changes, major rewrites)
- **Mixed commits** that do "a bit of everything" (split into logical commits first, then generate per commit)
- **Compliance/audit-critical changes** (regulatory, financial, customer-impacting)

**Why?** AI can't assess security implications, doesn't understand business context, and may include inappropriate details.

---

## Copilot Tool Sets

We've defined two tool sets for different workflows (see `.vscode/copilot-toolsets.jsonc`):

### `#reader` (safe, read-only-ish)
Use for exploration and analysis:
- `#changes` - what's currently changed
- `#codebase` - search/understand the code
- `#problems` - lint/build errors
- `#usages` - where is X used?

**Example prompts:**
```
"Explain how battery VLP revenue is calculated. #reader"
"Where is bmrs_costs table queried? #codebase #usages"
"What's currently failing? #problems"
```

### `#ship` (action-oriented, requires approvals)
Use when you're ready to make changes:
- All `#reader` tools
- `edit` - modify files
- `terminal` - run commands
- `fetch` - pull external docs

**Example prompts:**
```
"Fix the BigQuery location error in this file. #ship"
"Add a test for the DNO lookup function. #ship"
"Run the tests and fix any failures. #ship"
```

**Security note:** `#ship` tools can modify code and run commands. Always review suggested changes and approve/reject thoughtfully.

---

## Copilot Agents: When to Use Each Lane

We follow a **3-lane workflow** for different types of work (see `docs/copilot-agents.md` for details):

### 🔧 Local (interactive)
**Use for:** Exploration, debugging, rapid iteration, anything needing your current editor context.

**Example:** "Debug why this query is returning duplicates. #reader"

### ⚙️ Background (local autonomous)
**Use for:** Well-scoped parallel work that doesn't need your active session.

**Example:** "Add unit tests for all functions in dno_lookup_python.py" (runs in isolated worktree).

**Limitations:** No access to your current editor state, runtime context, or MCP/extension tools.

### ☁️ Cloud (PR-based)
**Use for:** Collaboration-first work where you want a reviewable PR.

**Example:** "Implement the new BESS cost analysis dashboard as described in issue #123."

**Limitations:** Runs remotely, no access to your local environment or runtime context.

---

## Todo List Management

VS Code Copilot supports **automatic todo tracking** for complex tasks:

### Enable the Todo Tool

Already enabled in `.vscode/settings.json`:
```json
"chat.todoListTool.enabled": true
```

### How to Use

1. **Ask Copilot to create a plan:**
   ```
   "Create a todo list to add DNO rate lookup to the BESS sheet, including:
   - Parse MPAN core
   - Query BigQuery for DNO details
   - Get DUoS rates by voltage
   - Update sheet with formatted output"
   ```

2. **Copilot generates a structured todo list** you can track and update.

3. **Work through items:**
   ```
   "Work on todo items 1-3"
   "Mark item 2 as done"
   "Add a new todo: validate postcode format"
   ```

This is especially useful for multi-step features, refactors, or complex debugging sessions.

---

## Code Quality Standards

### Before Committing

- Run linting/formatting (we use `ruff` for Python where applicable)
- Ensure no new errors: `#problems` or check the Problems panel
- Test your changes: manual testing + automated tests where they exist

### Python Standards

- Use **type hints** for function signatures
- **Docstrings** for public functions (especially BigQuery queries, API endpoints)
- **Limit query results during development** (`LIMIT 1000` until verified)
- **Project ID = `inner-cinema-476211-u9`** (always, not `jibber-jabber-knowledge`)
- **BigQuery location = `US`** (not `europe-west2`)

### BigQuery Best Practices

- **Always verify date coverage** before writing queries: `./check_table_coverage.sh TABLE_NAME`
- **Use UNION for historical + IRIS** to get complete timelines
- **Filter first, aggregate later** (avoid `SELECT *` on 391M row tables)
- **Check schema** in `STOP_DATA_ARCHITECTURE_REFERENCE.md` to avoid wrong column names

### Apps Script Standards

- **Enable required Advanced Services** in `appsscript.json` manifest
- **Use service account JSON** for server-side auth (not user OAuth)
- **Handle errors gracefully** (BigQuery can timeout, Sheets API can rate-limit)

---

## Getting Help

- **Documentation:** Start with `PROJECT_CONFIGURATION.md` → `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **Copilot prompts:** See `PROMPTS.md` for tested, working examples
- **Agent workflows:** See `docs/copilot-agents.md` for lane selection
- **Architecture:** See `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`

---

## Quick Reference: Useful Copilot Prompts

### Exploration
```
"Explain the IRIS vs historical pipeline architecture. #reader #codebase"
"Show me all references to bmrs_costs table. #usages"
"What's the difference between SSP and SBP? #fetch https://www.elexon.co.uk/..."
```

### Implementation
```
"Fix all lint errors in this file. #ship"
"Add error handling to this BigQuery query. #ship"
"Generate a commit message for my staged changes."
```

### Testing
```
"Write a pytest test for this function. #ship"
"Run the tests and show me failures. #ship #terminal"
```

### Debugging
```
"Why is this query returning duplicates? #reader #codebase"
"Trace through the DNO lookup logic. #usages"
"Check if there are any errors in recently modified files. #problems"
```

---

*Last updated: December 2025*
