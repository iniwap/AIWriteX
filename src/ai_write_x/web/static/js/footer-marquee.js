// 底部走马灯管理器  
class FooterMarqueeManager {  
    constructor() {  
        this.messages = [];  
        this.maxMessages = 10;  
        this.currentIndex = 0;  
        this.container = null;  
        this.animationDuration = 15;  // 每条消息15秒  
        this.rotationInterval = null;  
        this.init();  
    }  
      
    init() {  
        this.container = document.getElementById('footer-marquee');  
        if (!this.container) {  
            console.warn('Footer marquee container not found');  
            return;  
        }  
          
        // 从后端加载系统消息  
        this.loadSystemMessages();  
    }  
      
    async loadSystemMessages() {  
        try {  
            const response = await fetch('/api/config/system-messages');  
            if (response.ok) {  
                const result = await response.json();  
                const messages = result.data || [];  
                  
                messages.forEach(msg => {  
                    this.addMessage(msg.text, msg.type || 'info', true);  
                });  
            } else {  
                // 降级:使用默认消息  
                this.addMessage('欢迎使用AIWriteX智能内容创作平台', 'info', true);  
            }  
        } catch (error) {  
            console.error('加载系统消息失败:', error);  
            this.addMessage('欢迎使用AIWriteX智能内容创作平台', 'info', true);  
        }  
    }  
      
    addMessage(text, type = 'info', persistent = true, loopCount = null) {  
        const message = {  
            id: Date.now() + Math.random(),  
            text: text,  
            type: type,  
            persistent: persistent,  
            loopCount: loopCount,  
            currentLoop: 0,  
            timestamp: Date.now()  
        };  
        
        this.messages.push(message);  
        
        // 如果是loopCount=1的临时消息,立即显示  
        if (loopCount === 1) {  
            this.currentIndex = this.messages.length - 1;  
            this.showCurrentMessage();  
            
            // 设置自动移除(显示30秒后)  
            setTimeout(() => {  
                this.removeMessage(message.id);  
            }, 30000);  
        }  
        // 如果是非持久消息(persistent=false, loopCount=null),30秒后移除  
        else if (!persistent && loopCount === null) {  
            setTimeout(() => {  
                this.removeMessage(message.id);  
            }, 30000);  
        }  
        // 如果是有限循环消息,设置循环监听  
        else if (loopCount !== null && loopCount > 1) {  
            this.setupLoopCounter(message.id, loopCount);  
        }  
        
        // 限制消息数量  
        if (this.messages.length > this.maxMessages) {  
            const removeIndex = this.findRemovableMessageIndex();  
            if (removeIndex !== -1) {  
                this.messages.splice(removeIndex, 1);  
            }  
        }  
        
        // 如果当前没有显示消息,立即显示  
        if (this.messages.length === 1) {  
            this.showCurrentMessage();  
        }  
    }
      
    // 显示当前消息  
    showCurrentMessage() {      
        if (this.messages.length === 0) {      
            this.container.innerHTML = '';      
            return;      
        }      
            
        const message = this.messages[this.currentIndex];      
            
        this.container.innerHTML = `      
            <span class="marquee-item ${message.type}">      
                ${this.escapeHtml(message.text)}      
            </span>      
        `;        
            
        // 获取容器和消息宽度      
        const containerWidth = this.container.parentElement.offsetWidth;      
        const messageWidth = this.container.offsetWidth;      
            
        // 计算总移动距离      
        const totalDistance = containerWidth + messageWidth;      
            
        // 根据距离动态调整动画时长(保持恒定速度)      
        const speed = 100; // 像素/秒      
        const duration = Math.max(10, Math.min(60, totalDistance / speed));  
            
        // 设置CSS变量        
        this.container.style.setProperty('--start-pos', `${containerWidth}px`);        
        this.container.style.setProperty('--end-pos', `-${messageWidth}px`);  
            
        // 重置动画(先清空)  
        this.container.style.animation = 'none';        
        void this.container.offsetWidth; // 强制重排  
            
        // 使用完整的animation简写属性  
        this.container.style.animation = `marquee-scroll ${duration}s linear 1`;  
        
        // 动态设置下一次切换的时间    
        if (this.rotationTimeout) {    
            clearTimeout(this.rotationTimeout);    
        }    
        
        this.rotationTimeout = setTimeout(() => {    
            this.nextMessage();    
        }, duration * 1000);  
    }    
      
    // 切换到下一条消息  
    nextMessage() {  
        if (this.messages.length === 0) return;  
          
        const currentMessage = this.messages[this.currentIndex];  
          
        // 如果是有限循环消息,增加循环计数  
        if (currentMessage.loopCount !== null && currentMessage.loopCount > 0) {  
            currentMessage.currentLoop++;  
              
            // 如果达到循环次数,移除消息  
            if (currentMessage.currentLoop >= currentMessage.loopCount) {  
                this.removeMessage(currentMessage.id);  
                // 不增加索引,因为移除后当前位置已经是下一条消息  
                if (this.currentIndex >= this.messages.length) {  
                    this.currentIndex = 0;  
                }  
            } else {  
                // 继续循环,移动到下一条  
                this.currentIndex = (this.currentIndex + 1) % this.messages.length;  
            }  
        } else {  
            // 持久消息或临时消息,直接移动到下一条  
            this.currentIndex = (this.currentIndex + 1) % this.messages.length;  
        }  
          
        this.showCurrentMessage();  
    }  
      
    setupLoopCounter(messageId, maxLoops) {  
        // 循环计数在nextMessage中处理  
    }  
      
    removeMessage(messageId) {  
        const index = this.messages.findIndex(m => m.id === messageId);  
        if (index !== -1) {  
            this.messages.splice(index, 1);  
              
            // 调整当前索引  
            if (this.currentIndex >= this.messages.length) {  
                this.currentIndex = 0;  
            }  
              
            // 如果没有消息了,停止轮播  
            if (this.messages.length === 0) {  
                if (this.rotationInterval) {  
                    clearInterval(this.rotationInterval);  
                    this.rotationInterval = null;  
                }  
                this.container.innerHTML = '';  
            } else {  
                this.showCurrentMessage();  
            }  
        }  
    }  
      
    findRemovableMessageIndex() {  
        // 优先移除临时消息  
        const tempIndex = this.messages.findIndex(m => !m.persistent && m.loopCount === null);  
        if (tempIndex !== -1) return tempIndex;  
          
        // 其次移除已完成循环的消息  
        const completedIndex = this.messages.findIndex(m =>   
            m.loopCount !== null && m.currentLoop >= m.loopCount  
        );  
        if (completedIndex !== -1) return completedIndex;  
          
        return -1;  
    }  
      
    escapeHtml(text) {  
        const div = document.createElement('div');  
        div.textContent = text;  
        return div.innerHTML;  
    }  
}  

window.footerMarquee = new FooterMarqueeManager(); 