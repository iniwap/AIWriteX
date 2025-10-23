/**  
 * 悬浮预览面板管理器  
 */  
class PreviewPanelManager {  
    constructor() {  
        this.overlay = null;  
        this.panel = null;  
        this.isVisible = false;  
        this.currentSize = 'mobile';  
        this.sizePresets = {  
            mobile: { width: 375, label: '375×667 (iPhone)' },  
            tablet: { width: 768, label: '768×1024 (iPad)' },  
            desktop: { width: 1024, label: '1024×768 (Desktop)' }  
        };  
          
        this.init();  
    }  
      
    init() {  
        this.overlay = document.getElementById('preview-overlay');  
        this.panel = this.overlay?.querySelector('.preview-panel');  
          
        if (!this.overlay || !this.panel) {  
            console.warn('Preview panel elements not found');  
            return;  
        }  
          
        this.bindEvents();  
        this.initTriggerButton(); 
    }  
      
    bindEvents() {  
        // 关闭按钮  
        const closeBtn = document.getElementById('preview-close');  
        if (closeBtn) {  
            closeBtn.addEventListener('click', () => this.hide());  
        }  
          
        // 尺寸切换按钮  
        const toggleSizeBtn = document.getElementById('preview-toggle-size');  
        if (toggleSizeBtn) {  
            toggleSizeBtn.addEventListener('click', () => this.toggleSize());  
        }  
          
        // 点击遮罩关闭  
        this.overlay.addEventListener('click', (e) => {  
            if (e.target === this.overlay) {  
                this.hide();  
            }  
        });  
          
        // ESC 键关闭  
        document.addEventListener('keydown', (e) => {  
            if (e.key === 'Escape' && this.isVisible) {  
                this.hide();  
            }  
        });  
    }  
      
    show(content = null) {  
        if (!this.overlay) return;  
          
        if (content) {  
            this.setContent(content);  
        }  
          
        this.overlay.style.display = 'flex';  
        requestAnimationFrame(() => {  
            this.overlay.classList.add('active');  
        });  
          
        this.isVisible = true;  
        document.body.style.overflow = 'hidden';  
        this.updateTriggerState(); // 添加这行  
    }  
      
    hide() {  
        if (!this.overlay) return;  
          
        this.overlay.classList.remove('active');  
          
        setTimeout(() => {  
            this.overlay.style.display = 'none';  
            document.body.style.overflow = '';  
        }, 300);  
          
        this.isVisible = false;  
        this.updateTriggerState(); // 添加这行  
    }  
      
    toggle(content = null) {  
        if (this.isVisible) {  
            this.hide();  
        } else {  
            this.show(content);  
        }  
    }  
      
    initTriggerButton() {  
        const triggerBtn = document.getElementById('preview-trigger');  
        if (!triggerBtn) {  
            console.warn('Preview trigger button not found');  
            return;  
        }  
          
        triggerBtn.addEventListener('click', () => {  
            console.log('Trigger button clicked'); // 调试日志  
            this.toggle();  
        });  
    }  
      
    updateTriggerState() {  
        const triggerBtn = document.getElementById('preview-trigger');  
        if (!triggerBtn) return;  
          
        const tooltip = triggerBtn.querySelector('.trigger-tooltip');  
        if (this.isVisible) {  
            triggerBtn.classList.add('active');  
            if (tooltip) tooltip.textContent = '关闭预览';  
        } else {  
            triggerBtn.classList.remove('active');  
            if (tooltip) tooltip.textContent = '预览面板';  
        }  
    }  
      
    setContent(content) {  
        const previewArea = document.getElementById('preview-area');  
        if (previewArea) {  
            if (typeof content === 'string') {  
                previewArea.innerHTML = content;  
            } else {  
                previewArea.innerHTML = '';  
                previewArea.appendChild(content);  
            }  
        }  
    }  
      
    toggleSize() {  
        const sizes = Object.keys(this.sizePresets);  
        const currentIndex = sizes.indexOf(this.currentSize);  
        const nextIndex = (currentIndex + 1) % sizes.length;  
        const nextSize = sizes[nextIndex];  
          
        this.setSize(nextSize);  
    }  
      
    setSize(size) {  
        if (!this.sizePresets[size] || !this.panel) return;  
          
        this.currentSize = size;  
        const preset = this.sizePresets[size];  
          
        // 移除所有尺寸类  
        this.panel.classList.remove('tablet-size', 'desktop-size');  
          
        // 添加对应尺寸类  
        if (size === 'tablet') {  
            this.panel.classList.add('tablet-size');  
        } else if (size === 'desktop') {  
            this.panel.classList.add('desktop-size');  
        }  
          
        // 更新尺寸信息显示  
        const sizeInfo = this.overlay.querySelector('.preview-size-info');  
        if (sizeInfo) {  
            sizeInfo.textContent = preset.label;  
        }  
    }  
      
    async previewArticle(article) {  
        try {  
            const response = await fetch(`/api/articles/content?path=${encodeURIComponent(article.path)}`);  
            if (response.ok) {  
                const html = await response.text();  
                if (window.previewPanelManager) {  
                    window.previewPanelManager.show(html);  
                } else {  
                    this.showNotification('预览面板未初始化', 'error');  
                }  
            } else {  
                throw new Error('加载失败');  
            }  
        } catch (error) {  
            this.showNotification('预览失败: ' + error.message, 'error');  
        }  
    }  
      
    // 预览生成的内容  
    previewGenerated(content) {  
        this.show(content);  
    } 
}  
  
// 全局预览面板管理器实例  
let previewPanelManager;  
  
// 初始化预览面板管理器  
document.addEventListener('DOMContentLoaded', () => {  
    previewPanelManager = new PreviewPanelManager();  
    window.previewPanelManager = previewPanelManager;  
});  
  
// 导出给其他模块使用  
if (typeof module !== 'undefined' && module.exports) {  
    module.exports = PreviewPanelManager;  
}