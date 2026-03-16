# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A local tool for migrating Feishu (飞书) documents to DingTalk (钉钉) knowledge base. Supports single document and batch migration with format preservation. Markdown format is written directly to DingTalk documents.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run Web UI
python app.py
# Access at http://localhost:5000

# Run CLI migration
python run_migration.py
```

## Architecture

```
Web UI (index.html + app.js + style.css)
         ↓ HTTP API
Flask Backend (app.py)
         ↓
MigrationService (migration_service.py)
    ├── FeishuExporter (feishu_exporter.py) → Feishu API
    └── DingtalkImporter (dingtalk_importer.py) → DingTalk API
```

### Data Flow

```
Feishu URL → Extract Doc ID → Export Markdown → Create DingTalk Doc → Write Markdown Content
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Flask backend, API routes, serves static files |
| `migration_service.py` | Orchestrates export → import flow |
| `feishu_exporter.py` | Feishu API: token auth, document export, returns title + content |
| `dingtalk_importer.py` | DingTalk API: document creation and content writing |
| `index.html` / `app.js` / `style.css` | Frontend UI |
| `get_unionid.py` | Utility to retrieve user unionId from DingTalk |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main UI |
| `/api/auth/feishu` | POST | Validate Feishu credentials |
| `/api/auth/dingtalk` | POST | Validate DingTalk credentials |
| `/api/migrate/single` | POST | Migrate single document |
| `/api/migrate/batch` | POST | Batch migrate from wiki |
| `/api/dingtalk/get-unionid` | POST | Get user unionId |

## DingTalk API Details

### Content Update Endpoint
- Correct: `POST /v1.0/doc/suites/documents/{doc_key}/overwriteContent`
- Wrong: `PUT /v1.0/doc/docs/{doc_key}/content` (returns 404)

### Parameter Placement
- **Create document**: `operatorId` in request body
- **Update content**: `operatorId` in query params

### Authentication
- DingTalk document operations require **unionId** (not userId)
- Use `get_unionid.py` or `/api/dingtalk/get-unionid` endpoint

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| 404 on content update | Wrong API endpoint | Use `/v1.0/doc/suites/documents/{doc_key}/overwriteContent` |
| 400 "Unsupported dataType" | Extra parameter | Only send `content` field, remove `dataType` |
| 500 error on create | Using userId | Must use unionId from DingTalk API |
| Wrong document title | Using document ID | `feishu_exporter.py` returns `{'title': ..., 'content': ...}` |

## Feishu Block Types

See `_get_content_field()` in `feishu_exporter.py`:
- Types 3-11: Headings H1-H9 → `#` to `#########`
- Type 2: Text paragraph
- Type 12: Bullet list → `-`
- Type 13: Ordered list → `1.`
- Type 14: Code block → ``` ```
- Type 15: Quote → `>`
- Type 17: Todo → `- [ ]`
- Type 22: Horizontal rule → `---`

## Notes

- **Export directory**: `./exports/` - all migrated Markdown files saved here
- **Markdown format**: DingTalk API accepts and renders Markdown directly
- **Token caching**: `FeishuExporter` caches tenant token with 2-hour expiry
- **No image support**: Images are not migrated