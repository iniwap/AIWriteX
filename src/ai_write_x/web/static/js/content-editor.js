class ContentEditorDialog {    
    constructor() {    
        this.dialog = null;    
        this.editor = null;    
        this.currentTemplate = null;  
        this.contentType = 'template'; // 标识内容类型(template/article)  
        this.currentLanguage = 'html';    
        this.originalContent = '';    
        this.isDirty = false;    
        this.previewTimer = null;    
        this.isFullscreen = false;    
        this.monacoLoaded = false;    
        this.themeObserver = null;  
        this.isClosing = false;    
        this.keydownHandler = null;    
        this.overlayClickHandler = null;    
        this.resizeHandlers = null;  
        this.isResizing = false;  
    }    
        
    async initialize() {    
        if (this.monacoLoaded) return;    
        await this.preloadMonaco();    
    }    
        
    preloadMonaco() {    
        if (typeof monaco !== 'undefined') {    
            this.monacoLoaded = true;    
            return Promise.resolve();    
        }    
          
        return new Promise((resolve, reject) => {    
            if (typeof require === 'undefined') {    
                reject(new Error('Monaco Editor loader 未加载'));    
                return;    
            }    
              
            if (!window.monacoConfigured) {    
                require.config({       
                    paths: { 'vs': '/static/lib/monaco/vs' }    
                });    
                window.monacoConfigured = true;    
            }    
              
            require(['vs/editor/editor.main'], () => {    
                this.monacoLoaded = true;    
                resolve();    
            }, reject);    
        });    
    }    
        
    async open(templatePath, templateName, contentType = 'template') {    
        await this.initialize();    
          
        this.currentTemplate = templatePath;  
        this.contentType = contentType; // 保存内容类型  
          
        const ext = templatePath.toLowerCase().split('.').pop();    
        const languageMap = {    
            'html': 'html',    
            'htm': 'html',    
            'md': 'markdown',    
            'markdown': 'markdown',    
            'txt': 'plaintext'    
        };    
        this.currentLanguage = languageMap[ext] || 'html';    
          
        this.createDialog(templateName, contentType);    
          
        document.body.appendChild(this.dialog);    
        await new Promise(resolve => requestAnimationFrame(resolve));    
        await this.initMonacoEditor();    
        await this.loadTemplate();    
        this.bindEvents();    
          
        requestAnimationFrame(() => {    
            this.dialog.classList.add('show');    
        });    
    }   
        
    createDialog(contentName, contentType = 'template') {    
        this.dialog = document.createElement('div');    
        this.dialog.className = 'content-editor-dialog';    
          
        const titleText = contentType === 'article' ? '编辑文章' : '编辑模板';    
          
        this.dialog.innerHTML = `    
            <div class="editor-container">    
                <div class="editor-header">    
                    <h2 class="editor-title">    
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor">    
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>    
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>    
                        </svg>    
                        <span>${titleText} - ${contentName}</span>    
                    </h2>   
                    <div class="editor-actions">    
                        <select class="language-selector" id="language-selector">    
                            <option value="html">HTML</option>    
                            <option value="markdown">Markdown</option>    
                            <option value="plaintext">纯文本</option>    
                        </select>    
                          
                        <button class="btn-icon" id="format-code" title="格式化代码 (Shift+Alt+F)">    
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor">    
                                <path d="M4 7h16M4 12h10M4 17h16"/>    
                            </svg>    
                        </button>    
                        <button class="btn-icon" id="toggle-fullscreen" title="全屏 (F11)">    
                            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor">    
                                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>    
                            </svg>    
                        </button>    
                        <button class="btn btn-secondary" id="cancel-edit">关闭</button>    
                        <button class="btn btn-primary" id="save-template">    
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">    
                                <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>    
                                <polyline points="17 21 17 13 7 13 7 21"/>    
                                <polyline points="7 3 7 8 15 8"/>    
                            </svg>    
                            保存 (Ctrl+S)    
                        </button>    
                    </div>    
                </div>    
                  
                <div class="panels-header">    
                    <div class="panel-header-left">    
                        <span id="language-label">HTML 代码</span>    
                        <span class="editor-status" id="editor-status">行: 1, 列: 1</span>    
                    </div>    
                    <div class="panel-header-divider"></div>    
                    <div class="panel-header-right">    
                        <span>实时预览</span>    
                        <button class="btn-icon" id="refresh-preview" title="刷新预览">    
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">    
                                <path d="M1 4v6h6M23 20v-6h-6"></path>    
                                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>    
                            </svg>    
                        </button>    
                    </div>    
                </div>    
                  
                <div class="editor-body">    
                    <div class="editor-panel">    
                        <div id="monaco-editor-container"></div>    
                    </div>    
                      
                    <div class="resize-handle" id="resize-handle"></div>    
                      
                    <div class="editor-preview-panel">    
                        <iframe id="preview-iframe" sandbox="allow-same-origin allow-scripts"></iframe>    
                    </div>    
                </div>    
            </div>    
        `;    
    }  
        
    async initMonacoEditor() {    
        const container = this.dialog.querySelector('#monaco-editor-container');    
        const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark';    
          
        this.editor = monaco.editor.create(container, {    
            language: this.currentLanguage,    
            theme: isDarkTheme ? 'vs-dark' : 'vs',    
            automaticLayout: true,    
            fontSize: 14,    
            fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",    
            lineNumbers: 'on',    
            minimap: { enabled: true },    
            scrollBeyondLastLine: false,    
            wordWrap: 'on',    
            formatOnPaste: true,    
            formatOnType: true,    
            tabSize: 2,    
            insertSpaces: true,    
            renderWhitespace: 'selection',    
            bracketPairColorization: { enabled: true },    
            guides: {    
                bracketPairs: true,    
                indentation: true    
            }    
        });    
          
        this.themeObserver = new MutationObserver((mutations) => {    
            mutations.forEach((mutation) => {    
                if (mutation.attributeName === 'data-theme') {    
                    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';    
                    monaco.editor.setTheme(isDark ? 'vs-dark' : 'vs');    
                }    
            });    
        });    
          
        this.themeObserver.observe(document.documentElement, {    
            attributes: true,    
            attributeFilter: ['data-theme']    
        });    
          
        this.editor.onDidChangeModelContent(() => {    
            const currentContent = this.editor.getValue();    
            this.isDirty = currentContent !== this.originalContent;    
            this.updatePreviewDebounced();    
        });  
              
        this.editor.onDidChangeCursorPosition((e) => {    
            const status = this.dialog.querySelector('#editor-status');    
            if (status) {    
                status.textContent = `行: ${e.position.lineNumber}, 列: ${e.position.column}`;    
            }    
        });    
    }    
        
    async loadTemplate() {    
        try {    
            if (!this.editor) {    
                throw new Error('编辑器未初始化');    
            }    
              
            // 根据内容类型选择端点  
            const apiPath = this.contentType === 'article'   
                ? `/api/articles/content?path=${encodeURIComponent(this.currentTemplate)}`  
                : `/api/templates/content/${encodeURIComponent(this.currentTemplate)}`;  
              
            const response = await fetch(apiPath);    
            if (!response.ok) throw new Error(`HTTP ${response.status}`);    
              
            const content = await response.text();    
            this.originalContent = content;    
              
            setTimeout(() => {    
                this.editor.setValue(content);    
                this.isDirty = false;    
                  
                const languageSelector = this.dialog.querySelector('#language-selector');    
                if (languageSelector) {    
                    languageSelector.value = this.currentLanguage;    
                }    
                  
                this.updateLanguageLabel();    
                  
                if (this.currentLanguage === 'html') {    
                    this.updatePreview();    
                } else if (this.currentLanguage === 'markdown') {    
                    this.updateMarkdownPreview();    
                }    
            }, 100);    
        } catch (error) {    
            const errorMsg = this.contentType === 'article' ? '加载文章失败' : '加载模板失败';  
            window.dialogManager?.showAlert(`${errorMsg}: ${error.message}`, 'error');    
        }    
    }  
        
    updatePreviewDebounced() {      
        clearTimeout(this.previewTimer);      
        this.previewTimer = setTimeout(() => {      
            if (this.currentLanguage === 'html') {      
                this.updatePreview();      
            } else if (this.currentLanguage === 'markdown') {      
                this.updateMarkdownPreview();      
            } else if (this.currentLanguage === 'plaintext') {  
                this.updatePlaintextPreview();  
            }  
        }, 300);    
    }  
        
    updatePreview() {  
        const content = this.editor.getValue();  
        const previewContainer = this.dialog.querySelector('.editor-preview-panel');  
        
        if (!previewContainer) return;  
        
        const oldIframe = previewContainer.querySelector('#preview-iframe');  
        if (oldIframe) oldIframe.remove();  
        
        const iframe = document.createElement('iframe');  
        iframe.id = 'preview-iframe';  
        iframe.sandbox = 'allow-same-origin allow-scripts';  
        
        // 获取CSS变量值  
        const computedStyle = getComputedStyle(document.documentElement);  
        const bgColor = computedStyle.getPropertyValue('--background-color').trim();  
        const borderColor = computedStyle.getPropertyValue('--border-color').trim();  
        const secondaryColor = computedStyle.getPropertyValue('--secondary-color').trim();  
        
        const styledContent = `  
            <!DOCTYPE html>  
            <html>  
            <head>  
                <meta charset="UTF-8">  
                <style>  
                    body {  
                        margin: 0;  
                        padding: 16px;  
                        overflow: auto;  
                        background: transparent;  /* 改为透明 */  
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
        
        iframe.srcdoc = styledContent;  
        previewContainer.appendChild(iframe);  
    }
            
    updateMarkdownPreview() {  
        const content = this.editor.getValue();  
        const previewContainer = this.dialog.querySelector('.editor-preview-panel');  
        
        if (!previewContainer) return;  
        
        const oldIframe = previewContainer.querySelector('#preview-iframe');  
        if (oldIframe) oldIframe.remove();  
        
        const iframe = document.createElement('iframe');  
        iframe.id = 'preview-iframe';  
        iframe.sandbox = 'allow-same-origin allow-scripts';  
        
        const htmlContent = this.markdownToHtml(content);  
        
        // 获取CSS变量值  
        const computedStyle = getComputedStyle(document.documentElement);  
        const bgColor = computedStyle.getPropertyValue('--background-color').trim();  
        const borderColor = computedStyle.getPropertyValue('--border-color').trim();  
        const secondaryColor = computedStyle.getPropertyValue('--secondary-color').trim();  
        const textColor = computedStyle.getPropertyValue('--text-primary').trim();  
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';  
        
        const styledContent = `  
            <!DOCTYPE html>  
            <html>  
            <head>  
                <meta charset="UTF-8">  
                <style>  
                    body {  
                        margin: 0;  
                        padding: 16px;  
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;  
                        line-height: 1.6;  
                        overflow: auto;  
                        color: ${textColor};  
                        background: transparent;  
                    }  
                    
                    /* Markdown内容样式 */  
                    h1, h2, h3, h4, h5, h6 {   
                        margin-top: 24px;   
                        margin-bottom: 16px;  
                        font-weight: 600;  
                        line-height: 1.25;  
                    }  
                    h1 { font-size: 2em; border-bottom: 1px solid ${borderColor}; padding-bottom: 0.3em; }  
                    h2 { font-size: 1.5em; border-bottom: 1px solid ${borderColor}; padding-bottom: 0.3em; }  
                    h3 { font-size: 1.25em; }  
                    
                    p { margin-bottom: 16px; }  
                    
                    ul, ol { padding-left: 2em; margin-bottom: 16px; }  
                    li { margin-bottom: 4px; }  
                    
                    /* 关键:添加 blockquote 样式 */  
                    blockquote {  
                        margin: 0 0 16px 0;  
                        padding: 0 1em;  
                        color: #6a737d;  
                        border-left: 4px solid ${borderColor};  
                    }  
                    
                    code {  
                        background: ${isDark ? '#2d2d2d' : '#f6f8fa'};  
                        padding: 2px 6px;  
                        border-radius: 3px;  
                        font-family: 'Consolas', 'Monaco', monospace;  
                        font-size: 85%;  
                    }  
                    
                    pre {  
                        background: ${isDark ? '#2d2d2d' : '#f6f8fa'};  
                        padding: 16px;  
                        border-radius: 6px;  
                        overflow-x: auto;  
                        margin-bottom: 16px;  
                    }  
                    
                    pre code {  
                        background: none;  
                        padding: 0;  
                    }  
                    
                    table {  
                        border-collapse: collapse;  
                        width: 100%;  
                        margin-bottom: 16px;  
                    }  
                    
                    table th, table td {  
                        padding: 6px 13px;  
                        border: 1px solid ${borderColor};  
                    }  
                    
                    table th {  
                        background: ${isDark ? '#2d2d2d' : '#f6f8fa'};  
                        font-weight: 600;  
                    }  
                    
                    img {  
                        max-width: 100%;  
                        height: auto;  
                    }  
                    
                    a {  
                        color: #0366d6;  
                        text-decoration: none;  
                    }  
                    
                    a:hover {  
                        text-decoration: underline;  
                    }  
                    
                    hr {  
                        height: 0.25em;  
                        padding: 0;  
                        margin: 24px 0;  
                        background-color: ${borderColor};  
                        border: 0;  
                    }  
                    
                    /* 滚动条样式 */  
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
                ${htmlContent}  
            </body>  
            </html>  
        `;  
        
        iframe.srcdoc = styledContent;  
        previewContainer.appendChild(iframe);  
    }

    updatePlaintextPreview() {  
        const content = this.editor.getValue();  
        const previewContainer = this.dialog.querySelector('.editor-preview-panel');  
        
        if (!previewContainer) return;  
        
        const oldIframe = previewContainer.querySelector('#preview-iframe');  
        if (oldIframe) oldIframe.remove();  
        
        const iframe = document.createElement('iframe');  
        iframe.id = 'preview-iframe';  
        iframe.sandbox = 'allow-same-origin allow-scripts';  
        
        // 获取CSS变量值  
        const computedStyle = getComputedStyle(document.documentElement);  
        const bgColor = computedStyle.getPropertyValue('--background-color').trim();  
        const borderColor = computedStyle.getPropertyValue('--border-color').trim();  
        const secondaryColor = computedStyle.getPropertyValue('--secondary-color').trim();  
        const textColor = computedStyle.getPropertyValue('--text-primary').trim();  
        
        // 将纯文本转换为HTML段落  
        const txtHtml = content.split('\n')  
            .map(line => line.trim() ? `<p>${line}</p>` : '<br>')  
            .join('\n');  
        
        const styledContent = `  
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
                        background: transparent;  /* 改为透明 */  
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;  
                        line-height: 1.6;  
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
                ${txtHtml}  
            </body>  
            </html>  
        `;  
        
        iframe.srcdoc = styledContent;  
        previewContainer.appendChild(iframe);  
    }

    markdownToHtml(markdown) {  
        // 使用marked.js进行完整的Markdown渲染  
        if (window.markdownRenderer) {  
            return window.markdownRenderer.render(markdown);  
        }  
        
        // 降级到原有的简单实现  
        return markdown  
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')  
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')  
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')  
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')  
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')  
            .replace(/`(.*?)`/gim, '<code>$1</code>')  
            .replace(/\n/gim, '<br>');  
    }    
        
    bindEvents() {    
        const saveBtn = this.dialog.querySelector('#save-template');    
        if (saveBtn) {    
            saveBtn.addEventListener('click', () => this.saveContent());    
        }    
          
        const cancelBtn = this.dialog.querySelector('#cancel-edit');    
        if (cancelBtn) {    
            cancelBtn.addEventListener('click', () => this.close());    
        }    
          
        const formatBtn = this.dialog.querySelector('#format-code');    
        if (formatBtn) {    
            formatBtn.addEventListener('click', () => {    
                this.editor.getAction('editor.action.formatDocument').run();    
            });    
        }    
          
        const fullscreenBtn = this.dialog.querySelector('#toggle-fullscreen');    
        if (fullscreenBtn) {    
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());    
        }    
          
        const refreshBtn = this.dialog.querySelector('#refresh-preview');    
        if (refreshBtn) {    
            refreshBtn.addEventListener('click', () => {    
                if (this.currentLanguage === 'html') {    
                    this.updatePreview();    
                } else if (this.currentLanguage === 'markdown') {    
                    this.updateMarkdownPreview();    
                }    
            });    
        }    
          
        const languageSelector = this.dialog.querySelector('#language-selector');    
        if (languageSelector) {    
            languageSelector.value = this.currentLanguage;    
            languageSelector.addEventListener('change', (e) => {    
                this.switchLanguage(e.target.value);    
            });    
        }    
          
        this.initResizeHandle();    
          
        this.keydownHandler = this.handleKeydown.bind(this);    
        document.addEventListener('keydown', this.keydownHandler);    
          
        this.overlayClickHandler = (e) => {    
            if (e.target === this.dialog && !this.isClosing) {    
                this.close();    
            }    
        };    
        this.dialog.addEventListener('click', this.overlayClickHandler);    
    }  
      
    initResizeHandle() {    
        const handle = this.dialog.querySelector('#resize-handle');    
        const editorPanel = this.dialog.querySelector('.editor-panel');    
        const previewPanel = this.dialog.querySelector('.editor-preview-panel');    
        const panelHeaderLeft = this.dialog.querySelector('.panel-header-left');    
        const panelHeaderRight = this.dialog.querySelector('.panel-header-right');    
          
        if (!handle || !editorPanel || !previewPanel) return;    
          
        let startX = 0;    
        let startEditorWidth = 0;    
        let startPreviewWidth = 0;    
      
        const handleMouseDown = (e) => {    
            if (e.button !== 0) return;    
              
            if (this.isResizing) {    
                this.stopResizing();    
                return;    
            }    
              
            this.isResizing = true;    
            startX = e.clientX;    
            startEditorWidth = editorPanel.offsetWidth;    
            startPreviewWidth = previewPanel.offsetWidth;    
            document.body.style.cursor = 'col-resize';    
            document.body.style.userSelect = 'none';    
              
            const iframe = this.dialog.querySelector('#preview-iframe');    
            if (iframe) {    
                iframe.style.pointerEvents = 'none';    
            }    
              
            e.preventDefault();    
            e.stopPropagation();    
        };    
      
        const handleMouseMove = (e) => {    
            if (!this.isResizing) return;    
              
            e.preventDefault();    
            e.stopPropagation();    
              
            const delta = e.clientX - startX;    
            const newEditorWidth = startEditorWidth + delta;    
            const newPreviewWidth = startPreviewWidth - delta;    
            const minWidth = 50;    
              
            if (newEditorWidth >= minWidth && newPreviewWidth >= minWidth) {    
                editorPanel.style.width = `${newEditorWidth}px`;    
                editorPanel.style.flex = 'none';    
                editorPanel.style.maxWidth = 'none';    
                  
                previewPanel.style.width = `${newPreviewWidth}px`;    
                previewPanel.style.flex = 'none';    
                  
                if (panelHeaderLeft) {    
                    panelHeaderLeft.style.width = `${newEditorWidth}px`;    
                    panelHeaderLeft.style.flex = 'none';    
                    panelHeaderLeft.style.minWidth = 'unset';    
                }    
                  
                if (panelHeaderRight) {    
                    panelHeaderRight.style.width = `${newPreviewWidth}px`;    
                    panelHeaderRight.style.flex = 'none';    
                }    
            }    
        };    
      
        const stopResizing = () => {    
            if (!this.isResizing) return;    
              
            this.isResizing = false;    
            document.body.style.cursor = '';    
            document.body.style.userSelect = '';    
              
            const iframe = this.dialog.querySelector('#preview-iframe');    
            if (iframe) {    
                iframe.style.pointerEvents = '';    
            }    
        };    
          
        this.stopResizing = stopResizing;    
      
        const handleMouseUp = (e) => {    
            stopResizing();    
        };    
      
        const handleMouseLeave = (e) => {    
            if (e.target === document.body) {    
                stopResizing();    
            }    
        };    
      
        handle.addEventListener('mousedown', handleMouseDown);    
        document.addEventListener('mousemove', handleMouseMove);    
        document.addEventListener('mouseup', handleMouseUp);    
        document.addEventListener('mouseleave', handleMouseLeave);    
          
        this.resizeHandlers = {    
            handle: handle,    
            mouseDown: handleMouseDown,    
            mouseMove: handleMouseMove,    
            mouseUp: handleMouseUp,    
            mouseLeave: handleMouseLeave    
        };    
    }  
  
    switchLanguage(language) {      
        this.currentLanguage = language;      
            
        const model = this.editor.getModel();      
        monaco.editor.setModelLanguage(model, language);      
            
        this.updateLanguageLabel();      
            
        const previewPanel = this.dialog.querySelector('.editor-preview-panel');      
            
        if (language === 'html') {      
            if (previewPanel) previewPanel.style.display = '';      
            this.updatePreview();      
        } else if (language === 'markdown') {      
            if (previewPanel) previewPanel.style.display = '';      
            this.updateMarkdownPreview();      
        } else if (language === 'plaintext') {  
            if (previewPanel) previewPanel.style.display = '';  
            this.updatePlaintextPreview();  
        } else {      
            if (previewPanel) previewPanel.style.display = 'none';      
        }      
    } 
      
    updateLanguageLabel() {    
        const languageLabel = this.dialog.querySelector('#language-label');    
        const labelMap = {    
            'html': 'HTML 代码',    
            'markdown': 'Markdown 文档',    
            'plaintext': '纯文本'    
        };    
        if (languageLabel) {    
            languageLabel.textContent = labelMap[this.currentLanguage] || '代码';    
        }    
    }  
        
    handleKeydown(e) {    
        if (!this.dialog || !this.dialog.classList.contains('show')) return;    
            
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {    
            e.preventDefault();    
            this.saveContent();    
        }    
            
        if (e.key === 'Escape') {    
            e.preventDefault();    
            this.close();    
        }    
            
        if (e.key === 'F11') {    
            e.preventDefault();    
            this.toggleFullscreen();    
        }    
    }    
        
    toggleFullscreen() {    
        this.isFullscreen = !this.isFullscreen;    
        this.dialog.classList.toggle('fullscreen', this.isFullscreen);    
            
        const icon = this.dialog.querySelector('#toggle-fullscreen svg');    
        if (this.isFullscreen) {    
            icon.innerHTML = `    
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>    
            `;    
        } else {    
            icon.innerHTML = `    
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>    
            `;    
        }    
    }    
        
    async saveContent() {      
        const content = this.editor.getValue();        
        const saveBtn = this.dialog.querySelector('#save-template');        
                
        try {        
            saveBtn.disabled = true;        
            saveBtn.textContent = '保存中...';        
                
            // 修改为查询参数格式    
            const apiPath = this.contentType === 'article'       
                ? `/api/articles/content?path=${encodeURIComponent(this.currentTemplate)}`      
                : `/api/templates/content/${encodeURIComponent(this.currentTemplate)}`;      
                    
            const response = await fetch(apiPath, {        
                method: 'PUT',        
                headers: { 'Content-Type': 'application/json' },        
                body: JSON.stringify({ content })        
            });        
                    
            if (response.ok) {        
                this.originalContent = content;      
                this.isDirty = false;        
                    
                const successMsg = this.contentType === 'article' ? '文章已保存' : '模板已保存';      
                window.app?.showNotification(successMsg, 'success');        
                        
                // 刷新列表视图  
                if (this.contentType === 'article' && window.articleManager) {        
                    await window.articleManager.loadArticles();        
                } else if (this.contentType === 'template' && window.templateManager) {        
                    await window.templateManager.loadTemplates(window.templateManager.currentCategory);        
                    window.templateManager.renderTemplateGrid();        
                }  
                
                // 自动刷新预览面板(如果预览面板打开且有文章信息)  
                if (window.previewPanelManager &&   
                    window.previewPanelManager.isVisible &&   
                    window.previewPanelManager.currentArticleInfo) {  
                    
                    try {  
                        // 重新获取保存后的内容  
                        const contentResponse = await fetch(apiPath);  
                        if (contentResponse.ok) {  
                            const updatedContent = await contentResponse.text();  
                            
                            // 根据文件类型处理内容  
                            const ext = this.currentTemplate.toLowerCase().split('.').pop();  
                            let htmlContent = updatedContent;  
                            
                            if ((ext === 'md' || ext === 'markdown') && window.markdownRenderer) {  
                                const isDark = document.documentElement.getAttribute('data-theme') === 'dark';  
                                htmlContent = window.markdownRenderer.renderWithStyles(updatedContent, isDark);  
                            }  
                            
                            // 刷新预览内容(不改变 currentArticleInfo)  
                            window.previewPanelManager.setContent(htmlContent);  
                        }  
                    } catch (error) {  
                        console.error('刷新预览失败:', error);  
                        // 静默失败,不影响保存流程  
                    }  
                }  
            } else {        
                const error = await response.json();     
                window.dialogManager?.showAlert('保存失败: ' + (error.detail || '未知错误'), 'error');        
            }        
        } catch (error) {        
            window.dialogManager?.showAlert('保存失败: ' + error.message, 'error');        
        } finally {        
            saveBtn.disabled = false;        
            saveBtn.innerHTML = `        
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">        
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>        
                    <polyline points="17 21 17 13 7 13 7 21"/>        
                    <polyline points="7 3 7 8 15 8"/>        
                </svg>        
                保存 (Ctrl+S)        
            `;        
        }       
    }
          
    close() {        
        // 防止重入        
        if (this.isClosing) {        
            return;        
        }        
          
        if (this.isDirty) {        
            this.isClosing = true;        
              
            // 临时移除遮罩点击事件,防止重复触发        
            if (this.overlayClickHandler && this.dialog) {        
                this.dialog.removeEventListener('click', this.overlayClickHandler);        
            }        
              
            window.dialogManager.showConfirm(        
                '有未保存的修改,确认关闭?',        
                () => {        
                    this.destroy();        
                },        
                () => {        
                    // 取消时重新绑定遮罩点击事件,使用 setTimeout 确保在对话框关闭后执行    
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
          
        // 清理resize事件监听器    
        if (this.resizeHandlers) {    
            const { handle, mouseDown, mouseMove, mouseUp, mouseLeave } = this.resizeHandlers;    
            if (handle && mouseDown) {    
                handle.removeEventListener('mousedown', mouseDown);    
            }    
            document.removeEventListener('mousemove', mouseMove);    
            document.removeEventListener('mouseup', mouseUp);    
            document.removeEventListener('mouseleave', mouseLeave);    
            this.resizeHandlers = null;    
        }    
          
        // 确保停止拖动并重置状态    
        if (this.stopResizing) {    
            this.stopResizing();    
        }    
        this.isResizing = false;    
          
        if (this.themeObserver) {    
            this.themeObserver.disconnect();    
            this.themeObserver = null;    
        }    
          
        if (this.editor) {    
            this.editor.dispose();    
            this.editor = null;    
        }    
          
        if (this.dialog && this.dialog.parentNode) {    
            this.dialog.parentNode.removeChild(this.dialog);    
        }    
          
        this.dialog = null;    
        this.currentTemplate = null;    
        this.isDirty = false;    
        this.isClosing = false;    
    }  
}    
    
document.addEventListener('DOMContentLoaded', () => {    
    window.contentEditorDialog = new ContentEditorDialog();    
});