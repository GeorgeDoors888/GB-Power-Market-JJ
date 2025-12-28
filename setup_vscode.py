#!/usr/bin/env python3
"""
VS Code Auto-Setup Script for GB Power Market Project
Automatically installs VS Code, extensions, and configures settings

Usage: python3 setup_vscode.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import urllib.request
import shutil

class Colors:
    """Terminal colors"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def run_command(command, capture_output=False, check=True):
    """Run shell command"""
    try:
        if capture_output:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=check
            )
            return result.stdout.strip()
        else:
            subprocess.run(command, shell=True, check=check)
            return True
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"Command failed: {command}")
            print_error(f"Error: {e}")
        return False

def check_vscode_installed():
    """Check if VS Code is installed"""
    print_info("Checking if VS Code is installed...")
    
    # Check common installation paths
    vscode_paths = [
        "/Applications/Visual Studio Code.app",
        os.path.expanduser("~/Applications/Visual Studio Code.app")
    ]
    
    for path in vscode_paths:
        if os.path.exists(path):
            print_success(f"VS Code found at: {path}")
            return True
    
    # Check if 'code' command exists
    result = run_command("which code", capture_output=True, check=False)
    if result:
        print_success(f"VS Code CLI found at: {result}")
        return True
    
    return False

def install_vscode():
    """Install VS Code via Homebrew"""
    print_info("Installing VS Code via Homebrew...")
    
    # Check if Homebrew is installed
    if not run_command("which brew", capture_output=True, check=False):
        print_error("Homebrew not found. Installing Homebrew first...")
        install_homebrew = input("Install Homebrew? (y/n): ")
        if install_homebrew.lower() == 'y':
            run_command('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
        else:
            print_warning("Skipping Homebrew installation. Please install VS Code manually:")
            print_info("Visit: https://code.visualstudio.com/")
            return False
    
    # Install VS Code with Homebrew
    print_info("Running: brew install --cask visual-studio-code")
    if run_command("brew install --cask visual-studio-code", check=False):
        print_success("VS Code installed successfully!")
        return True
    else:
        print_warning("Homebrew installation failed. Please install manually from:")
        print_info("https://code.visualstudio.com/")
        return False

def install_code_command():
    """Install 'code' command in PATH"""
    print_info("Installing 'code' command in PATH...")
    
    # Check if already installed
    if run_command("which code", capture_output=True, check=False):
        print_success("'code' command already available")
        return True
    
    # Try to install via VS Code (if running)
    print_info("Attempting to install via VS Code...")
    print_warning("If VS Code opens, press Cmd+Shift+P, type 'shell command', and select 'Install code command in PATH'")
    
    vscode_path = "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
    if os.path.exists(vscode_path):
        # Create symlink
        symlink_path = "/usr/local/bin/code"
        try:
            if not os.path.exists(symlink_path):
                os.symlink(vscode_path, symlink_path)
                print_success("'code' command installed!")
                return True
        except PermissionError:
            print_warning("Need sudo permission to create symlink")
            if run_command(f"sudo ln -sf '{vscode_path}' '{symlink_path}'", check=False):
                print_success("'code' command installed!")
                return True
    
    print_warning("Please install manually: Open VS Code → Cmd+Shift+P → 'Shell Command: Install code command in PATH'")
    return False

def install_extensions():
    """Install VS Code extensions"""
    print_header("Installing VS Code Extensions")
    
    extensions = [
        ("ms-python.python", "Python"),
        ("ms-python.vscode-pylance", "Pylance"),
        ("ms-toolsai.jupyter", "Jupyter"),
        ("njpwerner.autodocstring", "autoDocstring"),
        ("github.copilot", "GitHub Copilot (optional)"),
        ("eamodio.gitlens", "GitLens"),
        ("aaron-bond.better-comments", "Better Comments"),
        ("christian-kohler.path-intellisense", "Path Intellisense"),
        ("yzhang.markdown-all-in-one", "Markdown All in One"),
    ]
    
    installed = []
    failed = []
    skipped = []
    
    for ext_id, ext_name in extensions:
        print_info(f"Installing {ext_name}...")
        
        # Special handling for GitHub Copilot (optional)
        if ext_id == "github.copilot":
            response = input(f"  Install {ext_name}? (requires subscription) (y/n): ")
            if response.lower() != 'y':
                print_warning(f"Skipping {ext_name}")
                skipped.append(ext_name)
                continue
        
        result = run_command(f"code --install-extension {ext_id}", check=False)
        if result:
            print_success(f"Installed {ext_name}")
            installed.append(ext_name)
        else:
            print_error(f"Failed to install {ext_name}")
            failed.append(ext_name)
    
    print(f"\n{Colors.BOLD}Extension Installation Summary:{Colors.END}")
    print(f"{Colors.GREEN}✅ Installed: {len(installed)}{Colors.END}")
    if installed:
        for ext in installed:
            print(f"   - {ext}")
    
    if skipped:
        print(f"{Colors.YELLOW}⏭️  Skipped: {len(skipped)}{Colors.END}")
        for ext in skipped:
            print(f"   - {ext}")
    
    if failed:
        print(f"{Colors.RED}❌ Failed: {len(failed)}{Colors.END}")
        for ext in failed:
            print(f"   - {ext}")
    
    return len(installed) > 0

def create_workspace_settings():
    """Create .vscode/settings.json"""
    print_header("Creating Workspace Settings")
    
    project_root = Path.cwd()
    vscode_dir = project_root / ".vscode"
    settings_file = vscode_dir / "settings.json"
    
    # Create .vscode directory
    vscode_dir.mkdir(exist_ok=True)
    print_success(f"Created directory: {vscode_dir}")
    
    # Settings configuration
    settings = {
        "python.defaultInterpreterPath": "/usr/local/bin/python3",
        "python.linting.enabled": True,
        "python.linting.pylintEnabled": True,
        "python.formatting.provider": "autopep8",
        "python.terminal.activateEnvironment": True,
        "editor.formatOnSave": False,
        "editor.rulers": [80, 120],
        "files.exclude": {
            "**/__pycache__": True,
            "**/*.pyc": True,
            "**/.DS_Store": True
        },
        "files.trimTrailingWhitespace": True,
        "files.insertFinalNewline": True,
        "[python]": {
            "editor.tabSize": 4,
            "editor.insertSpaces": True
        },
        "[markdown]": {
            "editor.wordWrap": "on",
            "editor.quickSuggestions": False
        }
    }
    
    # Write settings file
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)
    
    print_success(f"Created: {settings_file}")
    return True

def create_launch_config():
    """Create .vscode/launch.json for debugging"""
    print_info("Creating debug launch configuration...")
    
    project_root = Path.cwd()
    vscode_dir = project_root / ".vscode"
    launch_file = vscode_dir / "launch.json"
    
    # Get home directory for credentials path
    home_dir = str(Path.home())
    
    # Launch configuration
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Current File",
                "type": "debugpy",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "env": {
                    "GOOGLE_APPLICATION_CREDENTIALS": f"{home_dir}/.google-credentials/inner-cinema-credentials.json",
                    "GCP_PROJECT": "inner-cinema-476211-u9",
                    "BQ_DATASET": "uk_energy_prod",
                    "BQ_LOCATION": "US"
                }
            },
            {
                "name": "Python: BigQuery Test",
                "type": "debugpy",
                "request": "launch",
                "program": "${workspaceFolder}/test_bigquery_vscode.py",
                "console": "integratedTerminal"
            }
        ]
    }
    
    with open(launch_file, 'w') as f:
        json.dump(launch_config, f, indent=2)
    
    print_success(f"Created: {launch_file}")
    return True

def create_test_script():
    """Create test_bigquery_vscode.py"""
    print_info("Creating BigQuery test script...")
    
    test_script = '''#!/usr/bin/env python3
"""
VS Code BigQuery Connection Test
Tests that credentials work from VS Code environment
"""

import os
import sys

def check_environment():
    """Check environment variables are set"""
    print("🔍 Checking environment variables...\\n")
    
    required = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GCP_PROJECT',
        'BQ_DATASET',
        'BQ_LOCATION'
    ]
    
    missing = []
    for var in required:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value[:50]}...")
        else:
            print(f"   ❌ {var}: NOT SET")
            missing.append(var)
    
    if missing:
        print(f"\\n❌ Missing variables: {', '.join(missing)}")
        print("   Fix: Run 'source ~/.zshrc' in VS Code terminal")
        return False
    
    return True

def test_bigquery():
    """Test BigQuery connection"""
    print("\\n📊 Testing BigQuery connection...\\n")
    
    try:
        from google.cloud import bigquery
        
        client = bigquery.Client(
            project=os.getenv('GCP_PROJECT'),
            location=os.getenv('BQ_LOCATION')
        )
        
        query = f"""
        SELECT COUNT(*) as row_count
        FROM `{os.getenv('GCP_PROJECT')}.{os.getenv('BQ_DATASET')}.bmrs_mid`
        LIMIT 1
        """
        
        result = client.query(query).result()
        for row in result:
            print(f"   ✅ BigQuery connected!")
            print(f"   📈 bmrs_mid table has {row.row_count:,} rows")
        
        return True
        
    except Exception as e:
        print(f"   ❌ BigQuery connection failed:")
        print(f"   {str(e)}")
        return False

if __name__ == "__main__":
    print("╔════════════════════════════════════════════════╗")
    print("║  VS Code BigQuery Connection Test             ║")
    print("╚════════════════════════════════════════════════╝\\n")
    
    env_ok = check_environment()
    if not env_ok:
        sys.exit(1)
    
    bq_ok = test_bigquery()
    if not bq_ok:
        sys.exit(1)
    
    print("\\n╔════════════════════════════════════════════════╗")
    print("║  ✅ ALL TESTS PASSED!                         ║")
    print("║  VS Code is ready for BigQuery development    ║")
    print("╚════════════════════════════════════════════════╝\\n")
'''
    
    with open('test_bigquery_vscode.py', 'w') as f:
        f.write(test_script)
    
    # Make executable
    os.chmod('test_bigquery_vscode.py', 0o755)
    
    print_success("Created: test_bigquery_vscode.py")
    return True

def update_gitignore():
    """Update .gitignore to exclude VS Code settings if needed"""
    print_info("Checking .gitignore...")
    
    gitignore_path = Path(".gitignore")
    
    vscode_entries = [
        ".vscode/*",
        "!.vscode/settings.json",
        "!.vscode/launch.json",
        "!.vscode/extensions.json"
    ]
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        # Check if VS Code entries exist
        if ".vscode" in content:
            print_success(".gitignore already includes VS Code entries")
            return True
        
        # Append VS Code entries
        with open(gitignore_path, 'a') as f:
            f.write("\n# VS Code\n")
            for entry in vscode_entries:
                f.write(f"{entry}\n")
        
        print_success("Updated .gitignore with VS Code entries")
    else:
        # Create new .gitignore
        with open(gitignore_path, 'w') as f:
            f.write("# VS Code\n")
            for entry in vscode_entries:
                f.write(f"{entry}\n")
        
        print_success("Created .gitignore with VS Code entries")
    
    return True

def open_vscode():
    """Open VS Code in current directory"""
    print_info("Opening VS Code...")
    
    if run_command("code .", check=False):
        print_success("VS Code opened!")
        return True
    else:
        print_warning("Could not open VS Code automatically")
        print_info("Please open VS Code manually: Applications → Visual Studio Code")
        return False

def main():
    """Main setup function"""
    print_header("⚡ VS Code Auto-Setup for GB Power Market")
    print_info("This script will:")
    print_info("  1. Check/Install VS Code")
    print_info("  2. Install essential extensions")
    print_info("  3. Create workspace settings")
    print_info("  4. Create debug configuration")
    print_info("  5. Create test script")
    print_info("  6. Open VS Code")
    
    response = input(f"\n{Colors.BOLD}Continue with setup? (y/n): {Colors.END}")
    if response.lower() != 'y':
        print_warning("Setup cancelled")
        return
    
    # Step 1: Check VS Code
    print_header("Step 1: Checking VS Code Installation")
    vscode_installed = check_vscode_installed()
    
    if not vscode_installed:
        print_warning("VS Code not found")
        install_response = input("Install VS Code via Homebrew? (y/n): ")
        if install_response.lower() == 'y':
            if not install_vscode():
                print_error("VS Code installation failed")
                return
        else:
            print_error("VS Code is required. Please install manually:")
            print_info("https://code.visualstudio.com/")
            return
    
    # Step 2: Install code command
    print_header("Step 2: Installing 'code' Command")
    install_code_command()
    
    # Step 3: Install extensions
    print_header("Step 3: Installing Extensions")
    install_extensions()
    
    # Step 4: Create workspace settings
    print_header("Step 4: Creating Workspace Configuration")
    create_workspace_settings()
    create_launch_config()
    
    # Step 5: Create test script
    print_header("Step 5: Creating Test Script")
    create_test_script()
    
    # Step 6: Update .gitignore
    print_header("Step 6: Updating .gitignore")
    update_gitignore()
    
    # Step 7: Open VS Code
    print_header("Step 7: Opening VS Code")
    open_vscode()
    
    # Final summary
    print_header("✅ Setup Complete!")
    print_success("VS Code is now configured for GB Power Market development!")
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    print(f"{Colors.GREEN}1. VS Code should be open now{Colors.END}")
    print(f"{Colors.GREEN}2. Press Ctrl+` to open integrated terminal{Colors.END}")
    print(f"{Colors.GREEN}3. Run: python3 test_bigquery_vscode.py{Colors.END}")
    print(f"{Colors.GREEN}4. Check VSCODE_SETUP_GUIDE.md for full tutorial{Colors.END}")
    
    print(f"\n{Colors.BOLD}Keyboard Shortcuts to Learn:{Colors.END}")
    print(f"  Cmd+P          - Quick open file")
    print(f"  Cmd+Shift+P    - Command palette")
    print(f"  Ctrl+`         - Toggle terminal")
    print(f"  F5             - Start debugging")
    print(f"  Cmd+Shift+F    - Search all files")
    
    print(f"\n{Colors.BOLD}Documentation:{Colors.END}")
    print(f"  VSCODE_SETUP_GUIDE.md - Full VS Code guide")
    print(f"  BEGINNERS_GUIDE_CHATGPT_BIGQUERY.md - System overview")
    
    print(f"\n{Colors.GREEN}🎉 Happy coding!{Colors.END}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
