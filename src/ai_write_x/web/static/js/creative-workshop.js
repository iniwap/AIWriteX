/**  
 * 创意工坊管理器  
 * 职责:话题输入、内容生成、配置面板管理  
 */  
class CreativeWorkshopManager {  
    constructor() {  
        this.isGenerating = false;  
        this.currentTopic = '';  
        this.generationHistory = [];  
          
        this.init();  
    }  
      
    init() {  
        this.bindEventListeners();  
        this.loadHistory();  
        this.initKeyboardShortcuts();  
    }  
      
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
                    this.startGeneration();  
                }  
            });  
        }  
        
        // 生成按钮  
        const generateBtn = document.getElementById('generate-btn');  
        if (generateBtn) {  
            generateBtn.addEventListener('click', () => this.startGeneration());  
        }  
        
        // 停止按钮  
        const stopBtn = document.getElementById('stop-btn');  
        if (stopBtn) {  
            stopBtn.addEventListener('click', () => this.stopGeneration());  
        }  
        
        // 配置触发器 - 重新设计为切换式交互  
        document.querySelectorAll('.config-trigger').forEach(trigger => {  
            trigger.addEventListener('click', (e) => {  
                this.toggleReferenceMode(e.currentTarget);  
            });  
        });  
    } 

    toggleReferenceMode(trigger) {  
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
            
            // 禁用所有表单控件(可选,因为面板已收起)  
            this.setReferenceFormState(true);  
        }  
    }  

    setReferenceFormState(disabled) {  
        // 控制借鉴模式表单的启用/禁用状态  
        const formElements = [  
            'template-category',  
            'template-name',  
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

    async startGeneration() {  
        if (this.isGenerating) return;  
        
        let topic = this.currentTopic.trim();  
        
        // 如果没有输入话题,自动获取热搜  
        if (!topic) {  
            window.app?.showNotification('未输入话题,正在自动获取热搜...', 'info');  
            
            try {  
                // 调用后端API获取热搜话题  
                const response = await fetch('/api/hot-topics');  
                if (response.ok) {  
                    const data = await response.json();  
                    topic = data.topic || '';  
                    
                    if (!topic) {  
                        window.app?.showNotification('获取热搜失败,请手动输入话题', 'warning');  
                        return;  
                    }  
                    
                    // 更新输入框显示  
                    const topicInput = document.getElementById('topic-input');  
                    if (topicInput) {  
                        topicInput.value = topic;  
                        this.currentTopic = topic;  
                    }  
                    
                    window.app?.showNotification(`已自动选取话题: ${topic}`, 'success');  
                } else {  
                    throw new Error('获取热搜失败');  
                }  
            } catch (error) {  
                console.error('获取热搜失败:', error);  
                window.app?.showNotification('获取热搜失败,请手动输入话题', 'error');  
                return;  
            }  
        } 
          
        this.isGenerating = true;  
        this.updateGenerationUI(true);  
        this.addToHistory(topic);  
          
        try {  
            const response = await fetch('/api/generate', {  
                method: 'POST',  
                headers: {  
                    'Content-Type': 'application/json',  
                },  
                body: JSON.stringify({  
                    topic: topic,  
                    config: window.configManager ? window.configManager.getConfig() : {}  
                })  
            });  
              
            if (response.ok) {  
                window.app?.showNotification('内容生成已开始', 'success');  
            } else {  
                throw new Error('生成请求失败');  
            }  
        } catch (error) {  
            console.error('生成失败:', error);  
            window.app?.showNotification('生成失败，请重试', 'error');  
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
                window.app?.showNotification('已停止生成', 'info');  
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
            const btnText = generateBtn.querySelector('span');    
            if (btnText) {    
                btnText.textContent = isGenerating ? '生成中...' : '开始生成';    
            } 
        }  
          
        if (stopBtn) {  
            stopBtn.disabled = !isGenerating;  
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
                this.startGeneration();  
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