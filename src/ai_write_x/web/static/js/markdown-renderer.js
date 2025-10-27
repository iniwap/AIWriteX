/**  
 * Markdown渲染工具类  
 */  
class MarkdownRenderer {  
    constructor() {  
        this.initialized = false;  
        this.init();  
    }  
      
    init() {  
        if (typeof marked === 'undefined') {  
            console.error('marked.js 未加载');  
            return;  
        }  
          
        // 配置marked  
        marked.setOptions({  
            breaks: true,        // GFM换行  
            gfm: true,          // GitHub风格Markdown  
            headerIds: true,    // 为标题生成ID  
            mangle: false,      // 不混淆邮箱地址  
            pedantic: false,    // 不使用严格模式  
            smartLists: true,   // 智能列表  
            smartypants: false  // 不使用智能标点  
        });  
          
        this.initialized = true;  
    }  
      
    /**  
     * 渲染Markdown为HTML  
     */  
    render(markdown) {  
        if (!this.initialized || typeof marked === 'undefined') {  
            // 降级到简单实现  
            return this.simpleFallback(markdown);  
        }  
          
        try {  
            return marked.parse(markdown);  
        } catch (error) {  
            console.error('Markdown渲染失败:', error);  
            return this.simpleFallback(markdown);  
        }  
    }  
      
    /**  
     * 简单降级实现  
     */  
    simpleFallback(markdown) {  
        return markdown  
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')  
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')  
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')  
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')  
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')  
            .replace(/`(.*?)`/gim, '<code>$1</code>')  
            .replace(/\n/gim, '<br>');  
    }  
      
    /**  
     * 生成带样式的完整HTML文档(用于iframe)  
     */  
    renderWithStyles(markdown, isDarkTheme = false) {  
        const htmlContent = this.render(markdown);  
        
        // 获取CSS变量值,与全局样式保持一致  
        const computedStyle = getComputedStyle(document.documentElement);  
        const bgColor = computedStyle.getPropertyValue('--background-color').trim();  
        const borderColor = computedStyle.getPropertyValue('--border-color').trim();  
        const secondaryColor = computedStyle.getPropertyValue('--secondary-color').trim();  
        const textColor = computedStyle.getPropertyValue('--text-primary').trim();  
        
        return `  
    <!DOCTYPE html>  
    <html>  
    <head>  
        <meta charset="UTF-8">  
        <style>  
            body {  
                margin: 0;  
                padding: 16px;  
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;  
                line-height: 1.6;  
                overflow: auto;  
                color: ${textColor};  
                background: ${bgColor};  
            }  
            
            /* 使用与全局CSS相同的滚动条样式 - 6px宽,3px圆角 */  
            ::-webkit-scrollbar {  
                width: 6px;  
                height: 6px;  
            }  
            
            ::-webkit-scrollbar-track {  
                background: ${bgColor};  
            }  
            
            ::-webkit-scrollbar-thumb {  
                background: ${borderColor};  
                border-radius: 3px;  
            }  
            
            ::-webkit-scrollbar-thumb:hover {  
                background: ${secondaryColor};  
            }  
            
            /* Markdown内容样式 */  
            h1, h2, h3, h4, h5, h6 {   
                margin-top: 24px;   
                margin-bottom: 16px;  
                font-weight: 600;  
                line-height: 1.25;  
            }  
            h1 { font-size: 2em; border-bottom: 1px solid ${borderColor}; padding-bottom: 0.3em; }  
            h2 { font-size: 1.5em; border-bottom: 1px solid ${borderColor}; padding-bottom: 0.3em; }  
            h3 { font-size: 1.25em; }  
            
            p { margin-bottom: 16px; }  
            
            ul, ol { padding-left: 2em; margin-bottom: 16px; }  
            li { margin-bottom: 4px; }  
            
            blockquote {  
                margin: 0 0 16px 0;  
                padding: 0 1em;  
                color: #6a737d;  
                border-left: 4px solid ${borderColor};  
            }  
            
            code {  
                background: ${isDarkTheme ? '#2d2d2d' : '#f6f8fa'};  
                padding: 2px 6px;  
                border-radius: 3px;  
                font-family: 'Consolas', 'Monaco', monospace;  
                font-size: 85%;  
            }  
            
            pre {  
                background: ${isDarkTheme ? '#2d2d2d' : '#f6f8fa'};  
                padding: 16px;  
                border-radius: 6px;  
                overflow-x: auto;  
                margin-bottom: 16px;  
            }  
            
            pre code {  
                background: none;  
                padding: 0;  
            }  
            
            table {  
                border-collapse: collapse;  
                width: 100%;  
                margin-bottom: 16px;  
            }  
            
            table th, table td {  
                padding: 6px 13px;  
                border: 1px solid ${borderColor};  
            }  
            
            table th {  
                background: ${isDarkTheme ? '#2d2d2d' : '#f6f8fa'};  
                font-weight: 600;  
            }  
            
            img {  
                max-width: 100%;  
                height: auto;  
            }  
            
            a {  
                color: #0366d6;  
                text-decoration: none;  
            }  
            
            a:hover {  
                text-decoration: underline;  
            }  
            
            hr {  
                height: 0.25em;  
                padding: 0;  
                margin: 24px 0;  
                background-color: ${borderColor};  
                border: 0;  
            }  
        </style>  
    </head>  
    <body>  
        ${htmlContent}  
    </body>  
    </html>  
        `;  
    }
}  
  
// 全局实例  
window.markdownRenderer = new MarkdownRenderer();