# 飞书文档转钉钉文档迁移工具

一个本地工具，支持将飞书文档一键迁移到钉钉知识库。

## 功能特点

- ✅ 支持单个文档迁移
- ✅ 支持批量文档迁移（整个知识库）
- ✅ 保持文档格式（文本、标题、列表、代码块、引用等）
- ✅ Web 界面 + 命令行两种使用方式
- ✅ 知识库下拉选择（自动加载可用知识库）
- ✅ 高级选项：父节点、文档模板
- ✅ unionId 自动获取工具
- ✅ 简洁现代 UI 设计
- ✅ 本地执行，数据安全

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
├── index.html             # Web 界面（现代紧凑设计）
├── style.css              # 样式（CSS 变量 + 响应式）
├── run_migration.py       # 命令行迁移脚本
├── migration_service.py   # 迁移服务协调
├── feishu_exporter.py     # 飞书文档导出
├── dingtalk_importer.py   # 钉钉文档导入
├── format_converter.py    # 格式转换
├── get_unionid.py         # unionId 获取工具
├── exports/               # 导出文件目录
└── requirements.txt       # Python 依赖
```

## Web 界面功能

### 知识库选择

保存钉钉凭证后，系统自动加载可用的知识库列表：
- **下拉选择**：从列表中选择目标知识库
- **手动输入**：如果列表加载失败，可切换到手动输入 ID

### 高级选项

单个文档迁移支持以下高级选项：

| 选项 | 说明 |
|------|------|
| 父节点 ID | 在指定文件夹下创建文档，留空则在根目录创建 |
| 模板 ID | 使用文档模板创建 |
| 模板类型 | 官方模板 / 团队模板 / 个人模板 |

### unionId 获取工具

内置工具支持通过以下方式获取 unionId：
- 通过 userId 查询
- 通过手机号查询

## 迁移流程

```
飞书文档 → 导出 Markdown → 创建钉钉文档 → 写入 Markdown 内容
```

1. **导出飞书文档**：调用飞书 API 获取文档块，转换为 Markdown
2. **创建钉钉文档**：调用钉钉 API 创建空文档
3. **写入内容**：将 Markdown 内容直接写入钉钉文档

## API 端点

### 后端 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/feishu` | POST | 飞书凭证验证 |
| `/api/auth/dingtalk` | POST | 钉钉凭证验证 |
| `/api/migrate/single` | POST | 单文档迁移 |
| `/api/migrate/batch` | POST | 批量迁移 |
| `/api/dingtalk/workspaces` | POST | 获取知识库列表 |
| `/api/dingtalk/get-unionid` | POST | 获取用户 unionId |

### 钉钉开放平台 API

| 操作 | 端点 | 方法 |
|------|------|------|
| 创建文档 | `/v1.0/doc/workspaces/{workspace_id}/docs` | POST |
| 写入内容 | `/v1.0/doc/suites/documents/{doc_key}/overwriteContent` | POST |
| 获取知识库列表 | `/v1.0/wiki/workspaces` | GET |

### 飞书开放平台 API

| 操作 | 端点 | 方法 |
|------|------|------|
| 获取文档 | `/docx/v1/documents/{document_id}` | GET |
| 获取文档块 | `/docx/v1/documents/{document_id}/blocks` | GET |

## 注意事项

- 本工具为一次性迁移，不支持持续同步
- 图片和附件不会自动迁移
- 建议先测试单个文档，确认配置正确后再批量迁移
- 知识库列表加载失败时，请切换到手动输入模式

## 常见问题

### 知识库列表加载失败

**可能原因：**
- 应用未开通 `Document.Workspace.Read` 权限
- API 权限需等待审核生效

**解决方案：**
- 切换到"手动输入"模式，直接填写知识库 ID

### 文档创建失败（HTTP 500）

**原因：** operatorId 使用了 userId 而不是 unionId

**解决：** 使用内置的 unionId 获取工具

### 内容更新失败（HTTP 404）

**原因：** API 端点错误

**正确端点：** `POST /v1.0/doc/suites/documents/{doc_key}/overwriteContent`

### 获取 token 失败

**检查项：**
- 凭证是否正确
- 应用是否已上线
- IP 是否在白名单中

## License

MIT