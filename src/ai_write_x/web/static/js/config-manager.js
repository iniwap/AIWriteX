class AIWriteXConfigManager { 
    constructor() {
        // 维度分组定义  
        this.DIMENSION_GROUPS = {  
            'expression': {  
                name: '文体表达维度',  
                icon: 'icon-text',  
                dimensions: ['style', 'language', 'tone'],  
                description: '控制文章的文体风格、语言风格和语调语气'  
            },  
            'culture': {  
                name: '文化时空维度',  
                icon: 'icon-globe',  
                dimensions: ['culture', 'time', 'scene'],  
                description: '设置文化视角、时空背景和场景环境'  
            },  
            'character': {  
                name: '角色技法维度',  
                icon: 'icon-user',  
                dimensions: ['personality', 'technique', 'perspective'],  
                description: '选择人格角色、表现技法和叙述视角'  
            },  
            'structure': {  
                name: '结构节奏维度',  
                icon: 'icon-layout',  
                dimensions: ['structure', 'rhythm'],  
                description: '定义文章结构和节奏韵律'  
            },  
            'audience': {  
                name: '受众主题维度',  
                icon: 'icon-target',  
                dimensions: ['audience', 'theme', 'emotion', 'format'],  
                description: '针对目标受众、主题内容、情感调性和表达格式'  
            }  
        };

        this.apiEndpoint = '/api/config';    
        this.config = {};    
        this.uiConfig = this.loadUIConfig();    
          
        this.currentPanel = 'ui';  
        this.init();   
    }    
        
    async init() {    
        try {    
            // 1. 从后端加载 UI 配置    
            const uiResponse = await fetch('/api/config/ui-config');    
            if (uiResponse.ok) {    
                const uiConfig = await uiResponse.json();    
                localStorage.setItem('aiwritex_ui_config', JSON.stringify(uiConfig));    
                this.uiConfig = uiConfig;    
            }    
            
            // 2. 加载业务配置    
            await this.loadConfig();    
            
            // 2.5. 加载动态选项数据(新增)  
            await this.loadDynamicOptions();  
            
            // 3. 绑定事件监听器(只绑定一次)    
            this.bindEventListeners();    
            
            // 4. 填充UI(只负责填充值,不绑定事件)    
            this.populateUI();    
            this.showConfigPanel(this.currentPanel);    
            
            // 5. 通知主题管理器和窗口模式管理器    
            if (window.themeManager) {    
                window.themeManager.onConfigLoaded();    
            }    
            if (window.windowModeManager) {    
                window.windowModeManager.onConfigLoaded();    
            }    
            
            // 6. 最后绑定导航事件(确保DOM已加载)    
            this.bindConfigNavigation();    
        } catch (error) {    
            console.error('配置管理器初始化失败:', error);    
        }    
    }  
    
    bindEventListeners() {          
        // 主题选择器  
        const themeSelector = document.getElementById('theme-selector');    
        if (themeSelector) {    
            themeSelector.addEventListener('change', (e) => {    
                this.uiConfig.theme = e.target.value;    
                if (window.themeManager) {    
                    window.themeManager.applyTheme(e.target.value, false);    
                }    
                
                // ✅ 添加按钮状态变化逻辑  
                const saveBtn = document.getElementById('save-ui-config');    
                if (saveBtn && !saveBtn.classList.contains('has-changes')) {    
                    saveBtn.classList.add('has-changes');    
                    saveBtn.innerHTML = '<i class="icon-save"></i> 保存设置 <span style="color: var(--warning-color);">(有未保存更改)</span>';    
                }  
            });    
        }    
        
        // 窗口模式选择器    
        const windowModeSelector = document.getElementById('window-mode-selector');    
        if (windowModeSelector) {    
            windowModeSelector.addEventListener('change', (e) => {    
                this.uiConfig.windowMode = e.target.value;    
                if (window.windowModeManager) {    
                    window.windowModeManager.applyMode(e.target.value);    
                }    
                
                // ✅ 添加按钮状态变化逻辑  
                const saveBtn = document.getElementById('save-ui-config');    
                if (saveBtn && !saveBtn.classList.contains('has-changes')) {    
                    saveBtn.classList.add('has-changes');    
                    saveBtn.innerHTML = '<i class="icon-save"></i> 保存设置 <span style="color: var(--warning-color);">(有未保存更改)</span>';    
                }  
            });    
        }  
        
        // 保存按钮  
        const saveUIConfigBtn = document.getElementById('save-ui-config');    
        if (saveUIConfigBtn) {    
            saveUIConfigBtn.addEventListener('click', async () => {    
                const success = await this.saveUIConfig(this.uiConfig);    
                
                if (success) {  
                    // 清除未保存提示  
                    const saveBtn = document.getElementById('save-ui-config');  
                    if (saveBtn) {  
                        saveBtn.classList.remove('has-changes');  
                        saveBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
                    }  
                }  
                
                window.app?.showNotification(  
                    success ? '界面设置已保存' : '保存界面设置失败',  
                    success ? 'success' : 'error'  
                );  
            });    
        }
        
        // 恢复默认按钮  
        const resetUIConfigBtn = document.getElementById('reset-ui-config');  
        if (resetUIConfigBtn) {  
            resetUIConfigBtn.addEventListener('click', async () => {  
                const oldWindowMode = this.uiConfig.windowMode;  
                this.uiConfig = { theme: 'light', windowMode: 'STANDARD' };  
                
                // 更新UI显示  
                const themeSelector = document.getElementById('theme-selector');  
                const windowModeSelector = document.getElementById('window-mode-selector');  
                if (themeSelector) themeSelector.value = 'light';  
                if (windowModeSelector) windowModeSelector.value = 'STANDARD';  
                
                if (window.themeManager) window.themeManager.applyTheme('light', false);  
                if (window.windowModeManager) window.windowModeManager.applyMode('STANDARD');  
                
                const success = await this.saveUIConfig(this.uiConfig);  
                if (success && oldWindowMode !== 'STANDARD') {  
                    window.windowModeManager?.showRestartNotification();  
                }  
            });  
        }  
        
        // 基础设置保存按钮  
        const saveBaseConfigBtn = document.getElementById('save-base-config');  
        if (saveBaseConfigBtn) {  
            saveBaseConfigBtn.addEventListener('click', async () => {  
                const success = await this.saveConfig();  
                if (success) {  
                    saveBaseConfigBtn.classList.remove('has-changes');  
                    saveBaseConfigBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
                }  
                window.app?.showNotification(  
                    success ? '基础设置已保存' : '保存基础设置失败',  
                    success ? 'success' : 'error'  
                );  
            });  
        }  
        
        // 基础设置恢复默认按钮  
        const resetBaseConfigBtn = document.getElementById('reset-base-config');  
        if (resetBaseConfigBtn) {  
            resetBaseConfigBtn.addEventListener('click', async () => {  
                const success = await this.resetToDefault();  
                window.app?.showNotification(  
                    success ? '已恢复默认设置' : '恢复默认设置失败',  
                    success ? 'info' : 'error'  
                );  
            });  
        }

        // 文章格式  
        const articleFormatSelect = document.getElementById('article-format');  
        if (articleFormatSelect) {  
            articleFormatSelect.addEventListener('change', async (e) => {  
                await this.updateConfig({ article_format: e.target.value });  
                
                // 联动禁用逻辑  
                const formatPublishCheckbox = document.getElementById('format-publish');  
                if (formatPublishCheckbox) {  
                    formatPublishCheckbox.disabled = e.target.value === 'html';  
                }  
            });  
        }  
        
        // 自动发布  
        const autoPublishCheckbox = document.getElementById('auto-publish');  
        if (autoPublishCheckbox) {  
            autoPublishCheckbox.addEventListener('change', async (e) => {  
                await this.updateConfig({ auto_publish: e.target.checked });  
            });  
        }  
        
        // 格式化发布  
        const formatPublishCheckbox = document.getElementById('format-publish');  
        if (formatPublishCheckbox) {  
            formatPublishCheckbox.addEventListener('change', async (e) => {  
                await this.updateConfig({ format_publish: e.target.checked });  
            });  
        }  
        
        // 使用模板  
        const useTemplateCheckbox = document.getElementById('use-template');  
        if (useTemplateCheckbox) {  
            useTemplateCheckbox.addEventListener('change', async (e) => {  
                await this.updateConfig({ use_template: e.target.checked });  
                
                // 联动禁用逻辑  
                const templateCategorySelect = document.getElementById('template-category');  
                const templateSelect = document.getElementById('template');  
                if (templateCategorySelect) templateCategorySelect.disabled = !e.target.checked;  
                if (templateSelect) templateSelect.disabled = !e.target.checked;  
            });  
        }  
        
        // 模板分类(修改为级联加载)  
        const templateCategorySelect = document.getElementById('template-category');    
        if (templateCategorySelect) {    
            templateCategorySelect.addEventListener('change', async (e) => {    
                const category = e.target.value;  
                
                // 更新配置  
                await this.updateConfig({ template_category: category });    
                
                // 级联加载模板列表  
                const templateSelect = document.getElementById('template');  
                if (templateSelect) {  
                    // 清空现有选项  
                    templateSelect.innerHTML = '';  
                    
                    // 添加"随机模板"选项  
                    const randomOption = document.createElement('option');  
                    randomOption.value = '';  
                    randomOption.textContent = '随机模板';  
                    templateSelect.appendChild(randomOption);  
                    
                    // 加载新分类的模板  
                    if (category) {  
                        const templates = await this.loadTemplatesByCategory(category);  
                        templates.forEach(template => {  
                            const option = document.createElement('option');  
                            option.value = template;  
                            option.textContent = template;  
                            templateSelect.appendChild(option);  
                        });  
                    }  
                    
                    // 重置为"随机模板"  
                    templateSelect.value = '';  
                }  
            });    
        }  
        
        // 模板选择  
        const templateSelect = document.getElementById('template');  
        if (templateSelect) {  
            templateSelect.addEventListener('change', async (e) => {  
                await this.updateConfig({ template: e.target.value });  
            });  
        }  
        
        // 压缩模板  
        const useCompressCheckbox = document.getElementById('use-compress');  
        if (useCompressCheckbox) {  
            useCompressCheckbox.addEventListener('change', async (e) => {  
                await this.updateConfig({ use_compress: e.target.checked });  
            });  
        }  
        
        // 最大搜索结果  
        const maxSearchResultsInput = document.getElementById('max-search-results');  
        if (maxSearchResultsInput) {  
            maxSearchResultsInput.addEventListener('change', async (e) => {  
                await this.updateConfig({ aiforge_search_max_results: parseInt(e.target.value) });  
            });  
        }  
        
        // 最小搜索结果  
        const minSearchResultsInput = document.getElementById('min-search-results');  
        if (minSearchResultsInput) {  
            minSearchResultsInput.addEventListener('change', async (e) => {  
                await this.updateConfig({ aiforge_search_min_results: parseInt(e.target.value) });  
            });  
        }  
        
        // 最小文章字数  
        const minArticleLenInput = document.getElementById('min-article-len');  
        if (minArticleLenInput) {  
            minArticleLenInput.addEventListener('change', async (e) => {  
                await this.updateConfig({ min_article_len: parseInt(e.target.value) });  
            });  
        }  
        
        // 最大文章字数  
        const maxArticleLenInput = document.getElementById('max-article-len');  
        if (maxArticleLenInput) {  
            maxArticleLenInput.addEventListener('change', async (e) => {  
                await this.updateConfig({ max_article_len: parseInt(e.target.value) });  
            });  
        }

        // ========== 热搜平台设置事件绑定 ==========  

        // 保存平台配置按钮  
        const savePlatformsConfigBtn = document.getElementById('save-platforms-config');    
        if (savePlatformsConfigBtn) {    
            savePlatformsConfigBtn.addEventListener('click', async () => {    
                const success = await this.saveConfig();  
                
                if (success) {  
                    // 清除未保存提示  
                    const saveBtn = document.getElementById('save-platforms-config');  
                    if (saveBtn) {  
                        saveBtn.classList.remove('has-changes');  
                        saveBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
                    }  
                }  
                
                window.app?.showNotification(    
                    success ? '平台配置已保存' : '保存平台配置失败',    
                    success ? 'success' : 'error'    
                );    
            });    
        } 
        
        // 恢复默认平台配置按钮  
        const resetPlatformsConfigBtn = document.getElementById('reset-platforms-config');  
        if (resetPlatformsConfigBtn) {  
            resetPlatformsConfigBtn.addEventListener('click', async () => {  
                // 获取默认配置  
                const response = await fetch(`${this.apiEndpoint}/default`);  
                if (response.ok) {  
                    const result = await response.json();  
                    const defaultPlatforms = result.data.platforms;  
                    
                    // 更新配置  
                    await this.updateConfig({ platforms: defaultPlatforms });  
                    
                    // 刷新UI  
                    this.populatePlatformsUI();  
                    
                    window.app?.showNotification('已恢复默认平台配置', 'info');  
                } else {  
                    window.app?.showNotification('恢复默认配置失败', 'error');  
                }  
            });  
        }

        // ========== 微信公众号设置事件绑定 ==========  

        // 添加凭证按钮  
        const addWeChatCredentialBtn = document.getElementById('add-wechat-credential');  
        if (addWeChatCredentialBtn) {  
            addWeChatCredentialBtn.addEventListener('click', () => {  
                this.addWeChatCredential();  
            });  
        }  
        
        // 保存微信配置按钮  
        const saveWeChatConfigBtn = document.getElementById('save-wechat-config');  
        if (saveWeChatConfigBtn) {  
            saveWeChatConfigBtn.addEventListener('click', async () => {  
                await this.saveWeChatConfig();  
            });  
        }  
        
        // 恢复默认微信配置按钮  
        const resetWeChatConfigBtn = document.getElementById('reset-wechat-config');  
        if (resetWeChatConfigBtn) {  
            resetWeChatConfigBtn.addEventListener('click', async () => {  
                const response = await fetch(`${this.apiEndpoint}/default`);  
                if (response.ok) {  
                    const result = await response.json();  
                    const defaultCredentials = result.data.wechat.credentials;  
                    
                    await this.updateConfig({   
                        wechat: { credentials: defaultCredentials }   
                    });  
                    
                    this.populateWeChatUI();  
                    
                    window.app?.showNotification('已恢复默认微信配置', 'info');  
                } else {  
                    window.app?.showNotification('恢复默认配置失败', 'error');  
                }  
            });  
        }

        // ========== 微信公众号输入框事件绑定 ==========  
        // 注意:由于凭证是动态生成的,需要使用事件委托  
        
        const wechatContainer = document.getElementById('wechat-credentials-container');  
        if (wechatContainer) {            
            // 处理复选框的change事件  
            wechatContainer.addEventListener('change', async (e) => {  
                if (e.target.matches('input[type="checkbox"][id^="wechat-"]')) {  
                    const id = e.target.id;  
                    const match = id.match(/wechat-(\w+)-(\d+)/);  
                    if (match) {  
                        const [, field, indexStr] = match;  
                        const index = parseInt(indexStr);  
                        
                        if (field === 'call-sendall') {  
                            this.updateSendallOptions(index, e.target.checked);  
                        } else if (field === 'sendall') {  
                            const tagIdInput = document.getElementById(`wechat-tag-id-${index}`);  
                            if (tagIdInput) {  
                                tagIdInput.disabled = e.target.checked;  
                            }  
                            await this.updateWeChatCredential(index);  
                        }  
                    }  
                }  
            });  
        }

        // ========== 大模型API设置事件绑定 ==========  
  
        // 保存API配置按钮  
        const saveAPIConfigBtn = document.getElementById('save-api-config');  
        if (saveAPIConfigBtn) {  
            saveAPIConfigBtn.addEventListener('click', async () => {  
                const success = await this.saveConfig();  
                
                if (success) {  
                    saveAPIConfigBtn.classList.remove('has-changes');  
                    saveAPIConfigBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
                }  
                
                window.app?.showNotification(  
                    success ? 'API配置已保存' : '保存API配置失败',  
                    success ? 'success' : 'error'  
                );  
            });  
        } 
        
        // 恢复默认API配置按钮  
        const resetAPIConfigBtn = document.getElementById('reset-api-config');  
        if (resetAPIConfigBtn) {  
            resetAPIConfigBtn.addEventListener('click', async () => {  
                const response = await fetch(`${this.apiEndpoint}/default`);  
                if (response.ok) {  
                    const result = await response.json();  
                    const defaultAPI = result.data.api;  
                    
                    await this.updateConfig({ api: defaultAPI });  
                    
                    this.populateAPIUI();  
                    
                    window.app?.showNotification('已恢复默认API配置', 'info');  
                } else {  
                    window.app?.showNotification('恢复默认配置失败', 'error');  
                }  
            });  
        }

        // 保存图片API配置  
        const saveImgAPIConfigBtn = document.getElementById('save-img-api-config');  
        if (saveImgAPIConfigBtn) {  
            saveImgAPIConfigBtn.addEventListener('click', async () => {  
                const success = await this.saveConfig();  
                
                if (success) {  
                    saveImgAPIConfigBtn.classList.remove('has-changes');  
                    saveImgAPIConfigBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
                }  
                
                window.app?.showNotification(  
                    success ? '图片API配置已保存' : '保存图片API配置失败',  
                    success ? 'success' : 'error'  
                );  
            });  
        } 
        
        // 恢复默认图片API配置  
        const resetImgAPIConfigBtn = document.getElementById('reset-img-api-config');  
        if (resetImgAPIConfigBtn) {  
            resetImgAPIConfigBtn.addEventListener('click', async () => {  
                await this.resetImgAPIConfig();  
            });  
        }

        // 保存AIForge配置  
        const saveAIForgeConfigBtn = document.getElementById('save-aiforge-config');  
        if (saveAIForgeConfigBtn) {  
            saveAIForgeConfigBtn.addEventListener('click', async () => {  
                const success = await this.saveConfig();  
                
                if (success) {  
                    saveAIForgeConfigBtn.classList.remove('has-changes');  
                    saveAIForgeConfigBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
                }  
                
                window.app?.showNotification(  
                    success ? 'AIForge配置已保存' : '保存AIForge配置失败',  
                    success ? 'success' : 'error'  
                );  
            });  
        }  
        
        // 恢复默认AIForge配置  
        const resetAIForgeConfigBtn = document.getElementById('reset-aiforge-config');  
        if (resetAIForgeConfigBtn) {  
            resetAIForgeConfigBtn.addEventListener('click', async () => {  
                const response = await fetch(`${this.apiEndpoint}/default`);  
                if (response.ok) {  
                    const result = await response.json();  
                    const defaultAIForge = result.data.aiforge_config;  
                    
                    await this.updateConfig({ aiforge_config: defaultAIForge });  
                    
                    this.populateAIForgeUI();  
                    
                    window.app?.showNotification('已恢复默认AIForge配置', 'info');  
                } else {  
                    window.app?.showNotification('恢复默认配置失败', 'error');  
                }  
            });  
        }

        // ========== AIForge配置事件绑定 ==========  
        
        // 1. 通用配置 - 最大重试次数  
        const aiforgeMaxRounds = document.getElementById('aiforge-max-rounds');  
        if (aiforgeMaxRounds) {  
            aiforgeMaxRounds.addEventListener('change', async (e) => {  
                await this.updateConfig({  
                    aiforge_config: {  
                        ...this.config.aiforge_config,  
                        max_rounds: parseInt(e.target.value)  
                    }  
                });  
            });  
        }  
        
        // 2. 通用配置 - 默认最大Tokens  
        const aiforgeDefaultMaxTokens = document.getElementById('aiforge-default-max-tokens');  
        if (aiforgeDefaultMaxTokens) {  
            aiforgeDefaultMaxTokens.addEventListener('change', async (e) => {  
                await this.updateConfig({  
                    aiforge_config: {  
                        ...this.config.aiforge_config,  
                        max_tokens: parseInt(e.target.value)  // ✅ 改为 max_tokens  
                    }  
                });  
            });  
        }  
        
        // 3. 代码缓存配置 - 启用缓存  
        const cacheEnabled = document.getElementById('cache-enabled');  
        if (cacheEnabled) {  
            cacheEnabled.addEventListener('change', async (e) => {  
                await this.updateConfig({  
                    aiforge_config: {  
                        ...this.config.aiforge_config,  
                        cache: {  // ✅ 改为 cache  
                            ...this.config.aiforge_config.cache,  
                            code: {  // ✅ 添加 code 层级  
                                ...this.config.aiforge_config.cache.code,  
                                enabled: e.target.checked  
                            }  
                        }  
                    }  
                });  
            });  
        }  
        
        // 4. 代码缓存配置 - 最大模块数  
        const cacheMaxModules = document.getElementById('cache-max-modules');  
        if (cacheMaxModules) {  
            cacheMaxModules.addEventListener('change', async (e) => {  
                await this.updateConfig({  
                    aiforge_config: {  
                        ...this.config.aiforge_config,  
                        cache: {  // ✅ 改为 cache  
                            ...this.config.aiforge_config.cache,  
                            code: {  // ✅ 添加 code 层级  
                                ...this.config.aiforge_config.cache.code,  
                                max_modules: parseInt(e.target.value)  
                            }  
                        }  
                    }  
                });  
            });  
        }  
        
        // 5. 代码缓存配置 - 失败阈值  
        const cacheFailureThreshold = document.getElementById('cache-failure-threshold');  
        if (cacheFailureThreshold) {  
            cacheFailureThreshold.addEventListener('change', async (e) => {  
                await this.updateConfig({  
                    aiforge_config: {  
                        ...this.config.aiforge_config,  
                        cache: {  // ✅ 改为 cache  
                            ...this.config.aiforge_config.cache,  
                            code: {  // ✅ 添加 code 层级  
                                ...this.config.aiforge_config.cache.code,  
                                failure_threshold: parseFloat(e.target.value)  // ✅ 使用 parseFloat  
                            }  
                        }  
                    }  
                });  
            });  
        }  
        
        // 6. 代码缓存配置 - 最大保存天数  
        const cacheMaxAgeDays = document.getElementById('cache-max-save-days');  
        if (cacheMaxAgeDays) {  
            cacheMaxAgeDays.addEventListener('change', async (e) => {  
                await this.updateConfig({  
                    aiforge_config: {  
                        ...this.config.aiforge_config,  
                        cache: {  // ✅ 改为 cache  
                            ...this.config.aiforge_config.cache,  
                            code: {  // ✅ 添加 code 层级  
                                ...this.config.aiforge_config.cache.code,  
                                max_age_days: parseInt(e.target.value)  // ✅ 改为 max_age_days  
                            }  
                        }  
                    }  
                });  
            });  
        }  
        
        // 7. 代码缓存配置 - 清理间隔  
        const cacheCleanupInterval = document.getElementById('cache-cleanup-interval');  
        if (cacheCleanupInterval) {  
            cacheCleanupInterval.addEventListener('change', async (e) => {  
                await this.updateConfig({  
                    aiforge_config: {  
                        ...this.config.aiforge_config,  
                        cache: {  // ✅ 改为 cache  
                            ...this.config.aiforge_config.cache,  
                            code: {  // ✅ 添加 code 层级  
                                ...this.config.aiforge_config.cache.code,  
                                cleanup_interval: parseInt(e.target.value)  // ✅ 改为 cleanup_interval  
                            }  
                        }  
                    }  
                });  
            });  
        }

        const creativeEnabled = document.getElementById('creative-enabled');  
        if (creativeEnabled) {  
            creativeEnabled.addEventListener('change', async (e) => {  
                const enabled = e.target.checked;  
                
                // 更新所有相关控件的禁用状态  
                document.querySelectorAll('.dimension-checkbox, .dimension-select, .dimension-custom-input').forEach(el => {  
                    if (!document.getElementById('auto-dimension-selection').checked) {  
                        el.disabled = !enabled;  
                    }  
                });  
                
                await this.updateConfig({  
                    dimensional_creative: {  
                        ...this.config.dimensional_creative,  
                        enabled: enabled  
                    }  
                });  
            });  
        }  
        
        const autoSelection = document.getElementById('auto-dimension-selection');  
        if (autoSelection) {  
            autoSelection.addEventListener('change', async (e) => {  
                const auto = e.target.checked;  
                const globalEnabled = document.getElementById('creative-enabled').checked;  
                
                // 禁用/启用所有维度控件  
                document.querySelectorAll('.dimension-checkbox, .dimension-select, .dimension-custom-input').forEach(el => {  
                    el.disabled = !globalEnabled || auto;  
                });  
                
                // 显示/隐藏自动选择参数  
                document.getElementById('max-dimensions').disabled = !auto;  
                document.getElementById('compatibility-threshold').disabled = !auto;  
                
                await this.updateConfig({  
                    dimensional_creative: {  
                        ...this.config.dimensional_creative,  
                        auto_dimension_selection: auto  
                    }  
                });  
            });  
        }

        // 启用维度化创意复选框  
        const creativeEnabledCheckbox = document.getElementById('creative-enabled');    
        if (creativeEnabledCheckbox) {    
            creativeEnabledCheckbox.addEventListener('change', async (e) => {    
                const enabled = e.target.checked;    
                
                this.updateCreativeControlsState();    
                
                await this.updateConfig({    
                    dimensional_creative: {    
                        ...this.config.dimensional_creative,    
                        enabled: enabled    
                    }    
                });    
            });    
        }  
        
        // 自动选择维度复选框    
        const autoSelectionCheckbox = document.getElementById('auto-dimension-selection');    
        if (autoSelectionCheckbox) {    
            autoSelectionCheckbox.addEventListener('change', async (e) => {    
                const auto = e.target.checked;    
                
                this.updateCreativeControlsState();    
                
                await this.updateConfig({    
                    dimensional_creative: {    
                        ...this.config.dimensional_creative,    
                        auto_dimension_selection: auto    
                    }    
                });    
            });    
        }

        // 保存创意配置按钮  
        const saveCreativeConfigBtn = document.getElementById('save-creative-config');  
        if (saveCreativeConfigBtn) {  
            saveCreativeConfigBtn.addEventListener('click', async () => {  
                const success = await this.saveConfig();  
                
                if (success) {  
                    saveCreativeConfigBtn.classList.remove('has-changes');  
                    saveCreativeConfigBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
                }  
                
                window.app?.showNotification(  
                    success ? '创意配置已保存' : '保存创意配置失败',  
                    success ? 'success' : 'error'  
                );  
            });  
        }  
        
        // 恢复默认创意配置按钮  
        const resetCreativeConfigBtn = document.getElementById('reset-creative-config');  
        if (resetCreativeConfigBtn) {  
            resetCreativeConfigBtn.addEventListener('click', async () => {  
                const response = await fetch(`${this.apiEndpoint}/default`);  
                if (response.ok) {  
                    const result = await response.json();  
                    const defaultCreative = result.data.dimensional_creative;  
                    
                    await this.updateConfig({ dimensional_creative: defaultCreative });  
                    
                    this.populateCreativeUI();  
                    
                    window.app?.showNotification('已恢复默认创意配置', 'info');  
                } else {  
                    window.app?.showNotification('恢复默认配置失败', 'error');  
                }  
            });  
        }
    }  
    
    populateUI() {  
        // ========== 填充发布平台 ==========  
        const publishPlatformSelect = document.getElementById('publish-platform');  
        if (publishPlatformSelect && this.config.publish_platform) {  
            publishPlatformSelect.value = this.config.publish_platform;  
        }  
        
        // ========== 填充文章格式 ==========  
        const articleFormatSelect = document.getElementById('article-format');  
        if (articleFormatSelect && this.config.article_format) {  
            articleFormatSelect.value = this.config.article_format;  
        }  
        
        // ========== 填充自动发布 ==========  
        const autoPublishCheckbox = document.getElementById('auto-publish');  
        if (autoPublishCheckbox && this.config.auto_publish !== undefined) {  
            autoPublishCheckbox.checked = this.config.auto_publish;  
        }  
        
        // ========== 填充格式化发布 ==========  
        const formatPublishCheckbox = document.getElementById('format-publish');  
        if (formatPublishCheckbox && this.config.format_publish !== undefined) {  
            formatPublishCheckbox.checked = this.config.format_publish;  
            formatPublishCheckbox.disabled = this.config.article_format === 'html';  
        }  
        
        // ========== 填充使用模板 ==========  
        const useTemplateCheckbox = document.getElementById('use-template');  
        if (useTemplateCheckbox && this.config.use_template !== undefined) {  
            useTemplateCheckbox.checked = this.config.use_template;  
        }  
        
        // ========== 填充模板分类 ==========    
        const templateCategorySelect = document.getElementById('template-category');    
        if (templateCategorySelect) {    
            templateCategorySelect.value = this.config.template_category || '';    
            templateCategorySelect.disabled = !this.config.use_template;  
            
            // 触发级联加载模板列表  
            if (this.config.template_category) {  
                this.loadTemplatesByCategory(this.config.template_category).then(templates => {  
                    const templateSelect = document.getElementById('template');  
                    if (templateSelect) {  
                        // 清空现有选项  
                        templateSelect.innerHTML = '';  
                        
                        // 添加"随机模板"选项  
                        const randomOption = document.createElement('option');  
                        randomOption.value = '';  
                        randomOption.textContent = '随机模板';  
                        templateSelect.appendChild(randomOption);  
                        
                        // 添加模板选项  
                        templates.forEach(template => {  
                            const option = document.createElement('option');  
                            option.value = template;  
                            option.textContent = template;  
                            templateSelect.appendChild(option);  
                        });  
                        
                        // 设置当前选中的模板  
                        templateSelect.value = this.config.template || '';  
                        templateSelect.disabled = !this.config.use_template;  
                    }  
                });  
            }  
        }  
        
        const useCompressCheckbox = document.getElementById('use-compress');  
        if (useCompressCheckbox && this.config.use_compress !== undefined) {  
            useCompressCheckbox.checked = this.config.use_compress;  
        }
        
        // ========== 填充模板选择 ==========  
        const templateSelect = document.getElementById('template');  
        if (templateSelect) {  
            templateSelect.value = this.config.template || '';  
            // 关键:根据use_template设置禁用状态  
            templateSelect.disabled = !this.config.use_template;
        }    
        
        // ========== 6. 填充搜索数量配置 ==========  
        const maxSearchResultsInput = document.getElementById('max-search-results');  
        if (maxSearchResultsInput && this.config.aiforge_search_max_results !== undefined) {  
            maxSearchResultsInput.value = this.config.aiforge_search_max_results;  
        }  
        
        const minSearchResultsInput = document.getElementById('min-search-results');  
        if (minSearchResultsInput && this.config.aiforge_search_min_results !== undefined) {  
            minSearchResultsInput.value = this.config.aiforge_search_min_results;  
        }  
        
        // ========== 7. 填充文章长度配置 ==========  
        const minArticleLenInput = document.getElementById('min-article-len');  
        if (minArticleLenInput && this.config.min_article_len !== undefined) {  
            minArticleLenInput.value = this.config.min_article_len;  
        }  
        
        const maxArticleLenInput = document.getElementById('max-article-len');  
        if (maxArticleLenInput && this.config.max_article_len !== undefined) {  
            maxArticleLenInput.value = this.config.max_article_len;  
        }  
        
        // ========== 8. 填充界面配置 ==========  
        const themeSelector = document.getElementById('theme-selector');  
        if (themeSelector) {  
            themeSelector.value = this.getTheme();  
        }  
        
        const windowModeSelector = document.getElementById('window-mode-selector');  
        if (windowModeSelector) {  
            windowModeSelector.value = this.getWindowMode();  
        }
        
        // ========== 填充热搜平台配置 ==========  
        this.populatePlatformsUI();

        // ========== 填充微信公众号配置 ==========  
        this.populateWeChatUI();

        // ========== 填充大模型API配置 ==========  
        this.populateAPIUI();

        this.populateImgAPIUI();

        this.populateAIForgeUI();

        this.populateCreativeUI();
    }

    // 填充热搜平台UI  
    populatePlatformsUI() {  
        const platformListBody = document.getElementById('platform-list-body');  
        if (!platformListBody || !this.config.platforms) return;  
        
        // 清空现有内容  
        platformListBody.innerHTML = '';  
        
        // 生成平台行  
        this.config.platforms.forEach((platform, index) => {  
            const row = document.createElement('tr');  
            row.dataset.platformIndex = index;  
            
            // 启用复选框列 - 使用统一的checkbox-label样式  
            const enabledCell = document.createElement('td');  
            const checkboxLabel = document.createElement('label');  
            checkboxLabel.className = 'checkbox-label';  
            checkboxLabel.style.justifyContent = 'center';  
            checkboxLabel.style.margin = '0';  
            
            const enabledCheckbox = document.createElement('input');  
            enabledCheckbox.type = 'checkbox';  
            enabledCheckbox.checked = platform.enabled !== false;  
            enabledCheckbox.addEventListener('change', async (e) => {  
                await this.updatePlatformEnabled(index, e.target.checked);  
            });  
            
            const checkboxCustom = document.createElement('span');  
            checkboxCustom.className = 'checkbox-custom';  
            
            checkboxLabel.appendChild(enabledCheckbox);  
            checkboxLabel.appendChild(checkboxCustom);  
            enabledCell.appendChild(checkboxLabel);  
            
            // 平台名称列  
            const nameCell = document.createElement('td');  
            nameCell.className = 'platform-name';  
            nameCell.textContent = platform.name;  
            
            // 权重输入框列  
            const weightCell = document.createElement('td');  
            const weightInput = document.createElement('input');  
            weightInput.type = 'number';  
            weightInput.className = 'platform-weight-input';  
            weightInput.value = platform.weight;  
            weightInput.min = '0';  
            weightInput.max = '1';  
            weightInput.step = '0.01';  
            weightInput.disabled = platform.enabled === false;  
            weightInput.addEventListener('change', async (e) => {  
                await this.updatePlatformWeight(index, parseFloat(e.target.value));  
            });  
            weightCell.appendChild(weightInput);  
            
            // 说明列  
            const descCell = document.createElement('td');  
            descCell.className = 'platform-description';  
            descCell.textContent = this.getPlatformDescription(platform.name);  
            
            // 组装行  
            row.appendChild(enabledCell);  
            row.appendChild(nameCell);  
            row.appendChild(weightCell);  
            row.appendChild(descCell);  
            
            platformListBody.appendChild(row);  
        });  
    }
    
    // 填充微信公众号UI  
    populateWeChatUI() {  
        const container = document.getElementById('wechat-credentials-container');  
        if (!container) return;  
        
        const credentials = this.config.wechat?.credentials || [];  
        
        // 清空现有内容  
        container.innerHTML = '';  
        
        // 生成凭证卡片  
        credentials.forEach((credential, index) => {  
            const card = this.createWeChatCredentialCard(credential, index);  
            container.appendChild(card);  
        });  
    }  
    
    // 创建表单组辅助方法      
    createFormGroup(label, type, id, value, placeholder, required = false, readonly = false) {      
        const group = document.createElement('div');      
        group.className = 'form-group';      
        
        const labelEl = document.createElement('label');      
        labelEl.setAttribute('for', id);      
        labelEl.textContent = label;      
        if (required) {      
            const requiredSpan = document.createElement('span');      
            requiredSpan.className = 'required';      
            requiredSpan.textContent = ' *';      
            labelEl.appendChild(requiredSpan);      
        }      
        
        const input = document.createElement('input');      
        input.type = type;      
        input.id = id;      
        input.className = 'form-control';    
        
        if (value !== undefined && value !== null) {    
            input.value = value;    
        } else {    
            input.value = '';    
        }    
        
        if (placeholder) {      
            input.placeholder = placeholder;      
            input.title = placeholder;      
        }  
        
        if (readonly) {  
            input.readOnly = true;  
        }  
        
        // ✅ 通用的值变化检测逻辑      
        let originalValue = input.value;          
        input.addEventListener('blur', async (e) => {        
            // ✅ 只在值真正改变时才更新    
            if (e.target.value !== originalValue) {        
                originalValue = e.target.value;
                e.stopPropagation();        
                
                // ✅ 微信公众号凭证      
                const wechatMatch = id.match(/wechat-\w+-(\d+)/);        
                if (wechatMatch) {        
                    const index = parseInt(wechatMatch[1]);        
                    await this.updateWeChatCredential(index);        
                    return;      
                }      
                
                // ✅ 大模型API配置(只读字段不更新)  
                const apiMatch = id.match(/api-(\w+)-(key-name|api-base)/);    
                if (apiMatch) {    
                    // KEY名称和API BASE是只读的,不需要更新    
                    return;    
                }  
                
                // ✅ 图片API配置      
                const imgApiMatch = id.match(/img-api-(\w+)-(api-key|model)/);      
                if (imgApiMatch) {      
                    const [, provider, field] = imgApiMatch;      
                    await this.updateImgAPIProviderField(provider, field, e.target.value);      
                    return;      
                } 

                // ✅ AIForge LLM配置  
                const aiforgeMatch = id.match(/aiforge-(\w+)-(type|model|api-key|base-url|timeout|max-tokens)/);  
                if (aiforgeMatch) {  
                    const [, provider, field] = aiforgeMatch;  
                    await this.updateAIForgeLLMProviderField(provider, field, e.target.value);  
                    return;  
                }
                
                // ✅ 其他所有情况:直接调用updateConfig()  
                // 这样新增的配置界面无需修改此方法  
                console.warn(`未匹配的输入框ID: ${id}, 跳过更新`);  
            } else {
                e.stopPropagation();
            }       
        });        
        
        group.appendChild(labelEl);        
        group.appendChild(input);        
        
        return group;        
    }
    
    // 更新群发选项联动逻辑  
    updateSendallOptions(index, callSendallEnabled) {  
        const sendallCheckbox = document.getElementById(`wechat-sendall-${index}`);  
        const tagIdInput = document.getElementById(`wechat-tag-id-${index}`);  
        
        if (sendallCheckbox) {  
            sendallCheckbox.disabled = !callSendallEnabled;  
        }  
        
        if (tagIdInput) {  
            const sendallChecked = sendallCheckbox?.checked !== false;  
            tagIdInput.disabled = !callSendallEnabled || sendallChecked;  
        }  
        
        // 更新配置  
        this.updateWeChatCredential(index);  
    } 
    
    // 更新单个凭证配置  
    async updateWeChatCredential(index) {  
        const credentials = [...(this.config.wechat?.credentials || [])];  
        
        const credential = {  
            appid: document.getElementById(`wechat-appid-${index}`)?.value || '',  
            appsecret: document.getElementById(`wechat-appsecret-${index}`)?.value || '',  
            author: document.getElementById(`wechat-author-${index}`)?.value || '',  
            call_sendall: document.getElementById(`wechat-call-sendall-${index}`)?.checked || false,  
            sendall: document.getElementById(`wechat-sendall-${index}`)?.checked !== false,  
            tag_id: parseInt(document.getElementById(`wechat-tag-id-${index}`)?.value || 0)  
        };  
        
        credentials[index] = credential;  
        
        await this.updateConfig({   
            wechat: { credentials }   
        });  
    }  
    
    // 添加新凭证  
    addWeChatCredential() {  
        const credentials = [...(this.config.wechat?.credentials || [])];  
        
        // 添加默认凭证  
        credentials.push({  
            appid: '',  
            appsecret: '',  
            author: '',  
            call_sendall: false,  
            sendall: true,  
            tag_id: 0  
        });  
        
        // 更新配置  
        this.updateConfig({   
            wechat: { credentials }   
        }).then(() => {  
            // 刷新UI  
            this.populateWeChatUI();  
            
            window.app?.showNotification(  
                '已添加新凭证,请填写后保存',  
                'info'  
            );  
        });  
    }  
    
    // 删除凭证  
    deleteWeChatCredential(index) {  
        if (index === 0) {  
            window.app?.showNotification(  
                '第一个凭证不能删除',  
                'warning'  
            );  
            return;  
        }  
        
        const credentials = [...(this.config.wechat?.credentials || [])];  
        credentials.splice(index, 1);  
        
        this.updateConfig({   
            wechat: { credentials }   
        }).then(() => {  
            this.populateWeChatUI();  
            
            window.app?.showNotification(  
                '凭证已删除',  
                'info'  
            );  
        });  
    }  
    
    // 保存微信配置  
    async saveWeChatConfig() {  
        // 验证必填字段  
        const credentials = this.config.wechat?.credentials || [];  
        
        for (let i = 0; i < credentials.length; i++) {  
            const cred = credentials[i];  
            
            // 如果启用了自动发布,检查必填字段  
            if (this.config.auto_publish) {  
                if (!cred.appid || !cred.appsecret || !cred.author) {  
                    window.app?.showNotification(  
                        `凭证 ${i + 1} 缺少必填字段(AppID/AppSecret/作者)`,  
                        'error'  
                    );  
                    return;  
                }  
            }  
        }  
        
        // 调用通用保存方法  
        const success = await this.saveConfig();  
        
        if (success) {  
            const saveBtn = document.getElementById('save-wechat-config');  
            if (saveBtn) {  
                saveBtn.classList.remove('has-changes');  
                saveBtn.innerHTML = '<i class="icon-save"></i> 保存配置';  
            }  
        }  
        
        window.app?.showNotification(  
            success ? '微信配置已保存' : '保存微信配置失败',  
            success ? 'success' : 'error'  
        );  
    }

    // 创建微信凭证卡片  
    createWeChatCredentialCard(credential, index) {  
        const card = document.createElement('div');  
        card.className = 'wechat-credential-card';  
        card.dataset.credentialIndex = index;  
        
        // 标题栏  
        const header = document.createElement('div');  
        header.className = 'credential-header';  
        
        const title = document.createElement('div');  
        title.className = 'credential-title';  
        title.textContent = `凭证 ${index + 1}`;  
        
        const deleteBtn = document.createElement('button');  
        deleteBtn.className = 'credential-delete-btn';  
        deleteBtn.textContent = '删除';  
        deleteBtn.disabled = index === 0; // 第一个凭证不能删除  
        deleteBtn.addEventListener('click', () => {  
            this.deleteWeChatCredential(index);  
        });  
        
        header.appendChild(title);  
        header.appendChild(deleteBtn);  
        
        // 表单内容  
        const form = document.createElement('div');  
        form.className = 'credential-form';  
        
        // 行1: AppID、AppSecret、作者在同一行  
        const row1 = document.createElement('div');  
        row1.className = 'form-row';  
        
        const appidGroup = this.createFormGroup(  
            'AppID',  
            'text',  
            `wechat-appid-${index}`,  
            credential.appid || '',  
            '微信公众号AppID',  
            true  
        );  
        appidGroup.classList.add('form-group-third');  
        
        const appsecretGroup = this.createFormGroup(  
            'AppSecret',  
            'password',  
            `wechat-appsecret-${index}`,  
            credential.appsecret || '',  
            '微信公众号AppSecret',  
            true  
        );  
        appsecretGroup.classList.add('form-group-third');  
        
        const authorGroup = this.createFormGroup(  
            '作者',  
            'text',  
            `wechat-author-${index}`,  
            credential.author || '',  
            '文章作者名称'  
        );  
        authorGroup.classList.add('form-group-third');  
        
        row1.appendChild(appidGroup);  
        row1.appendChild(appsecretGroup);  
        row1.appendChild(authorGroup);  
        
        // 行2: 群发选项  
        const row2 = document.createElement('div');  
        row2.className = 'form-row';  
        
        const sendallOptionsDiv = document.createElement('div');  
        sendallOptionsDiv.className = 'sendall-options';  
        
        // 启用群发复选框  
        const callSendallGroup = document.createElement('div');  
        callSendallGroup.className = 'form-group';  
        
        const callSendallLabel = document.createElement('label');  
        callSendallLabel.className = 'checkbox-label';  
        callSendallLabel.title = '1. 启用群发,群发才生效\n2. 否则不启用,需要网页后台群发';  
        
        const callSendallCheckbox = document.createElement('input');  
        callSendallCheckbox.type = 'checkbox';  
        callSendallCheckbox.id = `wechat-call-sendall-${index}`;  
        callSendallCheckbox.checked = credential.call_sendall || false;  
        callSendallCheckbox.addEventListener('change', (e) => {  
            this.updateSendallOptions(index, e.target.checked);  
        });  
        
        const callSendallCustom = document.createElement('span');  
        callSendallCustom.className = 'checkbox-custom';  
        
        const callSendallText = document.createTextNode('启用群发');  
        
        callSendallLabel.appendChild(callSendallCheckbox);  
        callSendallLabel.appendChild(callSendallCustom);  
        callSendallLabel.appendChild(callSendallText);  
        callSendallGroup.appendChild(callSendallLabel);  
        
        const callSendallHelp = document.createElement('small');  
        callSendallHelp.className = 'form-help';  
        callSendallHelp.textContent = '仅对已认证公众号生效';  
        callSendallGroup.appendChild(callSendallHelp);  
        
        // 群发复选框  
        const sendallGroup = document.createElement('div');  
        sendallGroup.className = 'form-group';  
        
        const sendallLabel = document.createElement('label');  
        sendallLabel.className = 'checkbox-label';  
        sendallLabel.title = '1. 认证号群发数量有限,群发可控\n2. 非认证号,此选项无效(不支持群发)';  
        
        // 群发复选框  
        const sendallCheckbox = document.createElement('input');  
        sendallCheckbox.type = 'checkbox';  
        sendallCheckbox.id = `wechat-sendall-${index}`;  
        sendallCheckbox.checked = credential.sendall !== false;  
        sendallCheckbox.disabled = !credential.call_sendall;
        sendallCheckbox.addEventListener('change', async (e) => {  
            const tagIdInput = document.getElementById(`wechat-tag-id-${index}`);  
            if (tagIdInput) {  
                tagIdInput.disabled = e.target.checked;  
            }  
            await this.updateWeChatCredential(index);  
        });  
        
        const sendallCustom = document.createElement('span');  
        sendallCustom.className = 'checkbox-custom';  
        
        const sendallText = document.createTextNode('群发');  
        
        sendallLabel.appendChild(sendallCheckbox);  
        sendallLabel.appendChild(sendallCustom);  
        sendallLabel.appendChild(sendallText);  
        sendallGroup.appendChild(sendallLabel);  
        
        const sendallHelp = document.createElement('small');  
        sendallHelp.className = 'form-help';  
        sendallHelp.textContent = '发送给所有关注者';  
        sendallGroup.appendChild(sendallHelp);  
        
        // 标签组ID部分  
        const tagIdGroup = this.createFormGroup(  
            '标签组ID',  
            'number',  
            `wechat-tag-id-${index}`,  
            credential.tag_id || 0,  
            '群发的标签组ID'  
        );  
        const tagIdInput = tagIdGroup.querySelector('input');  
        tagIdInput.classList.add('tag-id-input');  // 添加特定宽度类  
        // form-control类已经在createFormGroup中添加,确保高度一致  
        tagIdInput.disabled = !credential.call_sendall || credential.sendall !== false;  
        tagIdInput.addEventListener('change', async () => {  
            await this.updateWeChatCredential(index);  
        }); 
        
        sendallOptionsDiv.appendChild(callSendallGroup);  
        sendallOptionsDiv.appendChild(sendallGroup);  
        sendallOptionsDiv.appendChild(tagIdGroup);  
        
        row2.appendChild(sendallOptionsDiv);  
        
        // 组装表单  
        form.appendChild(row1);  
        form.appendChild(row2);  
        
        // 组装卡片  
        card.appendChild(header);  
        card.appendChild(form);  
        
        return card;  
    }  

    // 更新平台启用状态  
    async updatePlatformEnabled(index, enabled) {  
        const platforms = [...this.config.platforms];  
        platforms[index] = { ...platforms[index], enabled };  
        
        await this.updateConfig({ platforms });  
        
        // 更新权重输入框的禁用状态  
        const row = document.querySelector(`tr[data-platform-index="${index}"]`);  
        if (row) {  
            const weightInput = row.querySelector('.platform-weight-input');  
            if (weightInput) {  
                weightInput.disabled = !enabled;  
            }  
        }  
    }  
    
    // 更新平台权重  
    async updatePlatformWeight(index, weight) {  
        const platforms = [...this.config.platforms];  
        platforms[index] = { ...platforms[index], weight };  
        
        await this.updateConfig({ platforms });  
    }  
    
    // 获取平台描述  
    getPlatformDescription(platformName) {  
        const descriptions = {  
            '微博': '社交媒体热搜话题',  
            '抖音': '短视频平台热点',  
            '小红书': '生活方式分享平台',  
            '今日头条': '新闻资讯聚合',  
            '百度热点': '搜索引擎热搜',  
            '哔哩哔哩': '视频弹幕网站',  
            '快手': '短视频社交平台',  
            '虎扑': '体育社区论坛',  
            '豆瓣小组': '文化兴趣社区',  
            '澎湃新闻': '专业新闻媒体',  
            '知乎热榜': '问答社区热榜'  
        };  
        return descriptions[platformName] || '热搜话题来源';  
    }

    // 填充大模型API UI  
    populateAPIUI() {  
        const container = document.getElementById('api-providers-container');  
        if (!container || !this.config.api) return;  
        
        const currentAPIType = this.config.api.api_type;  
        
        // 更新当前API类型指示器  
        const indicator = document.getElementById('current-api-type');  
        if (indicator) {  
            indicator.textContent = currentAPIType === 'SiliconFlow' ? '硅基流动' : currentAPIType;  
        }  
        
        // 清空现有内容  
        container.innerHTML = '';  
        
        const apiConfig = this.config.api;  
        const providers = Object.keys(apiConfig)  
            .filter(key => key !== 'api_type')  // 排除api_type字段  
            .map(key => ({  
                key: key,  
                display: key === 'SiliconFlow' ? '硅基流动' : key  
            }));  
        
        // 生成提供商卡片  
        providers.forEach(provider => {  
            const providerData = apiConfig[provider.key];  
            if (providerData) {  
                const card = this.createAPIProviderCard(provider.key, provider.display, providerData, currentAPIType);  
                container.appendChild(card);  
            }  
        });  
    } 

    // 创建API提供商卡片    
    createAPIProviderCard(providerKey, providerDisplay, providerData, currentAPIType) {  
        const card = document.createElement('div');  
        card.className = 'api-provider-card';  
        if (providerKey === currentAPIType) {  
            card.classList.add('active');  
        }  
        
        // 卡片头部  
        const header = document.createElement('div');  
        header.className = 'provider-header';  
        
        const titleGroup = document.createElement('div');  
        titleGroup.className = 'provider-title-group';  
        
        const name = document.createElement('div');  
        name.className = 'provider-name';  
        name.textContent = providerDisplay;  
        
        const badge = document.createElement('span');  
        badge.className = `provider-badge ${providerKey === currentAPIType ? 'active' : 'inactive'}`;  
        badge.textContent = providerKey === currentAPIType ? '使用中' : '未使用';  
        
        titleGroup.appendChild(name);  
        titleGroup.appendChild(badge);  
        
        const toggleBtn = document.createElement('button');  
        toggleBtn.className = `provider-toggle-btn ${providerKey === currentAPIType ? 'active' : ''}`;  
        toggleBtn.textContent = providerKey === currentAPIType ? '当前使用' : '设为当前';  
        toggleBtn.disabled = providerKey === currentAPIType;
        toggleBtn.addEventListener('click', async () => {  
            await this.setCurrentAPIProvider(providerKey);  
        });  
        
        header.appendChild(titleGroup);  
        header.appendChild(toggleBtn);  
        
        // 表单内容  
        const form = document.createElement('div');  
        form.className = 'provider-form';  
        
        // 行1: KEY名称和API BASE同一行,各占一半  
        const row1 = document.createElement('div');  
        row1.className = 'form-row';  
        
        const keyNameGroup = this.createFormGroup(  
            'KEY名称',  
            'text',  
            `api-${providerKey}-key-name`,  
            providerData.key || '',  
            '',  
            false,  
            true  // 只读  
        );  
        keyNameGroup.classList.add('form-group-half');  
        
        const apiBaseGroup = this.createFormGroup(  
            'API BASE',  
            'text',  
            `api-${providerKey}-api-base`,  
            providerData.api_base || '',  
            '',  
            false,  
            true  // 只读  
        );  
        apiBaseGroup.classList.add('form-group-half');  
        
        /*
        const keyNameGroup = this.createFormGroup(    
            'KEY名称',    
            'text',    
            `api-${providerKey}-key-name`,    
            providerData.key || '',    
            '',    
            false,    
            false
        );    
        keyNameGroup.classList.add('form-group-half');  
        const keyNameInput = keyNameGroup.querySelector('input');  
        if (keyNameInput) {  
            keyNameInput.disabled = true;  
            keyNameInput.style.userSelect = 'none';  
            keyNameInput.style.cursor = 'not-allowed';  
        }  
        
        const apiBaseGroup = this.createFormGroup(    
            'API BASE',    
            'text',    
            `api-${providerKey}-api-base`,    
            providerData.api_base || '',    
            '',    
            false,    
            false  
        );    
        apiBaseGroup.classList.add('form-group-half');  
        const apiBaseInput = apiBaseGroup.querySelector('input');  
        if (apiBaseInput) {  
            apiBaseInput.disabled = true;  
            apiBaseInput.style.userSelect = 'none';  
            apiBaseInput.style.cursor = 'not-allowed';  
        }
         */
        row1.appendChild(keyNameGroup);  
        row1.appendChild(apiBaseGroup);  
        
        // 行2: KEY选择和模型选择同一行,各占一半  
        const row2 = document.createElement('div');  
        row2.className = 'form-row';  
        
        // 左侧: KEY选择  
        const keySelectGroup = document.createElement('div');  
        keySelectGroup.className = 'form-group form-group-half';  
        
        const keySelectLabel = document.createElement('label');  
        keySelectLabel.textContent = 'API KEY';  
        const keyRequiredSpan = document.createElement('span');  
        keyRequiredSpan.className = 'required';  
        keyRequiredSpan.textContent = ' *';  
        keySelectLabel.appendChild(keyRequiredSpan);  
        
        const keySelect = this.createEditableSelect(  
            providerKey,  
            'API KEY',  
            providerData.api_key || [],  
            providerData.key_index || 0  
        );  
        
        keySelectGroup.appendChild(keySelectLabel);  
        keySelectGroup.appendChild(keySelect);  
        
        // 右侧: 模型选择  
        const modelSelectGroup = document.createElement('div');  
        modelSelectGroup.className = 'form-group form-group-half';  
        
        const modelSelectLabel = document.createElement('label');  
        modelSelectLabel.textContent = '模型';  
        const modelRequiredSpan = document.createElement('span');  
        modelRequiredSpan.className = 'required';  
        modelRequiredSpan.textContent = ' *';  
        modelSelectLabel.appendChild(modelRequiredSpan);  
        
        const modelSelect = this.createEditableSelect(  
            providerKey,  
            '模型',  
            providerData.model || [],  
            providerData.model_index || 0  
        );  
        
        modelSelectGroup.appendChild(modelSelectLabel);  
        modelSelectGroup.appendChild(modelSelect);  
        
        row2.appendChild(keySelectGroup);  
        row2.appendChild(modelSelectGroup);  
        
        // 组装表单  
        form.appendChild(row1);  
        form.appendChild(row2);  
        
        // 组装卡片  
        card.appendChild(header);  
        card.appendChild(form);  
        
        return card;  
    }

    // 创建自定义下拉框  
    createEditableSelect(providerKey, type, items, selectedIndex) {  
        const container = document.createElement('div');  
        container.className = 'editable-select';  
        
        const validItems = items.filter(item => item && item.trim() !== '');  
        
        // 当前选中值显示  
        const display = document.createElement('div');  
        display.className = 'select-display';  
        // 如果选中的是空字符串或索引超出有效范围,显示"-- 点击添加 --"  
        const selectedItem = validItems[selectedIndex];  
        display.textContent = selectedItem || '-- 点击添加 --';  
        
        // 下拉选项容器  
        const dropdown = document.createElement('div');  
        dropdown.className = 'select-dropdown';  
        dropdown.style.display = 'none';  
        
        // 渲染选项列表  
        const renderOptions = () => {  
            dropdown.innerHTML = '';  
            
            const addOption = document.createElement('div');  
            addOption.className = 'select-option select-option-add';  
            addOption.textContent = '-- 点击添加 --';  
            addOption.addEventListener('click', (e) => {  
                e.stopPropagation();   
                showAddInput();  
            });  
            dropdown.appendChild(addOption);  
            
            // 现有选项  
            validItems.forEach((item, index) => {  
                const option = document.createElement('div');  
                option.className = 'select-option';  
                option.textContent = item;  
                
                // 点击选项  
                option.addEventListener('click', async (e) => {  
                    e.stopPropagation(); 
                    display.textContent = item;  
                    dropdown.style.display = 'none';  
                    
                    const originalIndex = items.indexOf(item);  
                    const fieldName = type === 'API KEY' ? 'key_index' : 'model_index';  
                    
                    await this.updateConfig({  
                        api: {  
                            [providerKey]: {  
                                ...this.config.api[providerKey],  
                                [fieldName]: originalIndex  
                            }  
                        }  
                    });  
                });  
                
                // 右键菜单  
                option.addEventListener('contextmenu', (e) => {  
                    const originalIndex = items.indexOf(item);  
                    this.showContextMenu(e, providerKey, type, originalIndex, item);  
                });  
                
                dropdown.appendChild(option);  
            });  
        };  
        
        // 显示添加输入框  
        const showAddInput = () => {  
            dropdown.innerHTML = '';  
            
            const input = document.createElement('input');  
            input.type = 'text';  
            input.className = 'select-input';  
            input.placeholder = `输入新的${type}`;  
            
            // 回车添加  
            input.addEventListener('keydown', async (e) => {  
                if (e.key === 'Enter') {  
                    const newValue = input.value.trim();  
                    if (newValue) {  
                        if (type === 'API KEY') {  
                            await this.addAPIKey(providerKey, newValue);  
                        } else {  
                            await this.addModel(providerKey, newValue);  
                        }  
                        
                        dropdown.style.display = 'none';  
                    }  
                } else if (e.key === 'Escape') {  
                    renderOptions();  
                }  
            });  
            
            input.addEventListener('blur', () => {  
                if (!input.value.trim()) {  
                    renderOptions();  
                }  
            });  
            
            input.addEventListener('click', (e) => {  
                e.stopPropagation();  
            });  
            
            dropdown.appendChild(input);  
            setTimeout(() => input.focus(), 0);  
        };  
        
        // 初始化选项  
        renderOptions();  
        
        // 点击显示框切换下拉框  
        display.addEventListener('click', (e) => {  
            e.stopPropagation();  
            const isVisible = dropdown.style.display === 'block';  
            dropdown.style.display = isVisible ? 'none' : 'block';  
            
            if (!isVisible) {  
                renderOptions(); // 每次打开时重新渲染选项  
            }  
        });  
        
        // 点击外部关闭  
        document.addEventListener('click', (e) => {  
            if (!container.contains(e.target)) {  
                dropdown.style.display = 'none';  
            }  
        });  
        
        container.appendChild(display);  
        container.appendChild(dropdown);  
        
        return container;  
    }
        
    // 显示右键菜单    
    showContextMenu(e, providerKey, type, index, item) {  
        e.preventDefault();  
        
        // 移除已存在的菜单  
        const existingMenu = document.querySelector('.context-menu');  
        if (existingMenu) {  
            existingMenu.remove();  
        }  
        
        // 创建菜单  
        const menu = document.createElement('div');  
        menu.className = 'context-menu';  
        menu.style.left = `${e.pageX}px`;  
        menu.style.top = `${e.pageY}px`;  
        
        // 删除选项  
        const deleteItem = document.createElement('div');  
        deleteItem.className = 'context-menu-item';  
        deleteItem.textContent = '删除';  
        deleteItem.addEventListener('click', async () => {  
            // 使用自定义确认弹窗而非系统confirm  
            window.dialogManager.showConfirm(  
                `确定删除这个${type}吗?`,  
                async () => {  
                    if (type === 'API KEY') {  
                        await this.deleteAPIKey(providerKey, index);  
                    } else {  
                        await this.deleteModel(providerKey, index);  
                    }  
                }  
            );  
            menu.remove();  
        });  
        
        menu.appendChild(deleteItem);  
        document.body.appendChild(menu);  
        
        // 点击外部关闭菜单  
        setTimeout(() => {  
            const closeMenu = () => {  
                menu.remove();  
                document.removeEventListener('click', closeMenu);  
            };  
            document.addEventListener('click', closeMenu);  
        }, 0);  
    }
    
    // 更新API选择    
    async updateAPISelection(providerKey, type, index) {    
        const fieldName = type === 'API KEY' ? 'key_index' : 'model_index';    
        await this.updateConfig({    
            api: {    
                [providerKey]: {    
                    ...this.config.api[providerKey],    
                    [fieldName]: index    
                }    
            }    
        });    
    }

    // 添加API KEY    
    async addAPIKey(providerKey, value) {    
        const apiKeys = [...(this.config.api[providerKey].api_key || [])];    
        apiKeys.push(value || '');    
        
        await this.updateConfig({    
            api: {    
                [providerKey]: {    
                    ...this.config.api[providerKey],    
                    api_key: apiKeys    
                }    
            }    
        });    
        
        this.populateAPIUI();    
    }    
    
    // 删除API KEY    
    async deleteAPIKey(providerKey, index) {    
        const apiKeys = [...(this.config.api[providerKey].api_key || [])];    
        apiKeys.splice(index, 1);    
        
        let keyIndex = this.config.api[providerKey].key_index;    
        if (keyIndex >= apiKeys.length) {    
            keyIndex = Math.max(0, apiKeys.length - 1);    
        }    
        
        await this.updateConfig({    
            api: {    
                [providerKey]: {    
                    ...this.config.api[providerKey],    
                    api_key: apiKeys,    
                    key_index: keyIndex    
                }    
            }    
        });    
        
        this.populateAPIUI();    
    }

    // 更新指定索引的KEY    
    async updateAPIKeyAtIndex(providerKey, index, value) {    
        const apiKeys = [...(this.config.api[providerKey].api_key || [])];    
        apiKeys[index] = value;    
        
        await this.updateConfig({    
            api: {    
                [providerKey]: {    
                    ...this.config.api[providerKey],    
                    api_key: apiKeys    
                }    
            }    
        });    
    }  
    
    // 添加模型    
    async addModel(providerKey, value) {    
        const models = [...(this.config.api[providerKey].model || [])];    
        models.push(value || '');    
        
        await this.updateConfig({    
            api: {    
                [providerKey]: {    
                    ...this.config.api[providerKey],    
                    model: models    
                }    
            }    
        });    
        
        this.populateAPIUI();    
    }    
    
    // 删除模型    
    async deleteModel(providerKey, index) {    
        const models = [...(this.config.api[providerKey].model || [])];    
        models.splice(index, 1);    
        
        // 如果删除的是当前选中的模型,重置索引    
        let modelIndex = this.config.api[providerKey].model_index;    
        if (modelIndex >= models.length) {    
            modelIndex = Math.max(0, models.length - 1);    
        }    
        
        await this.updateConfig({    
            api: {    
                [providerKey]: {    
                    ...this.config.api[providerKey],    
                    model: models,    
                    model_index: modelIndex    
                }    
            }    
        });    
        
        this.populateAPIUI();    
    }    
    
    // 更新指定索引的模型    
    async updateModelAtIndex(providerKey, index, value) {    
        const models = [...(this.config.api[providerKey].model || [])];    
        models[index] = value;    
        
        await this.updateConfig({    
            api: {    
                [providerKey]: {    
                    ...this.config.api[providerKey],    
                    model: models    
                }    
            }    
        });    
    }  
    
    // 更新API选择(当用户从下拉框选择时)    
    async updateAPISelection(providerKey, type, index) {    
        const fieldName = type === 'API KEY' ? 'key_index' : 'model_index';    
        await this.updateConfig({    
            api: {    
                [providerKey]: {    
                    ...this.config.api[providerKey],    
                    [fieldName]: index    
                }    
            }    
        });    
    }  
    
    // 设置当前API提供商    
    async setCurrentAPIProvider(providerKey) {    
        await this.updateConfig({    
            api: {    
                ...this.config.api,    
                api_type: providerKey    
            }    
        });    
        
        // 刷新UI以更新激活状态    
        this.populateAPIUI();    
        
        window.app?.showNotification(    
            `已切换到 ${providerKey === 'SiliconFlow' ? '硅基流动' : providerKey}`,    
            'success'    
        );    
    }  
    
    // 保存API配置    
    async saveAPIConfig() {    
        const success = await this.saveConfig();    
        
        if (success) {    
            // 清除未保存提示    
            const saveBtn = document.getElementById('save-api-config');    
            if (saveBtn) {    
                saveBtn.classList.remove('has-changes');    
                saveBtn.innerHTML = '<i class="icon-save"></i> 保存配置';    
            }    
        }    
        
        window.app?.showNotification(    
            success ? 'API配置已保存' : '保存API配置失败',    
            success ? 'success' : 'error'    
        );    
    }  
    
    // 恢复默认API配置    
    async resetAPIConfig() {  
        // 使用自定义确认弹窗  
        window.dialogManager.showConfirm(  
            '确定要恢复默认API配置吗？这将清除所有自定义设置。',  
            async () => {  
                try {  
                    const response = await fetch(`${this.apiEndpoint}/default`);  
                    if (!response.ok) throw new Error('获取默认配置失败');  
                    
                    const result = await response.json();  
                    const defaultAPI = result.data.api;  
                    
                    // 更新配置到内存  
                    await this.updateConfig({ api: defaultAPI });  
                    
                    // 刷新UI  
                    this.populateAPIUI();  
                    
                    window.app?.showNotification('已恢复默认API配置', 'success');  
                } catch (error) {  
                    console.error('恢复默认配置失败:', error);  
                    window.app?.showNotification('恢复默认配置失败', 'error');  
                }  
            }  
        );  
    }

    bindConfigNavigation() {  
        const links = document.querySelectorAll('.nav-sublink');          
        links.forEach((link, index) => {  
            link.addEventListener('click', (e) => {  
                e.preventDefault();  
                const configType = link.dataset.config;  
                this.showConfigPanel(configType);  
            });  
        });  
    }    
        
    showConfigPanel(panelType) {  
        const configContent = document.querySelector('.config-content');  
        const targetPanel = document.getElementById(`config-${panelType}`);  
        
        this.currentPanel = panelType; 

        // 关键:在任何DOM操作之前立即重置滚动位置  
        if (configContent) {  
            configContent.scrollTop = 0;  
        }  
        
        // 隐藏所有配置面板  
        document.querySelectorAll('.config-panel').forEach(panel => {  
            if (panel !== targetPanel) {  
                panel.classList.remove('active');  
                panel.style.display = 'none';  
            }  
        });  
        
        // 显示目标面板  
        if (targetPanel) {  
            targetPanel.style.display = 'block';  
            targetPanel.offsetHeight; // 强制重排  
            targetPanel.classList.add('active');  
        }  
        
        // 更新导航状态  
        document.querySelectorAll('.config-nav-item').forEach(item => {  
            item.classList.remove('active');  
        });  
        
        const activeNavItem = document.querySelector(`[data-config="${panelType}"]`)?.parentElement;  
        if (activeNavItem) {  
            activeNavItem.classList.add('active');  
        }   
        
        this.populateUI();  
    }  
  
    // ========== UI配置管理(localStorage) ==========  
      
    loadUIConfig() {    
        try {    
            const saved = localStorage.getItem('aiwritex_ui_config');    
            const defaultConfig = {    
                theme: 'light',    
                windowMode: 'STANDARD'    
            };    
              
            if (saved) {    
                return { ...defaultConfig, ...JSON.parse(saved) };    
            }    
            return defaultConfig;    
        } catch (e) {    
            return { theme: 'light', windowMode: 'STANDARD' };    
        }    
    }    
      
    async saveUIConfig(updates) {    
        try {    
            const newConfig = updates.theme !== undefined && updates.windowMode !== undefined     
                ? updates     
                : { ...this.uiConfig, ...updates };    
              
            // 1. 保存到 localStorage    
            localStorage.setItem('aiwritex_ui_config', JSON.stringify(newConfig));    
            this.uiConfig = newConfig;    
              
            // 2. 同步到后端文件(持久化)    
            const response = await fetch('/api/config/ui-config', {    
                method: 'POST',    
                headers: { 'Content-Type': 'application/json' },    
                body: JSON.stringify(newConfig)    
            });    
              
            if (!response.ok) {    
                throw new Error('保存失败');    
            }    
              
            return true;    
        } catch (e) {    
            console.error('保存 UI 配置失败:', e);    
            return false;    
        }    
    }  
  
    getUIConfig() {    
        return this.uiConfig;    
    }  
  
    getTheme() {    
        return this.uiConfig.theme;    
    }    
        
    setTheme(theme) {    
        return this.saveUIConfig({ theme: theme });    
    }    
        
    getWindowMode() {    
        return this.uiConfig.windowMode;    
    }    
        
    setWindowMode(mode) {    
        return this.saveUIConfig({ windowMode: mode });    
    }    
        
    // ========== 业务配置管理(后端API) ==========  
      
    async loadConfig() {    
        try {    
            const response = await fetch(this.apiEndpoint);    
            if (!response.ok) {    
                throw new Error(`HTTP ${response.status}`);    
            }    
                
            const result = await response.json();    
            this.config = result.data;    
                
            return true;    
        } catch (error) {    
            console.error('加载配置失败:', error);  
            return false;    
        }    
    }

    // 加载动态选项数据  
    async loadDynamicOptions() {  
        try {  
            // 加载发布平台列表  
            const platformsResponse = await fetch('/api/config/platforms');  
            if (platformsResponse.ok) {  
                const result = await platformsResponse.json();  
                this.platforms = result.data;  
                this.populatePlatformOptions();  
            }  
            
            // 加载模板分类列表  
            const categoriesResponse = await fetch('/api/config/template-categories');  
            if (categoriesResponse.ok) {  
                const result = await categoriesResponse.json();  
                this.templateCategories = result.data;  
                this.populateTemplateCategoryOptions();  
            }  
        } catch (error) {  
            console.error('加载动态选项失败:', error);  
        }  
    }  
    
    // 填充发布平台选项  
    populatePlatformOptions() {  
        const publishPlatformSelect = document.getElementById('publish-platform');  
        if (!publishPlatformSelect || !this.platforms) return;  
        
        // 清空现有选项  
        publishPlatformSelect.innerHTML = '';  
        
        // 添加平台选项  
        this.platforms.forEach(platform => {  
            const option = document.createElement('option');  
            option.value = platform.value;  
            option.textContent = platform.label;  
            publishPlatformSelect.appendChild(option);  
        });  
        
        // 禁用选择器(只支持微信)  
        publishPlatformSelect.disabled = true;  
    }  
    
    // 填充模板分类选项  
    populateTemplateCategoryOptions() {  
        const templateCategorySelect = document.getElementById('template-category');  
        if (!templateCategorySelect || !this.templateCategories) return;  
        
        // 清空现有选项  
        templateCategorySelect.innerHTML = '';  
        
        // 添加"随机分类"选项  
        const randomOption = document.createElement('option');  
        randomOption.value = '';  
        randomOption.textContent = '随机分类';  
        templateCategorySelect.appendChild(randomOption);  
        
        // 添加分类选项  
        this.templateCategories.forEach(category => {  
            const option = document.createElement('option');  
            option.value = category;  
            option.textContent = category;  
            templateCategorySelect.appendChild(option);  
        });  
    }  
    
    // 加载指定分类的模板列表  
    async loadTemplatesByCategory(category) {  
        try {  
            if (!category || category === '随机分类') {  
                return [];  
            }  
            
            const response = await fetch(`/api/config/templates/${encodeURIComponent(category)}`);  
            if (!response.ok) {  
                throw new Error(`HTTP ${response.status}`);  
            }  
            
            const result = await response.json();  
            return result.data || [];  
        } catch (error) {  
            console.error('加载模板列表失败:', error);  
            return [];  
        }  
    }

    // 填充图片API UI  
    populateImgAPIUI() {  
        const container = document.getElementById('img-api-providers-container');  
        if (!container || !this.config.img_api) return;  
        
        const currentImgAPIType = this.config.img_api.api_type;  
        
        // 清空现有内容  
        container.innerHTML = '';  
        
        // 定义提供商列表(固定两个:picsum和ali)  
        const providers = [  
            { key: 'picsum', display: 'Picsum(随机)' },  
            { key: 'ali', display: '阿里' }  
        ];  
        
        // 生成提供商卡片  
        providers.forEach(provider => {  
            const providerData = this.config.img_api[provider.key];  
            if (providerData) {  
                const card = this.createImgAPIProviderCard(  
                    provider.key,   
                    provider.display,   
                    providerData,   
                    currentImgAPIType  
                );  
                container.appendChild(card);  
            }  
        });  
    }  
    
    // 创建图片API提供商卡片  
    createImgAPIProviderCard(providerKey, providerDisplay, providerData, currentImgAPIType) {  
        const card = document.createElement('div');  
        card.className = 'api-provider-card';  
        if (providerKey === currentImgAPIType) {  
            card.classList.add('active');  
        }  
        
        // 卡片头部  
        const header = document.createElement('div');  
        header.className = 'provider-header';  
        
        const titleGroup = document.createElement('div');  
        titleGroup.className = 'provider-title-group';  
        
        const name = document.createElement('div');  
        name.className = 'provider-name';  
        name.textContent = providerDisplay;  
        
        const badge = document.createElement('span');  
        badge.className = `provider-badge ${providerKey === currentImgAPIType ? 'active' : 'inactive'}`;  
        badge.textContent = providerKey === currentImgAPIType ? '使用中' : '未使用';  
        
        titleGroup.appendChild(name);  
        titleGroup.appendChild(badge);  
        
        const toggleBtn = document.createElement('button');  
        toggleBtn.className = `provider-toggle-btn ${providerKey === currentImgAPIType ? 'active' : ''}`;  
        toggleBtn.textContent = providerKey === currentImgAPIType ? '当前使用' : '设为当前';  
        toggleBtn.disabled = providerKey === currentImgAPIType;  
        toggleBtn.addEventListener('click', async () => {  
            await this.setCurrentImgAPIProvider(providerKey);  
        });  
        
        header.appendChild(titleGroup);  
        header.appendChild(toggleBtn);  
        
        // 表单内容  
        const form = document.createElement('div');  
        form.className = 'provider-form';  
        
        // API KEY字段  
        const apiKeyGroup = this.createFormGroup(  
            'API KEY',  
            'text',  
            `img-api-${providerKey}-api-key`,  
            providerData.api_key || '',  
            providerKey === 'picsum'?"随机图片无需API KEY" : "请输入API KEY",  
            false  
        );  
        apiKeyGroup.classList.add('form-group-half');  
        
        // 模型字段  
        const modelGroup = this.createFormGroup(  
            '模型',  
            'text',  
            `img-api-${providerKey}-model`,  
            providerData.model || '',  
            providerKey === 'picsum'?"随机图片无需模型" : "请输入模型名称",   
            false  
        );  
        modelGroup.classList.add('form-group-half');  
        
        if (providerKey === 'picsum') {  
            const inputs = [  
                apiKeyGroup.querySelector('input'),  
                modelGroup.querySelector('input')  
            ];  
            inputs.forEach(input => {  
                if (input) {  
                    input.disabled = true;  
                    input.style.userSelect = 'none';  
                    input.style.cursor = 'not-allowed';  
                }  
            });  
        }
        
        const row = document.createElement('div');  
        row.className = 'form-row';  
        row.appendChild(apiKeyGroup);  
        row.appendChild(modelGroup);  
        
        form.appendChild(row);  
        
        // 组装卡片  
        card.appendChild(header);  
        card.appendChild(form);  
        
        return card;  
    }
    
    // 切换当前图片API提供商  
    async setCurrentImgAPIProvider(providerKey) {  
        await this.updateConfig({  
            img_api: {  
                ...this.config.img_api,  
                api_type: providerKey  
            }  
        });  
        
        // 刷新UI  
        this.populateImgAPIUI();  
        
        window.app?.showNotification(  
            `已切换到${providerKey === 'picsum' ? 'Picsum(随机)' : '阿里'}`,  
            'success'  
        );  
    }  
    
    // 切换当前图片API提供商  
    async setCurrentImgAPIProvider(providerKey) {  
        await this.updateConfig({  
            img_api: {  
                ...this.config.img_api,  
                api_type: providerKey  
            }  
        });  
        
        // 刷新UI  
        this.populateImgAPIUI();  
        
        window.app?.showNotification(  
            `已切换到${providerKey === 'picsum' ? 'Picsum(随机)' : '阿里'}`,  
            'success'  
        );  
    }  
    
    // 更新图片API提供商字段  
    async updateImgAPIProviderField(providerKey, field, value) {  
        await this.updateConfig({  
            img_api: {  
                ...this.config.img_api,  
                [providerKey]: {  
                    ...this.config.img_api[providerKey],  
                    [field]: value  
                }  
            }  
        });  
    }
    // 保存图片API配置  
    async saveImgAPIConfig() {  
        // 收集所有提供商的配置  
        const imgApiConfig = {  
            api_type: this.config.img_api.api_type,  
            picsum: {  
                api_key: document.getElementById('img-api-picsum-api-key')?.value || '',  
                model: document.getElementById('img-api-picsum-model')?.value || ''  
            },  
            ali: {  
                api_key: document.getElementById('img-api-ali-api-key')?.value || '',  
                model: document.getElementById('img-api-ali-model')?.value || ''  
            }  
        };  
        
        // 验证:如果选择阿里,必须填写API KEY  
        if (imgApiConfig.api_type === 'ali' && !imgApiConfig.ali.api_key.trim()) {  
            window.app?.showNotification('阿里API需要配置API KEY', 'error');  
            return;  
        }  
        
        // 更新配置  
        await this.updateConfig({ img_api: imgApiConfig });  
        
        // 保存到文件  
        const success = await this.saveConfig();  
        
        if (success) {  
            // 清除未保存提示  
            const saveBtn = document.getElementById('save-img-api-config');  
            if (saveBtn) {  
                saveBtn.classList.remove('has-changes');  
                saveBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
            }  
        }  
        
        window.app?.showNotification(  
            success ? '图片API配置已保存' : '保存图片API配置失败',  
            success ? 'success' : 'error'  
        );  
    }  
    
    // 恢复默认图片API配置  
    async resetImgAPIConfig() {  
        window.dialogManager.showConfirm(  
            '确定要恢复默认图片API配置吗？这将清除所有自定义设置。',  
            async () => {  
                try {  
                    const response = await fetch(`${this.apiEndpoint}/default`);  
                    if (!response.ok) throw new Error('获取默认配置失败');  
                    
                    const result = await response.json();  
                    const defaultImgAPI = result.data.img_api;  
                    
                    await this.updateConfig({ img_api: defaultImgAPI });  
                    this.populateImgAPIUI();  
                    
                    window.app?.showNotification('已恢复默认图片API配置', 'success');  
                } catch (error) {  
                    console.error('恢复默认配置失败:', error);  
                    window.app?.showNotification('恢复默认配置失败', 'error');  
                }  
            }  
        );  
    }

    // 填充AIForge配置UI  
    populateAIForgeUI() {  
        if (!this.config.aiforge_config) return;  
        
        const aiforgeConfig = this.config.aiforge_config;  
        
        // 填充通用配置  
        const maxRoundsInput = document.getElementById('aiforge-max-rounds');  
        if (maxRoundsInput && aiforgeConfig.max_rounds !== undefined) {  
            maxRoundsInput.value = aiforgeConfig.max_rounds;  
        }  
        
        const defaultMaxTokensInput = document.getElementById('aiforge-default-max-tokens');  
        if (defaultMaxTokensInput && aiforgeConfig.max_tokens !== undefined) {  
            defaultMaxTokensInput.value = aiforgeConfig.max_tokens;  
        }  
        
        // 填充缓存配置  
        if (aiforgeConfig.cache && aiforgeConfig.cache.code) {  
            const cacheConfig = aiforgeConfig.cache.code;  
            
            const cacheEnabledCheckbox = document.getElementById('cache-enabled');  
            if (cacheEnabledCheckbox && cacheConfig.enabled !== undefined) {  
                cacheEnabledCheckbox.checked = cacheConfig.enabled;  
            }  
            
            const maxModulesInput = document.getElementById('cache-max-modules');  
            if (maxModulesInput && cacheConfig.max_modules !== undefined) {  
                maxModulesInput.value = cacheConfig.max_modules;  
            }  
            
            const failureThresholdInput = document.getElementById('cache-failure-threshold');  
            if (failureThresholdInput && cacheConfig.failure_threshold !== undefined) {  
                failureThresholdInput.value = cacheConfig.failure_threshold;  
            }  
            
            const maxAgeDaysInput = document.getElementById('cache-max-save-days');  
            if (maxAgeDaysInput && cacheConfig.max_age_days !== undefined) {  
                maxAgeDaysInput.value = cacheConfig.max_age_days;  
            }  
            
            const cleanupIntervalInput = document.getElementById('cache-cleanup-interval');  
            if (cleanupIntervalInput && cacheConfig.cleanup_interval !== undefined) {  
                cleanupIntervalInput.value = cacheConfig.cleanup_interval;  
            }  
        }  
        
        // 填充LLM提供商卡片  
        this.populateAIForgeLLMUI();  
    }

    // 填充AIForge LLM提供商UI  
    populateAIForgeLLMUI() {  
        const container = document.getElementById('aiforge-llm-providers-container');  
        if (!container || !this.config.aiforge_config) return;  
        
        const aiforgeConfig = this.config.aiforge_config;  
        const currentProvider = aiforgeConfig.default_llm_provider;  
        
        // 清空现有内容  
        container.innerHTML = '';  
        
        // 获取所有LLM提供商  
        const providers = Object.keys(aiforgeConfig.llm).map(key => ({  
            key: key,  
            display: key.charAt(0).toUpperCase() + key.slice(1)  
        }));  
        
        // 为每个提供商生成卡片  
        providers.forEach(provider => {  
            const providerData = aiforgeConfig.llm[provider.key];  
            if (providerData) {  
                const card = this.createAIForgeLLMProviderCard(  
                    provider.key,  
                    provider.display,  
                    providerData,  
                    currentProvider  
                );  
                container.appendChild(card);  
            }  
        });  
    } 
  
    // 创建AIForge LLM提供商卡片  
    createAIForgeLLMProviderCard(providerKey, providerDisplay, providerData, currentProvider) {  
        const card = document.createElement('div');  
        card.className = 'api-provider-card';  
        if (providerKey === currentProvider) {  
            card.classList.add('active');  
        }  
        
        // ========== 卡片头部 ==========  
        const header = document.createElement('div');  
        header.className = 'provider-header';  
        
        const titleGroup = document.createElement('div');  
        titleGroup.className = 'provider-title-group';  
        
        const name = document.createElement('div');  
        name.className = 'provider-name';  
        name.textContent = providerDisplay;  
        
        const badge = document.createElement('span');  
        badge.className = `provider-badge ${providerKey === currentProvider ? 'active' : 'inactive'}`;  
        badge.textContent = providerKey === currentProvider ? '使用中' : '未使用';  
        
        titleGroup.appendChild(name);  
        titleGroup.appendChild(badge);  
        
        const toggleBtn = document.createElement('button');  
        toggleBtn.className = `provider-toggle-btn ${providerKey === currentProvider ? 'active' : ''}`;  
        toggleBtn.textContent = providerKey === currentProvider ? '当前使用' : '设为当前';  
        toggleBtn.disabled = providerKey === currentProvider;  
        toggleBtn.addEventListener('click', async () => {  
            await this.setCurrentAIForgeLLMProvider(providerKey);  
        });  
        
        header.appendChild(titleGroup);  
        header.appendChild(toggleBtn);  
        
        // ========== 表单内容 ==========  
        const form = document.createElement('div');  
        form.className = 'provider-form';  
        
        // ✅ 第一行:类型、模型、API KEY(三个字段)  
        const row1 = document.createElement('div');  
        row1.className = 'form-row';  
        
        // 类型(只读)  
        const typeGroup = this.createFormGroup(  
            '类型',  
            'text',  
            `aiforge-${providerKey}-type`,  
            providerData.type || '',  
            '',  
            false,  
            false  
        );  
        typeGroup.classList.add('form-group-third');  
        const typeInput = typeGroup.querySelector('input');  
        if (typeInput) {  
            typeInput.disabled = true;  
            typeInput.style.userSelect = 'none';  
            typeInput.style.cursor = 'not-allowed';  
        }  
        
        // 模型  
        const modelGroup = this.createFormGroup(  
            '模型',  
            'text',  
            `aiforge-${providerKey}-model`,  
            providerData.model || '',  
            '使用的具体模型名称',  
            true  
        );  
        modelGroup.classList.add('form-group-third');  
        
        // API KEY  
        const apiKeyGroup = this.createFormGroup(  
            'API KEY',  
            'text',  
            `aiforge-${providerKey}-api-key`,  
            providerData.api_key || '',  
            '模型提供商的API KEY',  
            true  
        );  
        apiKeyGroup.classList.add('form-group-third');  
        
        row1.appendChild(typeGroup);  
        row1.appendChild(modelGroup);  
        row1.appendChild(apiKeyGroup);  
        
        // ✅ 第二行:Base URL、超时时间、最大Tokens(三个字段)  
        const row2 = document.createElement('div');  
        row2.className = 'form-row';  
        
        // Base URL  
        const baseUrlGroup = this.createFormGroup(  
            'Base URL',  
            'text',  
            `aiforge-${providerKey}-base-url`,  
            providerData.base_url || '',  
            'API的基础地址',  
            true,
            true
        );  
        baseUrlGroup.classList.add('form-group-third');  
        
        // 超时时间  
        const timeoutGroup = this.createFormGroup(  
            '超时时间(秒)',  
            'number',  
            `aiforge-${providerKey}-timeout`,  
            providerData.timeout || 30,  
            'API请求的超时时间'  
        );  
        timeoutGroup.classList.add('form-group-third');  
        
        // 最大Tokens  
        const maxTokensGroup = this.createFormGroup(  
            '最大Tokens',  
            'number',  
            `aiforge-${providerKey}-max-tokens`,  
            providerData.max_tokens || 8192,  
            '控制生成内容的长度'  
        );  
        maxTokensGroup.classList.add('form-group-third');  
        
        row2.appendChild(baseUrlGroup);  
        row2.appendChild(timeoutGroup);  
        row2.appendChild(maxTokensGroup);  
        
        // ========== 组装表单 ==========  
        form.appendChild(row1);  
        form.appendChild(row2);  
        
        // ========== 组装卡片 ==========  
        card.appendChild(header);  
        card.appendChild(form);  
        
        return card;  
    }  
    
    // 切换当前AIForge LLM提供商  
    async setCurrentAIForgeLLMProvider(providerKey) {  
        await this.updateConfig({  
            aiforge_config: {  
                ...this.config.aiforge_config,  
                default_llm_provider: providerKey  
            }  
        });  
        
        // 刷新UI  
        this.populateAIForgeLLMUI();  
        
        window.app?.showNotification(  
            `已切换到${providerKey}`,  
            'success'  
        );  
    }

    // 更新AIForge LLM提供商字段  
    async updateAIForgeLLMProviderField(providerKey, field, value) {  
        // 字段名映射  
        const fieldMap = {  
            'api-key': 'api_key',  
            'base-url': 'base_url',  
            'max-tokens': 'max_tokens'  
        };  
        const actualField = fieldMap[field] || field;  
        
        // 类型字段是只读的,不更新  
        if (actualField === 'type') {  
            return;  
        }  
        
        await this.updateConfig({  
            aiforge_config: {  
                ...this.config.aiforge_config,  
                llm: {  
                    ...this.config.aiforge_config.llm,  
                    [providerKey]: {  
                        ...this.config.aiforge_config.llm[providerKey],  
                        [actualField]: value  
                    }  
                }  
            }  
        });  
    }  
    
    // 填充创意配置UI  
    populateCreativeUI() {  
        if (!this.config.dimensional_creative) return;  
        
        const creativeConfig = this.config.dimensional_creative;  
        
        // 填充全局配置  
        const enabledCheckbox = document.getElementById('creative-enabled');  
        if (enabledCheckbox) {  
            enabledCheckbox.checked = creativeConfig.enabled || false;  
        }  
        
        const intensitySlider = document.getElementById('creative-intensity');  
        if (intensitySlider) {  
            intensitySlider.value = creativeConfig.creative_intensity || 1.0;  
            this.updateSliderValue(intensitySlider);
            intensitySlider.addEventListener('input', (e) => {  
                this.updateSliderValue(e.target);  
                
                // 更新配置  
                this.updateConfig({  
                    dimensional_creative: {  
                        ...this.config.dimensional_creative,  
                        creative_intensity: parseFloat(e.target.value)  
                    }  
                });  
            }); 
        }
        
        const preserveCheckbox = document.getElementById('preserve-core-info');  
        if (preserveCheckbox) {  
            preserveCheckbox.checked = creativeConfig.preserve_core_info !== false;  
        }  
        
        const autoSelectionCheckbox = document.getElementById('auto-dimension-selection');  
        if (autoSelectionCheckbox) {  
            autoSelectionCheckbox.checked = creativeConfig.auto_dimension_selection || false;  
        }  
        
        const maxDimensionsInput = document.getElementById('max-dimensions');  
        if (maxDimensionsInput) {  
            maxDimensionsInput.value = creativeConfig.max_dimensions || 5;  
        }  
        
        const thresholdSlider = document.getElementById('compatibility-threshold');  
        if (thresholdSlider) {  
            thresholdSlider.value = creativeConfig.compatibility_threshold || 0.6;  
            this.updateSliderValue(thresholdSlider);
            thresholdSlider.addEventListener('input', (e) => {  
                this.updateSliderValue(e.target);  
                
                // 更新配置  
                this.updateConfig({  
                    dimensional_creative: {  
                        ...this.config.dimensional_creative,  
                        compatibility_threshold: parseFloat(e.target.value)  
                    }  
                });  
            });
        }  
        
        const experimentalCheckbox = document.getElementById('allow-experimental');  
        if (experimentalCheckbox) {  
            experimentalCheckbox.checked = creativeConfig.allow_experimental || false;  
        }  
        
        // 生成维度分组卡片  
        this.populateDimensionGroups();  

        const globalEnabled = creativeConfig.enabled || false;  
        const autoSelection = creativeConfig.auto_dimension_selection || false;  
        const enabledDimensions = creativeConfig.enabled_dimensions || {};  
        
        // 更新全局控件  
        if (intensitySlider) intensitySlider.disabled = !globalEnabled;  
        if (preserveCheckbox) preserveCheckbox.disabled = !globalEnabled;  
        if (experimentalCheckbox) experimentalCheckbox.disabled = !globalEnabled;  
        if (autoSelectionCheckbox) autoSelectionCheckbox.disabled = !globalEnabled;  
        if (maxDimensionsInput) maxDimensionsInput.disabled = !globalEnabled || !autoSelection;  
        if (thresholdSlider) thresholdSlider.disabled = !globalEnabled || !autoSelection;  
        
        // 更新所有维度控件  
        Object.keys(enabledDimensions).forEach(dimensionKey => {  
            const checkbox = document.getElementById(`dimension-${dimensionKey}-enabled`);  
            const select = document.getElementById(`dimension-${dimensionKey}-select`);  
            const customInput = document.getElementById(`dimension-${dimensionKey}-custom`);  
            const isEnabled = enabledDimensions[dimensionKey];  
            
            if (checkbox) {  
                checkbox.disabled = !globalEnabled;  
            }  
            if (select) {  
                select.disabled = !globalEnabled || autoSelection || !isEnabled;  
            }  
            if (customInput) {  
                const selectValue = select?.value;  
                customInput.disabled = !globalEnabled || !isEnabled || selectValue !== 'custom';  
            }  
        });  

        this.updateCreativeControlsState(); 
    }

    // 生成维度分组卡片  
     populateDimensionGroups() {  
        const container = document.getElementById('dimension-groups-container');  
        if (!container || !this.config.dimensional_creative) return;  
        
        const creativeConfig = this.config.dimensional_creative;  
        const dimensionOptions = creativeConfig.dimension_options || {};  
        const enabledDimensions = creativeConfig.enabled_dimensions || {};  
        const autoSelection = creativeConfig.auto_dimension_selection || false;  
        const globalEnabled = creativeConfig.enabled || false;  
        
        container.innerHTML = '';  
        
        // 为每个维度分组创建卡片  
        Object.entries(this.DIMENSION_GROUPS).forEach(([groupKey, groupData]) => {  
            const card = this.createDimensionGroupCard(  
                groupKey,  
                groupData,  
                dimensionOptions,  
                enabledDimensions,  
                autoSelection,  
                globalEnabled  
            );  
            container.appendChild(card);  
        });  
    }

    // 更新创意配置所有控件的禁用状态    
    updateCreativeControlsState() {  
        const globalEnabled = document.getElementById('creative-enabled')?.checked || false;  
        const autoSelection = document.getElementById('auto-dimension-selection')?.checked || false;  
        
        // 更新全局控件  
        const intensitySlider = document.getElementById('creative-intensity');  
        const preserveCheckbox = document.getElementById('preserve-core-info');  
        const experimentalCheckbox = document.getElementById('allow-experimental');  
        const maxDimensionsInput = document.getElementById('max-dimensions');  
        const thresholdSlider = document.getElementById('compatibility-threshold');  
        
        if (intensitySlider) intensitySlider.disabled = !globalEnabled;  
        if (preserveCheckbox) preserveCheckbox.disabled = !globalEnabled;  
        if (experimentalCheckbox) experimentalCheckbox.disabled = !globalEnabled;  
        if (maxDimensionsInput) maxDimensionsInput.disabled = !globalEnabled || !autoSelection;  
        if (thresholdSlider) thresholdSlider.disabled = !globalEnabled || !autoSelection;  
        
        Object.entries(this.DIMENSION_GROUPS).forEach(([groupKey, groupData]) => {  
            // 统计该分组中已启用的维度数量  
            let enabledCount = 0;  
            groupData.dimensions.forEach(dimensionKey => {  
                const checkbox = document.getElementById(`dimension-${dimensionKey}-enabled`);  
                if (checkbox && checkbox.checked) {  
                    enabledCount++;  
                }  
            });  
            
            // 查找该分组的徽章元素并更新  
            const cards = document.querySelectorAll('.dimension-group-card');  
            cards.forEach(card => {  
                const cardName = card.querySelector('.dimension-group-name')?.textContent;  
                if (cardName === groupData.name) {  
                    const badge = card.querySelector('.dimension-count-badge');  
                    if (badge) {  
                        badge.textContent = `${enabledCount}/${groupData.dimensions.length}`;  
                    }  
                }  
            });  
        });  
        
        // 更新所有维度控件的禁用状态  
        Object.entries(this.DIMENSION_GROUPS).forEach(([groupKey, groupData]) => {  
            groupData.dimensions.forEach(dimensionKey => {  
                const checkbox = document.getElementById(`dimension-${dimensionKey}-enabled`);  
                const select = document.getElementById(`dimension-${dimensionKey}-select`);  
                const customInput = document.getElementById(`dimension-${dimensionKey}-custom`);  
                
                if (checkbox) {  
                    checkbox.disabled = !globalEnabled || autoSelection;  
                }  
                
                if (select) {  
                    const isEnabled = checkbox?.checked || false;  
                    select.disabled = !globalEnabled || autoSelection || !isEnabled;  
                }  
                
                if (customInput) {  
                    const isEnabled = checkbox?.checked || false;  
                    const selectValue = select?.value;  
                    customInput.disabled = !globalEnabled || !isEnabled || selectValue !== 'custom';  
                }  
            });  
        });  
    }

    // 创建维度分组卡片  
    createDimensionGroupCard(groupKey, groupData, dimensionOptions, enabledDimensions, autoSelection, globalEnabled) {  
        const card = document.createElement('div');  
        card.className = 'dimension-group-card';  
        
        // ========== 卡片头部 ==========  
        const header = document.createElement('div');  
        header.className = 'dimension-group-header';  
        header.style.cursor = 'pointer';  
        
        const titleGroup = document.createElement('div');  
        titleGroup.className = 'dimension-group-title-group';  
        
        const icon = document.createElement('i');  
        icon.className = groupData.icon;  
        
        const name = document.createElement('div');  
        name.className = 'dimension-group-name';  
        name.textContent = groupData.name;  
        
        // 统计已启用维度数量  
        const enabledCount = groupData.dimensions.filter(dim =>   
            enabledDimensions[dim] === true  
        ).length;  
        
        const badge = document.createElement('span');  
        badge.className = 'dimension-count-badge';  
        badge.textContent = `${enabledCount}/${groupData.dimensions.length}`;  
        
        titleGroup.appendChild(icon);  
        titleGroup.appendChild(name);  
        titleGroup.appendChild(badge);  
        
        const toggleIcon = document.createElement('i');  
        toggleIcon.className = 'icon-chevron-down dimension-toggle-icon';  
        
        header.appendChild(titleGroup);  
        header.appendChild(toggleIcon);  
        
        // ========== 卡片内容(默认折叠) ==========  
        const content = document.createElement('div');  
        content.className = 'dimension-group-content collapsed';  
        
        // 为每个维度创建配置行  
        groupData.dimensions.forEach(dimensionKey => {  
            const dimensionData = dimensionOptions[dimensionKey];  
            if (!dimensionData) return;  
            
            const dimensionRow = this.createDimensionRow(  
                dimensionKey,  
                dimensionData,  
                enabledDimensions[dimensionKey] || false,
                globalEnabled,
                autoSelection  
            );  
            content.appendChild(dimensionRow);  
        });  
        
        // 点击头部展开/折叠  
        header.addEventListener('click', () => {  
            content.classList.toggle('collapsed');  
            toggleIcon.classList.toggle('rotated');  
        });  
        
        card.appendChild(header);  
        card.appendChild(content);  
        
        return card;  
    }  
    
    // 创建维度配置行  
    createDimensionRow(dimensionKey, dimensionData, isEnabled, globalEnabled, autoSelection) {  
        const row = document.createElement('div');  
        row.className = 'dimension-row';  
        
        // ========== 维度启用复选框(使用统一的checkbox-label样式) ==========  
        const checkboxLabel = document.createElement('label');  
        checkboxLabel.className = 'checkbox-label';  
        
        const checkbox = document.createElement('input');  
        checkbox.type = 'checkbox';  
        checkbox.id = `dimension-${dimensionKey}-enabled`;  
        checkbox.checked = isEnabled;  
        checkbox.disabled = !globalEnabled || autoSelection;  
        
        const checkboxCustom = document.createElement('span');  
        checkboxCustom.className = 'checkbox-custom';  
        
        checkboxLabel.appendChild(checkbox);  
        checkboxLabel.appendChild(checkboxCustom);  
        
        // 绑定复选框事件  
        checkbox.addEventListener('change', async (e) => {    
            const newEnabled = e.target.checked;    
            
            const currentGlobalEnabled = document.getElementById('creative-enabled')?.checked || false;    
            const currentAutoSelection = document.getElementById('auto-dimension-selection')?.checked || false;    
            
            // 更新下拉框和自定义输入框的禁用状态    
            const select = document.getElementById(`dimension-${dimensionKey}-select`);    
            const customInput = document.getElementById(`dimension-${dimensionKey}-custom`);    
            
            if (select) {    
                select.disabled = !currentGlobalEnabled || currentAutoSelection || !newEnabled;    
            }    
            
            if (customInput) {    
                const selectValue = select?.value;    
                customInput.disabled = !currentGlobalEnabled || !newEnabled || selectValue !== 'custom';    
            }    
            
            await this.updateConfig({    
                dimensional_creative: {    
                    ...this.config.dimensional_creative,    
                    enabled_dimensions: {    
                        ...this.config.dimensional_creative.enabled_dimensions,    
                        [dimensionKey]: newEnabled    
                    }    
                }    
            });
            this.updateCreativeControlsState();   
        });  
        
        // ========== 维度名称标签 ==========  
        const label = document.createElement('label');  
        label.className = 'dimension-name-label';  
        label.textContent = dimensionData.name || dimensionKey;  
        label.setAttribute('for', `dimension-${dimensionKey}-select`);  
        
        // ========== 预设选项下拉框 ==========  
        const select = document.createElement('select');  
        select.id = `dimension-${dimensionKey}-select`;  
        select.className = 'dimension-select';  
        select.disabled = !globalEnabled || autoSelection || !isEnabled;  
        
        // 添加"自动选择"选项  
        const autoOption = document.createElement('option');  
        autoOption.value = '';  
        autoOption.textContent = '自动选择';  
        select.appendChild(autoOption);  
        
        // 添加预设选项  
        const presetOptions = dimensionData.preset_options || [];  
        presetOptions.forEach(option => {  
            const opt = document.createElement('option');  
            opt.value = option.name;  
            opt.textContent = `${option.value} (${option.description})`;  
            select.appendChild(opt);  
        });  
        
        // 添加"自定义"选项  
        const customOption = document.createElement('option');  
        customOption.value = 'custom';  
        customOption.textContent = '自定义';  
        select.appendChild(customOption);  
        
        // 设置当前选中值  
        const selectedOption = dimensionData.selected_option || '';  
        select.value = selectedOption;  
        
        // 绑定下拉框事件  
        select.addEventListener('change', async (e) => {  
            const selectedValue = e.target.value;  
            const customInput = document.getElementById(`dimension-${dimensionKey}-custom`);  
            
            if (customInput) {  
                // 只有选择"自定义"时才启用对应的输入框  
                customInput.disabled = selectedValue !== 'custom';  
                
                // 如果不是自定义,清空输入框  
                if (selectedValue !== 'custom') {  
                    customInput.value = '';  
                }  
            }  
            
            await this.updateConfig({  
                dimensional_creative: {  
                    ...this.config.dimensional_creative,  
                    dimension_options: {  
                        ...this.config.dimensional_creative.dimension_options,  
                        [dimensionKey]: {  
                            ...this.config.dimensional_creative.dimension_options[dimensionKey],  
                            selected_option: selectedValue,  
                            custom_input: selectedValue === 'custom' ? (customInput ? customInput.value : '') : ''  
                        }  
                    }  
                }  
            });  
        });  
        
        // ========== 自定义输入框 ==========  
        const customInput = document.createElement('input');  
        customInput.type = 'text';  
        customInput.id = `dimension-${dimensionKey}-custom`;  
        customInput.className = 'dimension-custom-input';  
        customInput.placeholder = '输入自定义内容...';  
        customInput.value = dimensionData.custom_input || '';  
        
        customInput.disabled = !globalEnabled || !isEnabled || select.value !== 'custom';  
        
        // 绑定自定义输入框事件(使用值变化检测)  
        let originalValue = customInput.value;  
        customInput.addEventListener('blur', async (e) => {  
            if (e.target.value !== originalValue) {  
                originalValue = e.target.value;  
                
                await this.updateConfig({  
                    dimensional_creative: {  
                        ...this.config.dimensional_creative,  
                        dimension_options: {  
                            ...this.config.dimensional_creative.dimension_options,  
                            [dimensionKey]: {  
                                ...this.config.dimensional_creative.dimension_options[dimensionKey],  
                                custom_input: e.target.value  
                            }  
                        }  
                    }  
                });  
            }  
        });  
        
        // 组装行  
        row.appendChild(checkboxLabel);  
        row.appendChild(label);  
        row.appendChild(select);  
        row.appendChild(customInput);  
        
        return row;  
    }
  
    // 更新维度选项  
    async updateDimensionOption(dimensionKey, selectedOption, customInput) {  
        await this.updateConfig({  
            dimensional_creative: {  
                ...this.config.dimensional_creative,  
                dimension_options: {  
                    ...this.config.dimensional_creative.dimension_options,  
                    [dimensionKey]: {  
                        ...this.config.dimensional_creative.dimension_options[dimensionKey],  
                        selected_option: selectedOption,  
                        custom_input: customInput  
                    }  
                }  
            }  
        });  
    }

    populateImageDesignUI() {  
        if (!this.config.image_design) return;  
        
        const imageMargin = document.getElementById('image-margin');  
        if (imageMargin) imageMargin.value = this.config.image_design.margin || 20;  
        
        const borderRadius = document.getElementById('image-border-radius');  
        if (borderRadius) borderRadius.value = this.config.image_design.border_radius || 8;  
        
        const maxWidth = document.getElementById('image-max-width');  
        if (maxWidth) maxWidth.value = this.config.image_design.max_width || 100;  
        
        const autoTheme = document.getElementById('auto-theme-adapt');  
        if (autoTheme) autoTheme.checked = this.config.image_design.auto_theme_adapt !== false;  
    }  
    
    // 保存配置  
    async saveImageDesignConfig() {  
        const imageDesignConfig = {  
            margin: parseInt(document.getElementById('image-margin')?.value || 20),  
            border_radius: parseInt(document.getElementById('image-border-radius')?.value || 8),  
            max_width: parseInt(document.getElementById('image-max-width')?.value || 100),  
            auto_theme_adapt: document.getElementById('auto-theme-adapt')?.checked || false,  
            light_bg_color: document.getElementById('light-bg-color')?.value || '#ffffff',  
            dark_bg_color: document.getElementById('dark-bg-color')?.value || '#1a1a1a'  
        };  
        
        await this.updateConfig({ image_design: imageDesignConfig });  
        const success = await this.saveConfig();  
        
        if (success) {  
            const saveBtn = document.getElementById('save-image-design-config');  
            if (saveBtn) {  
                saveBtn.classList.remove('has-changes');  
                saveBtn.innerHTML = '<i class="icon-save"></i> 保存设置';  
            }  
        }  
        
        window.app?.showNotification(  
            success ? '页面设计已保存' : '保存配置失败',  
            success ? 'success' : 'error'  
        );  
    }

    updateSliderValue(slider) {  
        const value = slider.value;  
        const valueDisplay = slider.parentElement.querySelector('.slider-value');  
        if (valueDisplay) {  
            valueDisplay.textContent = value;  
        }  
    }

    // 更新配置(仅内存,不保存文件)  
    async updateConfig(updates) {        
        try {        
            const response = await fetch(this.apiEndpoint, {        
                method: 'PATCH',        
                headers: { 'Content-Type': 'application/json' },        
                body: JSON.stringify({ config_data: updates })    
            });        
                
            if (!response.ok) {        
                throw new Error(`HTTP ${response.status}`);        
            }        
                
            // 同步更新前端内存        
            this.deepMerge(this.config, updates);    
            
            const panelButtonMap = {  
                'ui': 'save-ui-config',  
                'base': 'save-base-config',  
                'platforms': 'save-platforms-config',  
                'wechat': 'save-wechat-config',  
                'api': 'save-api-config',  
                'img-api': 'save-img-api-config',
                'aiforge': 'save-aiforge-config',
                'creative': 'save-creative-config',
                'image-design': 'save-image-design-config'
            };  
            
            const saveBtnId = panelButtonMap[this.currentPanel];  
            if (saveBtnId) {  
                const saveBtn = document.getElementById(saveBtnId);  
                if (saveBtn && !saveBtn.classList.contains('has-changes')) {  
                    saveBtn.classList.add('has-changes');  
                    saveBtn.innerHTML = `<i class="icon-save"></i> 保存设置 <span style="color: var(--warning-color);">(有未保存更改)</span>`;  
                }  
            }  
                
            return true;        
        } catch (error) {        
            console.error('更新配置失败:', error);        
            return false;        
        }        
    }
      
    // 保存配置到文件  
    async saveConfig() {  
        try {  
            const response = await fetch(this.apiEndpoint, {  
                method: 'POST',  
                headers: { 'Content-Type': 'application/json' }  
            });  
              
            if (!response.ok) {  
                throw new Error(`HTTP ${response.status}`);  
            }  
              
            const result = await response.json();  
            return result.status === 'success';  
        } catch (error) {  
            console.error('保存配置失败:', error);  
            return false;  
        }  
    }  
      
    // 恢复默认配置(仅更新内存,不保存)  
    async resetToDefault() {  
        try {  
            const response = await fetch(`${this.apiEndpoint}/default`);  
            if (!response.ok) {  
                throw new Error('获取默认配置失败');  
            }  
              
            const result = await response.json();  
              
            // 更新后端内存  
            await this.updateConfig(result.data);  
              
            // 更新前端内存  
            this.config = result.data;  
              
            // 刷新UI  
            this.populateUI();  
              
            return true;  
        } catch (error) {  
            console.error('恢复默认配置失败:', error);  
            return false;  
        }  
    }  
      
    // 深度合并辅助方法  
    deepMerge(target, source) {  
        for (const key in source) {  
            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {  
                if (!target[key]) target[key] = {};  
                this.deepMerge(target[key], source[key]);  
            } else {  
                target[key] = source[key];  
            }  
        }  
    }
        
    // 获取当前配置    
    getConfig() {    
        return this.config;    
    }    
        
    // 更新特定配置项(仅内存)  
    async updateConfigItem(key, value) {    
        const updateData = {};    
        updateData[key] = value;    
            
        try {    
            await this.updateConfig(updateData);    
            return true;    
        } catch (error) {    
            console.error(`更新配置项 ${key} 失败:`, error);    
            return false;    
        }    
    }    
}    
    
// 全局配置管理器实例    
let configManager;    
    
// 初始化配置管理器    
document.addEventListener('DOMContentLoaded', async () => {    
    configManager = new AIWriteXConfigManager();    
    window.configManager = configManager;    
});