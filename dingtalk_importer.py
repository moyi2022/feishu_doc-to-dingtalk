# -*- coding: utf-8 -*-
"""
钉钉文档导入模块 - 基于官方 SDK
https://open.dingtalk.com/document/development/create-team-space-document

安装依赖:
    pip install alibabacloud-dingtalk alibabacloud-tea-openapi alibabacloud-tea-util
"""

import os
from typing import Optional, Dict, Any

try:
    from alibabacloud_dingtalk.doc_1_0.client import Client as DingtalkDocClient
    from alibabacloud_dingtalk.wiki_2_0.client import Client as DingtalkWikiClient
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_dingtalk.doc_1_0 import models as dingtalkdoc_models
    from alibabacloud_dingtalk.wiki_2_0 import models as dingtalkwiki_models
    from alibabacloud_tea_util import models as util_models
    from alibabacloud_tea_util.client import Client as UtilClient
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("[WARNING] alibabacloud SDK 未安装，请运行: pip install alibabacloud-dingtalk")

import requests
import time


class DingtalkImporter:
    """
    钉钉文档导入器

    使用官方 SDK 创建钉钉知识库文档

    API 文档: https://open.dingtalk.com/document/development/create-team-space-document
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        corp_id: str,
        user_id: str = "",
        parent_node_id: str = "",
        template_id: str = "",
        template_type: str = ""
    ):
        """
        初始化钉钉导入器

        Args:
            client_id: 钉钉应用 Client ID
            client_secret: 钉钉应用 Client Secret
            corp_id: 企业 Corp ID
            user_id: 操作用户 ID (unionId)，创建文档时必填
            parent_node_id: 父节点 ID，可选
            template_id: 模板 ID，可选
            template_type: 模板类型，可选 (team_template / official_template)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.corp_id = corp_id
        self.user_id = user_id
        self.parent_node_id = parent_node_id
        self.template_id = template_id
        self.template_type = template_type

        self.base_url = "https://api.dingtalk.com"
        self.access_token = None
        self.token_expire_time = 0

        # SDK 客户端
        self._client = None

    def _create_client(self) -> Optional[Any]:
        """
        创建 SDK 客户端

        Returns:
            DingtalkDocClient 或 None
        """
        if not SDK_AVAILABLE:
            return None

        if self._client:
            return self._client

        config = open_api_models.Config()
        config.protocol = 'https'
        config.region_id = 'central'
        self._client = DingtalkDocClient(config)
        return self._client

    def get_access_token(self) -> str:
        """
        获取 access_token

        API 文档: https://open.dingtalk.com/document/orgapp/obtain-the-access_token-of-an-internal-app

        Returns:
            access_token 字符串
        """
        # 检查缓存的 token 是否有效
        if self.access_token and time.time() < self.token_expire_time - 300:
            print(f"[DEBUG] 使用缓存的 access_token")
            return self.access_token

        # 方法1: 使用新版 API (v1.0)
        url = f"{self.base_url}/v1.0/oauth2/{self.corp_id}/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {
            "Content-Type": "application/json"
        }

        print(f"[DEBUG] 请求钉钉 access_token: {url}")
        print(f"[DEBUG] 请求体: {payload}")

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            print(f"[DEBUG] access_token 响应状态码: {response.status_code}")
            print(f"[DEBUG] access_token 响应内容: {response.text}")

            if response.status_code == 200:
                data = response.json()
                # 新版 API 返回 accessToken
                if "access_token" in data:
                    self.access_token = data.get("access_token")
                    expire_in = data.get("expires_in", 7200)
                    self.token_expire_time = int(time.time()) + expire_in
                    print(f"[DEBUG] 新版 access_token 获取成功")
                    return self.access_token
                # 新版 API 返回格式
                if "accessToken" in data:
                    self.access_token = data.get("accessToken")
                    expire_in = data.get("expireIn", 7200)
                    self.token_expire_time = int(time.time()) + expire_in
                    print(f"[DEBUG] 新版 access_token 获取成功")
                    return self.access_token

            # 方法2: 尝试旧版 API (oapi)
            print(f"[DEBUG] 尝试旧版 API...")
            url2 = f"https://oapi.dingtalk.com/gettoken?appkey={self.client_id}&appsecret={self.client_secret}"
            response2 = requests.get(url2, timeout=10)
            print(f"[DEBUG] 旧版 API 响应状态码: {response2.status_code}")
            print(f"[DEBUG] 旧版 API 响应内容: {response2.text[:500]}")

            if response2.status_code == 200:
                data2 = response2.json()
                if data2.get("errcode") == 0 and "access_token" in data2:
                    self.access_token = data2.get("access_token")
                    expire_in = data2.get("expires_in", 7200)
                    self.token_expire_time = int(time.time()) + expire_in
                    print(f"[DEBUG] 旧版 access_token 获取成功")
                    return self.access_token

            # 解析错误
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_msg = error_json.get('message', error_detail)
                except:
                    error_msg = error_detail
                raise Exception(f"获取 access_token 失败: HTTP {response.status_code} - {error_msg}")

        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")

    def create_document(
        self,
        workspace_id: str,
        title: str,
        content: str,
        doc_type: str = "DOC"
    ) -> Optional[str]:
        """
        创建钉钉文档并写入内容

        Args:
            workspace_id: 知识库 ID
            title: 文档标题
            content: 文档内容 (Markdown 格式)
            doc_type: 文档类型，默认 "DOC"

        Returns:
            文档 URL，失败返回 None
        """
        try:
            print(f"\n[DEBUG] ========== 开始创建钉钉文档 ==========")
            print(f"[DEBUG] 知识库 ID: {workspace_id}")
            print(f"[DEBUG] 文档标题: {title}")
            print(f"[DEBUG] 文档类型: {doc_type}")
            print(f"[DEBUG] 操作用户: {self.user_id}")

            # 获取 access_token
            token = self.get_access_token()
            if not token:
                print(f"[ERROR] 获取 access_token 失败")
                return None

            # 尝试使用 SDK
            if SDK_AVAILABLE:
                print(f"[DEBUG] 使用 SDK 创建文档...")
                result = self._create_document_with_sdk(workspace_id, title, content, doc_type)
                if result:
                    return result

            # 回退到 HTTP API
            print(f"[DEBUG] 使用 HTTP API 创建文档...")
            return self._create_document_with_http(workspace_id, title, content, doc_type)

        except Exception as e:
            print(f"[ERROR] 创建钉钉文档异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _create_document_with_sdk(
        self,
        workspace_id: str,
        title: str,
        content: str,
        doc_type: str = "DOC"
    ) -> Optional[str]:
        """
        使用官方 SDK 创建文档

        参考: https://open.dingtalk.com/document/development/create-team-space-document
        """
        try:
            client = self._create_client()
            if not client:
                return None

            # Step 1: 创建文档
            print(f"[DEBUG] SDK Step 1: 创建文档...")

            create_headers = dingtalkdoc_models.CreateWorkspaceDocHeaders()
            create_headers.x_acs_dingtalk_access_token = self.access_token

            create_request = dingtalkdoc_models.CreateWorkspaceDocRequest(
                name=title,
                doc_type=doc_type,
                operator_id=self.user_id
            )

            # 可选参数
            if self.parent_node_id:
                create_request.parent_node_id = self.parent_node_id
            if self.template_id:
                create_request.template_id = self.template_id
            if self.template_type:
                create_request.template_type = self.template_type

            # 调用 API
            response = client.create_workspace_doc_with_options(
                workspace_id,
                create_request,
                create_headers,
                util_models.RuntimeOptions()
            )

            if not response or not response.body:
                print(f"[ERROR] SDK 创建文档响应为空")
                return None

            doc_key = response.body.doc_key
            node_id = response.body.node_id

            print(f"[DEBUG] SDK 文档创建成功: docKey={doc_key}, nodeId={node_id}")

            if not doc_key:
                print(f"[ERROR] SDK 创建文档失败: 无 docKey")
                return None

            # Step 2: 写入内容
            print(f"[DEBUG] SDK Step 2: 写入文档内容...")

            update_headers = dingtalkdoc_models.DocUpdateContentHeaders()
            update_headers.x_acs_dingtalk_access_token = self.access_token

            update_request = dingtalkdoc_models.DocUpdateContentRequest(
                content=content,
                operator_id=self.user_id
            )

            client.doc_update_content_with_options(
                doc_key,
                update_request,
                update_headers,
                util_models.RuntimeOptions()
            )

            print(f"[DEBUG] SDK 内容写入成功")

            # 构建文档 URL
            doc_url = f"https://alidocs.dingtalk.com/i/nodes/{node_id}"
            print(f"[DEBUG] 文档 URL: {doc_url}")
            print(f"[DEBUG] ========== 钉钉文档创建完成 ==========\n")

            return doc_url

        except Exception as err:
            if hasattr(err, 'code') and hasattr(err, 'message'):
                print(f"[ERROR] SDK 错误: code={err.code}, message={err.message}")
            else:
                print(f"[ERROR] SDK 异常: {str(err)}")
            return None

    def _create_document_with_http(
        self,
        workspace_id: str,
        title: str,
        content: str,
        doc_type: str = "DOC"
    ) -> Optional[str]:
        """
        使用 HTTP API 创建文档（SDK 不可用时的回退方案）
        """
        # Step 1: 创建文档
        print(f"[DEBUG] HTTP Step 1: 创建文档...")
        doc_info = self._create_workspace_doc_http(workspace_id, title, doc_type)

        if not doc_info:
            print(f"[ERROR] 创建文档失败")
            return None

        doc_key = doc_info.get("docKey")
        node_id = doc_info.get("nodeId")
        print(f"[DEBUG] 文档创建成功: docKey={doc_key}, nodeId={node_id}")

        # Step 2: 写入内容
        print(f"[DEBUG] HTTP Step 2: 写入文档内容...")
        success = self._update_doc_content_http(doc_key, content)

        if not success:
            print(f"[ERROR] 写入内容失败")
            return None

        print(f"[DEBUG] 内容写入成功")

        # 构建文档 URL
        doc_url = f"https://alidocs.dingtalk.com/i/nodes/{node_id}"
        print(f"[DEBUG] 文档 URL: {doc_url}")
        print(f"[DEBUG] ========== 钉钉文档创建完成 ==========\n")

        return doc_url

    def _create_workspace_doc_http(
        self,
        workspace_id: str,
        name: str,
        doc_type: str = "DOC"
    ) -> Optional[Dict[str, Any]]:
        """
        HTTP API: 创建知识库文档

        API: POST /v1.0/doc/workspaces/{workspace_id}/docs
        """
        url = f"{self.base_url}/v1.0/doc/workspaces/{workspace_id}/docs"
        # 构建请求体
        # 注意：钉钉知识库 API 有时对 operatorId 要求严格
        # 先尝试不传 operatorId 创建文档
        payload = {
            "name": name,
            "docType": doc_type
        }

        # 如果有用户 ID，添加到请求体
        if self.user_id:
            payload["operatorId"] = self.user_id
        headers = {
            "Content-Type": "application/json",
            "x-acs-dingtalk-access-token": self.access_token
        }

        # 可选参数
        if self.parent_node_id:
            payload["parentNodeId"] = self.parent_node_id
        if self.template_id:
            payload["templateId"] = self.template_id
        if self.template_type:
            payload["templateType"] = self.template_type

        print(f"[DEBUG] 创建文档请求 URL: {url}")
        print(f"[DEBUG] 创建文档请求体: {payload}")

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"[DEBUG] 创建文档响应状态码: {response.status_code}")
            print(f"[DEBUG] 创建文档响应内容: {response.text[:500]}")

            if response.status_code not in [200, 201]:
                print(f"[ERROR] 创建文档失败: HTTP {response.status_code}")
                return None

            data = response.json()

            # 检查错误
            if "code" in data and data["code"] != "0":
                print(f"[ERROR] API 返回错误: {data.get('code')} - {data.get('message')}")
                return None

            return {
                "docKey": data.get("docKey"),
                "nodeId": data.get("nodeId"),
                "name": data.get("name"),
                "docType": data.get("docType")
            }

        except requests.RequestException as e:
            print(f"[ERROR] 网络请求失败: {str(e)}")
            return None

    def _update_doc_content_http(self, doc_key: str, content: str) -> bool:
        """
        HTTP API: 更新文档内容（覆写全文）

        API: POST /v1.0/doc/suites/documents/{doc_key}/overwriteContent
        参考: alibabacloud-dingtalk SDK doc_update_content_with_options
        """
        url = f"{self.base_url}/v1.0/doc/suites/documents/{doc_key}/overwriteContent"
        headers = {
            "Content-Type": "application/json",
            "x-acs-dingtalk-access-token": self.access_token
        }

        # operatorId 作为查询参数传递
        params = {}
        if self.user_id:
            params["operatorId"] = self.user_id

        # 请求体包含 content (不需要 dataType)
        payload = {
            "content": content
        }

        print(f"[DEBUG] 更新内容请求 URL: {url}")
        print(f"[DEBUG] 查询参数: {params}")
        print(f"[DEBUG] 内容长度: {len(content)} 字符")

        try:
            response = requests.post(url, json=payload, headers=headers, params=params, timeout=30)
            print(f"[DEBUG] 更新内容响应状态码: {response.status_code}")

            if response.status_code not in [200, 204]:
                print(f"[ERROR] 更新内容失败: HTTP {response.status_code}")
                print(f"[DEBUG] 更新内容响应: {response.text[:500]}")
                return False

            print(f"[DEBUG] 更新内容响应: {response.text[:200] if response.text else '(empty)'}")
            return True

        except requests.RequestException as e:
            print(f"[ERROR] 网络请求失败: {str(e)}")
            return False

    def get_workspaces(self) -> list:
        """
        获取钉钉知识库列表

        API: wiki_2_0 ListWorkspaces
        文档: https://open.dingtalk.com/document/orgapp/obtain-the-knowledge-base-list

        Returns:
            知识库列表 [{'id': ..., 'name': ...}, ...]
        """
        try:
            print(f"\n[DEBUG] ========== 获取钉钉知识库列表 ==========")

            # 获取 access_token
            token = self.get_access_token()
            if not token:
                print(f"[ERROR] 获取 access_token 失败")
                return []

            # 优先尝试使用 SDK (wiki_2_0 模块)
            if SDK_AVAILABLE:
                print(f"[DEBUG] 尝试使用 wiki_2_0 SDK...")
                result = self._get_workspaces_with_sdk()
                if result:
                    return result
                print(f"[DEBUG] wiki_2_0 SDK 获取失败，尝试 HTTP API...")

            # 回退到 HTTP API
            url = f"{self.base_url}/v1.0/doc/workspaces"
            headers = {
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": token
            }
            params = {
                "operatorId": self.user_id or "system",
                "pageSize": 100
            }

            print(f"[DEBUG] 请求 URL: {url}")
            print(f"[DEBUG] 查询参数: {params}")

            response = requests.get(url, headers=headers, params=params, timeout=30)
            print(f"[DEBUG] 响应状态码: {response.status_code}")
            print(f"[DEBUG] 响应内容: {response.text[:500]}")

            if response.status_code != 200:
                print(f"[ERROR] 获取知识库列表失败: HTTP {response.status_code}")
                return []

            data = response.json()

            # 解析知识库列表
            workspaces = []
            items = data.get("workspaces", []) or data.get("items", [])

            for item in items:
                workspaces.append({
                    "id": item.get("id") or item.get("workspaceId"),
                    "name": item.get("name") or item.get("workspaceName"),
                    "description": item.get("description", ""),
                    "createTime": item.get("createTime", "")
                })

            print(f"[DEBUG] 获取到 {len(workspaces)} 个知识库")
            print(f"[DEBUG] ========== 知识库列表获取完成 ==========\n")

            return workspaces

        except Exception as e:
            print(f"[ERROR] 获取知识库列表异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def _get_workspaces_with_sdk(self) -> list:
        """
        使用 wiki_2_0 SDK 获取知识库列表

        参考: https://open.dingtalk.com/document/orgapp/obtain-the-knowledge-base-list
        """
        try:
            config = open_api_models.Config()
            config.protocol = 'https'
            config.region_id = 'central'
            client = DingtalkWikiClient(config)

            headers = dingtalkwiki_models.ListWorkspacesHeaders()
            headers.x_acs_dingtalk_access_token = self.access_token

            request = dingtalkwiki_models.ListWorkspacesRequest(
                max_results=100,
                with_permission_role=False,
                operator_id=self.user_id or 'system'
            )

            print(f"[DEBUG] SDK 请求参数: max_results=100, operator_id={self.user_id}")

            response = client.list_workspaces_with_options(
                request,
                headers,
                util_models.RuntimeOptions()
            )

            if not response or not response.body:
                print(f"[DEBUG] SDK 响应为空")
                return []

            print(f"[DEBUG] SDK 响应成功")

            # 解析响应
            workspaces = []
            items = response.body.workspaces or []

            for item in items:
                workspaces.append({
                    "id": item.workspace_id,
                    "name": item.name,
                    "description": getattr(item, 'description', '') or '',
                    "createTime": getattr(item, 'create_time', '') or ''
                })

            print(f"[DEBUG] SDK 获取到 {len(workspaces)} 个知识库")
            return workspaces

        except Exception as err:
            if hasattr(err, 'code') and hasattr(err, 'message'):
                print(f"[DEBUG] SDK 错误: code={err.code}, message={err.message}")
            else:
                print(f"[DEBUG] SDK 异常: {str(err)}")
            return []

    def create_folder(self, workspace_id: str, folder_name: str) -> Optional[str]:
        """
        创建文件夹

        Args:
            workspace_id: 知识库 ID
            folder_name: 文件夹名称

        Returns:
            文件夹 nodeId，失败返回 None
        """
        result = self._create_workspace_doc_http(workspace_id, folder_name, "FOLDER")
        if result:
            return result.get("nodeId")
        return None


# ============ 测试代码 ============

if __name__ == '__main__':
    print("=" * 60)
    print("钉钉文档导入器 - 测试")
    print("=" * 60)
    print()

    # 测试初始化
    print("1. 测试初始化...")
    importer = DingtalkImporter(
        client_id="test_client_id",
        client_secret="test_client_secret",
        corp_id="test_corp_id",
        user_id="test_user_id"
    )

    if importer.client_id == "test_client_id":
        print("   [OK] 初始化成功")
    else:
        print("   [FAIL] 初始化失败")

    print()
    print("2. SDK 状态...")
    if SDK_AVAILABLE:
        print("   [OK] alibabacloud SDK 已安装")
    else:
        print("   [WARNING] alibabacloud SDK 未安装")
        print("   请运行: pip install alibabacloud-dingtalk alibabacloud-tea-openapi alibabacloud-tea-util")

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)