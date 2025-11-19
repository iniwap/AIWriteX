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
                            保存 (Ctrl+S)     
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
            // 1. 尝试加载页面设计配置  
            let pageDesign = null;  
            try {  
                const configResponse = await fetch('/api/config/page-design');  
                if (configResponse.ok) {  
                    pageDesign = await configResponse.json();  
                }  
            } catch (error) {  
                console.warn('加载页面设计配置失败,使用原始HTML样式:', error);  
            }  
            
            // 2. 加载HTML内容  
            const designResponse = await fetch(`/api/articles/design?article=${encodeURIComponent(this.currentArticle)}`);  
            if (designResponse.ok) {  
                const data = await designResponse.json();  
                if (data.html) {  
                    this.editor.setComponents(data.html);  
                    this.editor.setStyle(data.css);  
                    this.isDirty = false;  
                    
                    // 3. 只有在配置存在且未启用原始样式时才应用全局样式  
                    if (pageDesign && !pageDesign.use_original_styles) {  
                        this.applyGlobalStyles(pageDesign);  
                    }  
                    return;  
                }  
            }  
            
            // 4. 加载原始HTML  
            const contentResponse = await fetch(`/api/articles/content?path=${encodeURIComponent(this.currentArticle)}`);  
            if (contentResponse.ok) {  
                const htmlContent = await contentResponse.text();  
                this.editor.setComponents(htmlContent);  
                this.isDirty = false;  
                
                // 5. 同样的逻辑:只有在配置存在且未启用原始样式时才应用  
                if (pageDesign && !pageDesign.use_original_styles) {  
                    this.applyGlobalStyles(pageDesign);  
                }  
            }  
        } catch (error) {  
            console.error('加载设计失败:', error);  
        }  
    }
    
    applyGlobalStyles(config) {  
        const canvas = this.editor.Canvas.getDocument();  
        if (!canvas) return;  
        
        const container = config.container || {};  
        const card = config.card || {};  
        const typography = config.typography || {};  
        const spacing = config.spacing || {};  
        const accent = config.accent || {};  
        
        // 创建或更新全局样式标签  
        let styleTag = canvas.getElementById('page-design-global-styles');  
        if (!styleTag) {  
            styleTag = canvas.createElement('style');  
            styleTag.id = 'page-design-global-styles';  
            canvas.head.appendChild(styleTag);  
        }  
        
        // 生成CSS规则  
        styleTag.textContent = `  
            /* 页面容器样式 */  
            body {  
                max-width: ${container.max_width || 750}px !important;  
                margin: 0 auto !important;  
                background-color: ${container.background_color || '#f8f9fa'} !important;  
                font-size: ${typography.base_font_size || 16}px !important;  
                line-height: ${typography.line_height || 1.6} !important;  
                color: ${typography.text_color || '#333333'} !important;  
            }  
            
            /* 卡片样式 */  
            section {  
                margin-left: ${container.margin_horizontal || 10}px !important;  
                margin-right: ${container.margin_horizontal || 10}px !important;  
                margin-top: ${spacing.section_margin || 24}px !important;  
                margin-bottom: ${spacing.section_margin || 24}px !important;  
                border-radius: ${card.border_radius || 12}px !important;  
                box-shadow: ${card.box_shadow || '0 4px 16px rgba(0,0,0,0.06)'} !important;  
                background-color: ${card.background_color || '#ffffff'} !important;  
            }  
            
            /* 卡片内部padding */  
            section > div {  
                padding: ${card.padding || 24}px !important;  
            }  
            
            /* 标题样式 */  
            h1, h2, h3, h4, h5, h6 {  
                color: ${typography.heading_color || '#333333'} !important;  
            }  
            
            h1 {  
                font-size: ${(typography.base_font_size || 16) * (typography.heading_scale || 1.5)}px !important;  
            }  
            
            h2 {  
                font-size: ${(typography.base_font_size || 16) * (typography.heading_scale || 1.5) * 0.9}px !important;  
            }  
            
            /* 段落间距 */  
            p {  
                margin-bottom: ${spacing.element_margin || 16}px !important;  
                color: ${typography.text_color || '#333333'} !important;  
            }  
            
            /* 色彩强调 - 顶部色条 */  
            section > div:first-child[style*="height: 8px"] {  
                background-color: ${accent.primary_color || '#3a7bd5'} !important;  
            }  
            
            /* SVG图标颜色 */  
            svg {  
                fill: ${accent.primary_color || '#3a7bd5'} !important;  
            }  
            
            /* 高亮区块背景 */  
            div[style*="background-color: #f0f7ff"],  
            div[style*="background-color: #fff4f0"],  
            div[style*="background-color: #f0f0ff"],  
            div[style*="background-color: #faf5ff"] {  
                background-color: ${accent.highlight_bg || '#f0f7ff'} !important;  
            }  
        `;  
    }  

    async saveDesign() {    
        const bodyHtml = this.editor.getHtml();    
        const css = this.editor.getCss();    
        
        // 检测原始文件格式  
        const ext = this.currentArticle.toLowerCase().split('.').pop();  
        const isHtmlFile = (ext === 'html' || ext === 'htm');  
        
        let finalContent;  
        
        if (isHtmlFile) {  
            // HTML 文件: 生成完整文档  
            const inlinedHtml = this.inlineCssToHtml(bodyHtml, css);    
            
            finalContent = `<!DOCTYPE html>    
    <html lang="zh-CN">    
    <head>    
        <meta charset="UTF-8">    
        <meta name="viewport" content="width=device-width, initial-scale=1.0">    
    </head>    
    <body>    
        ${inlinedHtml}    
    </body>    
    </html>`;  
        } else {  
            // Markdown/TXT 文件: 移除 body 标签,只保存内部内容  
            let content = bodyHtml;  
            
            // 移除开头的 <body> 标签  
            content = content.replace(/^<body[^>]*>/i, '');  
            
            // 移除结尾的 </body> 标签  
            content = content.replace(/<\/body>$/i, '');  
            
            finalContent = content.trim();  
        }  
                
        try {      
            // 读取现有封面设置  
            let existingCover = "";  
            
            try {  
                const existingDesignResponse = await fetch(`/api/articles/design?article=${encodeURIComponent(this.currentArticle)}`);  
                if (existingDesignResponse.ok) {  
                    const existingData = await existingDesignResponse.json();  
                    existingCover = existingData.cover || "";  
                }  
            } catch (e) {  
                console.warn('读取现有封面失败,将使用空值:', e);  
            }  
            
            // 保存设计数据  
            const designResponse = await fetch('/api/articles/design', {      
                method: 'POST',      
                headers: { 'Content-Type': 'application/json' },      
                body: JSON.stringify({      
                    article: this.currentArticle,      
                    html: bodyHtml,  
                    css: css,  
                    cover: existingCover  
                })      
            });      
            
            if (!designResponse.ok) {    
                throw new Error('保存设计数据失败');    
            }    
            
            // 更新原始文件  
            const contentResponse = await fetch(`/api/articles/content?path=${encodeURIComponent(this.currentArticle)}`, {    
                method: 'PUT',    
                headers: { 'Content-Type': 'application/json' },    
                body: JSON.stringify({     
                    content: finalContent  // 根据格式使用不同的内容  
                })    
            });    
            
            if (!contentResponse.ok) {    
                throw new Error('更新原始文件失败');    
            }    
            
            this.isDirty = false;      
            window.app?.showNotification('设计已保存', 'success');      
            
            if (window.articleManager) {    
                await window.articleManager.loadArticles();    
            }   

            // 刷新预览面板  
            if (window.previewPanelManager && window.previewPanelManager.isVisible) {  
                try {  
                    // 重新获取文章内容  
                    const response = await fetch(`/api/articles/content?path=${encodeURIComponent(this.currentArticle)}`);  
                    if (response.ok) {  
                        const htmlContent = await response.text();  
                        
                        // 使用 setContent() 而不是 show(),避免重置面板状态  
                        window.previewPanelManager.setContent(htmlContent);  
                    }  
                } catch (error) {  
                    console.error('刷新预览失败:', error);  
                    // 静默失败,不影响保存流程  
                }  
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
        
        // ESC键关闭 + Ctrl+S保存    
        this.keydownHandler = (e) => {    
            // 只在对话框显示时响应    
            if (!this.dialog || !this.dialog.classList.contains('show')) return;    
            
            // Ctrl+S 或 Cmd+S 保存    
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {    
                e.preventDefault();    
                this.saveDesign();    
            }    
            
            // ESC 关闭    
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
                                <button class="btn btn-secondary" id="clear-cover" style="flex: 1;">          
                                    清除封面          
                                </button>    
                                <button class="btn btn-secondary" id="restore-cover" style="flex: 1;">          
                                    恢复原始          
                                </button>          
                                <button class="btn btn-primary" id="confirm-cover" style="flex: 1;">          
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
        // 状态管理  
        let originalCover = currentCover;      // 对话框打开时的原始封面(不可变)          
        let selectedImage = currentCover;        // 用户当前选中的图片(前端临时状态)          
        
        const previewArea = dialog.querySelector('#current-cover-preview');          
        const confirmBtn = dialog.querySelector('#confirm-cover');          
        const clearBtn = dialog.querySelector('#clear-cover');        
        const restoreBtn = dialog.querySelector('#restore-cover');        
        
        // 更新预览区域      
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
        
        // 更新按钮状态 - 修正后的逻辑    
        const updateButtonStates = () => {            
            // 清除按钮: 只有当前选中的图片不为空时才启用  
            // 逻辑: 清除的是前端显示,如果已经是空的就不需要清除  
            clearBtn.disabled = !selectedImage;        
            
            // 恢复按钮: 只有当前选择与原始不同时才启用    
            // 逻辑: 如果当前选择和原始一样,恢复没有意义    
            restoreBtn.disabled = (selectedImage === originalCover);          
            
            // 确认按钮: 只有当前选择与原始不同时才启用    
            // 逻辑: 只有修改了封面设置才需要确认保存    
            confirmBtn.disabled = (selectedImage === originalCover);          
        };           
        
        // 更新图片列表选中状态          
        const updateImageSelection = (targetPath) => {              
            dialog.querySelectorAll('.cover-option').forEach(opt => {            
                const badge = opt.querySelector('.current-badge');            
                
                if (opt.dataset.src === targetPath) {              
                    // 选中当前图片  
                    opt.style.border = '1px solid var(--primary-color)';            
                    
                    // 关键修复: 只有当选中的图片是原始封面时才显示"当前"标志        
                    if (targetPath === originalCover) {  
                        if (badge) {  
                            badge.style.display = 'block';  
                        }  
                    } else {  
                        // 选中的不是原始封面,隐藏"当前"标志  
                        if (badge) {  
                            badge.style.display = 'none';  
                        }  
                    }  
                } else {              
                    // 未选中的图片  
                    opt.style.border = '1px solid transparent';            
                    
                    // 隐藏其他图片的"当前"标志        
                    if (badge) {            
                        badge.style.display = 'none';            
                    }            
                }              
            });              
        };        
                    
        // 关键: 立即初始化按钮状态    
        updateButtonStates();        
        updateImageSelection(selectedImage);        
        
        // 图片选择事件 - 只更新前端状态,不保存          
        dialog.querySelectorAll('.cover-option').forEach(option => {          
            // 初始高亮当前封面      
            if (option.dataset.src === currentCover) {          
                option.style.border = '1px solid var(--primary-color)';        
            }          
            
            option.addEventListener('click', () => {          
                selectedImage = option.dataset.src;          
                updatePreview(selectedImage);          
                updateImageSelection(selectedImage);          
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
        
        // 清除按钮 - 只清空前端显示,不保存    
        clearBtn.addEventListener('click', () => {              
            selectedImage = null;          
            updatePreview(null);          
            updateImageSelection(null);  // 这会隐藏所有"当前"标志  
            updateButtonStates();          
            window.app?.showNotification('已清空封面选择(未保存)', 'info');          
        });    
        
        // 恢复按钮 - 恢复到原始状态,不保存        
        restoreBtn.addEventListener('click', () => {            
            selectedImage = originalCover;            
            updatePreview(originalCover);            
            updateImageSelection(originalCover);  // 如果 originalCover 存在,会显示"当前"标志  
            updateButtonStates();            
            window.app?.showNotification(originalCover ? '已恢复到原始封面(未保存)' : '已恢复到未设置状态(未保存)', 'info');            
        });      
        
        // 确认按钮 - 保存当前选择到后端        
        confirmBtn.addEventListener('click', async () => {              
            if (!selectedImage) return;              
            
            try {              
                const designResponse = await fetch(`/api/articles/design?article=${encodeURIComponent(this.currentArticle)}`);              
                const designResult = await designResponse.json();              
                const designData = designResult || { html: "", css: "", cover: "" };              
                
                designData.cover = selectedImage;              
                designData.article = this.currentArticle;              
                
                const response = await fetch('/api/articles/design', {              
                    method: 'POST',              
                    headers: { 'Content-Type': 'application/json' },              
                    body: JSON.stringify(designData)              
                });              
                
                if (response.ok) {    
                    // 移除所有旧的"当前"标志    
                    dialog.querySelectorAll('.current-badge').forEach(badge => {    
                        badge.remove();    
                    });    
                    
                    // 在新选中的图片上添加"当前"标志    
                    if (selectedImage) {    
                        const selectedOption = dialog.querySelector(`.cover-option[data-src="${selectedImage}"]`);    
                        if (selectedOption && !selectedOption.querySelector('.current-badge')) {    
                            const badge = document.createElement('div');    
                            badge.className = 'current-badge';    
                            badge.style.cssText = `    
                                position: absolute;    
                                top: 8px;    
                                right: 8px;    
                                background: var(--primary-color);    
                                color: white;    
                                border-radius: 4px;    
                                padding: 2px 8px;    
                                font-size: 11px;    
                                font-weight: 600;    
                            `;    
                            badge.textContent = '当前';    
                            selectedOption.appendChild(badge);    
                        }    
                    }  
                    
                    originalCover = selectedImage;  
                    
                    updateButtonStates();  

                    window.app?.showNotification('封面设置成功', 'success');       
                } else {              
                    throw new Error('设置封面失败');              
                }              
            } catch (error) {              
                console.error('设置封面异常:', error);              
                window.app?.showNotification('设置封面失败: ' + error.message, 'error');              
            }              
        }); 
        
        // 取消和 ESC 键处理    
        dialog.querySelector('#cover-cancel').addEventListener('click', () => {          
            dialog.classList.remove('show');          
            setTimeout(() => document.body.removeChild(dialog), 300);          
        });          
        
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
            const response = await fetch(`/api/articles/design?article=${encodeURIComponent(this.currentArticle)}`); 
            if (response.ok) {  
                const data = await response.json();  
                return data.cover || null;  
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