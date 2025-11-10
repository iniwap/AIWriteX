/**    
 * 创意工坊管理器    
 * 职责:话题输入、内容生成、配置面板管理、日志流式传输    
 */    
const ErrorType = {  
    PROCESS: 'process',      // 过程提示(使用 showNotification)  
    SYSTEM: 'system',        // 系统级错误(使用模态弹窗)  
    VALIDATION: 'validation' // 参数校验错误(使用 showNotification)  
};

class CreativeWorkshopManager {    

    constructor() {    
        this.isGenerating = false;    
        this.currentTopic = '';    
        this.generationHistory = [];    
        this.templateCategories = [];  
        this.templates = [];  
        this.logWebSocket = null;  // WebSocket 连接  
        this.statusPollInterval = null;  // 状态轮询定时器  
        this.bottomProgress = new BottomProgressManager();
        this.init();    
    }    
        
    async init() {    
        this.bindEventListeners();    
        this.loadHistory();    
        this.initKeyboardShortcuts();    
        await this.loadTemplateCategories();  
    }    
        
    // ========== 模板数据加载 ==========  
      
    // 加载模板分类列表    
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
        
    // 填充模板分类选项    
    populateTemplateCategoryOptions() {  
        const select = document.getElementById('workshop-template-category');  
        if (!select || !this.templateCategories) return;  
        
        // 清空现有选项  
        select.innerHTML = '';  
        
        // 添加"随机分类"选项 
        const defaultOption = document.createElement('option');  
        defaultOption.value = '';  
        defaultOption.textContent = '随机分类';  
        select.appendChild(defaultOption);  
        
        // 添加分类选项  
        this.templateCategories.forEach(category => {  
            const option = document.createElement('option');  
            option.value = category;  
            option.textContent = category;  
            select.appendChild(option);  
        });  
    }    
        
    // 加载指定分类的模板列表    
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
        
    // 填充模板选项    
    populateTemplateOptions(templates) {  
        const select = document.getElementById('workshop-template-name');  
        if (!select) return;  
        
        // 清空现有选项  
        select.innerHTML = '';  
        
        // 添加"随机模板"选项(而不是"选择模板...")  
        const defaultOption = document.createElement('option');  
        defaultOption.value = '';  
        defaultOption.textContent = '随机模板';  
        select.appendChild(defaultOption);  
        
        // 添加模板选项  
        templates.forEach(template => {  
            const option = document.createElement('option');  
            option.value = template;  
            option.textContent = template;  
            select.appendChild(option);  
        });  
    }    
      
    // ========== 事件监听器 ==========  
        
    bindEventListeners() {    
        // 话题输入框    
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
          
        // 生成按钮 - 单按钮切换模式  
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
          
        // 模板分类选择 - 级联加载模板    
        const categorySelect = document.getElementById('workshop-template-category');    
        if (categorySelect) {    
            categorySelect.addEventListener('change', async (e) => {  
                const category = e.target.value;  
                
                if (!category) {  
                    // 选择了"随机分类",只显示"随机模板"  
                    this.populateTemplateOptions([]);  
                } else {  
                    // 选择了具体分类,加载该分类的模板  
                    const templates = await this.loadTemplatesByCategory(category);  
                    this.populateTemplateOptions(templates);  
                }  
            });    
        }    
          
        // 配置触发器 - 借鉴模式展开/收起  
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
            // 启用借鉴模式    
            panel.classList.remove('collapsed');    
            trigger.classList.add('active');    
              
            // 更新状态文本    
            if (status) {    
                status.textContent = '已启用';    
                status.classList.add('enabled');    
            }    
              
            // 重置表单为默认状态    
            await this.resetReferenceForm();    
              
            // 启用所有表单控件    
            this.setReferenceFormState(false);    
              
            // 平滑滚动到面板    
            setTimeout(() => {    
                panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });    
            }, 100);    
        } else {    
            // 禁用借鉴模式    
            panel.classList.add('collapsed');    
            trigger.classList.remove('active');    
              
            // 更新状态文本    
            if (status) {    
                status.textContent = '未启用';    
                status.classList.remove('enabled');    
            }    
              
            // 禁用所有表单控件    
            this.setReferenceFormState(true);    
        }    
    }    
  
    // 重置借鉴模式表单    
    async resetReferenceForm() {    
        // 重置分类选择    
        const categorySelect = document.getElementById('workshop-template-category');    
        if (categorySelect) {    
            categorySelect.value = '';    
        }    
          
        // 清空模板选择    
        this.populateTemplateOptions([]);    
          
        // 重置其他字段    
        const urlsTextarea = document.getElementById('reference-urls');    
        if (urlsTextarea) {    
            urlsTextarea.value = '';    
        }    
          
        const ratioSelect = document.getElementById('reference-ratio');    
        if (ratioSelect) {    
            ratioSelect.value = '30';  // 默认值    
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
  
    // 获取借鉴模式配置    
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
        // 检查后端是否有正在运行的任务    
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
        
        // 立即切换按钮状态和显示进度条  
        this.isGenerating = true;    
        this.updateGenerationUI(true);  
        
        // ========== 第一步: 系统配置校验 ==========    
        try {    
            const configResponse = await fetch('/api/config/validate');    
            if (!configResponse.ok) {    
                const error = await configResponse.json();  
                
                // 校验失败:清理进度条  
                if (this.bottomProgress) {  
                    this.bottomProgress.stop();  
                    const progressEl = document.getElementById('bottom-progress');  
                    if (progressEl) {  
                        progressEl.classList.add('hidden');  
                    }  
                    this.bottomProgress.reset();  
                }  
                
                this.showConfigErrorDialog(error.detail || '系统配置错误,请检查配置');    
                this.isGenerating = false;    
                this.updateGenerationUI(false);    
                return;    
            }
            
            // 获取完整配置以确定激活阶段  
            const fullConfigResponse = await fetch('/api/config/');  
            const configData = await fullConfigResponse.json();  
            const config = configData.data;  
            
            // 构建激活阶段和进度范围  
            const activeStages = this._buildActiveStages(config);  
            const progressRanges = this._calculateProgressRanges(activeStages);  
            
            // 配置进度管理器  
            if (this.bottomProgress) {  
                this.bottomProgress.setActiveStages(activeStages, progressRanges);  
            }  
            
            // 初始化进度状态  
            this._progressState = {  
                currentAgent: null,  
                searchStarted: false,  
                templateToolUsed: false,  
                activeStages: activeStages  
            };  
            
            // 启动进度条  
            if (this.bottomProgress) {  
                this.bottomProgress.start('init');  
            } 
        } catch (error) {    
            console.error('配置验证失败:', error);  
            
            // 异常:清理进度条  
            if (this.bottomProgress) {  
                this.bottomProgress.stop();  
                const progressEl = document.getElementById('bottom-progress');  
                if (progressEl) {  
                    progressEl.classList.add('hidden');  
                }  
                this.bottomProgress.reset();  
            }  
            
            this.showConfigErrorDialog('无法验证配置,请检查系统设置');    
            this.isGenerating = false;    
            this.updateGenerationUI(false);    
            return;    
        }    
        
        // ========== 第二步: 获取话题 ==========    
        let topic = this.currentTopic.trim();    
        const referenceConfig = this.getReferenceConfig();    
        
        // 借鉴模式参数校验    
        if (referenceConfig) {    
            if (!topic) {  
                // 清理进度条  
                if (this.bottomProgress) {  
                    this.bottomProgress.stop();  
                    const progressEl = document.getElementById('bottom-progress');  
                    if (progressEl) {  
                        progressEl.classList.add('hidden');  
                    }  
                    this.bottomProgress.reset();  
                }  
                
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
                    // 清理进度条  
                    if (this.bottomProgress) {  
                        this.bottomProgress.stop();  
                        const progressEl = document.getElementById('bottom-progress');  
                        if (progressEl) {  
                            progressEl.classList.add('hidden');  
                        }  
                        this.bottomProgress.reset();  
                    }  
                    
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
                // 清理进度条  
                if (this.bottomProgress) {  
                    this.bottomProgress.stop();  
                    const progressEl = document.getElementById('bottom-progress');  
                    if (progressEl) {  
                        progressEl.classList.add('hidden');  
                    }  
                    this.bottomProgress.reset();  
                }  
                
                window.app?.showNotification('请选择模板', 'warning');    
                this.isGenerating = false;    
                this.updateGenerationUI(false);    
                return;    
            }    
        }    
        
        // 如果没有输入话题且未启用借鉴模式,自动获取热搜    
        if (!topic && !referenceConfig) {    
            window.app?.showNotification('正在自动获取热搜...', 'info');    
            
            try {    
                const response = await fetch('/api/hot-topics');    
                if (response.ok) {    
                    const data = await response.json();    
                    topic = data.topic || '';
                    this._hotSearchPlatform = data.platform || '';    
                    
                    if (!topic) {  
                        // 清理进度条  
                        if (this.bottomProgress) {  
                            this.bottomProgress.stop();  
                            const progressEl = document.getElementById('bottom-progress');  
                            if (progressEl) {  
                                progressEl.classList.add('hidden');  
                            }  
                            this.bottomProgress.reset();  
                        }  
                        
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
                
                // 清理进度条  
                if (this.bottomProgress) {  
                    this.bottomProgress.stop();  
                    const progressEl = document.getElementById('bottom-progress');  
                    if (progressEl) {  
                        progressEl.classList.add('hidden');  
                    }  
                    this.bottomProgress.reset();  
                }  
                
                window.app?.showNotification('获取热搜失败,请手动输入话题', 'error');    
                this.isGenerating = false;    
                this.updateGenerationUI(false);    
                return;    
            }    
        }    
        
        // ========== 第三步: 启动生成 ==========    
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
                if (this.bottomProgress) {    
                    this.bottomProgress.stop();    
                    const progressEl = document.getElementById('bottom-progress');    
                    if (progressEl) {    
                        progressEl.classList.add('hidden');    
                    }    
                    this.bottomProgress.reset();    
                }    
                
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
            if (this.bottomProgress) {    
                this.bottomProgress.stop();    
                const progressEl = document.getElementById('bottom-progress');    
                if (progressEl) {    
                    progressEl.classList.add('hidden');    
                }    
                this.bottomProgress.reset();    
            }    
            
            window.app?.showNotification('生成失败: ' + error.message, 'error');    
            this.isGenerating = false;    
            this.updateGenerationUI(false);    
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
    
    // 根据错误消息判断应该跳转到哪个配置面板  
    getConfigPanelFromError(errorMessage) {  
        if (errorMessage.includes('微信公众号') || errorMessage.includes('appid') || errorMessage.includes('appsecret')) {  
            return 'wechat';  // 微信公众号配置  
        } else if (errorMessage.includes('API KEY') || errorMessage.includes('Model') || errorMessage.includes('api_key') || errorMessage.includes('model')) {  
            return 'api';  // 大模型API配置  
        } else if (errorMessage.includes('图片生成')) {  
            return 'img-api';  // 图片API配置  
        } else {  
            return 'api';  // 默认跳转到大模型API配置  
        }  
    }  
    
    goToConfig(panelId = 'api') {  
        this.closeConfigErrorDialog();  
        
        // 切换到配置管理视图  
        const configLink = document.querySelector('[data-view="config-manager"]');  
        if (configLink) {  
            configLink.click();  
            
            // 延迟切换到指定的配置面板  
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
                
                // 停止进度管理器  
                if (this.bottomProgress) {  
                    this.bottomProgress.stop();  
                }  
                
                // 隐藏进度区域  
                const progressEl = document.getElementById('bottom-progress');  
                if (progressEl) {  
                    progressEl.classList.add('hidden');  
                }  
                
                // 重置进度管理器  
                if (this.bottomProgress) {  
                    this.bottomProgress.reset();  
                }  
                
                // 关闭 WebSocket 连接  
                this.disconnectLogWebSocket();  
                
                // 停止状态轮询  
                this.stopStatusPolling();  
                
                this._hotSearchPlatform = '';
                // 清空输入框  
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
            // 确保在任何情况下都重置状态  
            this.isGenerating = false;  
            this.updateGenerationUI(false);  
        }  
    }  
      
    // ========== WebSocket 日志流式传输 ==========  
      
    connectLogWebSocket() {  
        // 如果已有连接,先关闭  
        if (this.logWebSocket) {  
            this.logWebSocket.close();  
        }  
        
        // 构建 WebSocket URL  
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
                        // 更新进度管理器  
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
     * 解析日志获取进度信息  
     */  
    parseLogForProgress(message) {  
        if (!this._progressState) {  
            this._progressState = {  
                currentAgent: null,  
                searchStarted: false,  
                searchCompleted: false,  
                writingStarted: false,  
                activeStages: ['init', 'search', 'writing', 'save', 'complete']  
            };  
        }  
        
        const state = this._progressState;  
        const activeStages = state.activeStages || [];  
        
        // 1. 初始化 (5%)  
        if (message.includes('任务参数') || message.includes('API类型')) {  
            return { stage: 'init', progress: 5 };  
        }  
        
        // 2. 搜索阶段 (15-27%)  
        if (message.includes('开始执行搜索') || message.includes('AIForge]🤖 正在连接')) {  
            state.searchStarted = true;  
            return { stage: 'search', progress: 15 };  
        }  
        
        if (state.searchStarted && !state.searchCompleted) {  
            if (message.includes('正在搜索') || message.includes('正在尝试')) {  
                return { stage: 'search', progress: 20 };  
            }  
            
            // 搜索完成的关键标志  
            if (message.includes('## Tool Output:') && message.includes('搜索结果')) {  
                state.searchCompleted = true;  
                return { stage: 'search', progress: 27 };  
            }  
        }  
        
        // 3. 写作阶段 (30-52%)  
        if (state.searchCompleted && !state.writingStarted) {  
            if (message.includes('## Thought:') || message.includes('## Using tool:')) {  
                state.writingStarted = true;  
                return { stage: 'writing', progress: 30 };  
            }  
        }  
        
        if (state.writingStarted) {  
            // 检测文章标题(markdown一级标题)  
            if (message.match(/^# [^#\s]/m) && !message.includes('# Agent:')) {  
                return { stage: 'writing', progress: 42 };  
            }  
            
            // 写作完成标志  
            if (message.includes('## Final Answer:') && state.currentAgent === null) {  
                return { stage: 'writing', progress: 52 };  
            }  
        }  
        
        // 4. 创意阶段 (55-68%) - 仅当启用时  
        if (activeStages.includes('creative')) {  
            if (message.includes('# Agent: 维度化创意专家')) {  
                state.currentAgent = 'creative';  
                return { stage: 'creative', progress: 55 };  
            }  
            
            if (state.currentAgent === 'creative') {  
                if (message.includes('## Task:')) {  
                    return { stage: 'creative', progress: 60 };  
                }  
                if (message.includes('## Final Answer:')) {  
                    state.currentAgent = null;  
                    return { stage: 'creative', progress: 68 };  
                }  
            }  
        }  
        
        // 5. 模板阶段 (70-83%) - 关键修正  
        if (activeStages.includes('template')) {  
            // 更精确的模板阶段识别  
            if (message.includes('# Agent: 模板调整') ||   
                message.includes('模板调整与内容填充专家') ||  
                message.includes('HTML内容适配任务')) {  
                state.currentAgent = 'template';  
                return { stage: 'template', progress: 70 };  
            }  
            
            if (state.currentAgent === 'template') {  
                if (message.includes('模板填充适配处理比较耗时')) {  
                    return { stage: 'template', progress: 73 };  
                }  
                
                if (message.includes('## Using tool: read_template_tool')) {  
                    return { stage: 'template', progress: 76 };  
                }  
                
                if (message.includes('## Tool Output:') && message.includes('HTML模板')) {  
                    return { stage: 'template', progress: 80 };  
                }  
                
                // 模板完成标志  
                if (message.includes('## Final Answer:') && message.includes('html')) {  
                    state.currentAgent = null;  
                    return { stage: 'template', progress: 83 };  
                }  
            }  
        }  
        
        // 6. 设计阶段 (70-78%) - 仅当启用时  
        if (activeStages.includes('design')) {  
            if (message.includes('# Agent: 微信排版专家') ||  
                message.includes('排版设计')) {  
                state.currentAgent = 'design';  
                return { stage: 'design', progress: 70 };  
            }  
            
            if (state.currentAgent === 'design') {  
                if (message.includes('## Task:')) {  
                    return { stage: 'design', progress: 74 };  
                }  
                if (message.includes('## Final Answer:')) {  
                    state.currentAgent = null;  
                    return { stage: 'design', progress: 78 };  
                }  
            }  
        }  
        
        // 7. 保存阶段 (85-93%)  
        if (message.includes('保存成功') || message.includes('文章《')) {  
            return { stage: 'save', progress: 85 };  
        }  
        
        // 8. 发布阶段 (95-98%) - 仅当启用时  
        if (activeStages.includes('publish')) {  
            if (message.includes('发布完成') || message.includes('发布结果')) {  
                return { stage: 'publish', progress: 95 };  
            }  
        }  
        
        // 9. 完成 (100%)  
        if (message.includes('[INTERNAL]: 任务执行完成')) {  
            return { stage: 'complete', progress: 100 };  
        }  
        
        return { stage: null, progress: null };  
    }
    
    /**  
     * 根据配置构建激活的阶段列表  
     */  
    _buildActiveStages(config) {  
        const stages = ['init', 'search', 'writing'];  
        
        // 创意阶段  
        if (config.dimensional_creative?.enabled) {  
            stages.push('creative');  
        }  
        
        // 格式化阶段  
        if (config.article_format?.toLowerCase() === 'html') {  
            if (config.use_template) {  
                stages.push('template');  
            } else {  
                stages.push('design');  
            }  
        }  
        
        stages.push('save');  
        
        // 发布阶段  
        if (config.auto_publish) {  
            stages.push('publish');  
        }  
        
        stages.push('complete');  
        
        return stages;  
    }  
    
    /**  
     * 动态计算进度范围  
     */  
    _calculateProgressRanges(activeStages) {  
        const ranges = {  
            init: { start: 5, end: 10 },  
            search: { start: 10, end: 15 },  
            writing: { start: 15, end: 30 }  
        };  
        
        let currentEnd = 30;  
        
        if (activeStages.includes('creative')) {  
            ranges.creative = { start: currentEnd, end: currentEnd + 10 };  
            currentEnd += 10;  
        }  
        
        if (activeStages.includes('template')) {  
            ranges.template = { start: currentEnd, end: currentEnd + 50 };  
            currentEnd += 50;  
        } else if (activeStages.includes('design')) {  
            ranges.design = { start: currentEnd, end: currentEnd + 15 };  
            currentEnd += 15;  
        }  
        
        const saveSpace = 95 - currentEnd;  
        ranges.save = { start: currentEnd, end: currentEnd + saveSpace };  
        currentEnd += saveSpace;  
        
        if (activeStages.includes('publish')) {  
            ranges.publish = { start: currentEnd, end: 98 };  
            currentEnd = 98;  
        }  
        
        ranges.complete = { start: 100, end: 100 };  
        
        return ranges;  
    }

    /**  
     * 处理生成完成  
     */  
    handleGenerationComplete(data) {  
        
        this.isGenerating = false; 

        // 停止进度管理器  
        if (this.bottomProgress) {  
            this.bottomProgress.stop();  
        }  
        
        if (data.type === 'completed') {  
            // 成功:更新到100%,显示完成状态  
            if (this.bottomProgress) {  
                this.bottomProgress.updateProgress('complete', 100);  
            }  
            
            // 延迟2秒隐藏,让用户看到100%的成功状态  
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
            // 失败:显示错误状态  
            if (this.bottomProgress) {  
                this.bottomProgress.showError(data.error || '未知错误');  
            }  
            
            // 延迟1秒隐藏(比成功时短,因为已经有错误通知了)  
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
            this.loadArticles();  
        } else if (data.type === 'failed') {  
            window.app?.showNotification('生成失败', 'error');  
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
                            type: result.status,  // 'completed', 'failed', 或 'stopped'  
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
            
            // 修复后的图标切换逻辑  
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