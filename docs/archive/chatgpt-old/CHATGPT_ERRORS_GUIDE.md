# Common ChatGPT GitHub Connector Errors & Fixes

## 🔴 Error: "Access Denied" or "403 Forbidden"

**Cause**: ChatGPT GitHub App not installed or lacks permissions

**Fix**:
1. Visit: https://github.com/settings/installations
2. Look for "ChatGPT" in the list
3. If NOT found:
   - Go to: https://github.com/apps/chatgpt
   - Click "Install"
   - Grant access to repositories
4. If found but greyed out:
   - Click "Configure"
   - Enable repository access
   - Save changes

---

## 🔴 Error: "Repository Not Found" or "404"

**Causes**:
- Private repo not shared with ChatGPT
- Repo name typo
- App permissions insufficient

**Fix**:
1. Verify repo exists: https://github.com/GeorgeDoors888/overarch-jibber-jabber
2. If private, grant ChatGPT access:
   ```bash
   # Check if repo is private
   gh api /repos/GeorgeDoors888/overarch-jibber-jabber | grep '"private"'
   ```
3. Go to: https://github.com/settings/installations
4. Click ChatGPT → Configure
5. Under "Repository access":
   - Select "All repositories" OR
   - Add "overarch-jibber-jabber" specifically

---

## 🔴 Error: "Authentication Required" or "Unauthorized"

**Cause**: OAuth token expired or revoked

**Fix**:
1. In ChatGPT:
   - Settings → Connections
   - Remove GitHub connection
   - Wait 10 seconds
   - Re-add GitHub connection
2. Complete OAuth flow again
3. Grant all requested permissions

---

## 🔴 Error: "Rate Limit Exceeded"

**Cause**: Too many API requests in short time

**Fix**:
- Wait 5-10 minutes
- Try again
- Check rate limit status:
  ```bash
  gh api /rate_limit
  ```

---

## 🔴 Error: "Invalid OAuth Token"

**Cause**: Token revoked or scopes changed

**Fix**:
```bash
# Refresh token with all scopes
gh auth refresh -h github.com -s read:user,user:email,repo,workflow,read:org

# Verify it worked
gh auth status
```

---

## 🔴 Error: "Repository is Empty" or "No Files Found"

**Cause**: Repo has no commits or branch doesn't exist

**Fix**:
1. Check repo has commits:
   ```bash
   gh api /repos/GeorgeDoors888/overarch-jibber-jabber/commits | head -20
   ```
2. Verify default branch:
   ```bash
   gh repo view GeorgeDoors888/overarch-jibber-jabber --json defaultBranchRef
   ```
3. Push at least one commit if empty

---

## 🔴 Error: "ChatGPT Cannot Access This Organization"

**Cause**: Organization-owned repo with restricted app access

**Fix**:
1. Go to organization settings (if applicable)
2. Settings → Third-party access → GitHub Apps
3. Find ChatGPT, grant access
4. Or contact org admin to approve

---

## 🔴 Error: "Connection Timeout" or "Network Error"

**Causes**:
- GitHub API temporarily down
- Network connectivity issues
- Rate limiting by GitHub

**Fix**:
1. Check GitHub status: https://www.githubstatus.com/
2. Wait a few minutes and retry
3. Verify your internet connection
4. Clear browser cache (if using web ChatGPT)

---

## 🟢 Quick Diagnostic Commands

Run these to check your setup:

```bash
# 1. Check authentication
gh auth status

# 2. Verify repo access
gh api /repos/GeorgeDoors888/overarch-jibber-jabber

# 3. List your repos
gh repo list GeorgeDoors888 --limit 10

# 4. Check ChatGPT app installation
gh api /user/installations

# 5. Run full diagnostic
cd ~/Overarch\ Jibber\ Jabber
python diagnose_github_oauth.py
```

---

## 🆘 Still Not Working?

### Complete Reset Procedure:

1. **Remove ChatGPT GitHub App**:
   - https://github.com/settings/installations
   - Click ChatGPT → Configure → Uninstall

2. **Revoke OAuth tokens**:
   - https://github.com/settings/applications
   - Find ChatGPT, click "Revoke"

3. **Clear GitHub CLI auth**:
   ```bash
   gh auth logout
   ```

4. **Start fresh**:
   ```bash
   # Re-authenticate
   gh auth login
   
   # Install app
   open https://github.com/apps/chatgpt
   
   # Reconnect in ChatGPT
   # Settings → Connections → GitHub → Connect
   ```

5. **Verify**:
   ```bash
   python diagnose_github_oauth.py
   ```

---

## 📞 Get Help

If none of these work:

1. **Copy error message exactly**
2. **Run diagnostic**:
   ```bash
   python diagnose_github_oauth.py > github_diagnostic.txt
   ```
3. **Share both** with GitHub support or in this chat

---

## ✅ Success Checklist

Before saying "it's working":

- [ ] Can list your repositories in ChatGPT
- [ ] Can view specific repo files
- [ ] Can read file contents
- [ ] Can search code
- [ ] No error messages

Test command in ChatGPT:
```
"Show me the README.md file from my overarch-jibber-jabber repository"
```
