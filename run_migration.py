# -*- coding: utf-8 -*-
"""
飞书文档 → 钉钉文档 迁移脚本

使用方法：
1. 安装依赖: pip install -r requirements.txt
2. 填写下方的飞书凭证和钉钉凭证
3. 设置要迁移的飞书文档 URL
4. 运行: python run_migration.py
"""
from migration_service import MigrationService

# ============ 飞书凭证配置 ============
# 获取路径：https://open.feishu.cn/ → 我的应用 → 凭证与基础信息
feishu_creds = {
    'app_id': '',       # 填写飞书 App ID
    'app_secret': ''    # 填写飞书 App Secret
}

# ============ 钉钉凭证配置 ============
# 获取路径：https://open.dingtalk.com/ → 应用开发 → 企业内部开发
dingtalk_creds = {
    'client_id': '',        # Client ID
    'client_secret': '',    # Client Secret
    'corp_id': '',          # 企业 CorpId
    'user_id': ''           # 操作用户 unionId（必填！）
}

# ============ 迁移配置 ============
# 目标钉钉知识库 ID（从知识库 URL 获取）
workspace_id = ''

# 要迁移的飞书文档 URL
feishu_url = ''  # 例如: 'https://xxx.feishu.cn/docx/xxxxx'


def main():
    """主函数"""
    # 检查凭证
    if not feishu_creds['app_id'] or not feishu_creds['app_secret']:
        print("错误：请先填写飞书凭证（app_id 和 app_secret）")
        print("获取路径：https://open.feishu.cn/ → 我的应用 → 凭证与基础信息")
        return

    if not dingtalk_creds['client_id'] or not dingtalk_creds['client_secret']:
        print("错误：请先填写钉钉凭证（client_id 和 client_secret）")
        print("获取路径：https://open.dingtalk.com/ → 应用开发 → 企业内部开发")
        return

    if not dingtalk_creds['corp_id']:
        print("错误：请先填写钉钉企业 ID（corp_id）")
        print("获取路径：https://open.dingtalk.com/ → 首页 → 组织信息 → CorpId")
        return

    if not dingtalk_creds['user_id']:
        print("错误：请先填写操作用户 unionId")
        print("重要：这里需要填写 unionId，不是 userId！")
        print("获取方法：通过钉钉开放平台 API 获取，或联系管理员")
        return

    if not feishu_url:
        print("错误：请先设置要迁移的飞书文档 URL")
        return

    if not workspace_id:
        print("错误：请先设置目标钉钉知识库 ID")
        return

    print("=" * 60)
    print("飞书 → 钉钉 文档迁移")
    print("=" * 60)
    print(f"飞书文档: {feishu_url}")
    print(f"目标知识库: {workspace_id}")
    print("=" * 60)

    # 创建迁移服务
    service = MigrationService(feishu_creds, dingtalk_creds)

    # 执行迁移
    result = service.migrate_single(feishu_url, workspace_id)

    # 输出结果
    print("\n" + "=" * 60)
    print("迁移结果")
    print("=" * 60)

    if result['success']:
        print("状态: 成功 ✓")
        print(f"文档标题: {result.get('title')}")
        print(f"钉钉链接: {result.get('dingtalk_url')}")
        print(f"Markdown 文件: {result.get('md_file')}")
        print(f"HTML 文件: {result.get('html_file')}")
        print(f"导出目录: {result.get('export_path')}")
    else:
        print("状态: 失败 ✗")
        print(f"错误: {result.get('error')}")

    print("=" * 60)


if __name__ == '__main__':
    main()