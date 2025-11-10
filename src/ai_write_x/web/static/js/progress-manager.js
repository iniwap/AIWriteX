class BottomProgressManager {    
    constructor() {    
        // 基础阶段定义(包含所有可能的阶段)  
        this.baseStages = {    
            init: {    
                id: 'init',    
                name: '正在初始化',    
                icon: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',    
                progress: 5,    
                maxProgress: 10      // 5% 空间  
            },  
            search: {    
                id: 'search',    
                name: '正在搜索信息',    
                icon: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',    
                progress: 10,    
                maxProgress: 15      // 5% 空间 
            },  
            writing: {    
                id: 'writing',    
                name: 'AI正在创作',    
                icon: '<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',    
                progress: 15,    
                maxProgress: 30      // 15% 空间 
            },  
            creative: {    
                id: 'creative',    
                name: '正在创意变换',    
                icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',    
                progress: 30,    
                maxProgress: 40      // 10% 空间
            },  
            template: {    
                id: 'template',    
                name: '正在模板化',    
                icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',    
                progress: 40,    
                maxProgress: 90      // 50% 空间
            },  
            save: {    
                id: 'save',    
                name: '正在保存',    
                icon: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>',    
                progress: 90,    
                maxProgress: 95      // 5% 空间  
            },  
            publish: {    
                id: 'publish',    
                name: '正在发布',    
                icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',    
                progress: 95,    
                maxProgress: 98      // 3% 空间  
            },  
            complete: {    
                id: 'complete',    
                name: '生成完成',    
                icon: '<polyline points="20 6 9 17 4 12"/>',    
                progress: 100,    
                maxProgress: 100  
            }  
        };
          
        // 当前激活的阶段(将在setActiveStages中设置)  
        this.stages = null;  
          
        this.currentStage = null;    
        this.currentProgress = 0;    
        this.targetProgress = 0;    
        this.stageMaxProgress = 100;  
        this.animationFrame = null;    
        this.autoProgressTimer = null;    
        this.isRunning = false;    
            
        // DOM元素引用    
        this.progressEl = document.getElementById('bottom-progress');    
        this.progressBar = document.querySelector('.progress-bar');    
        this.stageIcon = document.querySelector('.progress-stage-icon');    
        this.stageText = document.querySelector('.progress-stage');    
        this.percentageText = document.querySelector('.progress-percentage');    
    }  
      
    /**  
     * 设置激活的阶段和进度范围  
     * @param {Array<string>} activeStageIds - 激活的阶段ID列表  
     * @param {Object} progressRanges - 每个阶段的进度范围 {stageId: {start, end}}  
     */  
    setActiveStages(activeStageIds, progressRanges) {  
        this.stages = {};  
        activeStageIds.forEach(stageId => {  
            if (this.baseStages[stageId]) {  
                this.stages[stageId] = {  
                    ...this.baseStages[stageId],  
                    progress: progressRanges[stageId].start,  
                    maxProgress: progressRanges[stageId].end  
                };  
            }  
        });  
        console.log('[ProgressManager] 激活阶段:', activeStageIds, '进度范围:', progressRanges);  
    }  
        
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
            
        const stageConfig = this.stages?.[stage];    
        if (stageConfig) {    
            this.targetProgress = stageConfig.progress;    
            this.stageMaxProgress = stageConfig.maxProgress;    
        }    
            
        this.updateStageDisplay(stage);    
        this.startContinuousProgress();    
    }    
        
    updateProgress(stage, progress) {    
        const stageConfig = this.stages?.[stage];    
        if (!stageConfig) {  
            console.warn('[ProgressManager] 未知阶段:', stage);  
            return;  
        }  
          
        // 防止进度倒退    
        if (progress < this.targetProgress) {    
            return;    
        }    
          
        this.currentStage = stage;    
        this.targetProgress = progress;    
        this.stageMaxProgress = stageConfig.maxProgress;    
          
        this.updateStageDisplay(stage);    
          
        // 如果显示进度远低于目标进度,触发快速追赶    
        if (this.currentProgress < this.targetProgress - 10) {    
            this.catchUpProgress();    
        }    
    }    
        
    updateStageDisplay(stage) {    
        const stageConfig = this.stages?.[stage];    
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
     * 持续进度推进 - 根据阶段动态调整速度  
     */  
    startContinuousProgress() {    
        if (this.autoProgressTimer) {    
            clearInterval(this.autoProgressTimer);    
        }    
            
        this.autoProgressTimer = setInterval(() => {    
            if (!this.isRunning) {    
                return;    
            }    
                
            const maxAllowedProgress = Math.min(this.targetProgress, this.stageMaxProgress);    
            const gap = maxAllowedProgress - this.currentProgress;    
                
            if (gap > 0.1) {    
                let increment;  
                const stage = this.currentStage;  
                  
                // 根据阶段和实际耗时调整速度  
                if (stage === 'template') {  
                    // 模板阶段最慢(预计5-6分钟,50%进度空间)  
                    if (gap > 30) {  
                        increment = 0.05;  // 超慢  
                    } else if (gap > 15) {  
                        increment = 0.03;  // 极慢  
                    } else if (gap > 5) {  
                        increment = 0.015; // 超级慢  
                    } else {  
                        increment = 0.008; // 几乎静止  
                    }  
                } else if (stage === 'design') {  
                    // 设计阶段中速(预计1-2分钟)  
                    if (gap > 8) {  
                        increment = 0.15;  
                    } else if (gap > 4) {  
                        increment = 0.08;  
                    } else {  
                        increment = 0.04;  
                    }  
                } else if (stage === 'writing') {  
                    // 写作阶段较慢(预计1分钟)  
                    if (gap > 15) {  
                        increment = 0.25;  
                    } else if (gap > 8) {  
                        increment = 0.12;  
                    } else {  
                        increment = 0.06;  
                    }  
                } else if (stage === 'creative') {  
                    // 创意阶段中速(预计40秒)  
                    if (gap > 12) {  
                        increment = 0.3;  
                    } else if (gap > 6) {  
                        increment = 0.15;  
                    } else {  
                        increment = 0.08;  
                    }  
                } else {  
                    // 其他阶段使用默认速度  
                    if (gap > 20) {  
                        increment = 0.5;  
                    } else if (gap > 10) {  
                        increment = 0.3;  
                    } else if (gap > 5) {  
                        increment = 0.15;  
                    } else {  
                        increment = 0.05;  
                    }  
                }  
                    
                this.currentProgress += increment;    
                    
                if (this.currentProgress > maxAllowedProgress) {    
                    this.currentProgress = maxAllowedProgress;    
                }    
                    
                this.renderProgress();    
            }    
        }, 100);    
    }    
        
    catchUpProgress() {    
        if (this.animationFrame) {    
            cancelAnimationFrame(this.animationFrame);    
        }    
            
        const animate = () => {    
            const maxAllowedProgress = Math.min(this.targetProgress, this.stageMaxProgress);    
            const diff = maxAllowedProgress - this.currentProgress;    
                
            if (Math.abs(diff) < 0.5) {    
                this.currentProgress = maxAllowedProgress;    
                this.renderProgress();    
                return;    
            }    
                
            this.currentProgress += diff * 0.2;    
            this.renderProgress();    
                
            this.animationFrame = requestAnimationFrame(animate);    
        };    
            
        animate();    
    }    
        
    renderProgress() {    
        if (this.progressBar) {    
            this.progressBar.style.width = `${this.currentProgress}%`;    
        }    
            
        if (this.percentageText) {    
            this.percentageText.textContent = `(${Math.round(this.currentProgress)}%)`;    
        }    
    }    
        
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