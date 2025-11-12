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
        
        // 确保移除active类,重置状态  
        this.overlay.classList.remove('active');  
        this.overlay.style.display = 'flex';  
        
        // 使用双重 requestAnimationFrame 确保浏览器完成布局计算  
        requestAnimationFrame(() => {  
            requestAnimationFrame(() => {  
                this.overlay.classList.add('active');  
            });  
        });  
        
        this.isVisible = true;  
        document.body.style.overflow = 'hidden';  
        this.updateTriggerState();  
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
            return;  
        }  
          
        triggerBtn.addEventListener('click', () => {  
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
        if (!previewArea) return;  
        
        // 清空现有内容  
        previewArea.innerHTML = '';  
        
        if (typeof content === 'string') {  
            // 检测是否是HTML内容  
            const isHtml = content.trim().startsWith('<');  
            
            if (isHtml) {  
                // 检测是否已经包含完整的文档结构和样式  
                const hasDoctype = content.trim().toLowerCase().startsWith('<!doctype');  
                const hasHtmlTag = content.trim().toLowerCase().startsWith('<html');  
                const hasScrollbarStyles = content.includes('::-webkit-scrollbar') ||   
                                        content.includes('scrollbar-width');  
                
                let finalContent = content;  
                
                // 如果是完整文档但缺少滚动条样式,需要注入样式  
                if ((hasDoctype || hasHtmlTag) && !hasScrollbarStyles) {  
                    // 获取CSS变量值  
                    const computedStyle = getComputedStyle(document.documentElement);  
                    const bgColor = computedStyle.getPropertyValue('--background-color').trim();  
                    const borderColor = computedStyle.getPropertyValue('--border-color').trim();  
                    const secondaryColor = computedStyle.getPropertyValue('--secondary-color').trim();  
                    
                    // 注入与全局CSS相同的滚动条样式  
                    const styleTag = `  
                        <style>  
                            /* 使用与全局CSS相同的滚动条样式 */  
                            ::-webkit-scrollbar {  
                                width: 6px;  
                                height: 6px;  
                            }  
                            
                            ::-webkit-scrollbar-track {  
                                background: ${bgColor};  
                            }  
                            
                            ::-webkit-scrollbar-thumb {  
                                background: ${borderColor};  
                                border-radius: 3px;  
                            }  
                            
                            ::-webkit-scrollbar-thumb:hover {  
                                background: ${secondaryColor};  
                            }  
                        </style>  
                    `;  
                    
                    // 在 </head> 之前插入样式  
                    if (content.includes('</head>')) {  
                        finalContent = content.replace('</head>', `${styleTag}</head>`);  
                    } else if (content.includes('<head>')) {  
                        finalContent = content.replace('<head>', `<head>${styleTag}`);  
                    } else {  
                        // 如果没有 <head> 标签,在 <html> 后添加  
                        finalContent = content.replace(/<html[^>]*>/i, (match) => `${match}<head>${styleTag}</head>`);  
                    }  
                } else if (!hasDoctype && !hasHtmlTag) {  
                    // HTML片段,包装成完整文档  
                    const computedStyle = getComputedStyle(document.documentElement);  
                    const bgColor = computedStyle.getPropertyValue('--background-color').trim();  
                    const borderColor = computedStyle.getPropertyValue('--border-color').trim();  
                    const secondaryColor = computedStyle.getPropertyValue('--secondary-color').trim();  
                    const textColor = computedStyle.getPropertyValue('--text-primary').trim();  
                    
                    finalContent = `  
    <!DOCTYPE html>  
    <html>  
    <head>  
        <meta charset="UTF-8">  
        <style>  
            body {  
                margin: 0;  
                padding: 16px;  
                overflow: auto;  
                color: ${textColor};  
                background: ${bgColor};  
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;  
            }  
            
            /* 使用与全局CSS相同的滚动条样式 */  
            ::-webkit-scrollbar {  
                width: 6px;  
                height: 6px;  
            }  
            
            ::-webkit-scrollbar-track {  
                background: ${bgColor};  
            }  
            
            ::-webkit-scrollbar-thumb {  
                background: ${borderColor};  
                border-radius: 3px;  
            }  
            
            ::-webkit-scrollbar-thumb:hover {  
                background: ${secondaryColor};  
            }  
        </style>  
    </head>  
    <body>  
        ${content}  
    </body>  
    </html>  
                    `;  
                }  
                
                // 使用 iframe 渲染  
                const iframe = document.createElement('iframe');  
                iframe.style.cssText = `  
                    width: 100%;  
                    height: 100%;  
                    min-height: 100%;  
                    border: none;  
                    display: block;  
                    position: absolute;  
                    top: 0;  
                    left: 0;  
                    right: 0;  
                    bottom: 0;  
                `;  
                iframe.sandbox = 'allow-same-origin allow-scripts';  
                iframe.srcdoc = finalContent;  
                
                // 确保 preview-area 有正确的定位上下文  
                previewArea.style.position = 'relative';  
                previewArea.style.height = '100%';  
                
                previewArea.appendChild(iframe);  
            } else {  
                // 纯文本内容直接插入  
                previewArea.innerHTML = content;  
            }  
        } else {  
            previewArea.appendChild(content);  
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