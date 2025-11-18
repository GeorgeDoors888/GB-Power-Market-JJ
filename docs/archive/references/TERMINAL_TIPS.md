# Terminal Management Tips for VS Code + GitHub Copilot

## Problem
When GitHub Copilot runs terminal commands, you can't use that terminal simultaneously.

## Solutions

### 1. Open Multiple Terminals
- Press `Ctrl + Shift + ` (backtick) to open a new terminal
- Or click the "+" icon in the terminal panel
- Use separate terminals: one for Copilot, one for your commands

### 2. Kill Stuck Commands
If a command hangs:
- Press `Ctrl + C` to stop it
- Close the terminal tab if needed
- Open a new terminal

### 3. Background Long Commands
For long-running tasks:
```bash
# Run in background
command &

# Or use screen/tmux on remote servers
ssh server 'screen -dmS session_name command'
```

### 4. Let Copilot Finish
- Wait for the command prompt (➜) to appear
- Look for "Command exited with code X" messages
- Then the terminal is free for your use

## VS Code Terminal Shortcuts
- `Cmd + ` - Toggle terminal
- `Cmd + Shift + ` - New terminal
- `Cmd + W` - Close current terminal
- Split terminal: Click split icon in terminal panel

## Best Practice
Keep 2-3 terminals open:
1. For GitHub Copilot automation
2. For your manual commands
3. For SSH/remote sessions
