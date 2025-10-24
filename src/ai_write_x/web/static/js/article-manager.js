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
            this.renderArticles();
            
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
                        data-template-path="${article.path}"  
                        data-loaded="false"></iframe>  
                <div class="preview-loading">加载中...</div>  
            </div>  
            <div class="card-content">  
                <h4 class="card-title" title="${this.escapeHtml(article.title)}">${this.escapeHtml(article.title)}</h4>  
                <div class="card-meta">  
                    <span class="format-badge">${article.format}</span>  
                    <span class="meta-divider">•</span>  
                    <span class="status-badge ${statusClass}" title="点击查看发布记录">${statusText}</span>  
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
                <button class="btn-icon" data-action="illustration" title="配图">  
                    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor">  
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>  
                        <circle cx="8.5" cy="8.5" r="1.5"/>  
                        <polyline points="21 15 16 10 5 21"/>  
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
    
    // 绑定卡片事件  
    bindCardEvents() {  
        const grid = document.getElementById('article-content-grid');  
        if (!grid) return;  
        
        grid.querySelectorAll('.article-card').forEach(card => {  
            // 卡片点击预览 - 完全参照模板管理  
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
                this.showNotification('配图功能开发中', 'info');  
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
                    const iframe = card.querySelector('iframe[data-template-path]');    
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
        const templatePath = iframe.dataset.templatePath;    
        const loadingEl = iframe.parentElement.querySelector('.preview-loading');    
            
        try {    
            // 使用查询参数格式(与后端API一致)  
            const response = await fetch(`/api/articles/content?path=${encodeURIComponent(templatePath)}`);    
            if (!response.ok) {    
                throw new Error(`HTTP ${response.status}`);    
            }    
            const html = await response.text();    
            
            // 注入完全相同的CSS样式  
            const styledHtml = `    
                <style>    
                    body {     
                        overflow: hidden !important;     
                        margin: 0;    
                    }    
                    ::-webkit-scrollbar { display: none !important; }    
                    * { scrollbar-width: none !important; }    
                </style>    
                ${html}    
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
                const html = await response.text();    
                // 使用全局预览面板管理器    
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
                const allCredentials = config.data?.wechat_credentials || [];  
                // 过滤掉 appid 为空的占位配置  
                const validCredentials = allCredentials.filter(cred => cred.appid && cred.appid.trim() !== '');  
                
                accounts = validCredentials.map((cred, index) => ({  
                    index: allCredentials.indexOf(cred),  
                    author: cred.author_name || '未命名',  
                    appid: cred.appid.slice(-4)  
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
            // 无账号  
            accountSelectionGroup.style.display = 'none';  
            noAccountsTip.style.display = 'block';  
            this.updatePublishButtonState();  
        } else {  
            // 有账号  
            noAccountsTip.style.display = 'none';  
            accountSelectionGroup.style.display = 'block';  
            
            // 渲染账号列表  
            accountList.innerHTML = accounts.map(account => `  
                <div class="account-checkbox-item">  
                    <label class="checkbox-label">  
                        <input type="checkbox" class="account-checkbox" value="${account.index}">  
                        <div class="account-info">  
                            <div class="account-name">${account.author}</div>  
                            <div class="account-detail">AppID: ${account.appid}</div>  
                        </div>  
                    </label>  
                </div>  
            `).join('');  
            
            // 绑定账号选择事件  
            accountList.querySelectorAll('.account-checkbox').forEach(checkbox => {  
                checkbox.addEventListener('change', () => {  
                    this.updateSelectedAccountCount();  
                    this.updatePublishButtonState();  
                });  
            });  
            
            this.updateSelectedAccountCount();  
            this.updatePublishButtonState();  
        }  
    }

    // 更新发布按钮状态  
    updatePublishButtonState() {  
        const platformSelected = document.getElementById('publish-platform-select')?.value;  
        const accountSelected = document.querySelectorAll('.account-checkbox:checked').length > 0;  
        const confirmBtn = document.getElementById('confirm-publish-btn');  
        
        if (confirmBtn) {  
            confirmBtn.disabled = !(platformSelected && accountSelected);  
        }  
    }

    // 更新已选账号数量  
    updateSelectedAccountCount() {  
        const checkboxes = document.querySelectorAll('.account-checkbox:checked');  
        const count = checkboxes.length;  
        
        document.getElementById('selected-account-count').textContent = `(已选 ${count} 个)`;  
        document.getElementById('confirm-publish-btn').disabled = count === 0;  
    }  
    
    // 全选账号  
    selectAllAccounts() {  
        document.querySelectorAll('.account-checkbox').forEach(checkbox => {  
            checkbox.checked = true;  
        });  
        this.updateSelectedAccountCount();  
    }  
    
    // 取消全选  
    deselectAllAccounts() {  
        document.querySelectorAll('.account-checkbox').forEach(checkbox => {  
            checkbox.checked = false;  
        });  
        this.updateSelectedAccountCount();  
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
            document.querySelectorAll('.account-checkbox:checked')  
        ).map(input => parseInt(input.value));  
        
        if (!platformId || selectedAccounts.length === 0) {  
            this.showNotification('请选择平台和账号', 'warning');  
            return;  
        }  
        
        this.closePublishDialog();  
        
        try {  
            const response = await fetch('/api/articles/publish', {  
                method: 'POST',  
                headers: { 'Content-Type': 'application/json' },  
                body: JSON.stringify({  
                    article_paths: this.publishingArticles,  
                    account_indices: selectedAccounts,  
                    platform: platformId  
                })  
            });  
            
            if (response.ok) {  
                const result = await response.json();  
                this.showNotification(  
                    `发布完成: 成功 ${result.success_count}, 失败 ${result.fail_count}`,  
                    result.fail_count === 0 ? 'success' : 'warning'  
                );  
                await this.loadArticles();  
                this.renderStatusTree();  
            } else {  
                throw new Error('发布请求失败');  
            }  
        } catch (error) {  
            this.showNotification('发布失败: ' + error.message, 'error');  
        }  
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
                        this.renderStatusTree();  // 添加这一行  
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
                this.renderStatusTree();  // 添加这一行  
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