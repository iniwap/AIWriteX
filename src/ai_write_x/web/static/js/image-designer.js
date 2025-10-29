class ImageDesignerDialog {  
    constructor() {  
        this.dialog = null;  
        this.editor = null;  
        this.currentArticle = null;  
        this.isClosing = false;  
        this.isDirty = false;  
        this.keydownHandler = null;  
        this.overlayClickHandler = null;  
        this.themeObserver = null;  
    }
      
    async open(articlePath, articleTitle) {  
        this.currentArticle = articlePath;  
        this.createDialog(articleTitle);  
        
        document.body.appendChild(this.dialog);  
        
        // 使用第一个版本的等待方式  
        await new Promise(resolve => requestAnimationFrame(resolve));  
        
        await this.initGrapesJS();  
        await this.loadDesign();  
        this.bindEvents();  
        
        requestAnimationFrame(() => {  
            this.dialog.classList.add('show');  
        });  
    }    
      
    createDialog(articleTitle) {  
        this.dialog = document.createElement('div');  
        this.dialog.className = 'content-editor-dialog';  
        
        this.dialog.innerHTML = `  
            <div class="editor-container" style="display: flex; flex-direction: column; height: 85vh;">  
                <div class="editor-header" style="flex-shrink: 0;">   
                    <h2 class="editor-title">
                        <span>页面设计 - ${articleTitle}</span>  
                    </h2>  
                    <div class="editor-actions">  
                        <button class="btn btn-secondary" id="designer-cancel">关闭</button>  
                        <button class="btn btn-primary" id="designer-save">  
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>  
                                <polyline points="17 21 17 13 7 13 7 21"/>  
                                <polyline points="7 3 7 8 15 8"/>  
                            </svg>  
                            保存设计  
                        </button>  
                    </div>  
                </div>  
                
                <div class="editor-body" style="flex: 1; display: block; overflow: hidden;">  
                    <div id="gjs-editor" style="height: 100%;"></div>  
                </div>  
            </div>  
        `;  
    }   
      
    async initGrapesJS() {    
        const appTheme = document.documentElement.getAttribute('data-theme') || 'light';    
        const isDark = appTheme === 'dark';    
        
        const container = this.dialog.querySelector('#gjs-editor');    
        if (container.offsetHeight === 0) {    
            await new Promise(resolve => setTimeout(resolve, 200));     
        }    
        
        this.editor = grapesjs.init({    
            container: '#gjs-editor',    
            height: '100%',    
            width: 'auto',    
            fromElement: false,    
            
            storageManager: false,    
            
            plugins: ['grapesjs-preset-webpage'],    
            pluginsOpts: {    
                'grapesjs-preset-webpage': {    
                    // 移除 blocks 限制,使用所有预设组件  
                    modalImportTitle: '导入',    
                    modalImportLabel: '<div>粘贴HTML</div>',    
                }    
            },    
            
            canvas: {    
                styles: [    
                    '/static/css/themes/light-theme.css',    
                    '/static/css/themes/dark-theme.css',    
                ],    
            },    
            
            styleManager: {    
                sectors: [    
                    {    
                        name: '布局',    
                        open: true,    
                        properties: ['margin', 'padding', 'width', 'height', 'display']    
                    },    
                    {    
                        name: '排版',    
                        properties: ['font-family', 'font-size', 'font-weight', 'color', 'text-align']    
                    },    
                    {    
                        name: '背景',    
                        properties: ['background-color', 'background-image']    
                    },    
                    {    
                        name: '边框',    
                        properties: ['border', 'border-radius', 'box-shadow']    
                    }    
                ]    
            }  
        });    
        
        this.editor.on('load', () => {    
            this.syncTheme(isDark);  
            
            // 添加自定义blocks  
            this.addCustomBlocks();  
            
            // 如果画布为空,添加欢迎内容  
            if (!this.editor.getComponents().length) {  
                this.editor.setComponents(`  
                    <div style="padding: 40px; text-align: center; background: var(--surface-color); border-radius: 8px; margin: 20px;">  
                        <h2 style="color: var(--text-primary); margin-bottom: 16px;">欢迎使用页面设计器</h2>  
                        <p style="color: var(--text-secondary); margin-bottom: 24px;">从右侧拖拽组件开始设计,或导入现有HTML代码</p>  
                        <div style="display: flex; gap: 12px; justify-content: center;">  
                            <button style="padding: 8px 16px; background: var(--primary-color); color: white; border: none; border-radius: 4px; cursor: pointer;">开始设计</button>  
                        </div>  
                    </div>  
                `);  
            }  
            
            this.editor.refresh();    
        });    
        
        this.editor.on('change:changesCount', () => {    
            this.isDirty = true;    
        });    
    }
      
    addCustomBlocks() {  
        const bm = this.editor.BlockManager;  
          
        bm.add('article-image', {  
            label: '文章配图',  
            category: '配图组件',  
            content: `  
                <div style="margin: 20px 0; text-align: center;">  
                    <img src="https://via.placeholder.com/800x400"   
                         style="max-width: 100%; height: auto; border-radius: 8px;" />  
                    <p style="margin-top: 8px; font-size: 14px; color: #666;">图片说明</p>  
                </div>  
            `  
        });  
          
        bm.add('cover-image', {  
            label: '封面图',  
            category: '配图组件',  
            content: `  
                <div style="width: 100%; height: 400px; position: relative;">  
                    <img src="https://via.placeholder.com/1200x400"   
                         style="width: 100%; height: 100%; object-fit: cover;" />  
                </div>  
            `  
        });  
          
        bm.add('image-text-layout', {  
            label: '图文混排',  
            category: '配图组件',  
            content: `  
                <div style="display: flex; gap: 20px; margin: 20px 0;">  
                    <img src="https://via.placeholder.com/300x200"   
                         style="width: 300px; height: 200px; object-fit: cover; border-radius: 8px;" />  
                    <div style="flex: 1;">  
                        <h3>标题</h3>  
                        <p>这里是文字内容,可以自由编辑...</p>  
                    </div>  
                </div>  
            `  
        });  
    }  
      
    syncTheme(isDark) {            
        const canvas = this.editor?.Canvas?.getDocument();  
        if (!canvas) {  
            return;  
        }  
          
        // 设置data-theme属性  
        canvas.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');  
          
        // 从主应用复制CSS变量到iframe  
        const computedStyle = getComputedStyle(document.documentElement);  
        const cssVars = [  
            '--background-color',  
            '--text-primary',  
            '--text-secondary',  
            '--border-color',  
            '--surface-color',  
            '--primary-color',  
            '--secondary-color'  
        ];  
          
        const canvasBody = canvas.body;  
        if (canvasBody) {  
            cssVars.forEach(varName => {  
                const value = computedStyle.getPropertyValue(varName);  
                if (value) {  
                    canvasBody.style.setProperty(varName, value);  
                }  
            });  
        }  
    }  
      
    async loadDesign() {  
        try {  
            // 1. 先尝试加载已保存的设计  
            const designResponse = await fetch(`/api/articles/design?article=${encodeURIComponent(this.currentArticle)}`);  
            if (designResponse.ok) {  
                const data = await designResponse.json();  
                if (data.html) {  
                    // 如果有保存的设计,使用设计数据  
                    this.editor.setComponents(data.html);  
                    this.editor.setStyle(data.css);  
                    this.isDirty = false;  
                    return;  
                }  
            }  
            
            // 2. 如果没有保存的设计,加载原始 HTML  
            const contentResponse = await fetch(`/api/articles/content?path=${encodeURIComponent(this.currentArticle)}`);  
            if (contentResponse.ok) {  
                const htmlContent = await contentResponse.text();  
                
                // 将原始 HTML 加载到编辑器  
                this.editor.setComponents(htmlContent);  
                this.isDirty = false;  // 初始加载不算修改  
            }  
        } catch (error) {  
            console.error('加载内容失败:', error);  
        }  
    } 
      
    async saveDesign() {  
        const html = this.editor.getHtml();  
        const css = this.editor.getCss();  
          
        try {  
            const response = await fetch('/api/articles/design', {  
                method: 'POST',  
                headers: { 'Content-Type': 'application/json' },  
                body: JSON.stringify({  
                    article: this.currentArticle,  
                    html: html,  
                    css: css  
                })  
            });  
              
            if (response.ok) {  
                this.isDirty = false;  
                window.app?.showNotification('设计已保存', 'success');  
            }  
        } catch (error) {  
            window.app?.showNotification('保存失败: ' + error.message, 'error');  
        }  
    }  
      
    bindEvents() {  
        // 保存按钮  
        const saveBtn = this.dialog.querySelector('#designer-save');  
        saveBtn?.addEventListener('click', async () => {  
            await this.saveDesign();  
        });  
        
        // 关闭按钮  
        const cancelBtn = this.dialog.querySelector('#designer-cancel');  
        cancelBtn?.addEventListener('click', () => {  
            this.close();  
        });  
        
        // ESC键关闭  
        this.keydownHandler = (e) => {  
            if (e.key === 'Escape') {  
                this.close();  
            }  
        };  
        document.addEventListener('keydown', this.keydownHandler);  
        
        // 点击遮罩关闭(只检查dialog本身)  
        this.overlayClickHandler = (e) => {  
            if (e.target === this.dialog) {  
                this.close();  
            }  
        };  
        this.dialog.addEventListener('click', this.overlayClickHandler);  
        
        // 监听应用主题变化  
        this.themeObserver = new MutationObserver((mutations) => {  
            mutations.forEach((mutation) => {  
                if (mutation.attributeName === 'data-theme') {  
                    const appTheme = document.documentElement.getAttribute('data-theme');  
                    const isDark = appTheme === 'dark';  
                    this.syncTheme(isDark);  
                }  
            });  
        });  
        
        this.themeObserver.observe(document.documentElement, {  
            attributes: true,  
            attributeFilter: ['data-theme']  
        });  
    } 
      
    close() {  
        if (this.isClosing) return;  
        
        if (this.isDirty) {  
            this.isClosing = true;  
            
            // 移除对 overlay 的引用  
            if (this.overlayClickHandler && this.dialog) {  
                this.dialog.removeEventListener('click', this.overlayClickHandler);  
            }  
            
            window.dialogManager.showConfirm(  
                '有未保存的修改,确认关闭?',  
                () => {  
                    this.destroy();  
                },  
                () => {  
                    setTimeout(() => {  
                        if (this.overlayClickHandler && this.dialog) {  
                            this.dialog.addEventListener('click', this.overlayClickHandler);  
                        }  
                        this.isClosing = false;  
                    }, 100);  
                }  
            );  
        } else {  
            this.destroy();  
        }  
    }
      
    destroy() {  
        // 1. 先移除所有事件监听器  
        if (this.keydownHandler) {  
            document.removeEventListener('keydown', this.keydownHandler);  
            this.keydownHandler = null;  
        }  
        
        if (this.overlayClickHandler && this.dialog) {  
            this.dialog.removeEventListener('click', this.overlayClickHandler);  
            this.overlayClickHandler = null;  
        }  
        
        if (this.themeObserver) {  
            this.themeObserver.disconnect();  
            this.themeObserver = null;  
        }  
        
        // 2. 销毁GrapesJS实例  
        if (this.editor) {  
            try {  
                this.editor.destroy();  
            } catch (e) {  

            }  
            this.editor = null;  
        }  
        
        // 3. 强制移除dialog元素  
        if (this.dialog) {  
            this.dialog.classList.remove('show');  
            
            // 使用更可靠的移除方式  
            if (this.dialog.parentNode) {  
                this.dialog.parentNode.removeChild(this.dialog);  
            }  
            
            this.dialog = null;  
        }  
        
        // 4. 重置状态  
        this.currentArticle = null;  
        this.isDirty = false;  
        this.isClosing = false;  
    }
}  
  
document.addEventListener('DOMContentLoaded', () => {  
    window.imageDesignerDialog = new ImageDesignerDialog();
});