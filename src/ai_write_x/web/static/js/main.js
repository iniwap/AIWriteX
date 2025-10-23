// AIWriteX 主JavaScript文件    
    
class AIWriteXApp {    
    constructor() {    
        this.ws = null;    
        this.currentView = 'creative-workshop';    
        this.isGenerating = false;    
            
        this.init();    
    }    
        
    init() {    
        this.setupEventListeners();    
        this.connectWebSocket();    
        this.showView(this.currentView);    
            
        // 等待配置管理器初始化完成后再加载配置    
        this.waitForConfigManager();  
    }    
        
    waitForConfigManager() {    
        if (window.configManager) {    
            this.loadInitialData();    
        } else {    
            setTimeout(() => this.waitForConfigManager(), 100);    
        }    
    }    
        
    loadInitialData() {    
        // 根据当前视图加载相应数据    
        switch (this.currentView) {    
            case 'creative-workshop':    
                this.loadDimensionalConfig();    
                break;    
            // 移除 article-manager 的处理,由 ArticleManager 自己负责  
            case 'config-manager':    
                // 配置已由 configManager 自动加载    
                break;    
        }    
    }    
        
    setupEventListeners() {    
        // 原有的导航菜单点击事件（排除系统配置的切换按钮）    
        document.querySelectorAll('.nav-link:not(.nav-toggle)').forEach(link => {    
            link.addEventListener('click', (e) => {    
                e.preventDefault();    
                const view = link.dataset.view;    
                this.showView(view);    
            });    
        });    
      
        // 系统配置主菜单切换    
        const navToggle = document.querySelector('.nav-toggle');    
        if (navToggle) {    
            navToggle.addEventListener('click', (e) => {    
                e.preventDefault();    
                const navItem = e.target.closest('.nav-item-expandable');    
                if (navItem) {    
                    navItem.classList.toggle('expanded');    
                }    
                this.showView('config-manager');    
            });    
        }    
      
        // 配置二级菜单点击事件    
        document.querySelectorAll('.nav-sublink').forEach(link => {    
            link.addEventListener('click', (e) => {    
                e.preventDefault();    
                const configType = link.dataset.config;    
                  
                // 更新二级菜单状态    
                document.querySelectorAll('.nav-sublink').forEach(sublink => {    
                    sublink.classList.remove('active');    
                });    
                link.classList.add('active');    
                  
                // 显示对应配置面板    
                this.showConfigPanel(configType);    
            });    
        });    
      
        // 生成按钮事件    
        const generateBtn = document.getElementById('generate-btn');    
        if (generateBtn) {    
            generateBtn.addEventListener('click', () => this.startGeneration());    
        }    
      
        // 停止按钮事件    
        const stopBtn = document.getElementById('stop-btn');    
        if (stopBtn) {    
            stopBtn.addEventListener('click', () => this.stopGeneration());    
        }    
      
        // 配置保存事件 - 使用统一配置管理器    
        const saveConfigBtn = document.getElementById('save-config-btn');    
        if (saveConfigBtn) {    
            saveConfigBtn.addEventListener('click', () => this.saveConfig());    
        }    
      
        // 维度滑块事件    
        document.querySelectorAll('.dimension-slider').forEach(slider => {    
            slider.addEventListener('input', (e) => {    
                this.updateDimensionValue(e.target);    
            });    
        });    
    }  
  
    showConfigPanel(panelType) {    
        const configContent = document.querySelector('.config-content');    
        const targetPanel = document.getElementById(`config-${panelType}`);    
          
        // 立即重置滚动位置    
        if (configContent) {    
            configContent.scrollTop = 0;    
        }    
          
        // 隐藏其他配置面板    
        document.querySelectorAll('.config-panel').forEach(panel => {    
            if (panel !== targetPanel) {    
                panel.classList.remove('active');    
                panel.style.display = 'none';    
            }    
        });    
          
        // 显示目标面板    
        if (targetPanel) {    
            targetPanel.style.display = 'block';    
            targetPanel.offsetHeight; // 强制重排    
            targetPanel.classList.add('active');    
        }    
          
        // 更新导航状态    
        document.querySelectorAll('.config-nav-item').forEach(item => {    
            item.classList.remove('active');    
        });    
          
        const activeNavItem = document.querySelector(`[data-config="${panelType}"]`).parentElement;    
        if (activeNavItem) {    
            activeNavItem.classList.add('active');    
        }    
          
        this.currentPanel = panelType;    
    }  
          
    connectWebSocket() {    
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';    
        const wsUrl = `${protocol}//${window.location.host}/ws/logs`;    
            
        this.ws = new WebSocket(wsUrl);    
            
        this.ws.onopen = () => {    
            this.updateConnectionStatus(true);    
        };    
            
        this.ws.onmessage = (event) => {    
            // 忽略心跳响应    
            if (event.data === 'pong') {    
                return;    
            }    
              
            try {    
                const data = JSON.parse(event.data);    
                this.addLogEntry(data);    
            } catch (error) {    
                //console.warn('无法解析 WebSocket 消息:', event.data);    
            }    
        };    
            
        this.ws.onclose = () => {    
            this.updateConnectionStatus(false);    
            // 3秒后重连    
            setTimeout(() => this.connectWebSocket(), 3000);    
        };    
            
        this.ws.onerror = (error) => {    
            this.updateConnectionStatus(false);    
        };    
            
        // 发送心跳    
        setInterval(() => {    
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {    
                this.ws.send('ping');    
            }    
        }, 30000);    
    }    
        
    updateConnectionStatus(connected) {    
        const indicator = document.querySelector('.status-indicator');    
        if (indicator) {    
            indicator.style.backgroundColor = connected ?     
                'var(--success-color)' : 'var(--error-color)';    
        }    
    }    
        
    addLogEntry(logData) {    
        const logPanel = document.getElementById('log-panel');    
        if (!logPanel) return;    
            
        const entry = document.createElement('div');    
        entry.className = `log-entry ${logData.type}`;    
            
        const timestamp = new Date(logData.timestamp * 1000).toLocaleTimeString();    
        entry.innerHTML = `    
            <span class="log-timestamp">[${timestamp}]</span>    
            <span class="log-message">${this.escapeHtml(logData.message)}</span>    
        `;    
            
        logPanel.appendChild(entry);    
        logPanel.scrollTop = logPanel.scrollHeight;    
            
        // 限制日志条数    
        const entries = logPanel.querySelectorAll('.log-entry');    
        if (entries.length > 1000) {    
            entries[0].remove();    
        }    
    }    
        
    escapeHtml(text) {    
        const div = document.createElement('div');    
        div.textContent = text;    
        return div.innerHTML;    
    }    
        
    showView(viewName) {    
        // 更新导航状态    
        document.querySelectorAll('.nav-link').forEach(link => {    
            link.classList.remove('active');    
        });    
          
        requestAnimationFrame(() => {    
            document.querySelectorAll('.nav-link').forEach(link => {    
                if (link.dataset.view === viewName) {    
                    link.classList.add('active');    
                }    
            });    
        });    
          
        const targetView = document.getElementById(`${viewName}-view`);    
          
        // 隐藏其他视图    
        document.querySelectorAll('.view-content').forEach(view => {    
            if (view !== targetView) {    
                view.classList.remove('active');    
                setTimeout(() => {    
                    view.style.display = 'none';    
                }, 200);    
            }    
        });    
          
        // 显示目标视图    
        if (targetView) {    
            targetView.style.display = 'block';    
            requestAnimationFrame(() => {    
                targetView.classList.add('active');    
            });  
              
            // 延迟初始化各个管理器  
            if (viewName === 'template-manager' && !window.templateManager) {    
                window.templateManager = new TemplateManager();    
            }  
              
            // 延迟初始化文章管理器  
            if (viewName === 'article-manager' && !window.articleManager) {    
                window.articleManager = new ArticleManager();    
            }  
        }    
          
        // 关键修改:如果切换到配置管理视图,默认激活界面设置子菜单    
        if (viewName === 'config-manager') {    
            // 清除所有子菜单的active状态    
            document.querySelectorAll('.nav-sublink').forEach(sublink => {    
                sublink.classList.remove('active');    
            });    
              
            // 激活界面设置子菜单    
            const uiConfigSublink = document.querySelector('[data-config="ui"]');    
            if (uiConfigSublink) {    
                uiConfigSublink.classList.add('active');    
            }    
              
            // 显示界面设置面板    
            if (window.configManager) {    
                window.configManager.showConfigPanel('ui');    
            }    
        } else {    
            // 关键:如果切换到非配置管理视图,折叠系统设置菜单    
            const expandableNavItem = document.querySelector('.nav-item-expandable');    
            if (expandableNavItem) {    
                expandableNavItem.classList.remove('expanded');    
            }    
              
            // 同时清除所有子菜单的 active 状态    
            document.querySelectorAll('.nav-sublink').forEach(sublink => {    
                sublink.classList.remove('active');    
            });    
        }    
          
        // 控制预览按钮的显示/隐藏    
        const previewTrigger = document.getElementById('preview-trigger');    
        if (previewTrigger) {    
            const viewsWithPreview = ['creative-workshop', 'article-manager', 'template-manager'];    
            if (viewsWithPreview.includes(viewName)) {    
                previewTrigger.style.display = 'flex';    
            } else {    
                previewTrigger.style.display = 'none';    
            }    
        }    
          
        this.currentView = viewName;    
    }  
        
    async startGeneration() {    
        if (this.isGenerating) return;    
            
        const topic = document.getElementById('topic-input')?.value;    
        if (!topic || !topic.trim()) {    
            this.showNotification('请输入创作主题', 'warning');    
            return;    
        }    
            
        this.isGenerating = true;    
        this.updateGenerationUI(true);    
            
        try {    
            const response = await fetch('/api/generate', {    
                method: 'POST',    
                headers: {    
                    'Content-Type': 'application/json',    
                },    
                body: JSON.stringify({    
                    topic: topic.trim(),    
                    config: window.configManager ? window.configManager.getConfig() : {}    
                })    
            });    
                
            if (response.ok) {    
                const result = await response.json();    
                this.showNotification('内容生成已开始', 'success');    
            } else {    
                throw new Error('生成请求失败');    
            }    
        } catch (error) {    
            console.error('生成失败:', error);    
            this.showNotification('生成失败，请重试', 'error');    
        } finally {    
            this.isGenerating = false;    
            this.updateGenerationUI(false);    
        }    
    }

    async stopGeneration() {    
        try {    
            const response = await fetch('/api/generate/stop', {    
                method: 'POST'    
            });    
                
            if (response.ok) {    
                this.showNotification('已停止生成', 'info');    
            }    
        } catch (error) {    
            console.error('停止生成失败:', error);    
        }

        this.isGenerating = false;    
        this.updateGenerationUI(false);    
    }    
        
    updateGenerationUI(isGenerating) {    
        const generateBtn = document.getElementById('generate-btn');    
        const stopBtn = document.getElementById('stop-btn');    
            
        if (generateBtn) {    
            generateBtn.disabled = isGenerating;    
            generateBtn.textContent = isGenerating ? '生成中...' : '开始生成';    
        }    
            
        if (stopBtn) {    
            stopBtn.disabled = !isGenerating;    
        }    
    }    
        
    // 使用统一配置管理器保存配置    
    async saveConfig() {    
        if (!window.configManager) {    
            this.showNotification('配置管理器未初始化', 'error');    
            return;    
        }    
          
        try {    
            const success = await window.configManager.saveConfig();    
              
            if (success) {    
                this.showNotification('设置保存成功', 'success');    
            } else {    
                throw new Error('保存失败');    
            }    
        } catch (error) {    
            this.showNotification('设置保存失败', 'error');    
        }    
    }  
        
    async loadDimensionalConfig() {      
        // 必须通过配置管理器获取，无回退    
        if (!window.configManager) {    
            console.warn('配置管理器未初始化');    
            return;    
        }      
              
        try {      
            const config = window.configManager.getConfig();      
            if (config.dimensional_creative) {      
                this.updateDimensionalUI(config.dimensional_creative);      
            }      
        } catch (error) {      
            console.error('加载维度配置失败:', error);      
        }      
    }     
          
    updateDimensionValue(slider) {    
        const value = slider.value;    
        const valueDisplay = slider.parentElement.querySelector('.slider-value');    
        if (valueDisplay) {    
            valueDisplay.textContent = value;    
        }    
          
        // 通过配置管理器更新后端内存    
        const dimensionName = slider.dataset.dimension;    
        if (dimensionName && window.configManager) {    
            window.configManager.updateConfig({    
                dimensional_creative: {    
                    ...window.configManager.config.dimensional_creative,    
                    [dimensionName]: parseFloat(value)    
                }    
            });    
        } else {    
            console.warn('配置管理器不可用，无法保存维度配置');    
        }    
    }  
        
    updateDimensionalUI(dimensionalConfig) {    
        // 更新维度滑块    
        Object.entries(dimensionalConfig).forEach(([key, value]) => {    
            const slider = document.querySelector(`[data-dimension="${key}"]`);    
            if (slider) {    
                slider.value = value;    
                this.updateDimensionValue(slider);    
            }    
        });    
    }    
      
    // 添加新的预览方法    
    showPreview(content) {    
        if (window.previewPanelManager) {    
            window.previewPanelManager.show(content);    
        }    
    }    
      
    hidePreview() {    
        if (window.previewPanelManager) {    
            window.previewPanelManager.hide();    
        }    
    }  
  
    showNotification(message, type = 'info') {    
        const notification = document.createElement('div');    
        notification.className = `notification ${type}`;    
        notification.innerHTML = `    
            <div class="notification-content">    
                <span>${message}</span>    
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>    
            </div>    
        `;    
            
        document.body.appendChild(notification);    
            
        // 3秒后自动移除    
        setTimeout(() => {    
            if (notification.parentElement) {    
                notification.remove();    
            }    
        }, 3000);    
    }    
}    
    
// 初始化应用    
let app;    
document.addEventListener('DOMContentLoaded', () => {    
    app = new AIWriteXApp();  
    window.app = app;  
});