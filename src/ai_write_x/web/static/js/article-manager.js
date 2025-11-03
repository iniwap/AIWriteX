// 文章管理器类  
class ArticleManager {  
    constructor() {  
        this.articles = [];  
        this.filteredArticles = [];  
        this.currentStatus = 'all';  
        this.currentLayout = 'grid';  
        this.batchMode = false;  
        this.selectedArticles = new Set();  
        this.observer = null;  
        this.publishingArticles = [];  
        this.platforms = null;
        this.platformAccounts = {};
        this.initialized = false;
        
        this.init();  
    }  
        
    async init() {  
        if (this.initialized) {  
            await this.loadArticles();  
            this.renderStatusTree();            
            if (this.observer) {  
                const cards = document.querySelectorAll('.content-card');  
                cards.forEach(card => {  
                    if (card.querySelector('iframe[data-loaded="true"]')) {  
                        return;  
                    }  
                    this.observer.observe(card);  
                });  
            }  
            return;  
        }  
        
        // 首次初始化逻辑  
        await this.loadArticles();  
        this.renderStatusTree();   
        this.bindEvents();  
        this.initIntersectionObserver();  
        this.loadPlatforms().catch(err => {  
            console.error('加载平台列表失败:', err);  
        });  
        this.initialized = true;  
    }
    
    // 加载平台列表(仅初始化时调用一次)  
    async loadPlatforms() {  
        try {  
            const response = await fetch('/api/config/platforms');  
            if (response.ok) {  
                const result = await response.json();  
                this.platforms = result.data || [];  
            }  
        } catch (error) {  
            console.error('加载平台列表失败:', error);  
        }  
    }

    // 加载文章列表  
    async loadArticles() {    
        try {    
            const response = await fetch('/api/articles');    
            if (response.ok) {    
                const result = await response.json();  
                // 与模板管理保持一致,提取 data 字段  
                this.articles = result.data || [];  
                this.filterArticles();    
            }    
        } catch (error) {    
            console.error('加载文章失败:', error);    
            this.showNotification('加载文章失败', 'error');    
        }    
    }  
        
    // 渲染状态分类树  
    renderStatusTree() {  
        const statusTree = document.getElementById('article-sidebar-tree');  
        if (!statusTree) return;  
          
        const statusCounts = {  
            all: this.articles.length,  
            published: this.articles.filter(a => a.status === 'published').length,  
            failed: this.articles.filter(a => a.status === 'failed').length,  
            unpublished: this.articles.filter(a => a.status === 'unpublished').length  
        };  
          
        const statuses = [  
            {   
                key:'all',   
                label: '全部文章',   
                icon: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>  
                    <polyline points="14,2 14,8 20,8"/>  
                </svg>`  
            },  
            {   
                key: 'published',   
                label: '已发布',   
                icon: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>  
                    <polyline points="22 4 12 14.01 9 11.01"/>  
                </svg>`  
            },  
            {   
                key: 'failed',   
                label: '发布失败',   
                icon: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                    <circle cx="12" cy="12" r="10"/>  
                    <line x1="15" y1="9" x2="9" y2="15"/>  
                    <line x1="9" y1="9" x2="15" y2="15"/>  
                </svg>`  
            },  
            {   
                key: 'unpublished',   
                label: '未发布',   
                icon: `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                    <circle cx="12" cy="12" r="10"/>  
                    <line x1="8" y1="12" x2="16" y2="12"/>  
                </svg>`  
            }  
        ];  
        
        statusTree.innerHTML = statuses.map(status => `  
            <div class="tree-item ${this.currentStatus === status.key ? 'active' : ''}"   
                data-status="${status.key}">  
                <div>  
                    <span class="tree-icon">${status.icon}</span>  
                    <span>${status.label}</span>  
                </div>  
                <span class="item-count">${statusCounts[status.key]}</span>  
            </div>  
        `).join('');  
    }  
  
    // 过滤文章  
    filterArticles() {  
        if (this.currentStatus === 'all') {  
            this.filteredArticles = [...this.articles];  
        } else {  
            this.filteredArticles = this.articles.filter(  
                article => article.status === this.currentStatus  
            );  
        }  
        this.renderArticles();  
    }  
    
    // 渲染文章卡片  
    renderArticles() {    
        const grid = document.getElementById('article-content-grid');    
        if (!grid) return;    
        
        grid.className = `content-grid ${this.currentLayout === 'list' ? 'list-view' : ''}`;    
        
        // 添加空状态判断  
        if (this.filteredArticles.length === 0) {    
            grid.innerHTML = '<div class="empty-state">暂无文章</div>';    
            return;    
        }  
        
        grid.innerHTML = '';    
        
        this.filteredArticles.forEach(article => {    
            const card = this.createArticleCard(article);    
            grid.appendChild(card);    
        });    
        
        this.bindCardEvents();    
        
        requestAnimationFrame(() => {  
            if (this.observer) {    
                const cards = grid.querySelectorAll('.content-card');    
                cards.forEach(card => this.observer.observe(card));    
            }  
        });  
    } 
    
    // 创建文章卡片  
    createArticleCard(article) {  
        const card = document.createElement('div');  
        card.className = `content-card article-card ${this.batchMode ? 'batch-mode' : ''}`;
        card.dataset.path = article.path;  
        card.dataset.title = article.title;  
        
        const statusClass = {  
            'published': 'published',  
            'failed': 'failed',  
            'unpublished': 'unpublished'  
        }[article.status] || 'unpublished';  
        
        const statusText = {  
            'published': '已发布',  
            'failed': '发布失败',  
            'unpublished': '未发布'  
        }[article.status] || '未发布';  
        
        // 时间格式化函数  
        const formatTime = (timeStr) => {  
            const date = new Date(timeStr);  
            const today = new Date();  
            const diffDays = Math.floor((today - date) / (1000 * 60 * 60 * 24));  
            
            if (diffDays === 0) return '今天';  
            if (diffDays === 1) return '昨天';  
            if (diffDays < 7) return `${diffDays}天前`;  
            return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });  
        };  
        
        card.innerHTML = `  
            <input type="checkbox" class="batch-checkbox" ${this.selectedArticles.has(article.path) ? 'checked' : ''}>  
            <div class="card-preview">  
                <iframe sandbox="allow-same-origin allow-scripts"   
                        loading="lazy"   
                        data-article-path="${article.path}"  
                        data-loaded="false"></iframe>  
                <div class="preview-loading">加载中...</div>  
            </div>  
            <div class="card-content">  
                <h4 class="card-title" title="${this.escapeHtml(article.title)}">${this.escapeHtml(article.title)}</h4>  
                <div class="card-meta">  
                    <span class="format-badge">${article.format}</span>  
                    <span class="meta-divider">•</span>  
                    <span class="status-badge ${statusClass}"     
                        data-article-path="${article.path}"    
                        title="点击查看发布记录">    
                        ${statusText}    
                    </span>   
                    <span class="meta-divider">•</span>  
                    <span class="size-info">${article.size}</span>  
                    <span class="meta-divider">•</span>  
                    <span class="time-info">${formatTime(article.create_time)}</span>  
                </div> 
            </div>  
            <div class="card-actions">  
                <button class="btn-icon" data-action="edit" title="编辑">  
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>  
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>  
                    </svg>  
                </button>  
                <button class="btn-icon" data-action="illustration" title="设计">  
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                        <rect x="3" y="3" width="7" height="7"/>  
                        <rect x="14" y="3" width="7" height="7"/>  
                        <rect x="3" y="14" width="7" height="7"/>  
                        <rect x="14" y="14" width="7" height="7"/>  
                        <path d="M10 10l4 4"/>  
                    </svg>     
                </button>  
                <button class="btn-icon" data-action="publish" title="发布">  
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                        <path d="M22 2L11 13"/>  
                        <path d="M22 2l-7 20-4-9-9-4 20-7z"/>  
                    </svg>  
                </button>  
                <button class="btn-icon" data-action="delete" title="删除">  
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                        <polyline points="3 6 5 6 21 6"/>  
                        <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>  
                    </svg>  
                </button>  
            </div>  
        `;  
        
        return card;  
    }  
    
    async openImageDesigner(article) {  
        try {  
            // 检查文件扩展名  
            const ext = article.path.toLowerCase().split('.').pop();  
            
            if (ext === 'md' || ext === 'markdown' || ext === 'txt') {  
                // 显示警告对话框,让用户选择是否继续  
                window.dialogManager.showConfirm(  
                    `警告: ${ext.toUpperCase()} 格式文件不适合使用可视化设计器编辑。\n` +  
                    `使用页面设计器可能会破坏原始格式,建议使用"编辑"功能进行修改。\n` +  
                    `是否仍要继续使用页面设计器？`,  
                    async () => {  
                        // 用户点击确认,继续打开设计器  
                        if (!window.imageDesignerDialog) {  
                            window.imageDesignerDialog = new ImageDesignerDialog();  
                        }  
                        await window.imageDesignerDialog.open(article.path, article.title);  
                    },  
                    () => {  
                        // 用户点击取消,不执行任何操作  
                    }  
                );  
            } else {  
                // HTML 文件,直接打开  
                if (!window.imageDesignerDialog) {  
                    window.imageDesignerDialog = new ImageDesignerDialog();  
                }  
                await window.imageDesignerDialog.open(article.path, article.title);  
            }  
        } catch (error) {  
            this.showNotification('打开配图设计器失败: ' + error.message, 'error');  
        }  
    }

    // 添加新方法显示发布历史  
    async showPublishHistory(article) {  
        try {  
            const response = await fetch(`/api/articles/publish-history/${encodeURIComponent(article.path)}`);  
            if (!response.ok) {  
                throw new Error('获取发布历史失败');  
            }  
            
            const result = await response.json();  
            const records = result.data.records || [];  
            
            // 显示发布历史对话框  
            this.renderPublishHistoryDialog(article, records);  
        } catch (error) {  
            this.showNotification('获取发布历史失败: ' + error.message, 'error');  
        }  
    }  
    
    renderPublishHistoryDialog(article, records) {  
        const dialogHtml = `  
            <div class="modal-overlay" id="publish-history-dialog">  
                <div class="modal-content publish-history-modal">  
                    <div class="modal-header">  
                        <h3>发布记录</h3>  
                        <button class="modal-close" onclick="window.articleManager.closePublishHistoryDialog()">×</button>  
                    </div>  
                    <div class="modal-body">  
                        <div class="article-info">  
                            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>  
                                <polyline points="14,2 14,8 20,8"/>  
                            </svg>  
                            <span class="article-title">${this.escapeHtml(article.title)}</span>  
                        </div>  
                        
                        ${records.length === 0 ? `  
                            <div class="empty-state">  
                                <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor">  
                                    <circle cx="12" cy="12" r="10"/>  
                                    <line x1="12" y1="8" x2="12" y2="12"/>  
                                    <line x1="12" y1="16" x2="12.01" y2="16"/>  
                                </svg>  
                                <p>暂无发布记录</p>  
                            </div>  
                        ` : `  
                            <div class="history-timeline">  
                                ${records.map((record, index) => `  
                                    <div class="history-item ${record.success ? 'success' : 'failed'}">  
                                        <div class="history-icon">  
                                            ${record.success ? `  
                                                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">  
                                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>  
                                                    <polyline points="22 4 12 14.01 9 11.01"/>  
                                                </svg>  
                                            ` : `  
                                                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">  
                                                    <circle cx="12" cy="12" r="10"/>  
                                                    <line x1="15" y1="9" x2="9" y2="15"/>  
                                                    <line x1="9" y1="9" x2="15" y2="15"/>  
                                                </svg>  
                                            `}  
                                        </div>  
                                        <div class="history-content">  
                                            <div class="history-header">  
                                                <span class="history-account">${this.escapeHtml(record.account || '未知账号')}</span>  
                                                <span class="history-appid">AppID: ${this.escapeHtml(record.appid || 'N/A')}</span>  
                                            </div>  
                                            <div class="history-time">${this.formatHistoryTime(record.timestamp)}</div>  
                                            ${record.error ? `  
                                                <div class="history-${record.success ? 'warning' : 'error'}">  
                                                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor">  
                                                        ${record.success ? `  
                                                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>  
                                                            <line x1="12" y1="9" x2="12" y2="13"/>  
                                                            <line x1="12" y1="17" x2="12.01" y2="17"/>  
                                                        ` : `  
                                                            <circle cx="12" cy="12" r="10"/>  
                                                            <line x1="12" y1="8" x2="12" y2="12"/>  
                                                            <line x1="12" y1="16" x2="12.01" y2="16"/>  
                                                        `}  
                                                    </svg>  
                                                    <span>${this.escapeHtml(this.truncateError(record.error))}</span>  
                                                </div>  
                                            ` : ''}  
                                        </div>  
                                        ${index < records.length - 1 ? '<div class="history-line"></div>' : ''}  
                                    </div>  
                                `).join('')}  
                            </div>  
                        `}  
                    </div>
                </div>  
            </div>  
        `;  
        
        document.body.insertAdjacentHTML('beforeend', dialogHtml);  
    }
    
    // 辅助方法:格式化时间  
    formatHistoryTime(timestamp) {  
        const date = new Date(timestamp);  
        const now = new Date();  
        const diffMs = now - date;  
        const diffMins = Math.floor(diffMs / 60000);  
        const diffHours = Math.floor(diffMs / 3600000);  
        const diffDays = Math.floor(diffMs / 86400000);  
        
        if (diffMins < 1) return '刚刚';  
        if (diffMins < 60) return `${diffMins}分钟前`;  
        if (diffHours < 24) return `${diffHours}小时前`;  
        if (diffDays < 7) return `${diffDays}天前`;  
        
        return date.toLocaleString('zh-CN', {  
            year: 'numeric',  
            month: '2-digit',  
            day: '2-digit',  
            hour: '2-digit',  
            minute: '2-digit'  
        });  
    }  
    
    // 辅助方法:截断错误信息  
    truncateError(error) {  
        if (!error) return '';  
        const maxLength = 100;  
        return error.length > maxLength ? error.substring(0, maxLength) + '...' : error;  
    }  

    closePublishHistoryDialog() {  
        const dialog = document.getElementById('publish-history-dialog');  
        if (dialog) dialog.remove();  
    }

    // 绑定卡片事件  
    bindCardEvents() {  
        const grid = document.getElementById('article-content-grid');  
        if (!grid) return;  
        
        grid.querySelectorAll('.article-card').forEach(card => {  
            // 状态徽章点击事件  
            const statusBadge = card.querySelector('.status-badge');  
            if (statusBadge) {  
                statusBadge.addEventListener('click', (e) => {  
                    e.stopPropagation(); // 阻止事件冒泡  
                    const path = card.dataset.path;  
                    const article = this.articles.find(a => a.path === path);  
                    if (article) {  
                        this.showPublishHistory(article);  
                    }  
                });  
            }  

            // 卡片点击预览  
            card.addEventListener('click', (e) => {  
                if (!e.target.closest('.card-actions') && !e.target.closest('.batch-checkbox')) {  
                    const path = card.dataset.path;  
                    const article = this.articles.find(a => a.path === path);  
                    if (article) {  
                        this.previewArticle(article);  
                    }  
                }  
            });  
            
            // 操作按钮点击  
            card.querySelectorAll('[data-action]').forEach(btn => {  
                btn.addEventListener('click', (e) => {  
                    e.stopPropagation();  
                    const action = btn.dataset.action;  
                    const path = card.dataset.path;  
                    const article = this.articles.find(a => a.path === path);  
                    if (article) {  
                        this.handleCardAction(action, article);  
                    }  
                });  
            });  
        }); 
    }  
    
    async handleCardAction(action, article) {  
        switch(action) {  
            case 'edit':  
                await this.editArticle(article);  
                break;  
            case 'illustration':  
                await this.openImageDesigner(article)
                break;  
            case 'publish':  
                await this.showPublishDialog(article.path);  
                break;  
            case 'delete':  
                await this.deleteArticle(article.path);  
                break;  
        }  
    } 
        
    // 初始化懒加载观察器    
    initIntersectionObserver() {    
        const options = {    
            root: document.querySelector('#article-manager-view .manager-main'),
            rootMargin: '200px',  // 提前200px开始加载  
            threshold: 0.01    
        };    
        
        this.observer = new IntersectionObserver((entries) => {    
            entries.forEach(entry => {    
                if (entry.isIntersecting) {    
                    const card = entry.target;  // 观察的是卡片本身  
                    const iframe = card.querySelector('iframe[data-article-path]');    
                    if (iframe && iframe.dataset.loaded !== 'true') {    
                        this.loadSinglePreview(iframe);    
                        this.observer.unobserve(card);  // 加载后立即取消观察  
                    }    
                }    
            });    
        }, options);    
    }  
    
    // 加载单个预览    
    async loadSinglePreview(iframe) {    
        const articlePath = iframe.dataset.articlePath;    
        const loadingEl = iframe.parentElement.querySelector('.preview-loading');    
        
        try {    
            const response = await fetch(`/api/articles/content?path=${encodeURIComponent(articlePath)}`);    
            if (!response.ok) {    
                throw new Error(`HTTP ${response.status}`);    
            }    
            const content = await response.text();    
            
            const ext = articlePath.toLowerCase().split('.').pop();    
            let htmlContent = content;    
            
            if ((ext === 'md' || ext === 'markdown') && window.markdownRenderer) {    
                htmlContent = window.markdownRenderer.render(content);    
            } else if (ext === 'txt') {    
                htmlContent = content.split('\n')    
                    .map(line => line.trim() ? `<p>${line}</p>` : '<br>')    
                    .join('\n');    
            }    
            
            // 添加完整的Markdown样式定义(卡片预览版本)  
            const styledHtml = `    
                <style>    
                    body {     
                        overflow: hidden !important;     
                        margin: 0;    
                        padding: 8px;  
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;  
                        font-size: 12px;  
                        line-height: 1.4;  
                    }    
                    
                    /* 标题样式 - 更紧凑 */  
                    h1, h2, h3, h4, h5, h6 {   
                        margin: 4px 0 2px 0;   
                        font-weight: 600;  
                    }  
                    h1 { font-size: 16px; }  
                    h2 { font-size: 14px; }  
                    h3 { font-size: 13px; }  
                    
                    /* 段落样式 */  
                    p { margin: 0 0 4px 0; }  
                    
                    /* 引用块样式 - 关键! */  
                    blockquote {  
                        margin: 4px 0;  
                        padding: 2px 8px;  
                        border-left: 2px solid #ddd;  
                        background: #f9f9f9;  
                        font-style: italic;  
                    }  
                    
                    /* 代码样式 */  
                    code {  
                        background: #f0f0f0;  
                        padding: 1px 3px;  
                        border-radius: 2px;  
                        font-size: 11px;  
                    }  
                    
                    pre {  
                        background: #f0f0f0;  
                        padding: 4px;  
                        border-radius: 3px;  
                        font-size: 10px;  
                        margin: 4px 0;  
                    }  
                    
                    /* 表格样式 */  
                    table {  
                        border-collapse: collapse;  
                        width: 100%;  
                        font-size: 10px;  
                        margin: 4px 0;  
                    }  
                    
                    table th, table td {  
                        padding: 2px 4px;  
                        border: 1px solid #ddd;  
                    }  
                    
                    table th {  
                        background: #f0f0f0;  
                        font-weight: 600;  
                    }  
                    
                    /* 链接样式 */  
                    a {  
                        color: #0366d6;  
                        text-decoration: none;  
                    }  
                    
                    /* 列表样式 */  
                    ul, ol {  
                        margin: 2px 0;  
                        padding-left: 16px;  
                    }  
                    
                    li {  
                        margin: 1px 0;  
                    }  
                    
                    /* 分割线样式 */  
                    hr {  
                        height: 1px;  
                        background: #ddd;  
                        border: 0;  
                        margin: 4px 0;  
                    }  
                    
                    /* 隐藏滚动条 */  
                    ::-webkit-scrollbar { display: none !important; }    
                    * { scrollbar-width: none !important; }    
                </style>    
                ${htmlContent}    
            `;    
            
            iframe.srcdoc = styledHtml;    
            iframe.dataset.loaded = 'true';    
            if (loadingEl) loadingEl.style.display = 'none';    
        } catch (error) {    
            iframe.srcdoc = '<div style="padding: 20px; color: red;">加载失败</div>';    
            if (loadingEl) loadingEl.textContent = '加载失败';    
        }    
    }
    
    // 绑定事件  
    bindEvents() {    
        // 状态树点击    
        document.getElementById('article-sidebar-tree')?.addEventListener('click', (e) => {    
            const item = e.target.closest('.tree-item');    
            if (item) {    
                this.currentStatus = item.dataset.status;    
                this.filterArticles();    
                this.renderStatusTree();    
            }    
        });    
        
        // 搜索    
        document.getElementById('article-search')?.addEventListener('input', (e) => {    
            this.searchArticles(e.target.value);    
        });    
        
        // 视图切换 - 删除全局绑定,只保留限定作用域的绑定  
        const articleView = document.getElementById('article-manager-view');    
        if (articleView) {    
            articleView.querySelectorAll('.view-btn').forEach(btn => {    
                btn.addEventListener('click', () => {    
                    // 只移除文章管理视图内的active状态    
                    articleView.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));    
                    btn.classList.add('active');    
                    this.currentLayout = btn.dataset.layout;    
                    this.renderArticles();    
                });    
            });    
        }  
    
        // 批量操作模式    
        document.getElementById('batch-mode-toggle')?.addEventListener('click', () => {    
            this.toggleBatchMode();    
        });    
        
        // 批量删除    
        document.getElementById('batch-delete')?.addEventListener('click', () => {    
            this.batchDelete();    
        });    
        
        // 批量发布    
        document.getElementById('batch-publish')?.addEventListener('click', () => {    
            this.batchPublish();    
        });    
        
        // 卡片复选框变化    
        document.addEventListener('change', (e) => {    
            if (e.target.classList.contains('batch-checkbox')) {    
                const card = e.target.closest('.article-card');    
                const path = card.dataset.path;    
                if (e.target.checked) {    
                    this.selectedArticles.add(path);    
                } else {    
                    this.selectedArticles.delete(path);    
                }    
                this.updateBatchButtons();    
            }    
        });
        
        // 平台选择变化  
        const platformSelect = document.getElementById('publish-platform-select');  
        if (platformSelect) {  
            platformSelect.addEventListener('change', (e) => {  
                this.onPlatformChange(e.target.value);  
            });  
        }

        // 快捷键刷新 (F5 或 Ctrl+R) - 隐藏功能    
        document.addEventListener('keydown', (e) => {    
            const articleView = document.getElementById('article-manager-view');    
            if (articleView && articleView.style.display !== 'none') {    
                if (e.key === 'F5' || ((e.ctrlKey || e.metaKey) && e.key === 'r')) {    
                    e.preventDefault();    
                    this.refreshArticles();    
                }    
            }    
        });   
    }
    
    async refreshArticles() {  
        try {
            await this.loadArticles();  
            this.renderStatusTree();  
            this.renderArticles();

            window.app?.showNotification('已刷新文章列表', 'success');  
        } catch (error) {  
            window.app?.showNotification('刷新失败: ' + error.message, 'error');  
        }  
    }

    // 搜索文章  
    searchArticles(query) {  
        if (!query.trim()) {  
            this.filterArticles();  
            return;  
        }  
        
        const lowerQuery = query.toLowerCase();  
        this.filteredArticles = this.articles.filter(article =>   
            article.title.toLowerCase().includes(lowerQuery)  
        );  
        this.renderArticles();  
    }  
    
    // 切换批量操作模式  
    toggleBatchMode() {  
        this.batchMode = !this.batchMode;  
        
        document.querySelectorAll('.article-card').forEach(card => {  
            if (this.batchMode) {  
                card.classList.add('batch-mode');  
            } else {  
                card.classList.remove('batch-mode');  
            }  
        });  
        
        this.updateBatchButtons();  
    }  
    
    // 更新批量操作按钮状态  
    updateBatchButtons() {  
        const batchDelete = document.getElementById('batch-delete');  
        const batchPublish = document.getElementById('batch-publish');  
        
        if (this.selectedArticles.size > 0) {  
            batchDelete.style.display = 'block';  
            batchPublish.style.display = 'block';  
        } else {  
            batchDelete.style.display = 'none';  
            batchPublish.style.display = 'none';  
        }  
    }  
    
    // 预览文章  
    async previewArticle(article) {  
        try {  
            const response = await fetch(`/api/articles/content?path=${encodeURIComponent(article.path)}`);  
            if (response.ok) {  
                const content = await response.text();  
                
                // 检测文件扩展名  
                const ext = article.path.toLowerCase().split('.').pop();  
                let htmlContent = content;  
                
                // 如果是Markdown文件,使用 renderWithStyles 生成带滚动条的完整文档  
                if ((ext === 'md' || ext === 'markdown') && window.markdownRenderer) {  
                    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';  
                    htmlContent = window.markdownRenderer.renderWithStyles(content, isDark);  
                } else if (ext === 'txt') {  
                    // TXT文件:生成带滚动条的完整文档  
                    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';  
                    const computedStyle = getComputedStyle(document.documentElement);  
                    const bgColor = computedStyle.getPropertyValue('--background-color').trim();  
                    const borderColor = computedStyle.getPropertyValue('--border-color').trim();  
                    const secondaryColor = computedStyle.getPropertyValue('--secondary-color').trim();  
                    const textColor = computedStyle.getPropertyValue('--text-primary').trim();  
                    
                    // 将纯文本转换为HTML段落  
                    const txtHtml = content.split('\n')  
                        .map(line => line.trim() ? `<p>${line}</p>` : '<br>')  
                        .join('\n');  
                    
                    htmlContent = `  
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
                background: transparent;  
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;  
                line-height: 1.6;  
            }  
            
            p {  
                margin: 0 0 16px 0;  
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
                }  
                
                if (window.previewPanelManager) {  
                    window.previewPanelManager.show(htmlContent);  
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
    
    // 显示发布对话框  
    async showPublishDialog(path) {  
        this.publishingArticles = [path];  
        await this.loadAccountsAndShowDialog();  
    }  
    
    // 批量发布  
    async batchPublish() {  
        if (this.selectedArticles.size === 0) {  
            this.showNotification('请先选择要发布的文章', 'warning');  
            return;  
        }  
        
        this.publishingArticles = Array.from(this.selectedArticles);  
        await this.loadAccountsAndShowDialog();  
    }  
    
    // 加载平台并显示对话框  
    async loadAccountsAndShowDialog() {  
        try {
            // 清除缓存,强制重新加载    
            this.platformAccounts = {};   

            // 如果平台列表未加载,先加载  
            if (!this.platforms) {  
                await this.loadPlatforms();  
            }  
            
            // 填充平台选择器  
            const platformSelect = document.getElementById('publish-platform-select');  
            if (platformSelect) {  
                platformSelect.innerHTML = '<option value="">请选择发布平台...</option>' +  
                    this.platforms.map(p => `<option value="${p.value}">${p.label}</option>`).join('');  
            }  
            
            // 隐藏账号选择区域,等待用户选择平台  
            document.getElementById('account-selection-group').style.display = 'none';  
            document.getElementById('no-accounts-tip').style.display = 'none';  
            
            // 禁用确认按钮  
            document.getElementById('confirm-publish-btn').disabled = true;  
            
            // 显示对话框  
            document.getElementById('publish-dialog').style.display = 'flex';  
        } catch (error) {  
            this.showNotification('加载平台列表失败: ' + error.message, 'error');  
        }  
    }
    
    // 平台选择变化    
    async onPlatformChange(platformId) {    
        const accountSelectionGroup = document.getElementById('account-selection-group');    
        const noAccountsTip = document.getElementById('no-accounts-tip');    
        const accountList = document.getElementById('account-list');    
        
        if (!platformId) {    
            accountSelectionGroup.style.display = 'none';    
            noAccountsTip.style.display = 'none';    
            this.updatePublishButtonState();    
            return;    
        }    
        
        try {    
            // 检查缓存    
            if (this.platformAccounts[platformId]) {    
                this.renderPlatformAccounts(platformId, this.platformAccounts[platformId]);    
                return;    
            }    
            
            // 获取该平台的账号列表    
            const response = await fetch('/api/config/');    
            if (!response.ok) throw new Error('加载配置失败');    
            
            const config = await response.json();    
            let accounts = [];    
            
            if (platformId === 'wechat') {    
                const allCredentials = config.data?.wechat?.credentials || [];    
                const validCredentials = allCredentials.filter(cred => cred.appid && cred.appid.trim() !== '');    
                
                accounts = validCredentials.map((cred, index) => ({    
                    index: allCredentials.indexOf(cred),    
                    author: cred.author || '未命名',    
                    appid: cred.appid
                }));    
            }   
            
            // 缓存账号列表    
            this.platformAccounts[platformId] = accounts;    
            
            this.renderPlatformAccounts(platformId, accounts);    
        } catch (error) {    
            this.showNotification('加载账号失败: ' + error.message, 'error');    
        }    
    }
    
    // 渲染平台账号列表    
    renderPlatformAccounts(platformId, accounts) {    
        const accountSelectionGroup = document.getElementById('account-selection-group');    
        const noAccountsTip = document.getElementById('no-accounts-tip');    
        const accountList = document.getElementById('account-list');    
        
        if (accounts.length === 0) {    
            accountSelectionGroup.style.display = 'none';    
            noAccountsTip.style.display = 'block';    
            this.updatePublishButtonState();    
        } else {    
            noAccountsTip.style.display = 'none';    
            accountSelectionGroup.style.display = 'block';    
            
            // 渲染账号列表 - 新设计:可点击选择  
            accountList.innerHTML = accounts.map(account => `    
                <div class="account-item" data-account-index="${account.index}">    
                    <div class="account-info">    
                        <span class="account-name" title="${account.author}">${account.author}</span>  
                        <span class="account-detail">AppID: ${account.appid}</span>  
                    </div>  
                    <svg class="check-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">  
                        <polyline points="20 6 9 17 4 12"/>  
                    </svg>  
                </div>    
            `).join('');    
            
            // 绑定点击事件  
            accountList.querySelectorAll('.account-item').forEach(item => {    
                item.addEventListener('click', () => {    
                    item.classList.toggle('selected');  
                    this.updateSelectedAccountCount();    
                    this.updatePublishButtonState();    
                });    
            });    
            
            this.updateSelectedAccountCount();    
            this.updatePublishButtonState();    
        }    
    }  
    
    // 更新已选账号数量  
    updateSelectedAccountCount() {    
        const selectedItems = document.querySelectorAll('.account-item.selected');  // ✅ 修正  
        const count = selectedItems.length;    
        
        document.getElementById('selected-account-count').textContent = `(已选 ${count} 个)`;    
        document.getElementById('confirm-publish-btn').disabled = count === 0;    
    } 
    
    // 全选账号  
    selectAllAccounts() {    
        document.querySelectorAll('.account-item').forEach(item => {    
            item.classList.add('selected');    
        });    
        this.updateSelectedAccountCount();    
    }    
    
    // 取消全选  
    deselectAllAccounts() {    
        document.querySelectorAll('.account-item').forEach(item => {    
            item.classList.remove('selected');    
        });    
        this.updateSelectedAccountCount();    
    }

    // 更新发布按钮状态  
    updatePublishButtonState() {    
        const platformSelected = document.getElementById('publish-platform-select')?.value;    
        const accountSelected = document.querySelectorAll('.account-item.selected').length > 0;  
        const confirmBtn = document.getElementById('confirm-publish-btn');    
        
        if (confirmBtn) {    
            confirmBtn.disabled = !(platformSelected && accountSelected);    
        }    
    }
    
    // 前往设置  
    goToSettings() {  
        this.closePublishDialog();  
        // 切换到系统设置-微信公众号  
        const settingsLink = document.querySelector('[data-view="config-manager"]');  
        if (settingsLink) {  
            settingsLink.click();  
            // 延迟切换到微信公众号配置  
            setTimeout(() => {  
                const wechatConfig = document.querySelector('[data-config="wechat"]');  
                if (wechatConfig) wechatConfig.click();  
            }, 100);  
        }  
    }  
    
    // 关闭发布对话框  
    closePublishDialog() {  
        document.getElementById('publish-dialog').style.display = 'none';  
        this.publishingArticles = [];  
    }  
    
    // 确认发布  
    async confirmPublish() {  
        const platformId = document.getElementById('publish-platform-select')?.value;  
        const selectedAccounts = Array.from(  
            document.querySelectorAll('.account-item.selected')  
        ).map(item => parseInt(item.dataset.accountIndex));  
        
        if (!platformId || selectedAccounts.length === 0) {  
            this.showNotification('请选择平台和账号', 'warning');  
            return;  
        }  
        
        const articlePaths = [...this.publishingArticles];  
        this.closePublishDialog();  
        
        // 显示进度对话框  
        this.showPublishProgressDialog(articlePaths.length, selectedAccounts.length, true);  
        
        try {  
            const response = await fetch('/api/articles/publish', {  
                method: 'POST',  
                headers: { 'Content-Type': 'application/json' },  
                body: JSON.stringify({  
                    article_paths: articlePaths,  
                    account_indices: selectedAccounts,  
                    platform: platformId  
                })  
            });  
            
            if (response.ok) {  
                const result = await response.json();  
                
                // 获取文章标题  
                const articleTitles = articlePaths.map(path => {  
                    const article = this.articles.find(a => a.path === path);  
                    return article ? article.title : '未知文章';  
                }).filter(title => title !== '未知文章');  
                
                // 构建标题前缀  
                let titlePrefix = '';  
                if (articleTitles.length === 1) {  
                    titlePrefix = `《${articleTitles[0]}》 `;  
                } else if (articleTitles.length > 1) {  
                    titlePrefix = `《${articleTitles[0]}》等${articleTitles.length}篇 `;  
                }  
                
                // 检查进度对话框是否仍然存在  
                const progressDialog = document.getElementById('publish-progress-dialog');  
                
                if (progressDialog) {  
                    // 对话框仍然打开 - 更新为结果显示,不显示右上角通知  
                    this.updateProgressDialogWithResult(result);  
                } else {  
                    // 对话框已关闭 - 显示右上角通知(简洁版本,包含文章标题)  
                    let notificationMessage = titlePrefix + '发布完成: ';  // 添加标题前缀  
                    if (result.success_count > 0 && result.fail_count > 0) {  
                        notificationMessage += `成功 ${result.success_count}, 失败 ${result.fail_count}`;  
                    } else if (result.success_count > 0) {  
                        notificationMessage += `成功 ${result.success_count}`;  
                    } else {  
                        notificationMessage += `失败 ${result.fail_count}`;  
                    }  
                    
                    this.showNotification(  
                        notificationMessage,  
                        result.fail_count === 0 ? 'success' : (result.success_count > 0 ? 'warning' : 'error')  
                    );  
                }  
                
                // 构建走马灯消息(包含文章标题)  
                let marqueeMessage = titlePrefix;  // 以标题开头  
                
                if (result.success_count > 0 && result.fail_count === 0) {  
                    marqueeMessage += `发布完成: 成功 ${result.success_count}`;  
                } else if (result.success_count > 0 && result.fail_count > 0) {  
                    marqueeMessage += `发布完成: 成功 ${result.success_count}, 失败 ${result.fail_count}`;  
                } else {  
                    marqueeMessage += `发布完成: 失败 ${result.fail_count}`;  
                }  
                
                // 添加详细信息(最多3条)  
                if (result.error_details && result.error_details.length > 0) {  
                    const details = result.error_details.slice(0, 3).join('; ');  
                    marqueeMessage += ` | 详情: ${details}`;  
                    if (result.error_details.length > 3) {  
                        marqueeMessage += `...等${result.error_details.length}条`;  
                    }  
                }  
                
                // 判断消息类型(正确区分成功/警告/错误)  
                let messageType;  
                if (result.fail_count === 0) {  
                    // 全部成功  
                    if (result.error_details && result.error_details.length > 0) {  
                        messageType = 'warning';  // 成功但有警告(如权限回收) - 橙色  
                    } else {  
                        messageType = 'success';  // 完全成功 - 绿色  
                    }  
                } else if (result.success_count > 0) {  
                    messageType = 'warning';  // 部分成功 - 橙色  
                } else {  
                    messageType = 'error';  // 全部失败 - 红色  
                }  
                
                // 推送到走马灯(循环3次,使用正确的颜色)  
                if (window.footerMarquee) {  
                    window.footerMarquee.addMessage(  
                        marqueeMessage,  
                        messageType,  
                        false,  
                        1 
                    );  
                }  
                
                await this.loadArticles();  
                this.renderStatusTree();  
            } else {  
                throw new Error('发布请求失败');  
            }  
        } catch (error) {  
            this.showNotification('发布失败: ' + error.message, 'error');  
            
            if (window.footerMarquee) {  
                window.footerMarquee.addMessage(  
                    '发布失败: ' + error.message,  
                    'error',  
                    false,  
                    1  
                );  
            }  
            
            const progressDialog = document.getElementById('publish-progress-dialog');  
            if (progressDialog) progressDialog.remove();  
        }  
    }

    // 在进度对话框中显示结果  
    updateProgressDialogWithResult(result) {  
        const dialog = document.getElementById('publish-progress-dialog');  
        if (!dialog) return;  
        
        const modalBody = dialog.querySelector('.modal-body');  
        if (!modalBody) return;  
        
        // 判断标题颜色  
        const hasWarnings = result.warning_details && result.warning_details.length > 0;  
        const hasErrors = result.error_details && result.error_details.length > 0;  
        const resultType = result.fail_count === 0 ? 'success' : (result.success_count > 0 ? 'warning' : 'error');  
        
        // 合并所有详情信息  
        const allDetails = [];  
        
        // 添加警告信息(橙色竖线)  
        if (hasWarnings) {  
            result.warning_details.forEach(detail => {  
                allDetails.push({ text: detail, type: 'warning' });  
            });  
        }  
        
        // 添加错误信息(红色竖线)  
        if (hasErrors) {  
            result.error_details.forEach(detail => {  
                allDetails.push({ text: detail, type: 'error' });  
            });  
        }  
        
        modalBody.innerHTML = `  
            <div class="result-summary ${resultType}">  
                <h4>发布完成</h4>  
                ${result.success_count > 0 ? `<p>✓ 成功: ${result.success_count}</p>` : ''}  
                ${result.fail_count > 0 ? `<p>✗ 失败: ${result.fail_count}</p>` : ''}  
            </div>  
            ${allDetails.length > 0 ? `  
                <div class="error-details">  
                    <h5 style="color: ${result.fail_count > 0 && result.success_count === 0 ? '#ef4444' : '#f59e0b'};">结果详情</h5>  
                    <div class="error-list">  
                        ${allDetails.map(item => `  
                            <div class="${item.type === 'warning' ? 'warning-item' : 'error-item'}">${this.escapeHtml(item.text)}</div>  
                        `).join('')}  
                    </div>  
                </div>  
            ` : ''}  
        `;  
        
        // 更新对话框头部和按钮  
        const header = dialog.querySelector('.modal-header h3');  
        if (header) header.textContent = '发布结果';  
        
        const closeBtn = dialog.querySelector('.modal-close');  
        if (closeBtn) closeBtn.onclick = () => this.closeProgressDialog();  
        
        // 添加底部按钮  
        let footer = dialog.querySelector('.modal-footer');  
        if (!footer) {  
            footer = document.createElement('div');  
            footer.className = 'modal-footer';  
            dialog.querySelector('.modal-content').appendChild(footer);  
        }  
        
        footer.innerHTML = `  
            <button class="btn btn-secondary" onclick="window.articleManager.closeProgressDialog()">关闭</button>  
            <button class="btn btn-primary" onclick="window.open('https://mp.weixin.qq.com', '_blank')">打开公众号后台</button>  
        `;  
    }

    // 格式化发布结果为走马灯消息  
    formatPublishMarqueeMessage(result) {  
        const { success_count, fail_count } = result;  
        const parts = [];  
        
        if (success_count > 0) {  
            parts.push(`成功 ${success_count}`);  
        }  
        if (fail_count > 0) {  
            parts.push(`失败 ${fail_count}`);  
        }  
        
        return parts.length > 0 ? `发布完成: ${parts.join(', ')}` : '发布完成';  
    }

    // 推送发布结果到走马灯  
    pushResultToMarquee(result) {  
        if (!window.footerMarquee) return;  
        
        const { success_count, fail_count, error_details } = result;  
        
        // 构建详细的结果消息  
        let message = '发布完成: ';  
        
        // 只显示非零的统计  
        if (success_count > 0 && fail_count > 0) {  
            message += `成功 ${success_count}, 失败 ${fail_count}`;  
        } else if (success_count > 0) {  
            message += `成功 ${success_count}`;  
        } else if (fail_count > 0) {  
            message += `失败 ${fail_count}`;  
        }  
        
        // 添加失败详情(最多显示3条)  
        if (fail_count > 0 && error_details && error_details.length > 0) {  
            const details = error_details.slice(0, 3).join('; ');  
            message += ` | 失败详情: ${details}`;  
            if (error_details.length > 3) {  
                message += `...还有${error_details.length - 3}个错误`;  
            }  
        }  
        
        // 推送到走马灯  
        window.footerMarquee.addMessage(  
            message,  
            fail_count === 0 ? 'success' : (success_count > 0 ? 'warning' : 'error'),  
            false,  // persistent=false (临时消息)  
            1       // loopCount=1 (立即显示一次,不循环)  
        );  
    }

    showPublishProgressDialog(articleCount, accountCount, showCloseButton = true) {  // ✅ 改为showCloseButton  
        const dialogHtml = `    
            <div class="modal-overlay" id="publish-progress-dialog" data-user-closed="false">    
                <div class="modal-content publish-progress-modal">    
                    <div class="modal-header">    
                        <h3>正在发布</h3>    
                        ${showCloseButton ? '<button class="btn-icon modal-close" onclick="window.articleManager.closeProgressDialog()">×</button>' : ''}    
                    </div>  
                    <div class="modal-body">    
                        <div class="progress-info">    
                            <p>正在发布 ${articleCount} 篇文章到 ${accountCount} 个账号...</p>    
                            <p class="progress-detail">您可以关闭此窗口,发布将在后台继续</p>    
                        </div>    
                        <div class="progress-spinner">    
                            <svg class="spinner" viewBox="0 0 50 50">    
                                <circle cx="25" cy="25" r="20" fill="none" stroke-width="4"></circle>    
                            </svg>    
                        </div>    
                    </div>    
                </div>    
            </div>    
        `;    
        
        document.body.insertAdjacentHTML('beforeend', dialogHtml);    
    } 

    // 关闭进度对话框(转为后台执行)  
    closeProgressDialog() {  
        const dialog = document.getElementById('publish-progress-dialog');  
        if (dialog) dialog.remove();  
    }

    // 显示简洁的发布通知  
    showPublishNotification(result) {  
        const { success_count, fail_count } = result;  
        
        // 构建简洁消息  
        let message = '发布完成';  
        const parts = [];  
        
        if (success_count > 0) {  
            parts.push(`成功 ${success_count}`);  
        }  
        if (fail_count > 0) {  
            parts.push(`失败 ${fail_count}`);  
        }  
        
        if (parts.length > 0) {  
            message += ': ' + parts.join(', ');  
        }  
        
        const type = fail_count === 0 ? 'success' : (success_count > 0 ? 'warning' : 'error');  
        this.showNotification(message, type);  
    }  

    // 显示详细结果对话框  
    showPublishResultDialog(result) {  
        const { success_count, fail_count, error_details } = result;  
        
        let statusClass = 'success';  
        let statusText = '发布成功';  
        if (fail_count > 0 && success_count > 0) {  
            statusClass = 'warning';  
            statusText = '部分成功';  
        } else if (fail_count > 0) {  
            statusClass = 'error';  
            statusText = '发布失败';  
        }  
        
        const dialogHtml = `  
            <div id="publish-result-dialog" class="modal-overlay">  
                <div class="modal-content publish-result-modal">  
                    <div class="modal-header">  
                        <h3>发布结果</h3>  
                        <button class="modal-close" onclick="window.articleManager.closeResultDialog()">×</button>  
                    </div>  
                    <div class="modal-body">  
                        <div class="result-summary ${statusClass}">  
                            <h4>${statusText}</h4>  
                            <div class="result-stats">  
                                ${success_count > 0 ? `  
                                    <div class="stat-item">  
                                        <div class="stat-number success">${success_count}</div>  
                                        <div class="stat-label">成功</div>  
                                    </div>  
                                ` : ''}  
                                ${fail_count > 0 ? `  
                                    <div class="stat-item">  
                                        <div class="stat-number failed">${fail_count}</div>  
                                        <div class="stat-label">失败</div>  
                                    </div>  
                                ` : ''}  
                            </div>  
                        </div>  
                        
                        ${error_details && error_details.length > 0 ? `  
                            <div class="error-details-section">  
                                <div class="error-details-header">  
                                    <span class="error-details-title">失败详情</span>  
                                </div>  
                                <div class="error-list">  
                                    ${error_details.map(err => `  
                                        <div class="error-item">${this.escapeHtml(err)}</div>  
                                    `).join('')}  
                                </div>  
                            </div>  
                        ` : ''}  
                    </div>  
                    <div class="modal-footer">  
                        <button class="btn btn-secondary" onclick="window.articleManager.closeResultDialog()">关闭</button>  
                        <button class="btn btn-primary" onclick="window.open('https://mp.weixin.qq.com', '_blank')">打开公众号后台</button>  
                    </div>  
                </div>  
            </div>  
        `;  
        
        // 移除进度对话框  
        const progressDialog = document.getElementById('publish-progress-dialog');  
        if (progressDialog) progressDialog.remove();  
        
        document.body.insertAdjacentHTML('beforeend', dialogHtml);  
    }  

    closeResultDialog() {  
        const dialog = document.getElementById('publish-result-dialog');  
        if (dialog) dialog.remove();  
    }

    // 删除文章  
    async deleteArticle(path) {  
        window.dialogManager.showConfirm(  
            '确认删除这篇文章吗?',  
            async () => {  
                try {  
                    const response = await fetch(`/api/articles/${encodeURIComponent(path)}`, {  
                        method: 'DELETE'  
                    });  
                    
                    if (response.ok) {  
                        this.showNotification('文章已删除', 'success');  
                        await this.loadArticles();  
                        this.renderStatusTree(); 
                    } else {  
                        const error = await response.json();  
                        window.dialogManager.showAlert('删除失败: ' + (error.detail || '未知错误'), 'error');  
                    }  
                } catch (error) {  
                    window.dialogManager.showAlert('删除失败: ' + error.message, 'error');  
                }  
            }  
        );  
    }
    
    // 批量删除  
    async batchDelete() {  
        if (this.selectedArticles.size === 0) {  
            this.showNotification('请先选择要删除的文章', 'warning');  
            return;  
        }  
        
        const count = this.selectedArticles.size;  
        
        window.dialogManager.showConfirm(  
            `确认删除选中的 ${count} 篇文章吗?`,  
            async () => {  
                const paths = Array.from(this.selectedArticles);  
                let successCount = 0;  
                
                for (const path of paths) {  
                    try {  
                        const response = await fetch(`/api/articles/${encodeURIComponent(path)}`, {  
                            method: 'DELETE'  
                        });  
                        if (response.ok) successCount++;  
                    } catch (error) {  
                        console.error('删除失败:', path, error);  
                    }  
                }  
                
                this.showNotification(`删除完成: ${successCount}/${count}`, 'success');  
                this.selectedArticles.clear();  
                this.batchMode = false;  
                await this.loadArticles();  
                this.renderStatusTree();
            }  
        );  
    }
    
    // HTML转义  
    escapeHtml(text) {  
        const div = document.createElement('div');  
        div.textContent = text;  
        return div.innerHTML;  
    }  
    
    // 显示通知  
    showNotification(message, type = 'info') {  
        if (window.app?.showNotification) {  
            window.app.showNotification(message, type);  
        }  
    }  

    async editArticle(article) {  
        try {  
            if (!window.contentEditorDialog) {  
                window.contentEditorDialog = new ContentEditorDialog();  
            }  
            await window.contentEditorDialog.open(article.path, article.title, 'article');  
        } catch (error) {  
            this.showNotification('打开编辑器失败: ' + error.message, 'error');  
        }  
    }
}  
  
// 不要在这里自动初始化,由 main.js 控制  
// window.articleManager = new ArticleManager();