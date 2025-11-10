class BottomProgressManager {  
    constructor() {  
        this.stages = {  
            init: {  
                id: 'init',  
                name: '正在初始化',  
                icon: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',  
                progress: 5,  
                maxProgress: 10  
            },  
            search: {  
                id: 'search',  
                name: '正在搜索信息',  
                icon: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',  
                progress: 25,  
                maxProgress: 45  
            },  
            writing: {  
                id: 'writing',  
                name: 'AI正在创作',  
                icon: '<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',  
                progress: 60,  
                maxProgress: 70  
            },  
            creative: {  
                id: 'creative',  
                name: '正在创意变换',  
                icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',  
                progress: 75,  
                maxProgress: 85  
            },  
            template: {  
                id: 'template',  
                name: '正在模板化',  
                icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',  
                progress: 90,  
                maxProgress: 95  
            },  
            save: {  
                id: 'save',  
                name: '正在保存',  
                icon: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>',  
                progress: 98,  
                maxProgress: 99  
            }  
        }; 
          
        this.currentStage = null;  
        this.currentProgress = 0;  
        this.targetProgress = 0;  
        this.stageMaxProgress = 100; // 当前阶段的最大允许进度  
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
          
        // 设置初始目标进度和阶段上限  
        const stageConfig = this.stages[stage];  
        if (stageConfig) {  
            this.targetProgress = stageConfig.progress;  
            this.stageMaxProgress = stageConfig.maxProgress;  
        }  
          
        this.updateStageDisplay(stage);  
        this.startContinuousProgress();  
    }  
      
    updateProgress(stage, progress) {  
        const stageConfig = this.stages[stage];  
        if (!stageConfig) return;  
        
        // 防止进度倒退  
        if (progress < this.targetProgress) {  
            return;  
        }  
        
        // 更新目标进度和阶段上限  
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
     * 持续进度推进 - 核心方法  
     * 保持进度条始终在移动,但不超过目标进度和阶段上限  
     */  
    startContinuousProgress() {  
        if (this.autoProgressTimer) {  
            clearInterval(this.autoProgressTimer);  
        }  
          
        this.autoProgressTimer = setInterval(() => {  
            if (!this.isRunning) {  
                return;  
            }  
              
            // 计算当前允许的最大进度(取目标进度和阶段上限的较小值)  
            const maxAllowedProgress = Math.min(this.targetProgress, this.stageMaxProgress);  
              
            // 计算距离最大允许进度的差距  
            const gap = maxAllowedProgress - this.currentProgress;  
              
            if (gap > 0.1) {  
                // 根据差距动态调整增量  
                let increment;  
                if (gap > 20) {  
                    // 差距很大,快速追赶  
                    increment = 0.5;  
                } else if (gap > 10) {  
                    // 差距中等,中速前进  
                    increment = 0.3;  
                } else if (gap > 5) {  
                    // 差距较小,慢速前进  
                    increment = 0.15;  
                } else {  
                    // 接近上限,极慢速度保持动画感  
                    increment = 0.05;  
                }  
                  
                this.currentProgress += increment;  
                  
                // 确保不超过最大允许进度  
                if (this.currentProgress > maxAllowedProgress) {  
                    this.currentProgress = maxAllowedProgress;  
                }  
                  
                this.renderProgress();  
            }  
        }, 100); // 每100ms更新一次  
    }  
      
    /**  
     * 快速追赶 - 当显示进度远低于目标进度时触发  
     */  
    catchUpProgress() {  
        if (this.animationFrame) {  
            cancelAnimationFrame(this.animationFrame);  
        }  
          
        const animate = () => {  
            const maxAllowedProgress = Math.min(this.targetProgress, this.stageMaxProgress);  
            const diff = maxAllowedProgress - this.currentProgress;  
              
            if (Math.abs(diff) < 0.5) {  
                // 追赶完成,回到持续推进模式  
                this.currentProgress = maxAllowedProgress;  
                this.renderProgress();  
                return;  
            }  
              
            // 使用更快的缓动函数追赶  
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
        // 快速推进到100%  
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