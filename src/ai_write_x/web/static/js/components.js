// 维度滑块组件  
class DimensionSlider {  
    constructor(container, config) {  
        this.container = container;  
        this.config = config;  
        this.value = config.defaultValue || 0;  
        this.render();  
    }  
      
    render() {  
        this.container.innerHTML = `  
            <div class="dimension-group">  
                <div class="dimension-title">  
                    <span>${this.config.title}</span>  
                    <span class="slider-value">${this.value}</span>  
                </div>  
                <div class="slider-container">  
                    <input type="range"   
                           class="slider-input dimension-slider"   
                           min="${this.config.min || 0}"   
                           max="${this.config.max || 100}"   
                           value="${this.value}"  
                           data-dimension="${this.config.key}">  
                    <div class="slider-labels">  
                        <span>${this.config.minLabel || this.config.min}</span>  
                        <span>${this.config.maxLabel || this.config.max}</span>  
                    </div>  
                </div>  
                <div class="dimension-description">  
                    ${this.config.description || ''}  
                </div>  
            </div>  
        `;  
          
        const slider = this.container.querySelector('.slider-input');  
        const valueDisplay = this.container.querySelector('.slider-value');  
          
        slider.addEventListener('input', (e) => {  
            this.value = parseFloat(e.target.value);  
            valueDisplay.textContent = this.value;  
              
            if (this.config.onChange) {  
                this.config.onChange(this.value);  
            }  
        });  
    }  
      
    setValue(value) {  
        this.value = value;  
        const slider = this.container.querySelector('.slider-input');  
        const valueDisplay = this.container.querySelector('.slider-value');  
          
        if (slider) slider.value = value;  
        if (valueDisplay) valueDisplay.textContent = value;  
    }  
}  
  
// 预览标签页组件  
class PreviewTabs {  
    constructor(container) {  
        this.container = container;  
        this.tabs = [];  
        this.activeTab = 0;  
        this.render();  
    }  
      
    addTab(title, content) {  
        this.tabs.push({ title, content });  
        this.render();  
    }  
      
    render() {  
        this.container.innerHTML = `  
            <div class="preview-tabs">  
                ${this.tabs.map((tab, index) => `  
                    <button class="preview-tab ${index === this.activeTab ? 'active' : ''}"   
                            data-tab="${index}">  
                        ${tab.title}  
                    </button>  
                `).join('')}  
            </div>  
            <div class="preview-content">  
                ${this.tabs[this.activeTab]?.content || ''}  
            </div>  
        `;  
          
        // 绑定标签页点击事件  
        this.container.querySelectorAll('.preview-tab').forEach((tab, index) => {  
            tab.addEventListener('click', () => {  
                this.setActiveTab(index);  
            });  
        });  
    }  
      
    setActiveTab(index) {  
        if (index >= 0 && index < this.tabs.length) {  
            this.activeTab = index;  
            this.render();  
        }  
    }  
}
// 配置表单组件  
class ConfigForm {  
    constructor(container, config) {  
        this.container = container;  
        this.config = config;
        this.data = {};  
        this.render();  
    }  
      
    render() {  
        const fields = this.config.fields || [];  
          
        this.container.innerHTML = `  
            <form class="config-form">  
                ${fields.map(field => this.renderField(field)).join('')}  
                <div class="form-actions">  
                    <button type="submit" class="btn btn-primary">保存设置</button>  
                    <button type="button" class="btn btn-secondary" id="reset-config">重置</button>  
                </div>  
            </form>  
        `;  
          
        // 绑定表单事件  
        const form = this.container.querySelector('.config-form');  
        form.addEventListener('submit', (e) => {  
            e.preventDefault();  
            this.saveConfig();  
        });  
          
        const resetBtn = this.container.querySelector('#reset-config');  
        resetBtn.addEventListener('click', () => {  
            this.resetConfig();  
        });  
    }  
      
    renderField(field) {  
        switch (field.type) {  
            case 'text':  
                return `  
                    <div class="form-group">  
                        <label class="form-label">${field.label}</label>  
                        <input type="text" class="form-input"   
                               name="${field.name}"   
                               value="${this.data[field.name] || ''}"  
                               placeholder="${field.placeholder || ''}">  
                    </div>  
                `;  
            case 'select':  
                return `  
                    <div class="form-group">  
                        <label class="form-label">${field.label}</label>  
                        <select class="form-select" name="${field.name}">  
                            ${field.options.map(option => `  
                                <option value="${option.value}"   
                                        ${this.data[field.name] === option.value ? 'selected' : ''}>  
                                    ${option.label}  
                                </option>  
                            `).join('')}  
                        </select>  
                    </div>  
                `;  
            case 'checkbox':  
                return `  
                    <div class="form-group">  
                        <div class="config-toggle">  
                            <div class="toggle-switch ${this.data[field.name] ? 'active' : ''}"   
                                 data-field="${field.name}">  
                            </div>  
                            <label class="form-label">${field.label}</label>  
                        </div>  
                    </div>  
                `;  
            default:  
                return '';  
        }  
    }  
      
    saveConfig() {  
        // 收集表单数据  
        const formData = new FormData(this.container.querySelector('.config-form'));  
        for (const [key, value] of formData.entries()) {  
            this.data[key] = value;  
        }  
          
        if (this.config.onSave) {  
            this.config.onSave(this.data);  
        }  
    }  
      
    resetConfig() {  
        this.data = {};  
        this.render();  
          
        if (this.config.onReset) {  
            this.config.onReset();  
        }  
    }  
}  
  
// 通知组件  
class NotificationManager {  
    constructor() {  
        this.notifications = [];  
        this.container = this.createContainer();  
    }  
      
    createContainer() {  
        const container = document.createElement('div');  
        container.className = 'notification-container';  
        container.style.cssText = `  
            position: fixed;  
            top: 20px;  
            right: 20px;  
            z-index: 10100;  
            pointer-events: none;  
        `;  
        document.body.appendChild(container);  
        return container;  
    }  
      
    show(message, type = 'info', duration = 3000) {  
        const notification = document.createElement('div');  
        notification.className = `notification ${type}`;  
        notification.style.cssText = `  
            pointer-events: auto;  
            margin-bottom: 12px;  
            animation: notificationSlideIn 0.3s ease;  
        `;  
          
        notification.innerHTML = `  
            <div class="notification-content">  
                <span>${message}</span>  
                <button class="notification-close">×</button>  
            </div>  
        `;  
          
        // 绑定关闭事件  
        const closeBtn = notification.querySelector('.notification-close');  
        closeBtn.addEventListener('click', () => {  
            this.remove(notification);  
        });  
          
        this.container.appendChild(notification);  
        this.notifications.push(notification);  
          
        // 自动移除  
        if (duration > 0) {  
            setTimeout(() => {  
                this.remove(notification);  
            }, duration);  
        }  
    }  
      
    remove(notification) {  
        if (notification.parentElement) {  
            notification.style.animation = 'slideOut 0.3s ease';  
            setTimeout(() => {  
                notification.remove();  
                const index = this.notifications.indexOf(notification);  
                if (index > -1) {  
                    this.notifications.splice(index, 1);  
                }  
            }, 300);  
        }  
    }  
}  
  
// 全局通知管理器实例  
window.notificationManager = new NotificationManager();