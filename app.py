"""
飞书文档转钉钉文档本地工具
纯 HTML+JS 前端 + Python Flask 后端
"""

from flask import Flask, request, jsonify, send_from_directory
from migration_service import MigrationService

app = Flask(__name__)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大 16MB

# 全局状态（用于存储迁移服务和进度）
# 注意：这是简单的内存存储，生产环境应该使用 session 或数据库
migration_services = {}  # 按用户 session 存储迁移服务
migration_status = {
    'running': False,
    'progress': 0,
    'total': 0,
    'current': 0,
    'success': 0,
    'failed': 0,
    'results': []
}


@app.route('/')
def index():
    """返回主界面"""
    return send_from_directory('.', 'index.html')


@app.route('/app.js')
def app_js():
    """返回前端 JS"""
    return send_from_directory('.', 'app.js')


@app.route('/style.css')
def style_css():
    """返回样式文件"""
    return send_from_directory('.', 'style.css')


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': '飞书→钉钉文档迁移工具运行中'})


@app.route('/api/auth/feishu', methods=['POST'])
def auth_feishu():
    """验证飞书 API 凭证"""
    data = request.get_json() or {}
    app_id = data.get('app_id')
    app_secret = data.get('app_secret')
    
    if not app_id or not app_secret:
        return jsonify({'error': '缺少必要参数', 'success': False}), 400
    
    # 简单验证：尝试获取 token
    try:
        from feishu_exporter import FeishuExporter
        exporter = FeishuExporter(app_id, app_secret)
        # 不实际调用 API，只存储凭证
        # 在实际迁移时会验证 token
        
        # 存储凭证（简化实现，使用全局字典）
        migration_services['feishu_creds'] = {
            'app_id': app_id,
            'app_secret': app_secret
        }
        
        return jsonify({
            'success': True,
            'message': '飞书 API 凭证已保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/auth/dingtalk', methods=['POST'])
def auth_dingtalk():
    """验证钉钉 API 凭证"""
    data = request.get_json() or {}
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    corp_id = data.get('corp_id')
    
    if not all([client_id, client_secret, corp_id]):
        return jsonify({'error': '缺少必要参数', 'success': False}), 400
    
    # 存储凭证
    migration_services['dingtalk_creds'] = {
        'client_id': client_id,
        'client_secret': client_secret,
        'corp_id': corp_id
    }
    
    return jsonify({
        'success': True,
        'message': '钉钉 API 凭证已保存'
    })


@app.route('/api/migrate/single', methods=['POST'])
def migrate_single():
    """迁移单个文档"""
    data = request.get_json() or {}
    feishu_url = data.get('feishu_url', '')
    workspace_id = data.get('workspace_id', '')
    
    # 高级选项（可选）
    parent_node_id = data.get('parent_node_id', '')
    template_id = data.get('template_id', '')
    template_type = data.get('template_type', '')
    
    # 从请求中获取 API 凭据
    app_id = data.get('feishu_app_id')
    app_secret = data.get('feishu_app_secret')
    client_id = data.get('dingtalk_client_id')
    client_secret = data.get('dingtalk_client_secret')
    corp_id = data.get('dingtalk_corp_id')
    user_id = data.get('dingtalk_user_id', 'system')
    
    if not feishu_url:
        return jsonify({'error': '缺少飞书文档 URL', 'success': False}), 400
    
    if not workspace_id:
        return jsonify({'error': '缺少钉钉知识库 ID', 'success': False}), 400
    
    # 验证必需凭据
    missing = []
    if not app_id: missing.append('飞书 App ID')
    if not app_secret: missing.append('飞书 App Secret')
    if not client_id: missing.append('钉钉 Client ID')
    if not client_secret: missing.append('钉钉 Client Secret')
    if not corp_id: missing.append('钉钉 Corp ID')
    
    if missing:
        return jsonify({'error': f'缺少必要凭据：{", ".join(missing)}', 'success': False}), 400
    
    # 确保 user_id 有效
    if not user_id or user_id.strip() == '':
        user_id = 'system'
    
    try:
        # 创建迁移服务实例（安全类型转换）
        service = MigrationService(
            feishu_creds={
                'app_id': str(app_id) if app_id is not None else '',
                'app_secret': str(app_secret) if app_secret is not None else ''
            },
            dingtalk_creds={
                'client_id': str(client_id) if client_id is not None else '',
                'client_secret': str(client_secret) if client_secret is not None else '',
                'corp_id': str(corp_id) if corp_id is not None else '',
                'user_id': str(user_id) if user_id is not None else 'system',
                'parent_node_id': parent_node_id or '',
                'template_id': template_id or '',
                'template_type': template_type or ''
            }
        )
        
        # 执行迁移
        result = service.migrate_single(feishu_url, workspace_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'迁移失败：{str(e)}'
        }), 500



@app.route('/api/migrate/batch', methods=['POST'])
def migrate_batch():
    """批量迁移文档"""
    data = request.get_json() or {}
    wiki_id = data.get('wiki_id', '')
    workspace_id = data.get('workspace_id', '')
    max_depth = data.get('max_depth', 3)
    
    # 从请求中获取凭证
    app_id = data.get('feishu_app_id')
    app_secret = data.get('feishu_app_secret')
    client_id = data.get('dingtalk_client_id')
    client_secret = data.get('dingtalk_client_secret')
    corp_id = data.get('dingtalk_corp_id')
    user_id = data.get('dingtalk_user_id', 'system')
    
    if not wiki_id:
        return jsonify({'error': '缺少知识库 ID', 'success': False}), 400
    
    if not workspace_id:
        return jsonify({'error': '缺少目标知识库 ID', 'success': False}), 400
    
    # 验证所有必要的凭据都存在
    missing = []
    if not app_id: missing.append('飞书 App ID')
    if not app_secret: missing.append('飞书 App Secret')
    if not client_id: missing.append('钉钉 Client ID')
    if not client_secret: missing.append('钉钉 Client Secret')
    if not corp_id: missing.append('钉钉 Corp ID')
    
    if missing:
        return jsonify({'error': f'缺少必要凭据: {", ".join(missing)}', 'success': False}), 400
    
    # 确保 user_id 有值
    if not user_id or user_id.strip() == '':
        user_id = 'system'
    
    try:
        # 创建迁移服务实例（强制转换为字符串）
        service = MigrationService(
            feishu_creds={
                'app_id': str(app_id),
                'app_secret': str(app_secret)
            },
            dingtalk_creds={
                'client_id': str(client_id),
                'client_secret': str(client_secret),
                'corp_id': str(corp_id),
                'user_id': str(user_id)
            }
        )
        
        # 执行批量迁移
        result = service.migrate_batch(wiki_id, workspace_id, max_depth)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'批量迁移失败：{str(e)}'
        }), 500


@app.route('/api/dingtalk/workspaces', methods=['POST'])
def get_dingtalk_workspaces():
    """
    获取钉钉知识库列表

    用于前端下拉选择目标知识库
    """
    data = request.get_json() or {}
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    corp_id = data.get('corp_id')
    user_id = data.get('user_id', 'system')

    if not all([client_id, client_secret, corp_id]):
        return jsonify({
            'success': False,
            'error': '缺少钉钉凭证（client_id, client_secret, corp_id）'
        }), 400

    try:
        from dingtalk_importer import DingtalkImporter
        importer = DingtalkImporter(
            client_id=client_id,
            client_secret=client_secret,
            corp_id=corp_id,
            user_id=user_id or 'system'
        )

        workspaces = importer.get_workspaces()

        return jsonify({
            'success': True,
            'workspaces': workspaces
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取知识库列表失败：{str(e)}'
        }), 500


@app.route('/api/status')
def get_status():
    """获取迁移进度"""
    return jsonify(migration_status)


@app.route('/api/dingtalk/get-unionid', methods=['POST'])
def get_unionid():
    """
    自动获取钉钉用户 unionId

    所需权限（在钉钉开放平台开通）：
    - 通讯录只读权限 (Contact.User.Read)
    - 通过手机号获取用户信息 (qyapi_get_member_by_mobile)
    - 成员信息读权限 (qyapi_get_member)
    """
    import requests as req

    data = request.get_json() or {}
    corp_id = data.get('corp_id')
    client_id = data.get('client_id')
    client_secret = data.get('client_secret')
    search_type = data.get('search_type', 'userid')  # userid 或 mobile
    search_value = data.get('search_value')  # userId 或手机号

    # 验证参数
    if not all([corp_id, client_id, client_secret]):
        return jsonify({
            'success': False,
            'error': '缺少钉钉凭证（corp_id, client_id, client_secret）'
        }), 400

    if not search_value:
        return jsonify({
            'success': False,
            'error': f'缺少查询值（{"userId" if search_type == "userid" else "手机号"}）'
        }), 400

    try:
        # 1. 获取 access_token
        token_url = f'https://api.dingtalk.com/v1.0/oauth2/{corp_id}/token'
        token_resp = req.post(token_url, json={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        })

        if token_resp.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'获取 access_token 失败: {token_resp.text}'
            }), 500

        token = token_resp.json().get('access_token')

        # 2. 根据 search_type 获取 userId
        user_id = None
        if search_type == 'mobile':
            # 通过手机号获取 userId
            userid_url = f'https://oapi.dingtalk.com/topapi/v2/user/getbymobile?access_token={token}'
            userid_resp = req.post(userid_url, json={'mobile': search_value})

            if userid_resp.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': '请求钉钉 API 失败'
                }), 500

            userid_data = userid_resp.json()
            if userid_data.get('errcode') != 0:
                error_msg = userid_data.get('errmsg', '未知错误')
                if userid_data.get('errcode') == 60011:
                    error_msg = '权限不足，请开通"通过手机号获取用户信息"权限'
                return jsonify({
                    'success': False,
                    'error': error_msg,
                    'errcode': userid_data.get('errcode')
                }), 400

            user_id = userid_data.get('result', {}).get('userid')
            if not user_id:
                return jsonify({
                    'success': False,
                    'error': '未找到该手机号对应的用户'
                }), 404
        else:
            user_id = search_value

        # 3. 获取用户详情（包含 unionId）
        user_url = f'https://oapi.dingtalk.com/topapi/v2/user/get?access_token={token}'
        user_resp = req.post(user_url, json={'userid': user_id})

        if user_resp.status_code != 200:
            return jsonify({
                'success': False,
                'error': '请求钉钉 API 失败'
            }), 500

        user_data = user_resp.json()
        if user_data.get('errcode') != 0:
            error_msg = user_data.get('errmsg', '未知错误')
            if user_data.get('errcode') == 60011:
                error_msg = '权限不足，请开通"成员信息读权限"'
            return jsonify({
                'success': False,
                'error': error_msg,
                'errcode': user_data.get('errcode')
            }), 400

        result = user_data.get('result', {})

        return jsonify({
            'success': True,
            'data': {
                'userid': result.get('userid'),
                'unionid': result.get('unionid'),
                'name': result.get('name'),
                'mobile': result.get('mobile')
            }
        })

    except req.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'网络请求失败: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("[START] 飞书-> 钉钉文档迁移工具启动中...")
    print("[INFO] 访问地址：http://localhost:5000")
    print("[INFO] 按 Ctrl+C 停止服务")
    app.run(debug=True, host='0.0.0.0', port=5000)
