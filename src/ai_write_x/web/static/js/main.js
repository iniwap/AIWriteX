/**  
 * AIWriteX 主应用类  
 * 职责:应用初始化、视图路由、WebSocket连接、全局通知  
 */  
class AIWriteXApp {  
    constructor() {  
        this.ws = null;  
        this.currentView = 'creative-workshop';  
          
        this.init();  
    }  
      
    init() {  
        this.setupNavigation();  
        this.connectWebSocket();  
        this.showView(this.currentView);  
    }  
      
    // ========== 导航管理 ==========  
    setupNavigation() {  
        // 主导航菜单点击事件  
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
                  
                // 委托给配置管理器  
                if (window.configManager) {  
                    window.configManager.showConfigPanel(configType);  
                }  
            });  
        });  
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
            this.initializeViewManager(viewName);  
        }  
          
        // 处理配置管理视图的特殊逻辑  
        this.handleConfigViewSwitch(viewName);  
          
        // 控制预览按钮的显示/隐藏  
        this.updatePreviewButtonVisibility(viewName);  
          
        this.currentView = viewName;  
    }  
      
    initializeViewManager(viewName) {  
        switch(viewName) {  
            case 'creative-workshop':  
                if (!window.creativeWorkshopManager) {  
                    window.creativeWorkshopManager = new CreativeWorkshopManager();  
                }  
                break;  
            case 'template-manager':  
                if (!window.templateManager) {  
                    window.templateManager = new TemplateManager();  
                }  
                break;  
            case 'article-manager':  
                if (!window.articleManager) {  
                    window.articleManager = new ArticleManager();  
                }  
                break;  
        }  
    }  
      
    handleConfigViewSwitch(viewName) {  
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
            // 如果切换到非配置管理视图,折叠系统设置菜单  
            const expandableNavItem = document.querySelector('.nav-item-expandable');  
            if (expandableNavItem) {  
                expandableNavItem.classList.remove('expanded');  
            }  
              
            // 同时清除所有子菜单的 active 状态  
            document.querySelectorAll('.nav-sublink').forEach(sublink => {  
                sublink.classList.remove('active');  
            });  
        }  
    }  
      
    updatePreviewButtonVisibility(viewName) {  
        const previewTrigger = document.getElementById('preview-trigger');  
        if (previewTrigger) {  
            const viewsWithPreview = ['creative-workshop', 'article-manager', 'template-manager'];  
            previewTrigger.style.display = viewsWithPreview.includes(viewName) ? 'flex' : 'none';  
        }  
    }  
      
    // ========== WebSocket连接管理 ==========  
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
                // 静默处理解析错误  
            }  
        };  
          
        this.ws.onclose = () => {  
            this.updateConnectionStatus(false);  
            // 3秒后重连  
            setTimeout(() => this.connectWebSocket(), 3000);  
        };  
          
        this.ws.onerror = () => {  
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
          
        // 重要消息推送到走马灯  
        if (logData.type === 'success' || logData.type === 'error') {  
            if (window.footerMarquee) {  
                window.footerMarquee.addMessage(logData.message, logData.type);  
            }  
        }  
          
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
      
    // ========== 全局通知系统 ==========  
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
      
    // ========== 预览面板控制 ==========  
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
}  
  
// 初始化应用  
let app;  
document.addEventListener('DOMContentLoaded', () => {  
    app = new AIWriteXApp();  
    window.app = app;  
});