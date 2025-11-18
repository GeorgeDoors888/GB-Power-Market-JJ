# GitHub Copilot Background Mode Guide

## ✅ NOW ACTIVE FOR ALL REPOSITORIES

All your repositories are now configured to use background mode for remote operations, preventing terminal blocking.

## What Changed

### Global Settings Applied:
- ✅ Git auto-fetch: **DISABLED** (no background Git operations)
- ✅ SSH commands: **Require approval** (never auto-run)
- ✅ Safe commands: **Auto-approved** (grep, ls, cat, tail, etc.)
- ✅ Terminal confirmations: **Disabled** (smoother experience)

### New Background Helper Tool:
A helper script is now available at `~/.copilot_background_mode.sh`

## How It Works Now

### When You Ask Me to Check Remote Servers:
I will automatically:
1. Run the command in the background using `&` or `nohup`
2. Save output to a log file
3. Return immediately without blocking your terminal
4. Show you the results when complete

### Example Interactions:

**Before (Blocking):**
```
You: "Check IRIS status"
Me: *runs SSH command, terminal hangs for 30 seconds*
You: *can't use terminal*
```

**After (Background):**
```
You: "Check IRIS status"
Me: *starts background job*
Terminal: Available immediately
Me: *returns results when ready*
```

## Using the Background Helper Manually

New terminal commands available:

```bash
# Run SSH command in background
ssh_bg root@94.237.55.234 'tail /opt/iris-pipeline/logs/iris_uploader.log'

# Check if background job is still running
check_bg

# View output of last background job
get_bg_output

# Kill background job if needed
kill_bg
```

## For Different Repositories

### GB Power Market JJ (Current)
- ✅ Background mode: ENABLED
- ✅ Auto-fetch: DISABLED
- ✅ Terminal optimized

### Other Repositories
Same settings will apply globally, but workspace-specific overrides can be added:

```json
// .vscode/settings.json
{
  "git.autofetch": false,
  "terminal.integrated.confirmOnKill": "never"
}
```

## Commands That Run in Background

When you ask me to:
- Check remote server status → **Background**
- Monitor log files → **Background**
- Run long Python scripts → **Background** (with option)
- Fetch large datasets → **Background**
- SSH operations → **Background with output capture**

## Commands That Run Immediately

These run normally (fast, no blocking):
- Git status/log/branch
- List files (ls, find)
- Read files (cat, grep, tail)
- Process info (ps, pgrep)
- Local Python scripts

## Testing Background Mode

Try this:
```bash
# This will run in background and return immediately
ssh_bg root@94.237.55.234 'sleep 10 && echo "Done!"'

# Check status
check_bg

# View output after 10 seconds
get_bg_output
```

## Reverting if Needed

If you want to revert to synchronous operations:

```bash
# Edit global settings
code ~/Library/Application\ Support/Code/User/settings.json

# Change:
"git.autofetch": true  # Enable auto-fetch
```

## Benefits

1. ✅ **Never blocked terminal** - Always responsive
2. ✅ **Parallel operations** - Multiple commands can run
3. ✅ **Better experience** - No waiting for remote operations
4. ✅ **Full output** - All logs saved and accessible
5. ✅ **Easy monitoring** - Check status anytime

## Notes

- SSH commands require your approval (security)
- Background jobs save logs to `/tmp/ssh_bg_*.log`
- Old logs are automatically cleaned after 24 hours
- You can still run commands manually as before

---

**This is now active for all your repositories!** 🎉
