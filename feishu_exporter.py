"""
飞书文档导出模块 - 完整版
"""

import requests
import json
from typing import Optional, Dict, Any, List
import time


class FeishuExporter:
    """飞书文档导出器"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis"
        self.tenant_token = None
        self.token_expire_time = 0
    
    def get_tenant_token(self) -> str:
        """获取 tenant_access_token"""
        if self.tenant_token and time.time() < self.token_expire_time - 300:
            return self.tenant_token
        
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        
        if data.get("code") != 0:
            raise Exception(f"获取 token 失败：{data.get('msg')}")
        
        self.tenant_token = data["tenant_access_token"]
        self.token_expire_time = int(time.time()) + 7200
        return self.tenant_token
    
    def export_document(self, document_id: str) -> Optional[Dict[str, str]]:
        """
        导出单个文档为 Markdown

        Returns:
            {'title': 文档标题, 'content': Markdown内容} 或 None
        """
        try:
            print(f"\n[DEBUG] ========== 开始导出文档 ==========")
            print(f"[DEBUG] 文档 ID: {document_id}")
            
            # 获取 token
            token = self.get_tenant_token()
            print(f"[DEBUG] Token 获取成功：{token[:20]}...")
            
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            # 获取文档元数据 - 使用正确的 docx/v1 端点
            url = f"{self.base_url}/docx/v1/documents/{document_id}"
            print(f"[DEBUG] 请求文档元数据：{url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"[DEBUG] 文档元数据响应状态码：{response.status_code}")
            print(f"[DEBUG] 文档元数据响应内容：{response.text[:200]}")
            
            if response.status_code != 200:
                print(f"[ERROR] 文档元数据请求失败：{response.status_code}")
                return None
            
            data = response.json()
            print(f"[DEBUG] 解析后的响应：code={data.get('code')}, msg={data.get('msg')}")
            
            if data.get("code") != 0:
                print(f"[ERROR] API 返回错误：{data.get('code')} - {data.get('msg')}")
                return None
            
            document = data.get("data", {}).get("document", {})
            title = document.get("title", "未命名文档")
            print(f"[DEBUG] 文档标题：{title}")
            
            # 获取文档块 - 使用正确的 docx/v1 端点
            blocks_url = f"{self.base_url}/docx/v1/documents/{document_id}/blocks"
            print(f"[DEBUG] 请求文档块：{blocks_url}")
            
            blocks_response = requests.get(blocks_url, headers=headers, timeout=10, params={"page_size": 500})
            print(f"[DEBUG] 文档块响应状态码：{blocks_response.status_code}")
            print(f"[DEBUG] 文档块响应内容：{blocks_response.text[:200]}")
            
            if blocks_response.status_code != 200:
                print(f"[ERROR] 文档块请求失败：{blocks_response.status_code}")
                return None
            
            blocks_data = blocks_response.json()
            print(f"[DEBUG] 块 API 响应：code={blocks_data.get('code')}, msg={blocks_data.get('msg')}")
            
            if blocks_data.get("code") != 0:
                print(f"[ERROR] 块 API 返回错误：{blocks_data.get('code')} - {blocks_data.get('msg')}")
                return None
            
            blocks = blocks_data.get("data", {}).get("items", [])
            print(f"[DEBUG] 获取到 {len(blocks)} 个文档块")
            
            markdown = self._blocks_to_markdown(blocks, title)
            print(f"[DEBUG] Markdown 生成长度：{len(markdown)}")
            print(f"[DEBUG] ========== 导出完成 ==========\n")

            return {
                'title': title,
                'content': markdown
            }
            
        except Exception as e:
            print(f"[ERROR] 导出文档异常：{str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _blocks_to_markdown(self, blocks: List[Dict], title: str = "") -> str:
        """将飞书文档块转换为 Markdown（递归处理）"""
        lines = []
        
        if title:
            lines.append(f"# {title}")
            lines.append("")
        
        # 创建 block_id 到 block 对象的映射
        block_map = {}
        for block in blocks:
            block_id = block.get("block_id")
            if block_id:
                block_map[block_id] = block
        
        # 找出所有顶级块（不被其他块包含的块）
        all_children_ids = set()
        for block in blocks:
            all_children_ids.update(block.get("children", []))
        
        # 顶级块是不在任何 children 列表中的块
        top_level_blocks = [b for b in blocks if b.get("block_id") not in all_children_ids]
        
        # 如果只有一个顶级块且它只有 children（容器块），直接处理它的所有子块
        if len(top_level_blocks) == 1:
            container = top_level_blocks[0]
            if not container.get("text_run", {}).get("content") and container.get("children"):
                print(f"[DEBUG] 检测到容器块，处理 {len(container['children'])} 个子块")
                top_level_blocks = [block_map.get(cid, {}) for cid in container['children'] if cid in block_map]
        
        print(f"[DEBUG] 实际处理的顶级块数量：{len(top_level_blocks)}")
        
        # 递归处理所有顶级块
        self._process_blocks_recursive(top_level_blocks, lines, 0, block_map)
        
        result = "\n".join(lines)
        print(f"[DEBUG] 生成的 Markdown 长度：{len(result)}")
        
        return result
    
    def _process_blocks_recursive(self, blocks: List[Dict], lines: List[str], depth: int, block_map: Dict[str, Dict]):
        """递归处理文档块"""
        print(f"[DEBUG] _process_blocks_recursive: depth={depth}, blocks={len(blocks)}")
        
        processed_count = 0
        for i, block in enumerate(blocks):
            if not isinstance(block, dict):
                block = block_map.get(block, {})
                if not block:
                    continue
            
            # 获取块类型
            block_type = block.get("block_type", 0)
            
            # 根据块类型获取内容字段
            content_field = self._get_content_field(block_type)
            content_block = block.get(content_field, {})
            
            # 提取文本：block.{field}.elements[].text_run.content
            elements = content_block.get("elements", [])
            content = ""
            if elements:
                content = "".join(
                    elem.get("text_run", {}).get("content", "")
                    for elem in elements
                    if elem.get("text_run")
                )
            content = content.strip()
            
            # 如果没有内容，检查是否有子块
            if not content:
                children_ids = block.get("children", [])
                if children_ids and depth < 10:
                    child_blocks = [block_map.get(cid, {}) for cid in children_ids if cid in block_map]
                    if child_blocks:
                        print(f"[DEBUG] 块 {i} (type={block_type}, field={content_field}) 无内容，递归处理 {len(child_blocks)} 个子块")
                        self._process_blocks_recursive(child_blocks, lines, depth + 1, block_map)
                continue
            
            processed_count += 1
            text_style = elements[0].get("text_run", {}).get("text_element_style", {}) if elements else {}
            
            # 根据块类型添加 Markdown 标记
            if block_type == 1:  # 页面（跳过）
                pass
            elif block_type == 2:  # 文本段落
                lines.append(self._apply_styles(content, text_style))
            elif block_type in [3, 4, 5, 6, 7, 8, 9, 10, 11]:  # H1-H9
                header_mark = "#" * (block_type - 1)
                lines.append(f"{header_mark} {content}")
            elif block_type == 12:  # 无序列表
                lines.append(f"- {content}")
            elif block_type == 13:  # 有序列表
                order = content_block.get("order", 1)
                lines.append(f"{order}. {content}")
            elif block_type == 14:  # 代码块
                lang = content_block.get("language", "")
                lines.append(f"```{lang}")
                lines.append(content)
                lines.append("```")
            elif block_type == 15:  # 引用
                lines.append(f"> {content}")
            elif block_type == 17:  # 待办事项
                todo = content_block.get("todo", {})
                checked = "x" if todo.get("is_done") else " "
                lines.append(f"- [{checked}] {content}")
            elif block_type == 22:  # 分割线
                lines.append("---")
            elif content:
                lines.append(content)
            
            # 处理子块
            children_ids = block.get("children", [])
            if children_ids:
                child_blocks = [block_map.get(cid, {}) for cid in children_ids if cid in block_map]
                self._process_blocks_recursive(child_blocks, lines, depth + 1, block_map)
            
            if block_type not in [12, 13, 17]:
                lines.append("")
        
        print(f"[DEBUG] _process_blocks_recursive 完成：processed={processed_count}")
    
    def _get_content_field(self, block_type: int) -> str:
        """根据块类型获取内容字段名"""
        field_map = {
            1: "page",       # 页面
            2: "text",       # 文本
            3: "heading1",   # H1
            4: "heading2",   # H2
            5: "heading3",   # H3
            6: "heading4",   # H4
            7: "heading5",   # H5
            8: "heading6",   # H6
            9: "heading7",   # H7
            10: "heading8",  # H8
            11: "heading9",  # H9
            12: "bullet",    # 无序列表
            13: "ordered",   # 有序列表
            14: "code",      # 代码块
            15: "quote",     # 引用
            17: "todo",      # 待办
            19: "callout",   # 高亮块
        }
        return field_map.get(block_type, "text")
    
    def _apply_styles(self, text: str, style: Dict) -> str:
        """应用内联样式"""
        if not style:
            return text
        if style.get("bold"):
            text = f"**{text}**"
        if style.get("italic"):
            text = f"*{text}*"
        if style.get("strikethrough"):
            text = f"~~{text}~~"
        if style.get("inline_code"):
            text = f"`{text}`"
        return text
    
    def get_wiki_documents(self, wiki_id: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """获取知识库文档列表"""
        try:
            token = self.get_tenant_token()
            url = f"{self.base_url}/wiki/v1/nodes/search"
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            payload = {"wiki_id": wiki_id, "page_token": "", "page_size": 100}
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            if data.get("code") != 0:
                return []
            
            documents = []
            items = data.get("data", {}).get("items", [])
            
            for item in items:
                if item.get("obj_type") == "docx" and item.get("depth", 1) <= max_depth:
                    documents.append({
                        "id": item.get("obj_token") or item.get("obj_id"),
                        "title": item.get("title", "未命名"),
                        "depth": item.get("depth", 1)
                    })
            
            return documents
            
        except Exception as e:
            print(f"获取知识库文档失败：{str(e)}")
            return []
