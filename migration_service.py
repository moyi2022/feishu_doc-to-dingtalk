"""
迁移服务
整合飞书导出和钉钉导入
"""

import os
from typing import Dict, Any, List, Optional
from feishu_exporter import FeishuExporter
from dingtalk_importer import DingtalkImporter


class MigrationService:
    """迁移服务"""

    def __init__(self, feishu_creds: Dict[str, str], dingtalk_creds: Dict[str, str]):
        """
        初始化迁移服务

        Args:
            feishu_creds: 飞书凭证 {app_id, app_secret}
            dingtalk_creds: 钉钉凭证 {client_id, client_secret, corp_id}
        """
        self.feishu = FeishuExporter(
            feishu_creds['app_id'],
            feishu_creds['app_secret']
        )
        self.dingtalk = DingtalkImporter(
            dingtalk_creds['client_id'],
            dingtalk_creds['client_secret'],
            dingtalk_creds['corp_id'],
            dingtalk_creds.get('user_id', ''),
            dingtalk_creds.get('parent_node_id', ''),
            dingtalk_creds.get('template_id', ''),
            dingtalk_creds.get('template_type', '')
        )
        
        # 创建导出目录
        self.exports_dir = os.path.join(os.path.dirname(__file__), 'exports')
        if not os.path.exists(self.exports_dir):
            os.makedirs(self.exports_dir)
            print(f"[INFO] 创建导出目录：{self.exports_dir}")
    
    def migrate_single(self, feishu_url: str, workspace_id: str) -> Dict[str, Any]:
        """
        迁移单个文档
        
        Args:
            feishu_url: 飞书文档 URL
            workspace_id: 钉钉知识库 ID
            
        Returns:
            迁移结果
        """
        try:
            print(f"\n[INFO] ========== 开始迁移单个文档 ==========")
            print(f"[INFO] 飞书 URL: {feishu_url}")
            
            # 从 URL 提取文档 ID
            document_id = self._extract_document_id(feishu_url)
            if not document_id:
                return {
                    'success': False,
                    'error': '无法从 URL 提取文档 ID'
                }
            
            print(f"[INFO] 文档 ID: {document_id}")

            # 导出飞书文档为 Markdown
            print(f"[INFO] 正在导出飞书文档...")
            export_result = self.feishu.export_document(document_id)
            if not export_result:
                return {
                    'success': False,
                    'error': '导出飞书文档失败'
                }

            # 提取标题和内容
            doc_title = export_result.get('title', '未命名文档')
            markdown_content = export_result.get('content', '')
            print(f"[INFO] 导出成功，标题：{doc_title}，Markdown 长度：{len(markdown_content)}")

            # 保存 Markdown 文件到本地
            safe_title = self._sanitize_filename(doc_title)
            md_filename = f"{safe_title}.md"
            md_filepath = os.path.join(self.exports_dir, md_filename)

            print(f"[INFO] 保存 Markdown 文件：{md_filepath}")
            with open(md_filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"[INFO] Markdown 文件保存成功")

            # 创建钉钉文档（使用飞书文档的真实标题）
            print(f"[INFO] 开始创建钉钉文档...")
            doc_url = self.dingtalk.create_document(workspace_id, doc_title, markdown_content)
            
            if not doc_url:
                return {
                    'success': False,
                    'error': '创建钉钉文档失败'
                }
            
            print(f"[INFO] 钉钉文档创建成功：{doc_url}")
            print(f"[INFO] ========== 迁移完成 ==========\n")

            return {
                'success': True,
                'dingtalk_url': doc_url,
                'title': doc_title,
                'md_file': md_filename,
                'export_path': self.exports_dir
            }

        except Exception as e:
            print(f"[ERROR] 迁移异常：{str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # Windows 文件名非法字符
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        # 限制长度
        return filename[:100]
    
    def migrate_batch(self, wiki_id: str, workspace_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        批量迁移文档
        
        Args:
            wiki_id: 飞书知识库 ID
            workspace_id: 钉钉知识库 ID
            max_depth: 最大深度
            
        Returns:
            迁移结果统计
        """
        try:
            print(f"\n[INFO] ========== 开始批量迁移 ==========")
            print(f"[INFO] 飞书知识库 ID: {wiki_id}")
            print(f"[INFO] 钉钉知识库 ID: {workspace_id}")
            
            # 获取文档列表
            print(f"[INFO] 正在获取文档列表...")
            documents = self.feishu.get_wiki_documents(wiki_id, max_depth)
            print(f"[INFO] 获取到 {len(documents)} 个文档")
            
            total = len(documents)
            success_count = 0
            failed_count = 0
            results = []
            
            for i, doc in enumerate(documents, 1):
                print(f"\n[INFO] [{i}/{total}] 处理文档：{doc['title']}")
                
                # 构建飞书 URL
                feishu_url = f"https://example.feishu.cn/docx/{doc['id']}"
                
                # 复用单个文档迁移方法
                result = self.migrate_single(feishu_url, workspace_id)
                
                if result['success']:
                    success_count += 1
                    print(f"[INFO] [{i}/{total}] 迁移成功")
                else:
                    failed_count += 1
                    print(f"[ERROR] [{i}/{total}] 迁移失败：{result.get('error')}")
                
                results.append({
                    'title': doc['title'],
                    'success': result['success'],
                    'error': result.get('error'),
                    'md_file': result.get('md_file'),
                    'dingtalk_url': result.get('dingtalk_url')
                })
            
            print(f"\n[INFO] ========== 批量迁移完成 ==========")
            print(f"[INFO] 总计：{total} | 成功：{success_count} | 失败：{failed_count}")
            print(f"[INFO] 导出目录：{self.exports_dir}\n")
            
            return {
                'success': True,
                'total': total,
                'success_count': success_count,
                'failed_count': failed_count,
                'results': results,
                'export_path': self.exports_dir
            }
            
        except Exception as e:
            print(f"[ERROR] 批量迁移异常：{str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'total': 0,
                'success_count': 0,
                'failed_count': 0
            }
    
    def _extract_document_id(self, url: str) -> Optional[str]:
        """
        从飞书 URL 提取文档 ID
        
        Args:
            url: 飞书文档 URL
            
        Returns:
            文档 ID，无法提取返回 None
        """
        # 简单实现，可以根据实际 URL 格式调整
        if '/docx/' in url:
            return url.split('/docx/')[-1].split('?')[0].split('#')[0]
        return None
