class UpdateChecker {
    constructor() {
        this.updateInfo = null;
        this.checked = false;  // 防止重复检查  
        this.init();
    }

    async init() {
        // 只在页面首次加载时检查一次  
        if (this.checked) return;

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.checkForUpdatesOnce();
            });
        } else {
            this.checkForUpdatesOnce();
        }
    }

    async checkForUpdatesOnce() {
        if (this.checked) return;
        this.checked = true;

        try {
            const response = await fetch('/api/config/check-updates');
            const data = await response.json();

            if (data.status === 'success' && data.has_update) {
                this.updateInfo = data;
                this.showUpdateIndicator();
                this.showUpdateNotification();
            }
        } catch (error) {
            console.log('启动时版本检查失败:', error);
        }
    }

    showUpdateIndicator() {
        const statusIndicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.status-text');

        if (statusIndicator && statusText) {
            // 改为灰色  
            statusIndicator.style.background = 'var(--primary-hover-color)';

            statusText.innerHTML = `新版本 ${this.updateInfo.latest_version} 可用`;
            statusIndicator.style.cursor = 'pointer';
            statusIndicator.onclick = () => this.showUpdateDialog();
        }
    }

    showUpdateNotification() {
        if (window.showNotification) {
            window.showNotification(
                `发现新版本 ${this.updateInfo.latest_version}`,
                'info',
                5000
            );
        }
    }

    showUpdateDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'update-dialog-overlay';
        dialog.innerHTML = `    
        <div class="update-dialog">    
            <div class="update-dialog-header">    
                <h3>🚀 发现新版本 ${this.updateInfo.latest_version}</h3>    
                <button class="close-btn" onclick="this.closest('.update-dialog-overlay').remove()">×</button>    
            </div>    
            <div class="update-dialog-content">    
                <div class="version-info">    
                    <p><strong>当前版本:</strong> ${this.updateInfo.current_version}</p>    
                    <p><strong>最新版本:</strong> ${this.updateInfo.latest_version}</p>    
                </div>    
                <div class="release-notes">    
                    <h4>更新内容:</h4>    
                    <pre>${this.updateInfo.release_notes || '暂无更新说明'}</pre>    
                </div>    
            </div>    
            <div class="update-dialog-actions">    
                <button class="btn btn-primary" onclick="openDownloadPage()">    
                    官网下载    
                </button>   
                
                <button class="btn btn-outline" onclick="this.closest('.update-dialog-overlay').remove()">    
                    稍后提醒    
                </button>    
            </div>    
        </div>    
    `;

        document.body.appendChild(dialog);

        if (!document.querySelector('#update-dialog-styles')) {
            const style = document.createElement('style');
            style.id = 'update-dialog-styles';
            style.textContent = `    
            .update-dialog-overlay {    
                position: fixed;    
                top: 0;    
                left: 0;    
                right: 0;    
                bottom: 0;    
                background: rgba(0, 0, 0, 0.5);    
                display: flex;    
                align-items: center;    
                justify-content: center;    
                z-index: 10000;    
            }    
              
            .update-dialog {    
                background: var(--surface-color);    
                border-radius: 12px;    
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);    
                max-width: 600px;    
                width: 90%;    
                max-height: 80vh;    
                overflow: hidden;    
                animation: slideIn 0.3s ease-out;    
            }    
              
            @keyframes slideIn {    
                from {    
                    opacity: 0;    
                    transform: translateY(-20px);    
                }    
                to {    
                    opacity: 1;    
                    transform: translateY(0);    
                }    
            }    
              
            .update-dialog-header {    
                display: flex;    
                justify-content: space-between;    
                align-items: center;    
                padding: 20px 24px;    
                border-bottom: 1px solid var(--border-color);    
            }    
              
            .update-dialog-header h3 {    
                margin: 0;    
                color: var(--text-primary);    
            }    
              
            .close-btn {    
                background: none;    
                border: none;    
                font-size: 24px;    
                cursor: pointer;    
                color: var(--text-secondary);    
                padding: 0;    
                width: 32px;    
                height: 32px;    
                display: flex;    
                align-items: center;    
                justify-content: center;    
                border-radius: 6px;    
            }    
              
            .close-btn:hover {    
                background: var(--hover-color);    
            }    
              
            .update-dialog-content {    
                padding: 24px;    
                max-height: 400px;    
                overflow-y: auto;    
            }    
              
            .version-info p {    
                margin: 8px 0;    
                color: var(--text-secondary);    
            }    
              
            .release-notes h4 {    
                margin: 20px 0 12px 0;    
                color: var(--text-primary);    
            }    
              
            .release-notes pre {    
                background: var(--background-color);    
                border: 1px solid var(--border-color);    
                border-radius: 6px;    
                padding: 12px;    
                white-space: pre-wrap;    
                word-wrap: break-word;    
                font-family: inherit;    
                font-size: 14px;    
                line-height: 1.5;    
                color: var(--text-secondary);    
            }    
              
            .update-dialog-actions {    
                display: flex;    
                gap: 12px;    
                padding: 20px 24px;    
                border-top: 1px solid var(--border-color);    
                justify-content: flex-end;    
            }        
        `;
            document.head.appendChild(style);
        }
    }
}

async function openDownloadPage() {
    try {
        const response = await fetch('/api/config/open-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: 'https://aiwritex.voidai.cc' })
        });

        const result = await response.json();
        if (result.status !== 'success') {
            console.error('打开链接失败:', result.message);
        }
    } catch (error) {
        console.error('请求失败:', error);
    }
}