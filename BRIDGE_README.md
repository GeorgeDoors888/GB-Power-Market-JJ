# GitHub → GPT → BigQuery Bridge

This tool connects your GitHub repositories to OpenAI and Google BigQuery.
It lets you:
- Download repo content automatically
- Run GPT-4 summaries and embeddings on each file
- Store those results for search or analysis in BigQuery
- Diagnose connectivity for each API layer

---

## 🚀 Quick Start

### 1. Requirements
- Python 3.10+
- VS Code or GitHub Codespace
- Access tokens for:
  - GitHub (Personal Access Token with `repo` scope)
  - OpenAI API key
  - Google Cloud Service Account (BigQuery access)

### 2. Setup

```bash
# Clone the repository (if not already cloned)
git clone https://github.com/GeorgeDoors888/overarch-jibber-jabber.git
cd overarch-jibber-jabber

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your actual tokens
```

### 3. Configure `.env`

Edit `.env` with your credentials:

```bash
# GitHub
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_REPO=GeorgeDoors888/overarch-jibber-jabber
GITHUB_BRANCH=main

# OpenAI
OPENAI_API_KEY=sk-your_openai_key_here

# BigQuery (optional)
GCP_PROJECT_ID=your-gcp-project
BQ_DATASET=document_index
BQ_TABLE=repo_chunks
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## 🔍 Usage

### Test Connectivity (Diagnostics)

Before running the full pipeline, verify all APIs are reachable:

```bash
python bridge.py --diagnose
```

Expected output:
```
=== Diagnostics Mode ===
🔍 GitHub API: ✅ OK (GeorgeDoors888/overarch-jibber-jabber accessible)
🧠 OpenAI API: ✅ OK (GPT-4 responding)
🪣 BigQuery: ✅ OK (Dataset document_index reachable)
   └─ Table repo_chunks: ✅ Found

Diagnostics complete.
```

### Download & Summarize Repository

**Basic usage** (creates `REPO_SUMMARY.md`):

```bash
python bridge.py
```

**Without OpenAI summaries** (just download files):

```bash
python bridge.py --no-summarise --no-bq
```

**Include hidden files** (e.g., `.github/`, `.vscode/`):

```bash
python bridge.py --include-hidden
```

### Sync to BigQuery

**Full pipeline** (download → summarize → embed → upload):

```bash
python bridge.py
```

**Skip embeddings** (faster, lower cost):

```bash
python bridge.py --no-embed
```

**Skip BigQuery sync entirely**:

```bash
python bridge.py --no-bq
```

### Analyze a Different Repository

```bash
python bridge.py --repo GeorgeDoors888/another-repo --branch develop
```

---

## 📁 Output

### `REPO_SUMMARY.md`
Executive summary of the entire repository created by GPT-4, including:
- System overview
- Main components
- Runtime requirements
- External services
- Deployment instructions
- Key risks

### BigQuery Table Schema

If syncing to BigQuery, the tool creates a table with:

| Column | Type | Description |
|--------|------|-------------|
| `repo` | STRING | Repository name (owner/repo) |
| `branch` | STRING | Git branch |
| `path` | STRING | File path |
| `sha` | STRING | Git SHA of file |
| `summary` | STRING | GPT-4 generated summary |
| `content` | STRING | File content (first 20KB) |
| `embedding` | FLOAT[] | Text embedding vector |
| `updated_at` | TIMESTAMP | Last sync time |
| `content_sha1` | STRING | Content hash for deduplication |

---

## 🛠️ Advanced Options

### Command-Line Arguments

```bash
python bridge.py --help
```

| Flag | Description |
|------|-------------|
| `--diagnose` | Run connectivity tests only |
| `--repo OWNER/NAME` | Target repository |
| `--branch BRANCH` | Target branch (default: main) |
| `--include-hidden` | Include dotfiles/hidden folders |
| `--no-summarise` | Skip GPT summaries |
| `--no-embed` | Skip embedding generation |
| `--no-bq` | Skip BigQuery sync |
| `--save-repo-summary FILE` | Output path for repo summary |

### File Type Detection

The bridge auto-detects text files by extension:
- Code: `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.html`, `.css`, etc.
- Config: `.json`, `.yml`, `.yaml`, `.toml`, `.ini`, `.cfg`
- Docs: `.md`, `.txt`, `.rst`
- Scripts: `.sh`, `.ps1`, `.dockerfile`

Files larger than 400KB are skipped to prevent memory issues.

---

## 🔐 Security Notes

1. **Never commit `.env`** — it contains sensitive tokens
2. Store service account JSON outside the repo
3. Use environment-specific `.env` files (`.env.dev`, `.env.prod`)
4. Rotate tokens regularly
5. Use least-privilege IAM roles for BigQuery

---

## 🐛 Troubleshooting

### "GITHUB_TOKEN missing"
- Verify `.env` exists and is in the same directory as `bridge.py`
- Check `GITHUB_TOKEN` has `repo` scope
- Run `--diagnose` to test

### "OpenAI API: ❌ FAILED"
- Verify `OPENAI_API_KEY` is valid
- Check account has credits remaining
- Test with: `openai api chat.completions.create -m gpt-4o-mini`

### "BigQuery: ❌ FAILED"
- Check `GOOGLE_APPLICATION_CREDENTIALS` path is absolute
- Verify service account has `bigquery.dataEditor` role
- Ensure dataset exists or tool has permissions to create it

### Rate Limits
- GitHub: 5,000 requests/hour (authenticated)
- OpenAI: Depends on tier (watch for 429 errors)
- BigQuery: 100 inserts/second (batching handles this)

---

## 📊 Cost Estimates

### OpenAI (GPT-4o-mini)
- ~100 files: **$0.50 - $2.00**
- ~1,000 files: **$5 - $20**

### BigQuery
- Storage: ~$0.02/GB/month
- Queries: $5/TB scanned
- Inserts: Free (up to streaming limits)

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

See [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- GitHub Issues: [Create an issue](https://github.com/GeorgeDoors888/overarch-jibber-jabber/issues)
- Email: george@upowerenergy.uk
