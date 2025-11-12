class BottomProgressManager {  
    constructor() {  
        // 阶段定义  
        this.stages = {  
            init: {  
                id: 'init',  
                name: '正在初始化',  
                icon: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',  
                progress: 0, // 从0开始动画  
                maxProgress: 5 // 初始化阶段的最终目标  
            },  
            search: {  
                id: 'search',  
                name: '正在搜索信息',  
                icon: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',  
                progress: 5, // 搜索阶段的起始值  
                maxProgress: 20 // 搜索阶段的最终目标  
            },  
            writing: {  
                id: 'writing',  
                name: 'AI正在创作',  
                icon: '<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',  
                progress: 20, // 写作阶段的起始值  
                maxProgress: 35 // 写作阶段的最终目标  
            },  
            creative: {  
                id: 'creative',  
                name: '正在创意变换',  
                icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',  
                progress: 35, // 创意阶段的起始值  
                maxProgress: 45 // 创意阶段的最终目标  
            },  
            template: {  
                id: 'template',  
                name: '正在模板化',  
                icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',  
                progress: 45, // 模板阶段的起始值  
                maxProgress: 85 // 模板阶段的最终目标  
            },  
            design: { // 假设design阶段与template阶段并行或可选  
                id: 'design',  
                name: '正在设计排版',  
                icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>',  
                progress: 45,  
                maxProgress: 75  
            },  
            save: {  
                id: 'save',  
                name: '正在保存',  
                icon: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>',  
                progress: 85, // 保存阶段的起始值  
                maxProgress: 87 // 保存阶段的最终目标  
            },  
            publish: {  
                id: 'publish',  
                name: '正在发布',  
                icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',  
                progress: 87, // 发布阶段的起始值  
                maxProgress: 98 // 发布阶段的最终目标  
            },  
            complete: {  
                id: 'complete',  
                name: '生成完成',  
                icon: '<polyline points="20 6 9 17 4 12"/>',  
                progress: 100,  
                maxProgress: 100  
            }  
        };  
  
        this.currentStage = null;  
        this.currentProgress = 0;  
        this.targetProgress = 0;  
        this.stageMaxProgress = 100;  
        this.animationFrame = null;  
        this.autoProgressTimer = null;  
        this.isRunning = false;  
        this.quickCatchUpPromise = Promise.resolve(); // 用于等待快速追赶动画完成  
  
        // DOM元素引用  
        this.progressEl = document.getElementById('bottom-progress');  
        this.progressBar = document.querySelector('.progress-bar');  
        this.stageIcon = document.querySelector('.progress-stage-icon');  
        this.stageText = document.querySelector('.progress-stage');  
        this.percentageText = document.querySelector('.progress-percentage');  
    }  
  
    /**  
     * 启动进度条  
     * @param {string} stage - 初始阶段ID  
     */  
    start(stage) {  
        if (this.progressEl) {  
            this.progressEl.classList.remove('hidden');  
  
            const inputGroup = document.querySelector('.topic-input-group');  
            if (inputGroup) {  
                inputGroup.classList.add('showing-progress');  
            }  
  
            const inputEl = document.getElementById('topic-input');  
            if (inputEl) {  
                const inputWidth = inputEl.offsetWidth;  
                const trackEl = this.progressEl.querySelector('.progress-track');  
                if (trackEl) {  
                    trackEl.style.width = `${inputWidth}px`;  
                }  
            }  
        }  
  
        this.currentStage = stage;  
        this.isRunning = true;  
  
        const stageConfig = this.stages[stage];  
        if (stageConfig) {  
            this.currentProgress = 0; // 总是从0开始动画  
            this.targetProgress = stageConfig.maxProgress; // 目标是init阶段的maxProgress (5%)  
            this.stageMaxProgress = stageConfig.maxProgress;  
  
            this.renderProgress(); // 立即渲染0%  
        }  
  
        this.updateStageDisplay(stage);  
        this.startContinuousProgress();  
    }  
  
    /**  
     * 更新进度条状态  
     * @param {string} stage - 当前阶段ID  
     * @param {number} progress - 目标进度百分比  
     */  
    async updateProgress(stage, progress) {  
        const stageConfig = this.stages?.[stage];  
        if (!stageConfig) {  
            console.warn('[ProgressManager] 未知阶段:', stage);  
            return;  
        }  
        
        await this.quickCatchUpPromise;  
        
        if (stage !== this.currentStage) {  
            console.log('[ProgressManager] 切换阶段:', this.currentStage, '→', stage);  
            
            const prevStageConfig = this.stages?.[this.currentStage];  
            if (prevStageConfig && this.currentProgress < prevStageConfig.maxProgress) {  
                console.log(`[ProgressManager] 快速完成前阶段: ${this.currentProgress.toFixed(2)}% → ${prevStageConfig.maxProgress.toFixed(2)}%`);  
                this.quickCatchUpPromise = this.quickCatchUp(prevStageConfig.maxProgress, 500);  
                await this.quickCatchUpPromise;  
            }  
            
            this.currentStage = stage;  
            this.stageMaxProgress = stageConfig.maxProgress;  
            this.updateStageDisplay(stage);  
            
            if (this.currentProgress < progress) {  
                this.currentProgress = progress;  
                this.renderProgress();  
            }  
            
            // 重新启动连续进度动画  
            this.startContinuousProgress();  
            
            return;  
        }  
        
        console.log(`[ProgressManager] 同阶段内进度更新: ${progress}%, 当前=${this.currentProgress.toFixed(2)}%`);  
    }
    
    /**  
     * 更新阶段显示（图标和文本）  
     * @param {string} stage - 当前阶段ID  
     */  
    updateStageDisplay(stage) {  
        const stageConfig = this.stages[stage];  
        if (!stageConfig) return;  
  
        if (this.stageIcon) {  
            this.stageIcon.innerHTML = stageConfig.icon;  
            this.stageIcon.classList.add('rotating');  
        }  
  
        if (this.stageText) {  
            this.stageText.textContent = stageConfig.name;  
        }  
    }  
  
    /**  
     * 启动连续进度动画（前端估算）  
     */  
    startContinuousProgress() {  
        if (this.autoProgressTimer) {  
            clearInterval(this.autoProgressTimer);  
        }  
        
        this.autoProgressTimer = setInterval(() => {  
            if (!this.isRunning) {  
                return;  
            }  
            
            // 直接使用stageMaxProgress作为上限,不再计算"安全边界"  
            const maxAllowedProgress = this.stageMaxProgress;  
            const gap = maxAllowedProgress - this.currentProgress;  
            
            // 如果已经到达阶段的maxProgress,停止增长  
            if (gap <= 0.1) {  
                return;  
            }  
            
            let increment;  
            const stage = this.currentStage;  
            
            // 根据阶段和剩余距离动态调整速度  
            if (stage === 'init') {  
                increment = 0.05;  
            } else if (stage === 'search') {  
                increment = 0.03;  
            } else if (stage === 'writing') {      
                // 从20%到35% (15个百分点)    
                if (gap > 10) increment = 0.10; 
                else if (gap > 5) increment = 0.067; 
                else increment = 0.033;
            } else if (stage === 'creative') {    
                // 从35%到45% (10个百分点)  
                if (gap > 8) increment = 0.08;
                else if (gap > 4) increment = 0.053; 
                else increment = 0.033;
            } else if (stage === 'template') {    
                // 从45%到85% (40个百分点)  
                if (gap > 20) increment = 0.020; 
                else if (gap > 10) increment = 0.013; 
                else if (gap > 5) increment = 0.009;  
                else increment = 0.007;
            } else if (stage === 'design') {  
                increment = 0.02;  
            } else if (stage === 'save') {  
                increment = 0.05;  
            } else if (stage === 'publish') {  
                increment = 0.03;  
            } else {  
                increment = 0.05;  
            }  
            
            this.currentProgress += increment;  
            
            // 确保不超过maxAllowedProgress  
            if (this.currentProgress > maxAllowedProgress) {  
                this.currentProgress = maxAllowedProgress;  
            }  
            
            this.renderProgress();  
        }, 100);  
    }
  
    /**  
     * 渲染进度条和百分比  
     */  
    renderProgress() {  
        if (this.progressBar) {  
            this.progressBar.style.width = `${this.currentProgress}%`;  
        }  
  
        if (this.percentageText) {  
            this.percentageText.textContent = `(${Math.round(this.currentProgress)}%)`;  
        }  
    }  
  
    /**  
     * 显示错误状态  
     * @param {string} errorMessage - 错误信息  
     */  
    showError(errorMessage) {  
        this.stop();  
  
        if (this.progressBar) {  
            this.progressBar.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';  
        }  
  
        if (this.stageIcon) {  
            this.stageIcon.innerHTML = '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>';  
            this.stageIcon.classList.remove('rotating');  
        }  
  
        if (this.stageText) {  
            this.stageText.textContent = '生成失败';  
            this.stageText.style.color = '#ef4444';  
        }  
  
        if (this.percentageText) {  
            this.percentageText.style.color = '#ef4444';  
        }  
    }  
  
    /**  
     * 完成进度动画到100%  
     */  
    complete() {  
        this.targetProgress = 100;  
        this.stageMaxProgress = 100;  
  
        const finalAnimate = () => {  
            if (this.currentProgress < 99.5) {  
                this.currentProgress += (100 - this.currentProgress) * 0.3;  
                this.renderProgress();  
                requestAnimationFrame(finalAnimate);  
            } else {  
                this.currentProgress = 100;  
                this.renderProgress();  
  
                if (this.stageText) {  
                    this.stageText.textContent = '生成完成';  
                }  
  
                if (this.stageIcon) {  
                    this.stageIcon.classList.remove('rotating');  
                }  
            }  
        };  
  
        finalAnimate();  
    }  
  
    /**  
     * 快速追赶动画 - 在阶段切换时快速完成前一阶段的进度  
     * @param {number} targetProgress - 目标进度值  
     * @param {number} duration - 动画持续时间(毫秒)  
     * @returns {Promise<void>} - 返回一个Promise,在动画完成后resolve  
     */  
    quickCatchUp(targetProgress, duration = 200) {  
        return new Promise(resolve => {  
            const startProgress = this.currentProgress;  
            const gap = targetProgress - startProgress;  
            const startTime = Date.now();  
  
            const animate = () => {  
                const elapsed = Date.now() - startTime;  
                const ratio = Math.min(elapsed / duration, 1);  
  
                const easeRatio = ratio * (2 - ratio); // easeOutQuad缓动函数  
                this.currentProgress = startProgress + gap * easeRatio;  
                this.renderProgress();  
  
                if (ratio < 1) {  
                    requestAnimationFrame(animate);  
                } else {  
                    this.currentProgress = targetProgress;  
                    this.renderProgress();  
                    resolve(); // 动画完成时resolve Promise  
                }  
            };  
  
            requestAnimationFrame(animate);  
        });  
    } 
      
    stop() {  
        this.isRunning = false;  
          
        if (this.animationFrame) {  
            cancelAnimationFrame(this.animationFrame);  
            this.animationFrame = null;  
        }  
          
        if (this.autoProgressTimer) {  
            clearInterval(this.autoProgressTimer);  
            this.autoProgressTimer = null;  
        }  
    }  
      
    reset() {  
        this.stop();  
        this.currentProgress = 0;  
        this.targetProgress = 0;  
        this.stageMaxProgress = 100;  
        this.currentStage = null;  
          
        const inputGroup = document.querySelector('.topic-input-group');  
        if (inputGroup) {  
            inputGroup.classList.remove('showing-progress');  
        }  
          
        if (this.progressBar) {  
            this.progressBar.style.width = '0%';  
            this.progressBar.style.background = '';  
            this.progressBar.classList.remove('error');  
        }  
          
        if (this.stageText) {  
            this.stageText.textContent = '';  
            this.stageText.style.color = '';  
        }  
          
        if (this.percentageText) {  
            this.percentageText.textContent = '(0%)';  
            this.percentageText.style.color = '';  
        }  
          
        if (this.stageIcon) {  
            this.stageIcon.classList.remove('rotating');  
        }  
          
        if (this.progressEl) {  
            this.progressEl.classList.remove('error');  
        }  
    } 
}