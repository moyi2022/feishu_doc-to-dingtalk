"""
格式转换模块
将 Markdown 转换为 HTML（主要用于表格转换）
"""

import markdown
from bs4 import BeautifulSoup
from typing import Optional


class FormatConverter:
    """格式转换器"""
    
    def __init__(self):
        """初始化转换器"""
        self.md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
    
    def markdown_to_html(self, markdown_text: str) -> str:
        """
        将 Markdown 转换为 HTML
        
        Args:
            markdown_text: Markdown 文本
            
        Returns:
            HTML 字符串
        """
        # 使用 markdown 库转换
        html = self.md.convert(markdown_text)
        
        # 使用 BeautifulSoup 进一步优化
        soup = BeautifulSoup(html, 'lxml')
        
        # 可以在这里添加自定义的 HTML 处理逻辑
        # 例如：添加特定的样式类、处理表格等
        
        return str(soup)
    
    def convert_tables(self, markdown_text: str) -> str:
        """
        专门处理表格转换
        
        Args:
            markdown_text: 包含表格的 Markdown
            
        Returns:
            包含 HTML 表格的 Markdown
        """
        # 使用 markdown 的 tables 扩展
        html = self.md.convert(markdown_text)
        return html
    
    def preserve_code_blocks(self, markdown_text: str) -> str:
        """
        确保代码块正确保留
        
        Args:
            markdown_text: 包含代码块的 Markdown
            
        Returns:
            处理后的 Markdown
        """
        # markdown 库的 fenced_code 扩展会自动处理代码块
        return markdown_text
    
    def process_document(self, markdown_text: str, preserve_formatting: bool = True) -> str:
        """
        处理整个文档
        
        Args:
            markdown_text: Markdown 文档
            preserve_formatting: 是否保持原有格式
            
        Returns:
            HTML 文档内容
        """
        if preserve_formatting:
            # 完整转换，保持所有格式
            return self.markdown_to_html(markdown_text)
        else:
            # 简单转换
            return self.md.convert(markdown_text)


# 辅助函数
def markdown_table_to_html(markdown_table: str) -> str:
    """
    将 Markdown 表格转换为 HTML 表格
    
    Args:
        markdown_table: Markdown 表格字符串
        
    Returns:
        HTML 表格字符串
    """
    converter = FormatConverter()
    return converter.convert_tables(markdown_table)
