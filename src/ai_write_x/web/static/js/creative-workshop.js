/**      
 * 创意工坊管理器      
 * 职责:话题输入、内容生成、配置面板管理、日志流式传输      
 */      
const ErrorType = {    
    PROCESS: 'process',  
    SYSTEM: 'system',  
    VALIDATION: 'validation'  
};  
  
class CreativeWorkshopManager {      
  
    constructor() {      
        this.isGenerating = false;      
        this.currentTopic = '';      
        this.generationHistory = [];      
        this.templateCategories = [];    
        this.templates = [];    
        this.logWebSocket = null;  
        this.statusPollInterval = null;  
        this.bottomProgress = new BottomProgressManager();  
        this._hotSearchPlatform = '';  
        this.init();      
    }      
          
    async init() {      
        this.bindEventListeners();      
        this.loadHistory();      
        this.initKeyboardShortcuts();      
        await this.loadTemplateCategories();    
    }      
          
    // ========== 模板数据加载 ==========    
        
    async loadTemplateCategories() {      
        try {      
            const response = await fetch('/api/config/template-categories');      
            if (response.ok) {      
                const result = await response.json();      
                this.templateCategories = result.data || [];      
                this.populateTemplateCategoryOptions();      
            }      
        } catch (error) {      
            console.error('加载模板分类失败:', error);      
        }      
    }      
          
    populateTemplateCategoryOptions() {    
        const select = document.getElementById('workshop-template-category');    
        if (!select || !this.templateCategories) return;    
          
        select.innerHTML = '';    
          
        const defaultOption = document.createElement('option');    
        defaultOption.value = '';    
        defaultOption.textContent = '随机分类';    
        select.appendChild(defaultOption);    
          
        this.templateCategories.forEach(category => {    
            const option = document.createElement('option');    
            option.value = category;    
            option.textContent = category;    
            select.appendChild(option);    
        });    
    }      
          
    async loadTemplatesByCategory(category) {      
        try {      
            if (!category) {      
                return [];      
            }      
                  
            const response = await fetch(`/api/config/templates/${encodeURIComponent(category)}`);      
            if (!response.ok) {      
                throw new Error(`HTTP ${response.status}`);      
            }      
                  
            const result = await response.json();      
            return result.data || [];      
        } catch (error) {      
            console.error('加载模板列表失败:', error);      
            return [];      
        }      
    }      
          
    populateTemplateOptions(templates) {    
        const select = document.getElementById('workshop-template-name');    
        if (!select) return;    
          
        select.innerHTML = '';    
          
        const defaultOption = document.createElement('option');    
        defaultOption.value = '';    
        defaultOption.textContent = '随机模板';    
        select.appendChild(defaultOption);    
          
        templates.forEach(template => {    
            const option = document.createElement('option');    
            option.value = template;    
            option.textContent = template;    
            select.appendChild(option);    
        });    
    }      
        
    // ========== 事件监听器 ==========    
          
    bindEventListeners() {      
        const topicInput = document.getElementById('topic-input');      
        if (topicInput) {      
            topicInput.addEventListener('input', (e) => {      
                this.currentTopic = e.target.value;      
            });      
                
            topicInput.addEventListener('keydown', (e) => {      
                if (e.key === 'Enter' && !e.shiftKey) {      
                    e.preventDefault();      
                    if (!this.isGenerating) {    
                        this.startGeneration();    
                    }    
                }      
            });      
        }      
            
        const generateBtn = document.getElementById('generate-btn');      
        if (generateBtn) {      
            generateBtn.addEventListener('click', () => {    
                if (this.isGenerating) {    
                    this.stopGeneration();    
                } else {    
                    this.startGeneration();    
                }    
            });      
        }  
            
        const categorySelect = document.getElementById('workshop-template-category');      
        if (categorySelect) {      
            categorySelect.addEventListener('change', async (e) => {    
                const category = e.target.value;    
                  
                if (!category) {    
                    this.populateTemplateOptions([]);    
                } else {    
                    const templates = await this.loadTemplatesByCategory(category);    
                    this.populateTemplateOptions(templates);    
                }    
            });      
        }      
            
        document.querySelectorAll('.config-trigger').forEach(trigger => {      
            trigger.addEventListener('click', (e) => {      
                this.toggleReferenceMode(e.currentTarget);      
            });      
        });     
    }     
    
    // ========== 借鉴模式管理 ==========    
    
    async toggleReferenceMode(trigger) {      
        const targetId = trigger.dataset.target;      
        const panel = document.getElementById(`${targetId}-panel`);      
            
        if (!panel) {      
            console.error(`Panel not found: ${targetId}-panel`);      
            return;      
        }      
            
        const isCollapsed = panel.classList.contains('collapsed');      
        const status = trigger.querySelector('.trigger-status');      
            
        if (isCollapsed) {      
            panel.classList.remove('collapsed');      
            trigger.classList.add('active');      
                
            if (status) {      
                status.textContent = '已启用';      
                status.classList.add('enabled');      
            }      
                
            await this.resetReferenceForm();      
            this.setReferenceFormState(false);      
                
            setTimeout(() => {      
                panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });      
            }, 100);      
        } else {      
            panel.classList.add('collapsed');      
            trigger.classList.remove('active');      
                
            if (status) {      
                status.textContent = '未启用';      
                status.classList.remove('enabled');      
            }      
                
            this.setReferenceFormState(true);      
        }      
    }      
    
    async resetReferenceForm() {      
        const categorySelect = document.getElementById('workshop-template-category');      
        if (categorySelect) {      
            categorySelect.value = '';      
        }      
            
        this.populateTemplateOptions([]);      
            
        const urlsTextarea = document.getElementById('reference-urls');      
        if (urlsTextarea) {      
            urlsTextarea.value = '';      
        }      
            
        const ratioSelect = document.getElementById('reference-ratio');      
        if (ratioSelect) {      
            ratioSelect.value = '30';  
        }      
    }    
    
    setReferenceFormState(disabled) {      
        const formElements = [      
            'workshop-template-category',      
            'workshop-template-name',    
            'reference-urls',      
            'reference-ratio'      
        ];      
            
        formElements.forEach(id => {      
            const element = document.getElementById(id);      
            if (element) {      
                element.disabled = disabled;      
            }      
        });      
    }    
    
    getReferenceConfig() {      
        const panel = document.getElementById('reference-mode-panel');      
        const isEnabled = panel && !panel.classList.contains('collapsed');      
            
        if (!isEnabled) {      
            return null;      
        }      
            
        return {      
            template_category: document.getElementById('workshop-template-category')?.value || '',      
            template_name: document.getElementById('workshop-template-name')?.value || '',      
            reference_urls: document.getElementById('reference-urls')?.value || '',      
            reference_ratio: parseInt(document.getElementById('reference-ratio')?.value || '30')      
        };      
    }    
    
    // ========== 内容生成流程 ==========    
    
    async startGeneration() {      
        if (this.isGenerating) return;      
          
        this._hotSearchPlatform = '';   
          
        try {      
            const statusResponse = await fetch('/api/generate/status');      
            if (statusResponse.ok) {      
                const status = await statusResponse.json();      
                if (status.status === 'running') {      
                    window.app?.showNotification('已有任务正在运行,请稍后再试', 'warning');      
                    return;      
                }      
            }      
        } catch (error) {      
            console.error('检查任务状态失败:', error);      
        }      
          
        this.isGenerating = true;      
        this.updateGenerationUI(true);    
          
        // ========== 系统配置校验 ==========      
        try {      
            const configResponse = await fetch('/api/config/validate');      
            if (!configResponse.ok) {      
                const error = await configResponse.json();    
                  
                this.cleanupProgress();  
                this.showConfigErrorDialog(error.detail || '系统配置错误,请检查配置');      
                this.isGenerating = false;      
                this.updateGenerationUI(false);      
                return;      
            }  
  
            // 启动进度条    
            if (this.bottomProgress) {    
                this.bottomProgress.start('init');    
            }   
        } catch (error) {      
            console.error('配置验证失败:', error);    
              
            this.cleanupProgress();  
            this.showConfigErrorDialog('无法验证配置,请检查系统设置');      
            this.isGenerating = false;      
            this.updateGenerationUI(false);      
            return;      
        }      
          
        // ========== 获取话题 ==========      
        let topic = this.currentTopic.trim();      
        const referenceConfig = this.getReferenceConfig();      
          
        // 借鉴模式参数校验      
        if (referenceConfig) {      
            if (!topic) {    
                this.cleanupProgress();  
                window.app?.showNotification('借鉴模式下必须输入话题', 'error');      
                this.isGenerating = false;      
                this.updateGenerationUI(false);      
                return;      
            }      
              
            if (referenceConfig.reference_urls) {      
                const urls = referenceConfig.reference_urls.split('|')      
                    .map(u => u.trim())      
                    .filter(u => u);      
                  
                const invalidUrls = urls.filter(url => !this.isValidUrl(url));      
                if (invalidUrls.length > 0) {    
                    this.cleanupProgress();  
                    window.app?.showNotification(      
                        '存在无效的URL,请检查输入(确保使用http://或https://)',      
                        'error'      
                    );      
                    this.isGenerating = false;      
                    this.updateGenerationUI(false);      
                    return;      
                }      
            }      
              
            const category = document.getElementById('workshop-template-category')?.value;      
            const template = document.getElementById('workshop-template-name')?.value;      
              
            if (category && !template) {    
                this.cleanupProgress();  
                window.app?.showNotification('请选择模板', 'warning');      
                this.isGenerating = false;      
                this.updateGenerationUI(false);      
                return;      
            }      
        }      
          
        // 自动获取热搜      
        if (!topic && !referenceConfig) {      
            window.app?.showNotification('正在自动获取热搜...', 'info');      
              
            try {      
                const response = await fetch('/api/hot-topics');      
                if (response.ok) {      
                    const data = await response.json();      
                    topic = data.topic || '';  
                    this._hotSearchPlatform = data.platform || '';      
                      
                    if (!topic) {    
                        this.cleanupProgress();  
                        window.app?.showNotification('获取热搜失败,请手动输入话题', 'warning');      
                        this.isGenerating = false;      
                        this.updateGenerationUI(false);      
                        return;      
                    }      
                      
                    const topicInput = document.getElementById('topic-input');      
                    if (topicInput) {      
                        topicInput.value = topic;      
                        this.currentTopic = topic;      
                    }      
                      
                } else {      
                    throw new Error('获取热搜失败');      
                }      
            } catch (error) {      
                console.error('获取热搜失败:', error);    
                  
                this.cleanupProgress();  
                window.app?.showNotification('获取热搜失败,请手动输入话题', 'error');      
                this.isGenerating = false;      
                this.updateGenerationUI(false);      
                return;      
            }      
        }      

        // ========== 启动生成 ==========      
        this.addToHistory(topic);      
          
        try {      
            const response = await fetch('/api/generate', {      
                method: 'POST',      
                headers: {      
                    'Content-Type': 'application/json',      
                },      
                body: JSON.stringify({      
                    topic: topic,  
                    platform: this._hotSearchPlatform || '',      
                    reference: referenceConfig      
                })      
            });      
              
            if (!response.ok) {      
                const error = await response.json();      
                  
                // 请求失败:清理进度条      
                this.cleanupProgress();  
                  
                if (response.status === 400 && error.detail &&      
                    (error.detail.includes('API KEY') ||      
                    error.detail.includes('Model') ||      
                    error.detail.includes('配置错误'))) {      
                    this.showConfigErrorDialog(error.detail);      
                } else {      
                    window.app?.showNotification('生成失败: ' + (error.detail || '未知错误'), 'error');      
                }      
                  
                this.isGenerating = false;      
                this.updateGenerationUI(false);      
                return;      
            }      
              
            const result = await response.json();      
            window.app?.showNotification(result.message || '内容生成已开始', 'success');      
              
            // 连接 WebSocket 接收实时日志      
            this.connectLogWebSocket();      
              
            // 开始轮询任务状态      
            this.startStatusPolling();      
              
        } catch (error) {      
            console.error('生成失败:', error);      
              
            // 异常:清理进度条      
            this.cleanupProgress();  
              
            window.app?.showNotification('生成失败: ' + error.message, 'error');      
            this.isGenerating = false;      
            this.updateGenerationUI(false);      
        }      
    }  
      
    // 清理进度条的辅助方法  
    cleanupProgress() {  
        if (this.bottomProgress) {  
            this.bottomProgress.stop();  
            const progressEl = document.getElementById('bottom-progress');  
            if (progressEl) {  
                progressEl.classList.add('hidden');  
            }  
            this.bottomProgress.reset();  
        }  
    }  
      
    isValidUrl(url) {    
        try {    
            const urlObj = new URL(url);    
            return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';    
        } catch {    
            return false;    
        }    
    }  
  
    showConfigErrorDialog(errorMessage) {    
        const dialogHtml = `    
            <div class="modal-overlay" id="config-error-dialog">    
                <div class="modal-content" style="max-width: 500px;">    
                    <div class="modal-header">    
                        <h3>配置错误</h3>    
                        <button class="modal-close" onclick="window.creativeWorkshopManager.closeConfigErrorDialog()">×</button>    
                    </div>    
                    <div class="modal-body">    
                        <div class="error-icon" style="text-align: center; margin-bottom: 20px;">    
                            <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="#ef4444" stroke-width="2">    
                                <circle cx="12" cy="12" r="10"/>    
                                <line x1="12" y1="8" x2="12" y2="12"/>    
                                <line x1="12" y1="16" x2="12.01" y2="16"/>    
                            </svg>    
                        </div>    
                        <p style="text-align: center; color: var(--text-secondary); margin-bottom: 20px;">    
                            ${this.escapeHtml(errorMessage)}    
                        </p>    
                    </div>    
                    <div class="modal-footer">    
                        <button class="btn btn-secondary" onclick="window.creativeWorkshopManager.closeConfigErrorDialog()">取消</button>    
                        <button class="btn btn-primary" onclick="window.creativeWorkshopManager.goToConfig('${this.getConfigPanelFromError(errorMessage)}')">前往配置</button>    
                    </div>    
                </div>    
            </div>    
        `;    
          
        document.body.insertAdjacentHTML('beforeend', dialogHtml);    
    }    
      
    getConfigPanelFromError(errorMessage) {    
        if (errorMessage.includes('微信公众号') || errorMessage.includes('appid') || errorMessage.includes('appsecret')) {    
            return 'wechat';  
        } else if (errorMessage.includes('API KEY') || errorMessage.includes('Model') || errorMessage.includes('api_key') || errorMessage.includes('model')) {    
            return 'api';  
        } else if (errorMessage.includes('图片生成')) {    
            return 'img-api';  
        } else {    
            return 'api';  
        }    
    }    
      
    goToConfig(panelId = 'api') {    
        this.closeConfigErrorDialog();    
          
        const configLink = document.querySelector('[data-view="config-manager"]');    
        if (configLink) {    
            configLink.click();    
              
            setTimeout(() => {    
                const targetPanel = document.querySelector(`[data-config="${panelId}"]`);    
                if (targetPanel) {    
                    targetPanel.click();    
                }    
            }, 100);    
        }    
    }  
      
    closeConfigErrorDialog() {    
        const dialog = document.getElementById('config-error-dialog');    
        if (dialog) dialog.remove();    
    }    
      
    escapeHtml(text) {    
        const div = document.createElement('div');    
        div.textContent = text;    
        return div.innerHTML;    
    }  
  
    async stopGeneration() {    
        if (!this.isGenerating) return;    
          
        try {    
            const response = await fetch('/api/generate/stop', {    
                method: 'POST'    
            });    
              
            if (response.ok) {    
                const result = await response.json();    
                  
                this.cleanupProgress();  
                this.disconnectLogWebSocket();    
                this.stopStatusPolling();    
                  
                this._hotSearchPlatform = '';  
                const topicInput = document.getElementById('topic-input');    
                if (topicInput) {    
                    topicInput.value = '';    
                    this.currentTopic = '';    
                }    
                  
                window.app?.showNotification(result.message || '已停止生成', 'info');    
            }    
        } catch (error) {    
            console.error('停止生成失败:', error);    
            window.app?.showNotification('停止失败', 'error');    
        } finally {    
            this.isGenerating = false;    
            this.updateGenerationUI(false);    
        }    
    }    
        
    // ========== WebSocket 日志流式传输 ==========    
        
    connectLogWebSocket() {    
        if (this.logWebSocket) {    
            this.logWebSocket.close();    
        }    
          
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';    
        const wsUrl = `${protocol}//${window.location.host}/api/ws/generate/logs`;    
          
        try {    
            this.logWebSocket = new WebSocket(wsUrl);    
              
            this.logWebSocket.onopen = () => {    
                console.log('日志 WebSocket 已连接');    
            };    
              
            this.logWebSocket.onmessage = (event) => {    
                try {    
                    const data = JSON.parse(event.data);    
                      
                    // 解析阶段和进度    
                    const { stage, progress } = this.parseLogForProgress(data.message);    
                      
                    if (stage && progress !== null) {    
                        if (this.bottomProgress) {    
                            this.bottomProgress.updateProgress(stage, progress);    
                        }    
                    }    
                      
                    // 转发到全局日志面板    
                    this.appendLog(data.message, data.type);    
                      
                    // 检查完成状态    
                    if (data.type === 'completed' || data.type === 'failed') {    
                        this.handleGenerationComplete(data);    
                    }    
                } catch (error) {    
                    console.error('解析日志消息失败:', error);    
                }    
            };    
              
            this.logWebSocket.onerror = (error) => {    
                console.error('WebSocket 错误:', error);    
                if (this.bottomProgress) {    
                    this.bottomProgress.stop();    
                }    
            };    
              
            this.logWebSocket.onclose = () => {    
                console.log('日志 WebSocket 已关闭');    
                if (this.bottomProgress) {    
                    this.bottomProgress.stop();    
                }    
                this.logWebSocket = null;    
            };    
        } catch (error) {    
            console.error('创建 WebSocket 连接失败:', error);    
        }    
    }  
        
    disconnectLogWebSocket() {    
        if (this.logWebSocket) {    
            this.logWebSocket.close();    
            this.logWebSocket = null;    
        }    
    }    
      
    /**    
     * 解析日志获取进度信息 - 基于标准化进度标记  
     */    
    parseLogForProgress(message) {  
        // 1. 初始化 (5%)  
        if (message.includes('[PROGRESS:INIT:START]')) {  
            console.log('[Progress] init, 5%');  
            return { stage: 'init', progress: 5 };  
        }  
        
        // 2. 搜索阶段 (10-20%)  
        if (message.includes('[PROGRESS:SEARCH:START]')) {  
            console.log('[Progress] search, 10%');  
            return { stage: 'search', progress: 10 };  
        }  
        
        // 3. 搜索结束 = 写作开始  
        if (message.includes('[PROGRESS:SEARCH:END]')) {  
            console.log('[Progress] search end → writing start, 20%');  
            return { stage: 'writing', progress: 20 };  // 直接切换到 writing 阶段  
        }  
        
        // 写作阶段结束 (50%)  
        if (message.includes('[PROGRESS:WRITING:END]')) {  
            console.log('[Progress] writing, 50%');  
            return { stage: 'writing', progress: 50 };  
        }  
        
        // 4. 创意化阶段 (55-68%)  
        if (message.includes('[PROGRESS:CREATIVE:START]')) {  
            console.log('[Progress] creative, 55%');  
            return { stage: 'creative', progress: 55 };  
        }  
        
        if (message.includes('[PROGRESS:CREATIVE:END]')) {  
            console.log('[Progress] creative, 68%');  
            return { stage: 'creative', progress: 68 };  
        }   
          
        // 5. 模板化阶段 (70-83%)  
        if (message.includes('[PROGRESS:TEMPLATE:START]')) {  
            console.log('[Progress] template, 70%');  
            return { stage: 'template', progress: 70 };  
        }  
          
        if (message.includes('[PROGRESS:TEMPLATE:END]')) {  
            console.log('[Progress] template, 83%');  
            return { stage: 'template', progress: 83 };  
        }  
          
        // 6. 设计阶段 (70-78%)  
        if (message.includes('[PROGRESS:DESIGN:START]')) {  
            console.log('[Progress] design, 70%');  
            return { stage: 'design', progress: 70 };  
        }  
          
        if (message.includes('[PROGRESS:DESIGN:END]')) {  
            console.log('[Progress] design, 78%');  
            return { stage: 'design', progress: 78 };  
        }  
          
        // 7. 保存阶段 (85-93%)  
        if (message.includes('[PROGRESS:SAVE:START]')) {  
            console.log('[Progress] save, 85%');  
            return { stage: 'save', progress: 85 };  
        }  
          
        if (message.includes('[PROGRESS:SAVE:END]')) {  
            console.log('[Progress] save, 93%');  
            return { stage: 'save', progress: 93 };  
        }  
          
        // 8. 发布阶段 (95-98%)  
        if (message.includes('[PROGRESS:PUBLISH:START]')) {  
            console.log('[Progress] publish, 95%');  
            return { stage: 'publish', progress: 95 };  
        }  
          
        if (message.includes('[PROGRESS:PUBLISH:END]')) {  
            console.log('[Progress] publish, 98%');  
            return { stage: 'publish', progress: 98 };  
        }  
          
        // 9. 完成 (100%)  
        if (message.includes('[INTERNAL]: 任务执行完成')) {  
            console.log('[Progress] complete, 100%');  
            return { stage: 'complete', progress: 100 };  
        }  
          
        return { stage: null, progress: null };  
    }  

    /**    
     * 处理生成完成    
     */    
    handleGenerationComplete(data) {    
          
        this.isGenerating = false;   
  
        if (this.bottomProgress) {    
            this.bottomProgress.stop();    
        }    
          
        if (data.type === 'completed') {    
            if (this.bottomProgress) {    
                this.bottomProgress.updateProgress('complete', 100);    
            }    
              
            setTimeout(() => {    
                const progressEl = document.getElementById('bottom-progress');    
                if (progressEl) {    
                    progressEl.classList.add('hidden');    
                }    
                if (this.bottomProgress) {    
                    this.bottomProgress.reset();    
                }    
            }, 2000);    
              
        } else if (data.type === 'failed') {    
            if (this.bottomProgress) {    
                this.bottomProgress.showError(data.error || '未知错误');    
            }    
              
            setTimeout(() => {    
                const progressEl = document.getElementById('bottom-progress');    
                if (progressEl) {    
                    progressEl.classList.add('hidden');    
                }    
                if (this.bottomProgress) {    
                    this.bottomProgress.reset();    
                }    
            }, 1000);
                } else if (data.type === 'stopped') {  
            // 停止:立即隐藏  
            const progressEl = document.getElementById('bottom-progress');  
            if (progressEl) {  
                progressEl.classList.add('hidden');  
            }  
            if (this.bottomProgress) {  
                this.bottomProgress.reset();  
            }  
        }  
          
        // 更新UI状态  
        this.updateGenerationUI(false);  
        this.stopStatusPolling();  
          
        // 根据状态显示不同的通知  
        if (data.type === 'completed') {  
            window.app?.showNotification('生成完成', 'success');  
            // 刷新文章列表(如果有 ArticleManager)  
            if (window.articleManager && typeof window.articleManager.loadArticles === 'function') {  
                window.articleManager.loadArticles();  
            }  
        } else if (data.type === 'failed') {  
            window.app?.showNotification('生成失败: ' + (data.error || '未知错误'), 'error');  
        } else if (data.type === 'stopped') {  
            window.app?.showNotification('生成已停止', 'info');  
        }  
          
        this._hotSearchPlatform = '';  
  
        // 清空输入框  
        const topicInput = document.getElementById('topic-input');  
        if (topicInput) {  
            topicInput.value = '';  
            this.currentTopic = '';  
        }  
          
        // 关闭 WebSocket  
        if (this.logWebSocket) {  
            this.logWebSocket.close();  
        }  
    }  
  
    appendLog(message, type = 'info') {  
        // 使用全局日志面板 (main.js 中的 addLogEntry)  
        if (window.app && window.app.addLogEntry) {  
            window.app.addLogEntry({  
                type: type,  
                message: message,  
                timestamp: Date.now() / 1000  
            });  
        }  
    }  
      
    // ========== 状态轮询 ==========  
      
    startStatusPolling() {  
        this.stopStatusPolling();  
          
        this.statusPollInterval = setInterval(async () => {  
            if (!this.isGenerating) {  
                this.stopStatusPolling();  
                return;  
            }  
              
            try {  
                const response = await fetch('/api/generate/status');  
                if (response.ok) {  
                    const result = await response.json();  
                      
                    if (result.status === 'completed' || result.status === 'failed' || result.status === 'stopped') {  
                        this.stopStatusPolling();  
                          
                        this.handleGenerationComplete({  
                            type: result.status,  
                            error: result.error  
                        });  
                          
                        // 关闭 WebSocket  
                        this.disconnectLogWebSocket();  
                    }  
                }  
            } catch (error) {  
                console.error('轮询状态失败:', error);  
            }  
        }, 2000);  
    }  
      
    stopStatusPolling() {  
        if (this.statusPollInterval) {  
            clearInterval(this.statusPollInterval);  
            this.statusPollInterval = null;  
        }  
    }  
      
    // ========== 按钮状态管理 ==========  
  
    updateGenerationUI(isGenerating) {  
        const generateBtn = document.getElementById('generate-btn');  
        const topicInput = document.getElementById('topic-input');  
          
        if (generateBtn) {  
            const btnText = generateBtn.querySelector('span');  
            if (btnText) {  
                btnText.textContent = isGenerating ? '停止生成' : '开始生成';  
            }  
              
            // 切换按钮样式  
            if (isGenerating) {  
                generateBtn.classList.remove('btn-generate');  
                generateBtn.classList.add('btn-stop');  
            } else {  
                generateBtn.classList.remove('btn-stop');  
                generateBtn.classList.add('btn-generate');  
            }  
              
            // 图标切换逻辑  
            const btnIcon = generateBtn.querySelector('.btn-icon');  
            if (btnIcon) {  
                if (isGenerating) {  
                    // 停止状态:显示方块图标  
                    btnIcon.outerHTML = `  
                        <svg class="btn-icon" viewBox="0 0 24 24">  
                            <rect x="4" y="4" width="16" height="16" rx="2"/>  
                        </svg>  
                    `;  
                } else {  
                    // 开始状态:显示闪电图标  
                    btnIcon.outerHTML = `  
                        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">  
                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>  
                        </svg>  
                    `;  
                }  
            }  
        }  
          
        if (topicInput) {  
            topicInput.disabled = isGenerating;  
            topicInput.style.opacity = isGenerating ? '0.6' : '1';  
            topicInput.style.cursor = isGenerating ? 'not-allowed' : 'text';  
        }  
    }  
      
    loadHistory() {  
        const saved = localStorage.getItem('generation_history');  
        if (saved) {  
            try {  
                this.generationHistory = JSON.parse(saved);  
            } catch (e) {  
                console.error('加载历史记录失败:', e);  
            }  
        }  
    }  
      
    addToHistory(topic) {  
        const entry = {  
            topic: topic,  
            timestamp: new Date().toISOString()  
        };  
          
        this.generationHistory.unshift(entry);  
          
        if (this.generationHistory.length > 50) {  
            this.generationHistory = this.generationHistory.slice(0, 50);  
        }  
          
        localStorage.setItem('generation_history', JSON.stringify(this.generationHistory));  
    }  
      
    initKeyboardShortcuts() {  
        document.addEventListener('keydown', (e) => {  
            // Ctrl/Cmd + Enter: 快速生成  
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {  
                e.preventDefault();  
                if (!this.isGenerating) {  
                    this.startGeneration();  
                }  
            }  
              
            // Ctrl/Cmd + K: 聚焦输入框  
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {  
                e.preventDefault();  
                document.getElementById('topic-input')?.focus();  
            }  
              
            // Esc: 停止生成  
            if (e.key === 'Escape' && this.isGenerating) {  
                this.stopGeneration();  
            }  
        });  
    }  
}