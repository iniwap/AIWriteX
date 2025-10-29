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
        
        // 直接添加dialog到body  
        document.body.appendChild(this.dialog);  
        
        // 等待DOM渲染  
        await new Promise(resolve => setTimeout(resolve, 100));  
        
        // 初始化GrapesJS  
        await this.initGrapesJS();  
        await this.loadDesign();  
        this.bindEvents();  
        
        // 显示对话框  
        requestAnimationFrame(() => {  
            this.dialog.classList.add('show');  
        });  
    }     
      
    createDialog(articleTitle) {  
        this.dialog = document.createElement('div');  
        this.dialog.className = 'content-editor-dialog';  
        
        this.dialog.innerHTML = `  
            <div class="editor-container" style="display: flex; flex-direction: column; height: 85vh; max-height: 85vh;">  
                <div class="editor-header" style="flex-shrink: 0;">  
                    <h2 class="editor-title">  
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">  
                            <path d="M12 19l7-7 3 3-7 7-3-3z"/>  
                            <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/>  
                            <path d="M2 2l7.586 7.586"/>  
                            <circle cx="11" cy="11" r="2"/>  
                        </svg>  
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
                
                <div class="editor-body" style="flex: 1; display: flex; overflow: hidden; min-height: 0;">  
                    <div id="gjs-editor" style="width: 100%; height: 100%; min-height: 500px;"></div>  
                </div>  
            </div>  
        `;  
    }   
      
    async initGrapesJS() {  
        const appTheme = document.documentElement.getAttribute('data-theme') || 'light';  
        const isDark = appTheme === 'dark';  
        
        console.log('[ImageDesigner] Initializing GrapesJS with theme:', appTheme);  
        
        // 检查容器尺寸  
        const container = this.dialog.querySelector('#gjs-editor');  
        console.log('[ImageDesigner] Container dimensions:', {  
            width: container.offsetWidth,  
            height: container.offsetHeight,  
            clientWidth: container.clientWidth,  
            clientHeight: container.clientHeight  
        });  
        
        if (container.offsetHeight === 0) {  
            console.error('[ImageDesigner] Container height is 0! Waiting...');  
            await new Promise(resolve => setTimeout(resolve, 200));  
            console.log('[ImageDesigner] After wait, dimensions:', {  
                width: container.offsetWidth,  
                height: container.offsetHeight  
            });  
        }  
        
        this.editor = grapesjs.init({  
            container: '#gjs-editor',  
            height: '100%',  
            width: 'auto',  
            fromElement: false,  
            
            storageManager: false,  
            
            // 明确启用默认面板  
            panels: {   
                defaults: [  
                    {  
                        id: 'basic-actions',  
                        el: '.panel__basic-actions',  
                        buttons: [  
                            {  
                                id: 'visibility',  
                                active: true,  
                                className: 'btn-toggle-borders',  
                                label: '<i class="fa fa-clone"></i>',  
                                command: 'sw-visibility',  
                            }  
                        ],  
                    },  
                    {  
                        id: 'panel-devices',  
                        el: '.panel__devices',  
                        buttons: [  
                            {  
                                id: 'device-desktop',  
                                label: '<i class="fa fa-desktop"></i>',  
                                command: 'set-device-desktop',  
                                active: true,  
                                togglable: false,  
                            },  
                            {  
                                id: 'device-mobile',  
                                label: '<i class="fa fa-mobile"></i>',  
                                command: 'set-device-mobile',  
                                togglable: false,  
                            }  
                        ],  
                    }  
                ]  
            },  
            
            plugins: ['grapesjs-preset-webpage'],  
            pluginsOpts: {  
                'grapesjs-preset-webpage': {  
                    blocks: ['link-block', 'quote', 'text-basic'],  
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
                        properties: [  
                            'margin',  
                            'padding',  
                            'width',  
                            'height',  
                            'display',  
                            'flex-direction',  
                            'justify-content',  
                            'align-items'  
                        ]  
                    },  
                    {  
                        name: '排版',  
                        properties: [  
                            'font-family',  
                            'font-size',  
                            'font-weight',  
                            'color',  
                            'text-align',  
                            'line-height'  
                        ]  
                    },  
                    {  
                        name: '背景',  
                        properties: [  
                            'background-color',  
                            'background-image',  
                            'background-size',  
                            'background-position'  
                        ]  
                    },  
                    {  
                        name: '边框',  
                        properties: [  
                            'border',  
                            'border-radius',  
                            'box-shadow'  
                        ]  
                    }  
                ]  
            },  
            
            blockManager: {  
                blocks: []  
            }  
        });  
        
        console.log('[ImageDesigner] GrapesJS instance created:', this.editor);  
        
        // 等待编辑器完全加载  
        this.editor.on('load', () => {  
            console.log('[ImageDesigner] Editor loaded event fired');  
            this.syncTheme(isDark);  
            
            // 强制刷新编辑器  
            this.editor.refresh();  
            
            console.log('[ImageDesigner] Editor panels:', this.editor.Panels.getPanels());  
            console.log('[ImageDesigner] Editor canvas:', this.editor.Canvas);  
        });  
        
        this.addCustomBlocks();  
        
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
        console.log('[ImageDesigner] Syncing theme:', isDark ? 'dark' : 'light');  
          
        const canvas = this.editor?.Canvas?.getDocument();  
        if (!canvas) {  
            console.warn('[ImageDesigner] Canvas not available');  
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
          
        console.log('[ImageDesigner] Theme synced to canvas');  
    }  
      
    async loadDesign() {  
        try {  
            const response = await fetch(`/api/articles/design?article=${encodeURIComponent(this.currentArticle)}`);  
            if (response.ok) {  
                const data = await response.json();  
                if (data.html) {  
                    this.editor.setComponents(data.html);  
                    this.editor.setStyle(data.css);  
                    this.isDirty = false;  
                }  
            }  
        } catch (error) {  
            console.error('加载设计失败:', error);  
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
                console.warn('[ImageDesigner] Editor destroy failed:', e);  
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