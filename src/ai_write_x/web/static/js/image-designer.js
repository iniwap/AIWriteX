class ImageDesignerDialog {  
    constructor() {  
        this.dialog = null;  
        this.editor = null;  
        this.currentArticle = null;  
        this.isClosing = false;  
        this.isDirty = false;
        this.isInitializing = true;  
        this.keydownHandler = null;  
        this.overlayClickHandler = null;  
        this.themeObserver = null;  
    }
      
    async open(articlePath, articleTitle) {    
        // 重置状态标志  
        this.isInitializing = true;  
        this.isDirty = false;  
        this.isClosing = false;  
        
        this.currentArticle = articlePath;    
        this.createDialog(articleTitle);    
        
        document.body.appendChild(this.dialog);    
        
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
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor">    
                            <rect x="3" y="3" width="7" height="7"/>    
                            <rect x="14" y="3" width="7" height="7"/>    
                            <rect x="3" y="14" width="7" height="7"/>    
                            <rect x="14" y="14" width="7" height="7"/>    
                            <path d="M10 10l4 4"/>    
                        </svg>    
                        <span>页面设计 - ${articleTitle}</span>    
                    </h2>    
                    <div class="editor-actions">    
                        <button class="btn btn-secondary" id="designer-cancel">关闭</button>  
                        <button class="btn btn-secondary" id="designer-set-cover">  
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>  
                                <circle cx="8.5" cy="8.5" r="1.5"/>  
                                <polyline points="21 15 16 10 5 21"/>  
                            </svg>  
                            设置封面  
                        </button>  
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
                    modalImportTitle: '导入',        
                    modalImportLabel: '<div>粘贴HTML</div>',        
                }        
            },  
            
            assetManager: {  
                upload: '/api/articles/upload-image',  
                uploadName: 'image',  
                assets: [],  
                multiUpload: false,  
                autoAdd: true,  
                
                // 自定义上传处理  
                uploadFile: async (e) => {  
                    const files = e.dataTransfer ? e.dataTransfer.files : e.target.files;  
                    const formData = new FormData();  
                    
                    for (let i = 0; i < files.length; i++) {  
                        formData.append('image', files[i]);  
                    }  
                    
                    try {  
                        const response = await fetch('/api/articles/upload-image', {  
                            method: 'POST',  
                            body: formData  
                        });  
                        
                        if (response.ok) {  
                            const result = await response.json();  
                            const assetManager = this.editor.AssetManager;  
                            
                            // 添加到资源管理器  
                            assetManager.add({  
                                src: result.path,  
                                name: result.filename,  
                                type: 'image'  
                            });  
                            
                            // 刷新资源列表  
                            assetManager.render();  
                        }  
                    } catch (error) {  
                        console.error('上传失败:', error);  
                    }  
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
                    { name: '布局', open: true, properties: ['margin', 'padding', 'width', 'height', 'display'] },        
                    { name: '排版', properties: ['font-family', 'font-size', 'font-weight', 'color', 'text-align'] },        
                    { name: '背景', properties: ['background-color', 'background-image'] },        
                    { name: '边框', properties: ['border', 'border-radius', 'box-shadow'] }        
                ]        
            }      
        });        
        
        // 添加一个变量来存储最后选中的资源  
        this.selectedAsset = null;  
        
        // 监听 Asset Manager 的资源选择事件  
        this.editor.on('asset:select', (asset) => {  
            this.selectedAsset = asset;  
        });

        this.editor.on('load', async () => {          
            this.syncTheme(isDark);        
            this.addCustomBlocks();        
            
            // 延迟加载,确保 Asset Manager 完全就绪    
            setTimeout(async () => {    
                await this.loadExistingImages();    
            }, 1000);    
            
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
            
            // 在所有初始化完成后,延迟设置初始化完成标志  
            // 这个延迟要足够长,确保所有自动触发的change事件都已完成  
            setTimeout(() => {  
                this.isInitializing = false;  
            }, 1000);  
        });        
        
        this.editor.on('change:changesCount', () => {  
            // 只有在初始化完成后才标记为已修改  
            if (!this.isInitializing) {  
                this.isDirty = true;  
            }  
        });           
    }
      
    async loadExistingImages() {  
        try {  
            const response = await fetch('/api/articles/images');  
            if (response.ok) {  
                const images = await response.json();  
                const assetManager = this.editor.AssetManager;  
                
                // 将图片添加到资源管理器  
                images.forEach(image => {  
                    assetManager.add({  
                        src: image.path,  
                        name: image.filename,  
                        type: 'image'  
                    });  
                });  
            }  
        } catch (error) {  
            console.error('加载图片列表失败:', error);  
        }  
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
                this.isDirty = false;  
            }      
        } catch (error) {      

        }      
    }
      
    async saveDesign() {  
        const bodyHtml = this.editor.getHtml();  
        const css = this.editor.getCss();  
        
        // 使用第三方库或自定义函数内联化CSS  
        const inlinedHtml = this.inlineCssToHtml(bodyHtml, css);  
        
        const fullHtml = `<!DOCTYPE html>  
    <html lang="zh-CN">  
    <head>  
        <meta charset="UTF-8">  
        <meta name="viewport" content="width=device-width, initial-scale=1.0">  
    </head>  
    <body>  
        ${inlinedHtml}  
    </body>  
    </html>`; 
            
        try {    
            // 1. 保存设计数据(用于设计器重新打开)  
            const designResponse = await fetch('/api/articles/design', {    
                method: 'POST',    
                headers: { 'Content-Type': 'application/json' },    
                body: JSON.stringify({    
                    article: this.currentArticle,    
                    html: bodyHtml,  // 设计数据仍保存 body 内容  
                    css: css    
                })    
            });    
            
            if (!designResponse.ok) {  
                throw new Error('保存设计数据失败');  
            }  
            
            // 2. 更新原始 HTML 文件(保存完整文档)  
            const contentResponse = await fetch(`/api/articles/content?path=${encodeURIComponent(this.currentArticle)}`, {  
                method: 'PUT',  
                headers: { 'Content-Type': 'application/json' },  
                body: JSON.stringify({   
                    content: fullHtml  // 保存完整的 HTML 文档  
                })  
            });  
            
            if (!contentResponse.ok) {  
                throw new Error('更新原始 HTML 失败');  
            }  
            
            this.isDirty = false;    
            window.app?.showNotification('设计已保存', 'success');    
            
            // 3. 刷新文章管理器的预览  
            if (window.articleManager) {  
                await window.articleManager.loadArticles();  
            }  
        } catch (error) {    
            window.app?.showNotification('保存失败: ' + error.message, 'error');    
        }    
    }
       
    inlineCssToHtml(html, css) {  
        // 使用DOMParser解析HTML  
        const parser = new DOMParser();  
        const doc = parser.parseFromString(html, 'text/html');  
        
        // 解析CSS规则  
        const styleSheet = new CSSStyleSheet();  
        styleSheet.replaceSync(css);  
        
        // 遍历CSS规则,应用到对应元素  
        for (const rule of styleSheet.cssRules) {  
            if (rule.type === CSSRule.STYLE_RULE) {  
                const selector = rule.selectorText;  
                const styles = rule.style.cssText;  
                
                // 查找匹配的元素  
                const elements = doc.querySelectorAll(selector);  
                elements.forEach(el => {  
                    const existingStyle = el.getAttribute('style') || '';  
                    el.setAttribute('style', `${existingStyle};${styles}`);  
                });  
            }  
        }  
        
        return doc.body.innerHTML;  
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

        const setCoverBtn = this.dialog.querySelector('#designer-set-cover');  
        setCoverBtn?.addEventListener('click', async () => {  
            await this.setCover();  
        });   
    } 
    
    async setCover() {  
        try {  
            const response = await fetch('/api/articles/images');  
            if (!response.ok) throw new Error('获取图片列表失败');  
            
            const images = await response.json();  
            if (!images || images.length === 0) {  
                window.app?.showNotification('没有可用的图片,请先上传图片', 'warning');  
                return;  
            }  
            
            const currentCover = await this.getCurrentCover();  
            
            const dialog = document.createElement('div');  
            dialog.className = 'content-editor-dialog';  
            dialog.innerHTML = `  
                <div class="editor-container" style="max-width: 900px; max-height: 70vh;">  
                    <div class="editor-header">  
                        <h2 class="editor-title">  
                            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor">  
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>  
                                <circle cx="8.5" cy="8.5" r="1.5"/>  
                                <polyline points="21 15 16 10 5 21"/>  
                            </svg>  
                            设置封面图片  
                        </h2>  
                        <button class="btn-icon modal-close" id="cover-cancel">×</button>  
                    </div>  
                    
                    <div class="editor-body" style="display: flex; gap: 20px; padding: 20px; overflow: hidden; height: calc(70vh - 80px);">  
                        <!-- 左侧: 当前封面预览区 -->  
                        <div style="flex: 1; display: flex; flex-direction: column; gap: 12px; min-width: 400px;">  
                            <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: var(--text-primary);">  
                                当前封面预览  
                            </h3>  
                            <div id="current-cover-preview" style="  
                                width: 100%;  
                                aspect-ratio: 900/384;  
                                border: 2px dashed var(--border-color);  
                                border-radius: 8px;  
                                display: flex;  
                                align-items: center;  
                                justify-content: center;  
                                background: var(--surface-color);  
                                overflow: hidden;  
                            ">  
                                ${currentCover ? `  
                                    <img src="${currentCover}" style="width: 100%; height: 100%; object-fit: cover;" />  
                                ` : `  
                                    <div style="text-align: center; color: var(--text-secondary);">  
                                        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" style="opacity: 0.3;">  
                                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>  
                                            <circle cx="8.5" cy="8.5" r="1.5"/>  
                                            <polyline points="21 15 16 10 5 21"/>  
                                        </svg>  
                                        <p style="margin-top: 8px; font-size: 13px;">未设置封面</p>  
                                    </div>  
                                `}  
                            </div>  
                            
                            <div style="padding: 10px; background: var(--surface-color); border-radius: 6px; font-size: 12px; color: var(--text-secondary);">  
                                <p style="margin: 0 0 6px 0; font-weight: 500;">封面尺寸要求:</p>  
                                <ul style="margin: 0; padding-left: 18px; line-height: 1.6;">  
                                    <li>推荐比例: 900×384</li>  
                                    <li>支持格式: JPG, PNG, GIF</li>  
                                </ul>  
                            </div>  
                            
                            <div style="display: flex; gap: 8px; margin-top: auto;">    
                                <button class="btn btn-secondary" id="clear-cover" style="flex: 1;" ${!currentCover ? 'disabled' : ''}>    
                                    清除封面    
                                </button>    
                                <button class="btn btn-primary" id="confirm-cover" style="flex: 1;" disabled>    
                                    确认设置    
                                </button>    
                            </div> 
                        </div>  
                        
                        <!-- 右侧: 图片选择区 -->  
                        <div style="flex: 0 0 400px; display: flex; flex-direction: column; gap: 12px;">  
                            <div style="display: flex; align-items: center; justify-content: space-between;">  
                                <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: var(--text-primary);">  
                                    选择图片 (${images.length})  
                                </h3>  
                            </div>  
                            
                            <div style="  
                                flex: 1;  
                                overflow-y: auto;  
                                border: 1px solid var(--border-color);  
                                border-radius: 8px;  
                                padding: 12px;  
                                background: var(--background-color);  
                            ">  
                                <div style="display: flex; flex-direction: column; gap: 10px;">  
                                    ${images.map(img => `  
                                        <div class="cover-option"  
                                            data-src="${img.path}"  
                                            data-filename="${img.filename}"  
                                            style="  
                                                cursor: pointer;  
                                                border: 1px solid transparent;  
                                                border-radius: 8px;  
                                                overflow: hidden;  
                                                transition: all 0.2s;  
                                                background: var(--surface-color);  
                                                display: flex;  
                                                align-items: center;  
                                                gap: 12px;  
                                                padding: 8px;  
                                                position: relative;  
                                            "  
                                            ${currentCover === img.path ? 'data-current="true"' : ''}>  
                                            <div style="  
                                                flex: 0 0 auto;  
                                                width: 120px;  
                                                height: 51px;  
                                                border-radius: 4px;  
                                                overflow: hidden;  
                                            ">  
                                                <img src="${img.path}"  
                                                    style="width: 100%; height: 100%; object-fit: cover;"  
                                                    loading="lazy" />  
                                            </div>  
                                            <div style="flex: 1; min-width: 0;">  
                                                <p style="  
                                                    margin: 0;  
                                                    font-size: 13px;  
                                                    color: var(--text-primary);  
                                                    white-space: nowrap;  
                                                    overflow: hidden;  
                                                    text-overflow: ellipsis;  
                                                " title="${img.filename}">${img.filename}</p>  
                                            </div>  
                                            ${currentCover === img.path ? `  
                                                <div class="current-badge" style="  
                                                    position: absolute;  
                                                    top: 8px;  
                                                    right: 8px;  
                                                    background: var(--primary-color);  
                                                    color: white;  
                                                    border-radius: 4px;  
                                                    padding: 2px 8px;  
                                                    font-size: 11px;  
                                                    font-weight: 600;  
                                                ">当前</div>  
                                            ` : ''}  
                                        </div>  
                                    `).join('')}  
                                </div>  
                            </div>  
                        </div>  
                    </div>  
                </div>  
            `;  
            
            document.body.appendChild(dialog);  
            requestAnimationFrame(() => dialog.classList.add('show'));  
            
            this.bindCoverDialogEvents(dialog, currentCover);  
            
        } catch (error) {  
            window.app?.showNotification('设置封面失败: ' + error.message, 'error');  
        }  
    }
    
    bindCoverDialogEvents(dialog, currentCover) {  
        // 三个关键状态  
        const originalCover = currentCover;      // 对话框打开时的原始封面(不可变)  
        let selectedImage = currentCover;        // 用户当前选中的图片  
        let hasUserSelection = false;            // 标记用户是否做过选择  
        
        const previewArea = dialog.querySelector('#current-cover-preview');  
        const confirmBtn = dialog.querySelector('#confirm-cover');  
        const clearBtn = dialog.querySelector('#clear-cover');  
        
        // 更新预览区域的辅助函数  
        const updatePreview = (imagePath) => {  
            if (imagePath) {  
                previewArea.innerHTML = `  
                    <img src="${imagePath}" style="width: 100%; height: 100%; object-fit: cover;" />  
                `;  
            } else {  
                previewArea.innerHTML = `  
                    <div style="text-align: center; color: var(--text-secondary);">  
                        <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" style="opacity: 0.3;">  
                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>  
                            <circle cx="8.5" cy="8.5" r="1.5"/>  
                            <polyline points="21 15 16 10 5 21"/>  
                        </svg>  
                        <p style="margin-top: 8px; font-size: 13px;">未设置封面</p>  
                    </div>  
                `;  
            }  
        };  
        
        // 更新按钮状态的辅助函数  
        const updateButtonStates = () => {  
            if (hasUserSelection) {  
                // 用户做过选择  
                clearBtn.textContent = originalCover ? '恢复原始' : '清空选择';  
                clearBtn.disabled = false;  
                confirmBtn.disabled = (selectedImage === originalCover);  
            } else {  
                // 用户未做选择  
                clearBtn.textContent = '清除封面';  
                clearBtn.disabled = !originalCover;  
                confirmBtn.disabled = true;  
            }  
        };  

        // 更新图片列表选中状态的辅助函数  
        const updateImageSelection = (targetPath) => {  
            dialog.querySelectorAll('.cover-option').forEach(opt => {  
                if (opt.dataset.src === targetPath) {  
                    opt.style.border = '1px solid var(--primary-color)';  
                    opt.style.boxShadow = 'none';  
                } else {  
                    opt.style.border = '1px solid transparent';  
                    opt.style.boxShadow = 'none';  
                }  
            });  
        };  
        
        // 初始化按钮状态  
        updateButtonStates();  
        
        // 图片选择事件  
        dialog.querySelectorAll('.cover-option').forEach(option => {  
            // 高亮当前封面  
            if (option.dataset.src === currentCover) {  
                option.style.border = '1px solid var(--primary-color)';  
                option.style.boxShadow = 'none';  
            }  
            
            option.addEventListener('click', () => {  
                selectedImage = option.dataset.src;  
                hasUserSelection = true;  
                
                // 更新预览  
                updatePreview(selectedImage);  
                
                // 更新选中状态  
                updateImageSelection(selectedImage);  
                
                // 更新按钮状态  
                updateButtonStates();  
            });  
            
            // 悬停效果  
            option.addEventListener('mouseenter', () => {  
                if (option.dataset.src !== selectedImage) {  
                    option.style.border = '1px solid var(--border-color)';  
                }  
            });  
            option.addEventListener('mouseleave', () => {  
                if (option.dataset.src !== selectedImage) {  
                    option.style.border = '1px solid transparent';  
                }  
            });  
        });  
        
        // 确认按钮  
        confirmBtn.addEventListener('click', async () => {    
            if (!selectedImage) return;    
            
            try {    
                console.log('正在设置封面:', selectedImage);  // 添加日志  
                
                const response = await fetch('/api/articles/config/set-cover', {    
                    method: 'POST',    
                    headers: { 'Content-Type': 'application/json' },    
                    body: JSON.stringify({ cover_path: selectedImage })    
                });    
                
                console.log('响应状态:', response.status, response.statusText);  // 添加日志  
                
                if (response.ok) {    
                    const result = await response.json();  // 获取响应内容  
                    console.log('设置成功:', result);  // 添加日志  
                    window.app?.showNotification('封面设置成功', 'success');    
                    dialog.classList.remove('show');    
                    setTimeout(() => document.body.removeChild(dialog), 300);    
                } else {    
                    // 获取详细错误信息  
                    const errorText = await response.text();    
                    console.error('设置失败 - 状态码:', response.status);    
                    console.error('设置失败 - 响应内容:', errorText);    
                    
                    let errorMessage = '设置封面失败';    
                    try {    
                        const errorJson = JSON.parse(errorText);    
                        errorMessage = errorJson.detail || errorJson.message || errorText;    
                    } catch (e) {    
                        errorMessage = errorText || `HTTP ${response.status}`;    
                    }    
                    
                    throw new Error(errorMessage);    
                }    
            } catch (error) {    
                console.error('设置封面异常:', error);  // 添加详细日志  
                window.app?.showNotification('设置封面失败: ' + error.message, 'error');    
            }    
        }); 
                
        // 清除/恢复按钮  
        clearBtn.addEventListener('click', async () => {  
            if (hasUserSelection) {  
                // 用户做过选择,恢复到原始状态  
                selectedImage = originalCover;  
                hasUserSelection = false;  
                
                // 更新预览  
                updatePreview(originalCover);  
                
                // 更新选中状态  
                updateImageSelection(originalCover);  
                
                // 更新按钮状态  
                updateButtonStates();  
                
                window.app?.showNotification(originalCover ? '已恢复到原始封面' : '已清空选择', 'info');  
            } else {  
                // 用户未做选择,调用API清除封面  
                try {  
                    const response = await fetch('/api/config/set-cover', {  
                        method: 'POST',  
                        headers: { 'Content-Type': 'application/json' },  
                        body: JSON.stringify({ cover_path: '' })  
                    });  
                    
                    if (response.ok) {  
                        // 更新预览区域  
                        updatePreview(null);  
                        
                        // 清除所有图片的选中状态  
                        dialog.querySelectorAll('.cover-option').forEach(opt => {  
                            opt.style.border = '1px solid transparent';  
                            opt.style.boxShadow = 'none';  
                            // 移除"当前"标签  
                            const currentBadge = opt.querySelector('.current-badge');  
                            if (currentBadge) {  
                                currentBadge.remove();  
                            }  
                        });  
                        
                        // 重置状态  
                        selectedImage = null;  
                        
                        // 更新按钮状态  
                        updateButtonStates();  
                        
                        window.app?.showNotification('封面已清除', 'success');  
                    } else {  
                        throw new Error('清除封面失败');  
                    }  
                } catch (error) {  
                    window.app?.showNotification('清除封面失败: ' + error.message, 'error');  
                }  
            }  
        });  
        
        // 取消按钮  
        dialog.querySelector('#cover-cancel').addEventListener('click', () => {  
            dialog.classList.remove('show');  
            setTimeout(() => document.body.removeChild(dialog), 300);  
        });  
        
        // ESC键关闭  
        const escHandler = (e) => {  
            if (e.key === 'Escape') {  
                dialog.classList.remove('show');  
                setTimeout(() => {  
                    document.body.removeChild(dialog);  
                    document.removeEventListener('keydown', escHandler);  
                }, 300);  
            }  
        };  
        document.addEventListener('keydown', escHandler);  
    }

    async getCurrentCover() {  
        try {  
            // 需要添加获取当前封面的API  
            const response = await fetch('/api/articles/config/get-cover'); 
            if (response.ok) {  
                const data = await response.json();  
                return data.cover_path || null;  
            }  
        } catch (error) {  
            console.error('获取当前封面失败:', error);  
        }  
        return null;  
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
        
        if (this.editor) {    
            try {    
                this.editor.destroy();    
            } catch (e) {    
                // 忽略销毁错误  
            }    
            this.editor = null;    
        }    
        
        if (this.dialog) {    
            this.dialog.classList.remove('show');    
            if (this.dialog.parentNode) {    
                this.dialog.parentNode.removeChild(this.dialog);    
            }    
            this.dialog = null;    
        }    
        
        this.currentArticle = null;    
        this.isDirty = false;    
        this.isClosing = false;    
    }
}  
  
document.addEventListener('DOMContentLoaded', () => {  
    window.imageDesignerDialog = new ImageDesignerDialog();
});