class BottomProgressManager {  
    constructor() {  
        // 阶段定义  
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
                progress: 10,  
                maxProgress: 20
            },  
            writing: {  
                id: 'writing',  
                name: 'AI正在创作',   
                icon: '<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',  
                progress: 20,  
                maxProgress: 50
            },  
            creative: {  
                id: 'creative',  
                name: '正在创意变换',  
                icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',  
                progress: 55,  
                maxProgress: 68  
            },  
            template: {  
                id: 'template',  
                name: '正在模板化',  
                icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',  
                progress: 70,  
                maxProgress: 83  
            },  
            design: {  
                id: 'design',  
                name: '正在设计排版',  
                icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>',  
                progress: 70,  
                maxProgress: 78  
            },  
            save: {  
                id: 'save',  
                name: '正在保存',  
                icon: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>',  
                progress: 85,  
                maxProgress: 93  
            },  
            publish: {  
                id: 'publish',  
                name: '正在发布',  
                icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',  
                progress: 95,  
                maxProgress: 98  
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
          
        const stageConfig = this.stages[stage];  
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
        
        // 【关键修复】只在同一阶段内防止倒退  
        if (stage === this.currentStage && progress < this.targetProgress) {  
            console.log('[ProgressManager] 忽略同阶段内的倒退进度:', progress, '当前目标:', this.targetProgress);  
            return;  
        }  
        
        // 【关键修复】切换到新阶段时,总是更新  
        if (stage !== this.currentStage) {  
            console.log('[ProgressManager] 切换阶段:', this.currentStage, '→', stage);  
        }  
        
        this.currentStage = stage;  
        this.targetProgress = progress;  
        this.stageMaxProgress = stageConfig.maxProgress;  
        
        console.log(`[ProgressManager] 更新进度: 阶段=${stage}, 目标=${progress}%, 当前=${this.currentProgress.toFixed(2)}%`);  
        
        this.updateStageDisplay(stage);  
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
                
                // 大幅降低CrewAI相关阶段的速度  
                if (stage === 'template') {  
                    // 模板阶段最慢 
                    if (gap > 10) {  
                        increment = 0.02;
                    } else if (gap > 5) {  
                        increment = 0.012; 
                    } else {  
                        increment = 0.005; 
                    }  
                } else if (stage === 'writing') {  
                    // 写作阶段较慢  
                    if (gap > 15) {  
                        increment = 0.08;  
                    } else if (gap > 8) {  
                        increment = 0.04; 
                    } else {  
                        increment = 0.02; 
                    }  
                } else if (stage === 'creative') {  
                    // 创意阶段中速
                    if (gap > 12) {  
                        increment = 0.09;   
                    } else if (gap > 6) {  
                        increment = 0.045; 
                    } else {  
                        increment = 0.024;
                    }  
                } else if (stage === 'design') {  
                    // 设计阶段保持原速度  
                    if (gap > 8) {  
                        increment = 0.15;  
                    } else if (gap > 4) {  
                        increment = 0.08;  
                    } else {  
                        increment = 0.04;  
                    }  
                } else {  
                    // 其他阶段(init, search, save, publish)保持原速度  
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