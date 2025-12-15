# GitHub Copilot Agents: The 3-Lane Workflow

This guide explains **when and how** to use different types of Copilot agents in VS Code for the GB Power Market JJ project.

---

## Overview: Three Agent Types

VS Code's agent model provides three distinct "lanes" for different work styles:

1. **Local (interactive)** - Work with you in real-time in the editor
2. **Background (local autonomous)** - Run independently on your machine in parallel
3. **Cloud (PR-based)** - Run remotely and create pull requests for review

Each has different strengths, limitations, and ideal use cases.

---

## 🔧 Lane 1: Local Agent (Interactive)

### What It Is
The standard Copilot Chat experience you use in the editor. Interactive, conversational, context-aware.

### When to Use
- **Exploring the codebase** ("How does the IRIS pipeline work?")
- **Debugging issues** ("Why is this query returning duplicates?")
- **Iterating quickly** ("Try this approach, then that approach")
- **Needs runtime context** (current test failures, active editor selection, local env quirks)
- **Learning/understanding** ("Explain this function")

### Key Strengths
✅ Has access to your **current editor context** (open files, selections, problems panel)  
✅ Can use **all VS Code built-in tools** (codebase, usages, problems, changes, etc.)  
✅ Can access **MCP servers** and **extension tools** (if configured)  
✅ **Interactive** - you can guide and course-correct in real-time  
✅ Immediate feedback loop

### Limitations
⚠️ **Not autonomous** - requires your attention and input  
⚠️ **Single-threaded** - you can't work on something else while it runs

### Example Prompts
```
"Explain how battery VLP revenue is calculated. #reader #codebase"

"Debug why the DNO lookup is returning the wrong distributor. #reader #usages"

"Fix the BigQuery location error in ingest_elexon_fixed.py. #ship"

"Where is bmrs_costs table queried? Show all usages. #codebase #usages"

"What's currently failing? #problems"
```

### Tool Sets to Use
- **`#reader`** for exploration (changes, codebase, problems, usages)
- **`#ship`** for making changes (adds edit, terminal, fetch)

---

## ⚙️ Lane 2: Background Agent (Local Autonomous)

### What It Is
A Copilot agent that runs **autonomously on your local machine**, often in a separate Git worktree. You give it a task, and it works independently while you continue other work.

### When to Use
- **Well-scoped parallel work** ("Add unit tests for all functions in dno_lookup_python.py")
- **Refactoring tasks** ("Extract battery arbitrage logic into a separate module")
- **Documentation generation** ("Add docstrings to all BigQuery query functions")
- **Repetitive tasks** ("Add type hints to all function signatures in src/")

### Key Strengths
✅ **Runs in parallel** - you can work on something else  
✅ **Isolated environment** - often uses Git worktrees (clean separation)  
✅ **Good for well-defined tasks** - clear input/output, no ambiguity

### Limitations
⚠️ **No VS Code built-in tools or runtime context** unless explicitly provided  
⚠️ **No MCP/extension tools** (treats the task as isolated)  
⚠️ **Needs clear, complete instructions** - can't ask you clarifying questions mid-task  
⚠️ **Local only** - runs on your machine (not cloud-based)

### How to Use
1. **Scope the task clearly:**
   ```
   "Add pytest unit tests for:
   - extract_core_from_full_mpan()
   - mpan_core_lookup()
   - parse_dno_details()
   
   Use mock BigQuery responses. Place tests in tests/test_dno_lookup.py."
   ```

2. **Let it run autonomously** while you work on something else.

3. **Review the output** when complete (usually creates a branch or worktree).

### Best Practices
- ✅ **Provide complete context** (file paths, function names, acceptance criteria)
- ✅ **One logical task per agent session** (not "fix everything")
- ✅ **Review carefully** before merging (it's autonomous but not infallible)

### Example Tasks
```
"Refactor update_analysis_bi_enhanced.py to extract BigQuery queries 
into a separate queries.py module with clear function names."

"Add comprehensive logging to iris_to_bigquery_unified.py using 
Python's logging module. Log at INFO level for normal operations, 
WARNING for retries, ERROR for failures."

"Generate API documentation for all functions in vercel-proxy/api/ 
and create docs/api-reference.md with examples."
```

---

## ☁️ Lane 3: Cloud Agent (PR-Based)

### What It Is
A **remote coding agent** that runs in GitHub's cloud, creates a new branch, implements changes, and **opens a pull request** for your review.

### When to Use
- **PR-first collaboration** ("Implement the new BESS cost analysis feature as described in issue #123")
- **Feature development** with clear acceptance criteria
- **Bug fixes** where you want a reviewable, auditable workflow
- **Team visibility** - the PR documents what was done and why

### Key Strengths
✅ **PR-centric workflow** - creates reviewable changes with context  
✅ **Runs remotely** - doesn't consume your local resources  
✅ **Auditable** - PR comments, commit history, CI/CD checks  
✅ **Collaboration-friendly** - teammates can review, comment, iterate

### Limitations
⚠️ **No access to your local runtime context** (local test failures, env vars, local files)  
⚠️ **Runs in remote environment** (may not match your exact setup)  
⚠️ **Requires good issue/task description** (clear requirements, acceptance criteria)  
⚠️ **Limited tool access** - configured cloud tools/MCP only

### Prerequisites
Before you can use the cloud coding agent:

1. **Copilot plan** that includes coding agents (Business/Enterprise)
2. **Write access** to the repository
3. **Agent enabled** for your account/organization
4. **GitHub Pull Requests extension** installed and signed in

### How to Use

#### Step 1: Create a Clear Issue/Task
```markdown
Title: Add BESS Cost Analysis Dashboard

Description:
Create a new analysis that:
1. Queries bmrs_costs for System Sell Price (SSP) over last 30 days
2. Calculates daily average, peak, and off-peak prices
3. Computes potential battery arbitrage revenue (2hr/4hr/6hr discharge)
4. Writes results to "BESS Analysis" sheet in dashboard spreadsheet

Acceptance criteria:
- BigQuery query uses correct project (inner-cinema-476211-u9)
- Handles UNION of historical + IRIS data for complete timeline
- Includes error handling and logging
- Updates sheet using gspread
- Follows existing code patterns in update_analysis_bi_enhanced.py
```

#### Step 2: Invoke the Cloud Agent
In Copilot Chat or via the GitHub PR extension:
```
"Use #github-pull-request_copilot-coding-agent to implement issue #123"
```

#### Step 3: Review the PR
- Check the implementation matches requirements
- Review for security issues (secrets, credentials)
- Verify BigQuery queries are efficient
- Test locally if needed
- Iterate via PR comments if changes needed

### Example Tasks for Cloud Agents
```
"Implement the DNO rate lookup webhook as described in BESS_DNO_INTEGRATION.md"

"Add real-time frequency monitoring dashboard based on bmrs_freq_iris table"

"Refactor duplicate code in iris-clients/python/ and create shared utilities"

"Fix bug #456: handle missing settlement periods in bmrs_costs gracefully"
```

---

## Decision Matrix: Which Lane to Choose?

| Scenario | Best Lane | Why |
|----------|-----------|-----|
| "Why is this failing?" | 🔧 Local | Needs your runtime context, interactive debugging |
| "Explain how X works" | 🔧 Local | Exploration, learning, Q&A |
| "Add tests for module Y" | ⚙️ Background | Well-scoped, can run in parallel |
| "Refactor Z to use better patterns" | ⚙️ Background | Clear scope, isolated work |
| "Implement feature from issue #123" | ☁️ Cloud | PR-first, team collaboration |
| "Fix urgent production bug" | 🔧 Local | Speed, control, your environment |
| "Add logging to all scripts" | ⚙️ Background | Repetitive, well-defined |
| "Quick experiment: try this approach" | 🔧 Local | Iterative, exploratory |

---

## Practical Tips

### For All Lanes

✅ **Be specific** - vague tasks get vague results  
✅ **Provide context** - file paths, function names, acceptance criteria  
✅ **Review everything** - agents are tools, not teammates (yet)  
✅ **Check for secrets** - always audit generated code for credentials/keys

### For Local Agents

✅ Use **tool sets** (`#reader` / `#ship`) to guide tool selection  
✅ **Iterate** - it's interactive, so refine as you go  
✅ **Save progress** - commit working states before trying risky changes

### For Background Agents

✅ **One task at a time** - don't ask for multiple unrelated changes  
✅ **Clear constraints** - specify limits, patterns to follow, files to touch  
✅ **Check the worktree** - background agents may create isolated Git worktrees

### For Cloud Agents

✅ **Good issues make good PRs** - invest time in clear requirements  
✅ **Link to docs** - reference architecture docs, API guides, examples  
✅ **Set expectations** - specify what tests to run, what to validate  
✅ **Review promptly** - stale PRs are harder to merge

---

## Agent Sessions View

VS Code provides an **Agent Sessions view** to track all your active agent work:

**Setting:** `chat.agentSessionsViewLocation: "view"` (already enabled in `.vscode/settings.json`)

This shows:
- 🔧 Local chat sessions
- ⚙️ Background agent sessions  
- ☁️ Cloud coding agent PRs

Use this to **monitor progress**, switch between tasks, and keep track of what's running.

---

## Common Pitfalls

### ❌ Using Background Agents for Exploratory Work
**Problem:** Background agents can't ask clarifying questions.  
**Solution:** Use local agent first to explore, then hand off to background once scope is clear.

### ❌ Using Cloud Agents Without Clear Requirements
**Problem:** Ambiguous issues → poor PRs → wasted time.  
**Solution:** Write detailed issue descriptions with acceptance criteria first.

### ❌ Not Reviewing Agent Output
**Problem:** Agents can make mistakes (wrong assumptions, hallucinations, security issues).  
**Solution:** Always review. Treat agents like junior developers - helpful but need oversight.

### ❌ Mixing Multiple Tasks in One Agent Session
**Problem:** Scope creep, harder to review, harder to revert.  
**Solution:** One logical task per agent session. Split complex work into sequential tasks.

---

## Real-World Workflow Example

**Task:** "Add DNO rate lookup to BESS sheet with webhook trigger"

### Phase 1: Exploration (Local Agent)
```
Me: "How does the current BESS sheet structure work? #reader #codebase"

Agent: [Explains layout, Apps Script setup, existing automation]

Me: "Show me all references to MPAN parsing. #usages"

Agent: [Shows mpan_generator_validator usage, existing parsing code]

Me: "What's the right way to parse MPAN distributor ID?"

Agent: [Explains extract_core_from_full_mpan(), first 2 digits = distributor]
```

### Phase 2: Implementation (Background Agent)
```
Me: "Create a background task to implement DNO lookup webhook:
- Flask server on port 5001
- Receives POST with MPAN and voltage from Apps Script
- Parses MPAN using mpan_generator_validator
- Queries BigQuery for DNO details and DUoS rates
- Returns JSON with DNO name, rates, time bands
- Place in dno_webhook_server.py
- Follow patterns from existing webhook code"

[Background agent works autonomously, creates implementation]
```

### Phase 3: Review & Test (Local Agent)
```
Me: "Review the generated dno_webhook_server.py for security issues. #ship"

Agent: [Reviews, suggests rate limiting, input validation improvements]

Me: "Add comprehensive error handling and logging."

Agent: [Edits file to add try/except, logging]

Me: "Test it manually. #ship #terminal"

Agent: [Runs server, sends test request, validates output]
```

### Phase 4: PR & Documentation (Cloud Agent)
```
Me: "Create a PR for this DNO webhook feature using #github-pull-request_copilot-coding-agent"

[Cloud agent creates PR with:
- Summary of changes
- Testing steps
- Documentation updates
- Deployment instructions]

[Team reviews PR, I address feedback, merge]
```

---

## Quick Reference Card

| Need | Use | Command Pattern |
|------|-----|----------------|
| Understand code | 🔧 Local | `"Explain X. #reader"` |
| Debug issue | 🔧 Local | `"Why is Y failing? #reader #problems"` |
| Fix bug quickly | 🔧 Local | `"Fix Z. #ship"` |
| Add tests | ⚙️ Background | `"Add pytest tests for module M"` |
| Refactor | ⚙️ Background | `"Refactor N to use pattern P"` |
| New feature | ☁️ Cloud | `"#github-pull-request_copilot-coding-agent implement #123"` |
| Team change | ☁️ Cloud | `"Create PR for feature F"` |

---

*Last updated: December 2025*  
*See also: CONTRIBUTING.md, PROMPTS.md*
