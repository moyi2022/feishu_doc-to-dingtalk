// API 基础 URL
const API_BASE = '';

// 全局状态
let feishuConfigured = false;
let dingtalkConfigured = false;

window.addEventListener('DOMContentLoaded', async () => {
    loadSavedConfig();
    try {
        const response = await fetch(`${API_BASE}/api/health`);
        const data = await response.json();
        console.log('工具状态:', data.message);
    } catch (error) {
        console.error('无法连接到后端服务:', error);
    }
});

function loadSavedConfig() {
    const savedFeishu = localStorage.getItem('feishu_config');
    const savedDingtalk = localStorage.getItem('dingtalk_config');
    const savedUserId = localStorage.getItem('dingtalk_user_id');

    if (savedFeishu) {
        const config = JSON.parse(savedFeishu);
        document.getElementById('feishu-app-id').value = config.app_id || '';
        document.getElementById('feishu-app-secret').value = config.app_secret || '';
        if (config.configured) {
            feishuConfigured = true;
            updateConfigStatus('feishu', true);
        }
    }

    if (savedDingtalk) {
        const config = JSON.parse(savedDingtalk);
        document.getElementById('dingtalk-client-id').value = config.client_id || '';
        document.getElementById('dingtalk-client-secret').value = config.client_secret || '';
        document.getElementById('dingtalk-corp-id').value = config.corp_id || '';
        if (config.configured) {
            dingtalkConfigured = true;
            updateConfigStatus('dingtalk', true);
            // 自动加载知识库列表
            loadDingtalkWorkspaces('dingtalk-workspace-id-single');
            loadDingtalkWorkspaces('dingtalk-workspace-id-batch');
        }
    }

    if (savedUserId) {
        document.getElementById('dingtalk-user-id').value = savedUserId;
    }
}

function saveConfig(type, config) {
    if (type === 'feishu') {
        localStorage.setItem('feishu_config', JSON.stringify({
            app_id: config.app_id,
            app_secret: config.app_secret,
            configured: true
        }));
    } else if (type === 'dingtalk') {
        localStorage.setItem('dingtalk_config', JSON.stringify({
            client_id: config.client_id,
            client_secret: config.client_secret,
            corp_id: config.corp_id,
            configured: true
        }));
    } else if (type === 'userId') {
        localStorage.setItem('dingtalk_user_id', config.user_id);
    }
}

function updateConfigStatus(type, configured) {
    const funcName = 'test' + type.charAt(0).toUpperCase() + type.slice(1) + 'Auth';
    const btn = document.querySelector('button[onclick*="' + funcName + '"]');
    if (btn) {
        if (configured) {
            btn.textContent = '✅ 已配置';
            btn.className = 'btn btn-success';
        } else {
            btn.textContent = '保存配置';
            btn.className = 'btn btn-primary';
        }
    }
}

function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(tabName + '-tab').classList.add('active');
    event.target.classList.add('active');
}

function testFeishuAuth() {
    const appId = document.getElementById('feishu-app-id').value;
    const appSecret = document.getElementById('feishu-app-secret').value;
    
    if (!appId || !appSecret) {
        alert('请输入完整的飞书凭证');
        return;
    }
    
    fetch(API_BASE + '/api/auth/feishu', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_id: appId, app_secret: appSecret })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            feishuConfigured = true;
            updateConfigStatus('feishu', true);
            saveConfig('feishu', { app_id: appId, app_secret: appSecret });
            alert('✅ 飞书配置已保存！');
        } else {
            alert('❌ 飞书配置失败：' + data.error);
        }
    })
    .catch(error => {
        alert('❌ 连接失败：' + error.message);
    });
}

function testDingtalkAuth() {
    const clientId = document.getElementById('dingtalk-client-id').value;
    const clientSecret = document.getElementById('dingtalk-client-secret').value;
    const corpId = document.getElementById('dingtalk-corp-id').value;
    const userId = document.getElementById('dingtalk-user-id').value;

    if (!clientId || !clientSecret || !corpId) {
        alert('请输入完整的钉钉凭证');
        return;
    }

    if (!userId) {
        alert('请输入钉钉用户 ID');
        return;
    }

    fetch(API_BASE + '/api/auth/dingtalk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            client_id: clientId,
            client_secret: clientSecret,
            corp_id: corpId,
            user_id: userId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            dingtalkConfigured = true;
            updateConfigStatus('dingtalk', true);
            saveConfig('dingtalk', { client_id: clientId, client_secret: clientSecret, corp_id: corpId });
            saveConfig('userId', { user_id: userId });
            alert('✅ 钉钉配置已保存！');

            // 自动加载知识库列表
            loadDingtalkWorkspaces('dingtalk-workspace-id-single');
            loadDingtalkWorkspaces('dingtalk-workspace-id-batch');
        } else {
            alert('❌ 钉钉配置失败：' + data.error);
        }
    })
    .catch(error => {
        alert('❌ 连接失败：' + error.message);
    });
}

function migrateSingle() {
    const feishuUrl = document.getElementById('feishu-doc-url').value;
    const workspaceId = getWorkspaceId('single');
    
    // 获取高级选项
    const parentNodeId = document.getElementById('dingtalk-parent-node-id').value || '';
    const templateId = document.getElementById('dingtalk-template-id').value || '';
    const templateType = document.getElementById('dingtalk-template-type').value || '';
    
    if (!feishuUrl) {
        alert('请输入飞书文档 URL');
        return;
    }
    
    if (!workspaceId) {
        alert('请输入钉钉知识库 ID（必填）');
        return;
    }
    
    const savedFeishu = localStorage.getItem('feishu_config');
    const savedDingtalk = localStorage.getItem('dingtalk_config');
    const savedUserId = localStorage.getItem('dingtalk_user_id');
    
    if (!savedFeishu || !savedDingtalk || !savedUserId) {
        alert('请先配置并保存 API 凭证和用户 ID');
        return;
    }
    
    const feishuConfig = JSON.parse(savedFeishu);
    const dingtalkConfig = JSON.parse(savedDingtalk);
    
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    
    updateProgress(0, 1, 0, 0, '正在迁移单个文档...');
    
    console.log('迁移请求数据:', {
        feishu_url: feishuUrl,
        workspace_id: workspaceId,
        parent_node_id: parentNodeId,
        template_id: templateId,
        template_type: templateType,
        feishu_app_id: feishuConfig.app_id,
        dingtalk_client_id: dingtalkConfig.client_id,
        dingtalk_corp_id: dingtalkConfig.corp_id,
        dingtalk_user_id: savedUserId
    });
    
    const requestData = {
        feishu_url: feishuUrl,
        workspace_id: workspaceId,
        parent_node_id: parentNodeId,
        template_id: templateId,
        template_type: templateType,
        feishu_app_id: feishuConfig.app_id,
        feishu_app_secret: feishuConfig.app_secret,
        dingtalk_client_id: dingtalkConfig.client_id,
        dingtalk_client_secret: dingtalkConfig.client_secret,
        dingtalk_corp_id: dingtalkConfig.corp_id,
        dingtalk_user_id: savedUserId
    };
    
    fetch(API_BASE + '/api/migrate/single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        updateProgress(100, 1, data.success ? 1 : 0, data.success ? 0 : 1, 
            data.success ? '迁移完成！' : '迁移失败');
        showResults([{
            success: data.success,
            title: '文档迁移',
            url: data.dingtalk_url,
            error: data.error
        }]);
    })
    .catch(error => {
        updateProgress(100, 1, 0, 1, '迁移失败');
        showResults([{
            success: false,
            title: '文档迁移',
            error: error.message
        }]);
    });
}

function migrateBatch() {
    const wikiId = document.getElementById('feishu-wiki-id').value;
    const workspaceId = getWorkspaceId('batch');
    const maxDepth = document.getElementById('max-depth').value;
    
    if (!wikiId) {
        alert('请输入飞书知识库 ID');
        return;
    }
    if (!workspaceId) {
        alert('请输入钉钉知识库 ID');
        return;
    }
    
    const savedFeishu = localStorage.getItem('feishu_config');
    const savedDingtalk = localStorage.getItem('dingtalk_config');
    const savedUserId = localStorage.getItem('dingtalk_user_id');
    
    if (!savedFeishu || !savedDingtalk || !savedUserId) {
        alert('请先配置并保存 API 凭证和用户 ID');
        return;
    }
    
    const feishuConfig = JSON.parse(savedFeishu);
    const dingtalkConfig = JSON.parse(savedDingtalk);
    
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('results-section').style.display = 'none';
    
    updateProgress(0, 100, 0, 0, '正在获取文档列表...');
    
    console.log('批量迁移请求数据:', {
        wiki_id: wikiId,
        workspace_id: workspaceId,
        feishu_app_id: feishuConfig.app_id,
        dingtalk_client_id: dingtalkConfig.client_id,
        dingtalk_corp_id: dingtalkConfig.corp_id,
        dingtalk_user_id: savedUserId
    });
    const requestData = {
        wiki_id: wikiId,
        workspace_id: workspaceId,
        max_depth: parseInt(maxDepth),
        feishu_app_id: feishuConfig.app_id,
        feishu_app_secret: feishuConfig.app_secret,
        dingtalk_client_id: dingtalkConfig.client_id,
        dingtalk_client_secret: dingtalkConfig.client_secret,
        dingtalk_corp_id: dingtalkConfig.corp_id,
        dingtalk_user_id: savedUserId
    };
    
    fetch(API_BASE + '/api/migrate/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        updateProgress(100, data.total || 0, data.success_count || 0, data.failed_count || 0, 
            '批量迁移完成！');
        showResults([{ success: true, title: '批量迁移完成', url: '#', error: null }]);
    })
    .catch(error => {
        updateProgress(100, 100, 0, 100, '迁移失败');
        showResults([{ success: false, title: '批量迁移', error: error.message }]);
    });
}

function updateProgress(percent, total, success, failed, text) {
    document.getElementById('progress-fill').style.width = percent + '%';
    document.getElementById('progress-percent').textContent = percent + '%';
    document.getElementById('progress-text').textContent = text;
    document.getElementById('success-count').textContent = success;
    document.getElementById('failed-count').textContent = failed;
    document.getElementById('total-count').textContent = total;
}

function showResults(results) {
    const resultsSection = document.getElementById('results-section');
    const resultsContent = document.getElementById('results-content');

    resultsSection.style.display = 'block';

    let html = '';
    results.forEach(result => {
        if (result.success) {
            html += '<div class="result-item success"><span class="result-icon">✅</span><div class="result-info"><div class="result-title">' + result.title + '</div><a href="' + (result.url || '#') + '" target="_blank" class="result-link">查看文档 →</a></div></div>';
        } else {
            html += '<div class="result-item failed"><span class="result-icon">❌</span><div class="result-info"><div class="result-title">' + result.title + '</div><div class="result-error" style="color: #f56565;">' + (result.error || '未知错误') + '</div></div></div>';
        }
    });

    resultsContent.innerHTML = html;
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// ========== unionId 获取工具 ==========

function toggleUnionIdTool() {
    const content = document.getElementById('unionid-tool-content');
    const icon = document.getElementById('unionid-toggle-icon');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.textContent = '▲';
    } else {
        content.style.display = 'none';
        icon.textContent = '▼';
    }
}

async function getUnionId() {
    const resultBox = document.getElementById('unionid-result');
    resultBox.style.display = 'block';
    resultBox.className = 'result-box';
    resultBox.textContent = '正在查询...';

    // 获取钉钉凭证
    const corpId = document.getElementById('dingtalk-corp-id').value;
    const clientId = document.getElementById('dingtalk-client-id').value;
    const clientSecret = document.getElementById('dingtalk-client-secret').value;
    const searchType = document.getElementById('unionid-search-type').value;
    const searchValue = document.getElementById('unionid-search-value').value;

    // 验证必填项
    if (!corpId || !clientId || !clientSecret) {
        resultBox.className = 'result-box error';
        resultBox.textContent = '错误：请先填写钉钉凭证（Corp ID、Client ID、Client Secret）';
        return;
    }

    if (!searchValue) {
        resultBox.className = 'result-box error';
        resultBox.textContent = '错误：请输入查询值';
        return;
    }

    try {
        const response = await fetch(API_BASE + '/api/dingtalk/get-unionid', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                corp_id: corpId,
                client_id: clientId,
                client_secret: clientSecret,
                search_type: searchType,
                search_value: searchValue
            })
        });

        const data = await response.json();

        if (data.success) {
            const userInfo = data.data;
            resultBox.className = 'result-box success';

            // 使用 DOM 方法安全创建内容
            resultBox.innerHTML = '';

            const infoDiv = document.createElement('div');
            infoDiv.style.marginBottom = '10px';

            const fields = [
                { label: '用户名', value: userInfo.name || '-' },
                { label: '手机号', value: userInfo.mobile || '-' },
                { label: 'userId', value: userInfo.userid || '-' },
                { label: 'unionId', value: userInfo.unionid || '-' }
            ];

            fields.forEach(field => {
                const p = document.createElement('p');
                p.style.margin = '5px 0';
                const strong = document.createElement('strong');
                strong.textContent = field.label + ': ';
                p.appendChild(strong);
                p.appendChild(document.createTextNode(field.value));
                infoDiv.appendChild(p);
            });

            resultBox.appendChild(infoDiv);

            // 添加复制按钮
            if (userInfo.unionid) {
                const copyBtn = document.createElement('button');
                copyBtn.className = 'btn btn-secondary copy-btn';
                copyBtn.textContent = '复制 unionId';
                copyBtn.onclick = function() {
                    copyUnionId(userInfo.unionid);
                };
                resultBox.appendChild(copyBtn);

                // 自动填充到输入框
                document.getElementById('dingtalk-user-id').value = userInfo.unionid;
                localStorage.setItem('dingtalk_user_id', userInfo.unionid);
            }
        } else {
            resultBox.className = 'result-box error';
            resultBox.textContent = '错误：' + (data.error || '查询失败');
        }
    } catch (error) {
        resultBox.className = 'result-box error';
        resultBox.textContent = '请求失败：' + error.message;
    }
}

function copyUnionId(unionId) {
    navigator.clipboard.writeText(unionId).then(function() {
        alert('unionId 已复制到剪贴板！');
    }).catch(function(err) {
        // 降级方案：创建临时输入框
        const input = document.createElement('input');
        input.value = unionId;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        alert('unionId 已复制到剪贴板！');
    });
}

// ========== 钉钉知识库列表 ==========

function toggleWorkspaceInputMode(mode) {
    /**
     * 切换知识库输入模式（下拉选择 / 手动输入）
     * @param {string} mode - 'single' 或 'batch'
     */
    const selectWrapper = document.getElementById(`workspace-select-wrapper-${mode}`);
    const inputWrapper = document.getElementById(`workspace-input-wrapper-${mode}`);
    const selectedRadio = document.querySelector(`input[name="workspace-input-mode-${mode}"]:checked`);

    if (selectedRadio.value === 'select') {
        selectWrapper.style.display = 'flex';
        inputWrapper.style.display = 'none';
    } else {
        selectWrapper.style.display = 'none';
        inputWrapper.style.display = 'block';
    }
}

function getWorkspaceId(mode) {
    /**
     * 获取知识库 ID（根据当前选择的输入模式）
     * @param {string} mode - 'single' 或 'batch'
     * @returns {string} 知识库 ID
     */
    const selectedRadio = document.querySelector(`input[name="workspace-input-mode-${mode}"]:checked`);

    if (selectedRadio.value === 'select') {
        return document.getElementById(`dingtalk-workspace-id-${mode}`).value;
    } else {
        return document.getElementById(`dingtalk-workspace-id-${mode}-manual`).value;
    }
}

async function loadDingtalkWorkspaces(targetSelectId) {
    /**
     * 加载钉钉知识库列表到指定的下拉框
     * @param {string} targetSelectId - 目标 select 元素的 ID
     */
    const selectElement = document.getElementById(targetSelectId);
    if (!selectElement) {
        console.error('找不到目标 select 元素:', targetSelectId);
        return;
    }

    // 显示加载状态
    selectElement.innerHTML = '<option value="">加载中...</option>';
    selectElement.disabled = true;

    // 获取钉钉凭证
    const savedDingtalk = localStorage.getItem('dingtalk_config');
    const savedUserId = localStorage.getItem('dingtalk_user_id');

    if (!savedDingtalk) {
        selectElement.innerHTML = '<option value="">请先配置钉钉凭证</option>';
        selectElement.disabled = false;
        return;
    }

    const dingtalkConfig = JSON.parse(savedDingtalk);

    try {
        const response = await fetch(API_BASE + '/api/dingtalk/workspaces', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                client_id: dingtalkConfig.client_id,
                client_secret: dingtalkConfig.client_secret,
                corp_id: dingtalkConfig.corp_id,
                user_id: savedUserId || 'system'
            })
        });

        const data = await response.json();

        if (data.success && data.workspaces && data.workspaces.length > 0) {
            let optionsHtml = '<option value="">-- 请选择知识库 --</option>';
            data.workspaces.forEach(workspace => {
                optionsHtml += `<option value="${workspace.id}">${workspace.name}</option>`;
            });
            selectElement.innerHTML = optionsHtml;
            selectElement.disabled = false;
        } else {
            // 显示错误信息，提示用户切换到手动输入
            const errorMsg = data.error || '暂无知识库';
            selectElement.innerHTML = `<option value="">${errorMsg}（请切换到手动输入）</option>`;
            selectElement.disabled = false;
        }
    } catch (error) {
        selectElement.innerHTML = '<option value="">加载失败，请切换到手动输入</option>';
        selectElement.disabled = false;
    }
}

// 刷新知识库列表按钮
function refreshWorkspaces(targetSelectId) {
    loadDingtalkWorkspaces(targetSelectId);
}
