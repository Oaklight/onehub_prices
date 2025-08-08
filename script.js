class PriceViewer {
    constructor() {
        this.data = [];
        this.filteredData = [];
        this.channelTypes = new Set();
        this.ownedByData = {};
        
        this.initElements();
        this.bindEvents();
        this.loadData();
    }
    
    initElements() {
        this.searchInput = document.getElementById('searchInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.channelFilter = document.getElementById('channelFilter');
        this.typeFilter = document.getElementById('typeFilter');
        this.tableBody = document.getElementById('tableBody');
        this.totalModels = document.getElementById('totalModels');
        this.filteredModels = document.getElementById('filteredModels');
        this.loading = document.getElementById('loading');
        this.noResults = document.getElementById('noResults');
        this.tableContainer = document.querySelector('.table-container');
        this.channelsGrid = document.getElementById('channelsGrid');
        
        // 标签页元素
        this.tabButtons = document.querySelectorAll('.tab-button');
        this.tabContents = document.querySelectorAll('.tab-content');
        
        // 帮助页面元素
        this.helpLoading = document.getElementById('helpLoading');
        this.helpContent = document.getElementById('helpContent');
        this.helpError = document.getElementById('helpError');
    }
    
    bindEvents() {
        this.searchBtn.addEventListener('click', () => this.performSearch());
        this.clearBtn.addEventListener('click', () => this.clearFilters());
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
        this.searchInput.addEventListener('input', () => this.performSearch());
        this.channelFilter.addEventListener('change', () => this.performSearch());
        this.typeFilter.addEventListener('change', () => this.performSearch());
        
        // 标签页事件
        this.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
    }
    
    async loadData() {
        try {
            // 并行加载价格数据和渠道信息（从 prices 分支）
            const [pricesResponse, ownedByResponse] = await Promise.all([
                fetch('https://raw.githubusercontent.com/Oaklight/onehub_prices/prices/oneapi_prices.json'),
                fetch('https://raw.githubusercontent.com/Oaklight/onehub_prices/prices/ownedby.json')
            ]);
            
            if (!pricesResponse.ok) {
                throw new Error(`价格数据加载失败: ${pricesResponse.status} ${pricesResponse.statusText}`);
            }
            
            const pricesData = await pricesResponse.json();
            this.data = pricesData.data || [];
            console.log('成功加载价格数据，条数:', this.data.length);
            
            // 加载渠道信息
            if (ownedByResponse.ok) {
                const ownedByData = await ownedByResponse.json();
                this.ownedByData = ownedByData.data || {};
                console.log('成功加载渠道信息，渠道数:', Object.keys(this.ownedByData).length);
            } else {
                console.warn('渠道信息加载失败，将使用默认显示');
            }
            
        } catch (error) {
            console.error('数据加载失败:', error);
            
            // 显示用户友好的错误信息
            this.showError(`数据加载失败: ${error.message}`);
            
            // 使用示例数据作为后备
            console.warn('使用示例数据作为后备');
            this.data = this.getSampleData();
        }
        
        this.processData();
        this.populateFilters();
        this.renderChannels();
        this.filteredData = [...this.data];
        this.renderTable();
        this.updateStats();
        this.hideLoading();
    }
    
    getSampleData() {
        // 基于之前看到的数据结构创建示例数据
        return [
            {
                "model": "gpt-3.5-turbo",
                "type": "tokens",
                "channel_type": 1,
                "input": 0.25,
                "output": 0.75
            },
            {
                "model": "gpt-4",
                "type": "tokens",
                "channel_type": 1,
                "input": 15.0,
                "output": 30.0
            },
            {
                "model": "gpt-4o",
                "type": "tokens",
                "channel_type": 1,
                "input": 1.25,
                "output": 5.0,
                "extra_ratios": {
                    "cached_tokens": 0.5
                }
            },
            {
                "model": "claude-3-haiku",
                "type": "tokens",
                "channel_type": 14,
                "input": 0.125,
                "output": 0.625
            },
            {
                "model": "claude-3-opus",
                "type": "tokens",
                "channel_type": 14,
                "input": 7.5,
                "output": 37.5
            },
            {
                "model": "dall-e-3",
                "type": "tokens",
                "channel_type": 1,
                "input": 20,
                "output": 20
            }
        ];
    }
    
    processData() {
        // 收集所有渠道类型
        this.data.forEach(item => {
            this.channelTypes.add(item.channel_type);
        });
    }
    
    populateFilters() {
        // 填充渠道类型筛选器
        const sortedChannelTypes = Array.from(this.channelTypes).sort((a, b) => a - b);
        sortedChannelTypes.forEach(channelType => {
            const option = document.createElement('option');
            option.value = channelType;
            
            // 使用 ownedby 数据显示渠道名称
            const channelInfo = this.ownedByData[channelType];
            const displayName = channelInfo ? channelInfo.name : `渠道类型 ${channelType}`;
            option.textContent = `${displayName} (${channelType})`;
            
            this.channelFilter.appendChild(option);
        });
    }
    
    switchTab(tabName) {
        // 更新标签按钮状态
        this.tabButtons.forEach(button => {
            button.classList.remove('active');
            if (button.dataset.tab === tabName) {
                button.classList.add('active');
            }
        });
        
        // 更新标签内容显示
        this.tabContents.forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none';
            if (content.id === `${tabName}-tab`) {
                content.classList.add('active');
                content.style.display = 'block';
            }
        });
        
        // 如果切换到帮助页面，加载 README 内容
        if (tabName === 'help') {
            this.loadHelpContent();
        }
    }
    
    async loadHelpContent() {
        // 如果已经加载过内容，直接显示
        if (this.helpContent && this.helpContent.innerHTML.trim() !== '') {
            this.helpLoading.style.display = 'none';
            this.helpContent.style.display = 'block';
            return;
        }
        
        if (!this.helpLoading || !this.helpContent || !this.helpError) {
            console.warn('帮助页面元素未找到');
            return;
        }
        
        this.helpLoading.style.display = 'block';
        this.helpContent.style.display = 'none';
        this.helpError.style.display = 'none';
        
        try {
            // 首先尝试从本地加载 README
            let response = await fetch('./README.md');
            
            if (!response.ok) {
                console.log('本地 README 不存在，尝试从 master 分支获取');
                // 如果本地没有，从 master 分支获取
                response = await fetch('https://raw.githubusercontent.com/Oaklight/onehub_prices/master/README.md');
            }
            
            if (!response.ok) {
                throw new Error(`无法获取 README: ${response.status}`);
            }
            
            const markdownContent = await response.text();
            
            // 简单的 Markdown 转 HTML
            const htmlContent = this.markdownToHtml(markdownContent);
            
            this.helpContent.innerHTML = htmlContent;
            this.helpLoading.style.display = 'none';
            this.helpContent.style.display = 'block';
            
        } catch (error) {
            console.error('加载帮助内容失败:', error);
            this.helpLoading.style.display = 'none';
            this.helpError.style.display = 'block';
        }
    }
    
    markdownToHtml(markdown) {
        let html = markdown;
        
        // 转换标题
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
        
        // 转换粗体和斜体
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // 转换代码块
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // 转换链接
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        
        // 转换列表
        html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
        html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');
        
        // 包装列表项
        html = html.replace(/(<li>.*<\/li>)/gs, (match) => {
            return '<ul>' + match + '</ul>';
        });
        
        // 转换段落
        html = html.split('\n\n').map(paragraph => {
            paragraph = paragraph.trim();
            if (paragraph === '') return '';
            if (paragraph.startsWith('<h') || paragraph.startsWith('<ul') || 
                paragraph.startsWith('<pre') || paragraph.startsWith('<li')) {
                return paragraph;
            }
            return '<p>' + paragraph.replace(/\n/g, '<br>') + '</p>';
        }).join('\n');
        
        // 清理多余的换行
        html = html.replace(/\n+/g, '\n');
        
        return html;
    }
    
    renderChannels() {
        if (!this.channelsGrid) return;
        
        this.channelsGrid.innerHTML = '';
        
        // 统计每个渠道的模型数量
        const channelStats = {};
        this.data.forEach(item => {
            const channelType = item.channel_type;
            if (!channelStats[channelType]) {
                channelStats[channelType] = {
                    total: 0,
                    tokens: 0,
                    times: 0
                };
            }
            channelStats[channelType].total++;
            if (item.type === 'tokens') {
                channelStats[channelType].tokens++;
            } else if (item.type === 'times') {
                channelStats[channelType].times++;
            }
        });
        
        // 按渠道ID排序
        const sortedChannels = Object.keys(channelStats).sort((a, b) => parseInt(a) - parseInt(b));
        
        sortedChannels.forEach(channelId => {
            const channelInfo = this.ownedByData[channelId];
            const stats = channelStats[channelId];
            
            const channelCard = document.createElement('div');
            channelCard.className = 'channel-card';
            
            const channelName = channelInfo ? channelInfo.name : `渠道 ${channelId}`;
            const channelIcon = channelInfo ? channelInfo.icon : '';
            
            channelCard.innerHTML = `
                <div class="channel-header">
                    ${channelIcon ? 
                        `<img src="${channelIcon}" alt="${channelName}" class="channel-icon" onerror="this.style.display='none'">` : 
                        `<div class="channel-icon" style="background: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold;">${channelId}</div>`
                    }
                    <div class="channel-info">
                        <h3>${channelName}</h3>
                        <div class="channel-id">ID: ${channelId}</div>
                    </div>
                </div>
                <div class="channel-stats">
                    <div class="stat-box">
                        <span class="number">${stats.total}</span>
                        <span class="label">总模型</span>
                    </div>
                    <div class="stat-box">
                        <span class="number">${stats.tokens}</span>
                        <span class="label">Token 模型</span>
                    </div>
                </div>
            `;
            
            // 点击卡片切换到价格页面并筛选该渠道
            channelCard.addEventListener('click', () => {
                this.switchTab('prices');
                this.channelFilter.value = channelId;
                this.performSearch();
            });
            
            this.channelsGrid.appendChild(channelCard);
        });
    }
    
    performSearch() {
        const searchTerm = this.searchInput.value.toLowerCase().trim();
        const channelFilter = this.channelFilter.value;
        const typeFilter = this.typeFilter.value;
        
        this.filteredData = this.data.filter(item => {
            const matchesSearch = !searchTerm || 
                item.model.toLowerCase().includes(searchTerm);
            
            const matchesChannel = !channelFilter || 
                item.channel_type.toString() === channelFilter;
            
            const matchesType = !typeFilter || 
                item.type === typeFilter;
            
            return matchesSearch && matchesChannel && matchesType;
        });
        
        this.renderTable();
        this.updateStats();
    }
    
    clearFilters() {
        this.searchInput.value = '';
        this.channelFilter.value = '';
        this.typeFilter.value = '';
        this.filteredData = [...this.data];
        this.renderTable();
        this.updateStats();
    }
    
    renderTable() {
        if (this.filteredData.length === 0) {
            this.showNoResults();
            return;
        }
        
        this.hideNoResults();
        
        this.tableBody.innerHTML = '';
        
        this.filteredData.forEach(item => {
            const row = document.createElement('tr');
            
            // 模型名称
            const modelCell = document.createElement('td');
            modelCell.innerHTML = `<span class="model-name">${this.escapeHtml(item.model)}</span>`;
            row.appendChild(modelCell);
            
            // 类型
            const typeCell = document.createElement('td');
            typeCell.innerHTML = `<span class="type-badge type-${item.type}">${item.type}</span>`;
            row.appendChild(typeCell);
            
            // 渠道类型
            const channelCell = document.createElement('td');
            const channelInfo = this.ownedByData[item.channel_type];
            const channelName = channelInfo ? channelInfo.name : `渠道 ${item.channel_type}`;
            channelCell.innerHTML = `
                <div class="channel-display">
                    ${channelInfo && channelInfo.icon ? 
                        `<img src="${channelInfo.icon}" alt="${channelName}" class="channel-icon-small" onerror="this.style.display='none'">` : 
                        ''
                    }
                    <span class="channel-name">${channelName}</span>
                    <span class="channel-id">(${item.channel_type})</span>
                </div>
            `;
            row.appendChild(channelCell);
            
            // 输入价格
            const inputCell = document.createElement('td');
            const inputPrice = this.formatPrice(item.input);
            inputCell.innerHTML = `<span class="price ${item.input === 0 ? 'zero' : ''}">${inputPrice}</span>`;
            row.appendChild(inputCell);
            
            // 输出价格
            const outputCell = document.createElement('td');
            const outputPrice = this.formatPrice(item.output);
            outputCell.innerHTML = `<span class="price ${item.output === 0 ? 'zero' : ''}">${outputPrice}</span>`;
            row.appendChild(outputCell);
            
            // 额外费率
            const extraCell = document.createElement('td');
            if (item.extra_ratios) {
                const ratios = Object.entries(item.extra_ratios)
                    .map(([key, value]) => `<span class="ratio-item">${key}: ${value}</span>`)
                    .join('');
                extraCell.innerHTML = `<div class="extra-ratios">${ratios}</div>`;
            } else {
                extraCell.innerHTML = '<span class="extra-ratios">-</span>';
            }
            row.appendChild(extraCell);
            
            this.tableBody.appendChild(row);
        });
    }
    
    formatPrice(price) {
        if (price === 0) {
            return '免费';
        }
        return price.toFixed(3);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateStats() {
        this.totalModels.textContent = this.data.length;
        this.filteredModels.textContent = this.filteredData.length;
    }
    
    hideLoading() {
        this.loading.style.display = 'none';
        this.tableContainer.style.display = 'block';
    }
    
    showNoResults() {
        this.tableContainer.style.display = 'none';
        this.noResults.style.display = 'block';
    }
    
    hideNoResults() {
        this.noResults.style.display = 'none';
        this.tableContainer.style.display = 'block';
    }
    
    showError(message) {
        // 创建或更新错误显示元素
        let errorDiv = document.getElementById('errorMessage');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'errorMessage';
            errorDiv.className = 'error-message';
            errorDiv.style.cssText = `
                background-color: #fee;
                border: 1px solid #fcc;
                color: #c33;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
                display: block;
            `;
            // 插入到加载指示器之后
            this.loading.parentNode.insertBefore(errorDiv, this.loading.nextSibling);
        }
        
        errorDiv.innerHTML = `
            <strong>⚠️ 错误:</strong> ${message}
            <br><small>正在使用示例数据，功能可能受限</small>
        `;
        errorDiv.style.display = 'block';
        
        // 5秒后自动隐藏错误消息
        setTimeout(() => {
            if (errorDiv) {
                errorDiv.style.display = 'none';
            }
        }, 5000);
    }
}

// 当页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new PriceViewer();
});

// 添加一些实用功能
document.addEventListener('DOMContentLoaded', () => {
    // 添加键盘快捷键
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + K 聚焦搜索框
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('searchInput').focus();
        }
        
        // Escape 清除搜索
        if (e.key === 'Escape') {
            const searchInput = document.getElementById('searchInput');
            if (document.activeElement === searchInput) {
                searchInput.blur();
            }
        }
    });
    
    // 添加搜索框提示
    const searchInput = document.getElementById('searchInput');
    searchInput.setAttribute('title', '支持模糊搜索，按 Ctrl+K 快速聚焦');
});