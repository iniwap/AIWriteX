class BottomProgressManager {  
    constructor() {  
        this.stages = {  
            init: {  
                id: 'init',  
                name: '正在初始化',  
                icon: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',  
                progress: 5  
            },  
            search: {  
                id: 'search',  
                name: '正在搜索信息',  
                icon: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',  
                progress: 25  
            },  
            writing: {  
                id: 'writing',  
                name: 'AI正在创作',  
                icon: '<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',  
                progress: 60  
            },  
            creative: {  
                id: 'creative',  
                name: '正在创意变换',  
                icon: '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>',  
                progress: 75  
            },  
            template: {  
                id: 'template',  
                name: '正在模板化',  
                icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',  
                progress: 90  
            },  
            save: {  
                id: 'save',  
                name: '正在保存',  
                icon: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/>',  
                progress: 98  
            }  
        };  
          
        this.currentStage = null;  
        this.currentProgress = 0;  
        this.targetProgress = 0;  
        this.animationFrame = null;  
          
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
            // 动态计算进度条宽度  
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
        this.stageStartTime = Date.now();  
        this.updateStageDisplay(stage);  
        this.startAutoProgress();  
    }  
      
    updateProgress(stage, progress) {  
        const stageConfig = this.stages[stage];  
        if (!stageConfig) return;  
          
        // 防止进度倒退  
        if (progress < this.currentProgress) {  
            return;  
        }  
          
        this.currentStage = stageConfig;  
        this.targetProgress = progress;  
          
        this.updateStageDisplay(stage);  
        this.animateToTarget();  
    }  
      
    updateStageDisplay(stage) {  
        const stageConfig = this.stages[stage];  
        if (!stageConfig) return;  
          
        // 更新 SVG 图标  
        if (this.stageIcon) {  
            this.stageIcon.innerHTML = stageConfig.icon;  
        }  
          
        // 更新阶段文字  
        if (this.stageText) {  
            this.stageText.textContent = stageConfig.name;  
        }  
    }  
      
    animateToTarget() {  
        if (this.animationFrame) {  
            cancelAnimationFrame(this.animationFrame);  
        }  
          
        const animate = () => {  
            const diff = this.targetProgress - this.currentProgress;  
              
            if (Math.abs(diff) < 0.1) {  
                this.currentProgress = this.targetProgress;  
                this.renderProgress();  
                  
                // 继续自动推进  
                if (this.currentProgress < 95) {  
                    this.startAutoProgress();  
                }  
                return;  
            }  
              
            // 缓动函数  
            this.currentProgress += diff * 0.1;  
            this.renderProgress();  
              
            this.animationFrame = requestAnimationFrame(animate);  
        };  
          
        animate();  
    }  
      
    startAutoProgress() {  
        // 缓慢自动推进,避免卡顿  
        const autoIncrement = () => {  
            if (this.currentProgress < this.targetProgress - 1) {  
                this.currentProgress += 0.1;  
                this.renderProgress();  
                setTimeout(autoIncrement, 100);  
            }  
        };  
          
        autoIncrement();  
    }  
      
    renderProgress() {  
        // 更新进度条  
        if (this.progressBar) {  
            this.progressBar.style.width = `${this.currentProgress}%`;  
        }  
          
        // 更新百分比文字  
        if (this.percentageText) {  
            this.percentageText.textContent = `(${Math.round(this.currentProgress)}%)`;  
        }  
    }  
      
    complete() {  
        this.updateProgress('complete', 100);  
        
        // 更新阶段文字为"完成"  
        if (this.stageText) {  
            this.stageText.textContent = '生成完成';  
        }  
        
        // 1.5秒后开始淡出  
        setTimeout(() => {  
            const progressEl = document.getElementById('bottom-progress');  
            if (progressEl) {  
                // 添加淡出动画类  
                progressEl.style.transition = 'opacity 0.5s ease';  
                progressEl.style.opacity = '0';  
                
                // 淡出完成后隐藏  
                setTimeout(() => {  
                    this.reset();  
                    progressEl.style.opacity = '1'; // 重置透明度供下次使用  
                }, 500);  
            }  
        }, 1500);  
    }
      
    reset() {  
        this.stop();  
        this.currentProgress = 0;  
        this.targetProgress = 0;  
        this.currentStage = null;  
        
        const inputGroup = document.querySelector('.topic-input-group');  
        if (inputGroup) {  
            inputGroup.classList.remove('showing-progress');  
        }  

        // 重置UI  
        if (this.progressBar) {  
            this.progressBar.style.width = '0%';  
        }  
          
        if (this.stageText) {  
            this.stageText.textContent = '';  
        }  
          
        if (this.percentageText) {  
            this.percentageText.textContent = '(0%)';  
        }  
    }   
      
    stop() {  
        if (this.animationFrame) {  
            cancelAnimationFrame(this.animationFrame);  
            this.animationFrame = null;  
        }  
    }  
}