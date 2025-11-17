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
          
        // 【新增】消息队列相关  
        this.messageQueue = [];  // 消息队列  
        this.isProcessingQueue = false;  // 是否正在处理队列  
          
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
        
        // 【新增】借鉴模式按钮事件  
        const referenceModeBtn = document.getElementById('reference-mode-btn');  
        if (referenceModeBtn) {  
            referenceModeBtn.addEventListener('click', () => {  
                this.toggleReferenceMode();  
            });  
        }  
        
        // 【新增】日志按钮事件 - 切换进度条显示  
        const logProgressBtn = document.getElementById('log-progress-btn');  
        if (logProgressBtn) {  
            logProgressBtn.addEventListener('click', () => {  
                const progressEl = document.getElementById('bottom-progress');  
                if (progressEl) {  
                    progressEl.classList.toggle('hidden');  
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
    }   
      
    // ========== 借鉴模式管理 ==========      
      
    toggleReferenceMode() {  
        const panel = document.getElementById('reference-mode-panel');  
        const referenceModeBtn = document.getElementById('reference-mode-btn');  
        
        if (!panel || !referenceModeBtn) return;  
        
        if (panel.classList.contains('collapsed')) {  
            // 展开面板  
            panel.classList.remove('collapsed');  
            referenceModeBtn.classList.add('active');  
            this.resetReferenceForm();  
            this.setReferenceFormState(false);  
            
            // 滚动到视图  
            setTimeout(() => {  
                panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });  
            }, 100);  
        } else {  
            // 收起面板  
            panel.classList.add('collapsed');  
            referenceModeBtn.classList.remove('active');  
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
          
        // 【关键】清空消息队列,开始新的任务  
        this.messageQueue = [];  
        this.isProcessingQueue = false;  
            
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
                const progressEl = document.getElementById('bottom-progress');  
                if (progressEl) {  
                    progressEl.classList.remove('hidden');  // 显式移除hidden类  
                }  
            } 
            
            // 【新增】初始化日志按钮显示  
            this.updateLogButtonProgress('init', 0);  
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
          
        // 【新增】清空消息队列,准备新任务  
        this.clearMessageQueue();  
            
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
                    
                // 请求失败:清理进度条和队列  
                this.cleanupProgress();  
                this.clearMessageQueue();  // 清空队列  
                    
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
                
            // 异常:清理进度条和队列  
            this.cleanupProgress();  
            this.clearMessageQueue();  // 清空队列  
                
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
                
                // 等待队列处理完毕  
                while (this.isProcessingQueue) {  
                    await new Promise(resolve => setTimeout(resolve, 100));  
                }  
                
                // 清空队列  
                this.clearMessageQueue();  
                
                // 清理进度条  
                this.cleanupProgress();  
                
                // 【新增】重置日志按钮  
                this.resetLogButton();  
                
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
      
    resetLogButton() {  
        const progressText = document.getElementById('progress-text');  
        const btnIcon = document.querySelector('#log-progress-btn .btn-icon');  
        
        if (progressText) {  
            progressText.textContent = '日志';  
        }  
        
        if (btnIcon) {  
            // 恢复默认图标  
            btnIcon.innerHTML = '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>';  
            btnIcon.classList.remove('rotating');  
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
                      
                    if (data.message && data.message.includes('[PROGRESS:')) {  
                        console.log('🔵 [Progress Marker Detected]', data.message);  
                        
                        // 【关键调试点3】提取所有进度标记  
                        const progressMarkers = data.message.match(/\[PROGRESS:[^\]]+\]/g);  
                        if (progressMarkers) {  
                            console.log('📊 [All Progress Markers in this message]', progressMarkers);  
                        }  
                    }  
                    // 将消息加入队列而不是直接处理  
                    this.messageQueue.push(data);  
                      
                    // 如果没有在处理队列,启动处理  
                    if (!this.isProcessingQueue) {  
                        this.processMessageQueue();  
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
            };      
                
            this.logWebSocket.onclose = () => {      
                console.log('日志 WebSocket 已关闭');          
                this.logWebSocket = null;      
            };      
        } catch (error) {      
            console.error('创建 WebSocket 连接失败:', error);      
        }      
    }    
      
    // 处理消息队列  
    async processMessageQueue() {  
        this.isProcessingQueue = true;  
        
        while (this.messageQueue.length > 0) {  
            const data = this.messageQueue.shift();  
            const markers = this.extractProgressMarkers(data.message);  
            
            for (const marker of markers) {  
                const { stage, progress } = this.mapMarkerToProgress(marker);  
                
                if (stage && progress !== null) {  
                    if (this.bottomProgress) {  
                        this.bottomProgress.updateProgress(stage, progress);  
                        
                        this.updateLogButtonProgress(stage, progress);  
                    }  
                    
                    await new Promise(resolve => setTimeout(resolve, 100));  
                }  
            }  
        }  
        
        this.isProcessingQueue = false;  
    }
   
    updateLogButtonProgress(stage, progress) {  
        const progressText = document.getElementById('progress-text');  
        const btnIcon = document.querySelector('#log-progress-btn .btn-icon');  
        
        if (!progressText || !btnIcon || !this.bottomProgress) return;  
        
        const stageConfig = this.bottomProgress.stages[stage];  
        if (!stageConfig) return;  
        
        const currentProgress = Math.round(this.bottomProgress.currentProgress);  
        progressText.textContent = `${stageConfig.name} ${currentProgress}%`;  
        
        // 更新SVG图标并添加旋转动画  
        btnIcon.innerHTML = stageConfig.icon;  
        btnIcon.classList.add('rotating');  
    }

    // 从消息中提取所有进度标记  
    extractProgressMarkers(message) {  
        const markers = [];  
        const progressRegex = /\[PROGRESS:(\w+):(START|END)\]/g;  
        let match;  
          
        while ((match = progressRegex.exec(message)) !== null) {  
            markers.push({  
                stage: match[1],  
                status: match[2]  
            });  
        }  
          
        // 特殊处理完成标记  
        if (message.includes('[INTERNAL]: 任务执行完成')) {  
            markers.push({  
                stage: 'COMPLETE',  
                status: 'END'  
            });  
        }  
          
        return markers;  
    }  
      
    mapMarkerToProgress(marker) {    
        const stageMap = {    
            'INIT': { stage: 'init', start: 0, end: 5 }, 
            'SEARCH': { stage: 'search', start: 5, end: 20 },
            'WRITING': { stage: 'writing', start: 20, end: 35 },  
            'CREATIVE': { stage: 'creative', start: 35, end: 45 },  
            'TEMPLATE': { stage: 'template', start: 45, end: 85 },  
            'DESIGN': { stage: 'design', start: 45, end: 75 },  
            'SAVE': { stage: 'save', start: 85, end: 87 },  
            'PUBLISH': { stage: 'publish', start: 87, end: 98 },  
            'COMPLETE': { stage: 'complete', start: 100, end: 100 }    
        };    
        
        const config = stageMap[marker.stage];    
        if (!config) {    
            return { stage: null, progress: null };    
        }    
        
        const progress = marker.status === 'START' ? config.start : config.end;    
        return { stage: config.stage, progress };    
    }
      
    // 清空消息队列  
    clearMessageQueue() {  
        this.messageQueue = [];  
        this.isProcessingQueue = false;  
        console.log('[Queue] 消息队列已清空');  
    }  
          
    disconnectLogWebSocket() {      
        if (this.logWebSocket) {      
            this.logWebSocket.close();      
            this.logWebSocket = null;      
        }      
    }      
        
    /**      
     * 处理生成完成      
     */      
    async handleGenerationComplete(data) {  
        // 等待队列处理完毕  
        while (this.isProcessingQueue) {  
            await new Promise(resolve => setTimeout(resolve, 100));  
        }  
        
        this.isGenerating = false;  
        
        if (data.type === 'completed') {  
            if (this.bottomProgress) {  
                this.bottomProgress.complete();  
            }  
            
            // 等待进度条动画到达100%后再停止  
            setTimeout(() => {  
                if (this.bottomProgress) {  
                    this.bottomProgress.stop();  
                }  
                
                // 【新增】重置日志按钮  
                this.resetLogButton();  
                
                setTimeout(() => {  
                    const progressEl = document.getElementById('bottom-progress');  
                    if (progressEl) {  
                        progressEl.classList.add('hidden');  
                    }  
                    if (this.bottomProgress) {  
                        this.bottomProgress.reset();  
                    }  
                    
                    this.autoPreviewGeneratedArticle();  
                }, 1000);  
            }, 1000);  
            
        } else if (data.type === 'failed') {  
            if (this.bottomProgress) {  
                this.bottomProgress.showError(data.error || '未知错误');  
            }  
            
            // 【新增】重置日志按钮  
            this.resetLogButton();  
            
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
            const progressEl = document.getElementById('bottom-progress');  
            if (progressEl) {  
                progressEl.classList.add('hidden');  
            }  
            if (this.bottomProgress) {  
                this.bottomProgress.reset();  
            }  
            
            // 【新增】重置日志按钮  
            this.resetLogButton();  
        }  
        
        this.updateGenerationUI(false);  
        this.stopStatusPolling();   
        
        if (data.type === 'completed') {  
            window.app?.showNotification('生成完成', 'success');  
            if (window.articleManager && typeof window.articleManager.loadArticles === 'function') {  
                window.articleManager.loadArticles();  
            }  
        } else if (data.type === 'failed') {  
            window.app?.showNotification('生成失败: ' + (data.error || '未知错误'), 'error');  
        } else if (data.type === 'stopped') {  
            window.app?.showNotification('生成已停止', 'info');  
        }  
        
        this._hotSearchPlatform = '';  
        
        const topicInput = document.getElementById('topic-input');  
        if (topicInput) {  
            topicInput.value = '';  
            this.currentTopic = '';  
        }  
        
        if (this.logWebSocket) {  
            this.logWebSocket.close();  
        }  
    }
  
    /**  
     * 自动预览最新生成的文章  
     */  
    async autoPreviewGeneratedArticle() {  
        try {  
            // 获取最新生成的文章  
            const response = await fetch('/api/articles');  
            if (!response.ok) {  
                console.error('获取文章列表失败');  
                return;  
            }  
            
            const result = await response.json();  
            if (result.status === 'success' && result.data && result.data.length > 0) {  
                // 按创建时间排序,获取最新的文章  
                const articles = result.data.sort((a, b) => {  
                    return new Date(b.create_time) - new Date(a.create_time);  
                });  
                const latestArticle = articles[0];  
                
                // 获取文章内容  
                const contentResponse = await fetch(  
                    `/api/articles/content?path=${encodeURIComponent(latestArticle.path)}`  
                );  
                if (contentResponse.ok) {  
                    const content = await contentResponse.text();  
                    
                    // 根据文件类型处理内容  
                    const ext = latestArticle.path.toLowerCase().split('.').pop();  
                    let htmlContent = content;  
                    
                    if ((ext === 'md' || ext === 'markdown') && window.markdownRenderer) {  
                        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';  
                        htmlContent = window.markdownRenderer.renderWithStyles(content, isDark);  
                    }  
                    
                    // 打开预览面板  
                    if (window.previewPanelManager) {  
                        window.previewPanelManager.show(htmlContent);  
                    }  
                }  
            }  
        } catch (error) {  
            console.error('自动预览失败:', error);  
            // 静默失败,不影响用户体验  
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
      
    escapeHtml(text) {  
        const div = document.createElement('div');  
        div.textContent = text;  
        return div.innerHTML;  
    }  
}