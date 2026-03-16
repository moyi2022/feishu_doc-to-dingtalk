# 飞书文档转钉钉文档迁移工具

一个本地工具，支持将飞书文档一键迁移到钉钉知识库。

## 功能特点

- 支持单个文档迁移
- 支持批量文档迁移（整个知识库）
- 保持文档格式（文本、标题、列表、代码块、引用等）
- Web 界面 + 命令行两种使用方式
- 本地执行，数据安全

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 方式一：Web 界面

```bash
python app.py
```

访问 http://localhost:5000

### 3. 方式二：命令行脚本

编辑 `run_migration.py`，填写凭证和文档 URL：

```python
feishu_creds = {
    'app_id': '你的飞书AppID',
    'app_secret': '你的飞书AppSecret'
}

dingtalk_creds = {
    'client_id': '你的钉钉ClientID',
    'client_secret': '你的钉钉ClientSecret',
    'corp_id': '你的企业CorpId',
    'user_id': '操作用户unionId'  # 重要：必须是 unionId
}

workspace_id = '目标钉钉知识库ID'
feishu_url = '飞书文档URL'
```

运行迁移：

```bash
python run_migration.py
```

## API 凭证获取

### 飞书凭证

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 开通权限：
   - 查看新版文档
   - 查看知识库
   - 下载云文档中的图片和附件
4. 获取 App ID 和 App Secret

### 钉钉凭证

1. 访问 [钉钉开放平台](https://open.dingtalk.com/)
2. 创建企业内部应用
3. 开通权限：
   - 知识库文档写权限
   - 企业存储文件写权限
   - 通讯录只读权限（用于获取 unionId）
4. 获取 Client ID、Client Secret、Corp ID

### 获取 unionId（重要）

钉钉文档 API 需要使用 **unionId**，不是 userId。获取方法：

```python
# 使用钉钉 API 获取用户 unionId
import requests

# 获取 access_token
token_url = f'https://api.dingtalk.com/v1.0/oauth2/{corp_id}/token'
response = requests.post(token_url, json={
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret
})
token = response.json()['access_token']

# 获取用户详情（需要知道 userId）
user_url = f'https://oapi.dingtalk.com/topapi/v2/user/get?access_token={token}'
response = requests.post(user_url, json={'userid': '用户的userId'})
union_id = response.json()['result']['unionid']
```

## 知识库 ID 获取

### 钉钉知识库 ID

打开钉钉知识库，查看浏览器 URL：

```
https://alidocs.dingtalk.com/i/nodes/知识库ID/...
```

中间的部分就是知识库 ID。

### 飞书知识库 ID

打开飞书知识库，查看浏览器 URL：

```
https://xxx.feishu.cn/wiki/知识库ID?...
```

## 项目结构

```
├── app.py                 # Flask 后端 API
├── app.js                 # 前端逻辑
├── index.html             # Web 界面
├── style.css              # 样式
├── run_migration.py       # 命令行迁移脚本
├── migration_service.py   # 迁移服务协调
├── feishu_exporter.py     # 飞书文档导出
├── dingtalk_importer.py   # 钉钉文档导入
├── format_converter.py    # 格式转换
├── exports/               # 导出文件目录
└── requirements.txt       # Python 依赖
```

## 迁移流程

```
飞书文档 → 导出 Markdown → 创建钉钉文档 → 写入 Markdown 内容
```

1. **导出飞书文档**：调用飞书 API 获取文档块，转换为 Markdown
2. **创建钉钉文档**：调用钉钉 API 创建空文档
3. **写入内容**：将 Markdown 内容直接写入钉钉文档

## API 端点

### 钉钉文档操作

| 操作 | 端点 | 方法 |
|------|------|------|
| 创建文档 | `/v1.0/doc/workspaces/{workspace_id}/docs` | POST |
| 写入内容 | `/v1.0/doc/suites/documents/{doc_key}/overwriteContent` | POST |

### 飞书文档操作

| 操作 | 端点 | 方法 |
|------|------|------|
| 获取文档 | `/docx/v1/documents/{document_id}` | GET |
| 获取文档块 | `/docx/v1/documents/{document_id}/blocks` | GET |

## 常见问题

### 文档创建失败（HTTP 500）

原因：operatorId 使用了 userId 而不是 unionId

解决：使用正确的 unionId

### 内容更新失败（HTTP 404）

原因：API 端点错误

正确端点：`POST /v1.0/doc/suites/documents/{doc_key}/overwriteContent`

### 获取 token 失败

检查：
- 凭证是否正确
- 应用是否已上线
- IP 是否在白名单中

## 注意事项

- 本工具为一次性迁移，不支持持续同步
- 图片和附件不会自动迁移
- 建议先测试单个文档，确认配置正确后再批量迁移

## License

MIT