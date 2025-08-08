class PriceViewer {
    constructor() {
        this.data = [];
        this.filteredData = [];
        this.channelTypes = new Set();
        this.ownedByData = {};
        this.priceMode = 'ratio'; // 默认显示倍率模式
        
        // 价格转换常量（来自 src/utils.py）
        this.SCALE_FACTOR_CNY = 0.014;
        this.SCALE_FACTOR_USD = 0.002;
        
        this.initElements();
        this.bindEvents();
        this.loadData();
    }
    
    initElements() {
        this.searchInput = document.getElementById('searchInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.channelFilter = document.getElementById('channelFilter');
        this.channelFilterTrigger = this.channelFilter.querySelector('.select-trigger');
        this.channelFilterOptions = this.channelFilter.querySelector('.select-options');
        this.channelFilterText = this.channelFilter.querySelector('.select-text');
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
        
        // 价格模式切换按钮
        this.ratioModeBtn = document.getElementById('ratioModeBtn');
        this.cnyModeBtn = document.getElementById('cnyModeBtn');
        this.usdModeBtn = document.getElementById('usdModeBtn');
        this.priceModeButtons = document.querySelectorAll('.price-mode-btn');
        
        // 自定义下拉组件状态
        this.selectedChannelValue = '';
        
        // 清空搜索框（页面刷新时）
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        
        // 帮助页面元素（已移除动态加载逻辑）
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
        this.typeFilter.addEventListener('change', () => this.performSearch());
        
        // 自定义下拉组件事件
        this.channelFilterTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleChannelDropdown();
        });
        
        // 点击外部关闭下拉菜单
        document.addEventListener('click', (e) => {
            if (!this.channelFilter.contains(e.target)) {
                this.closeChannelDropdown();
            }
        });
        
        // 标签页事件
        this.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // 价格模式切换事件
        this.priceModeButtons.forEach(button => {
            button.addEventListener('click', (e) => this.switchPriceMode(e.target.dataset.mode));
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
        // 填充渠道类型筛选器（自定义下拉组件）
        const sortedChannelTypes = Array.from(this.channelTypes).sort((a, b) => a - b);
        
        // 清空现有选项（保留默认选项）
        this.channelFilterOptions.innerHTML = `
            <div class="select-option" data-value="">
                <span class="option-text">所有渠道类型</span>
            </div>
        `;
        
        sortedChannelTypes.forEach(channelType => {
            const channelInfo = this.ownedByData[channelType];
            const displayName = channelInfo ? channelInfo.name : `渠道类型 ${channelType}`;
            
            const optionDiv = document.createElement('div');
            optionDiv.className = 'select-option';
            optionDiv.dataset.value = channelType;
            
            optionDiv.innerHTML = `
                ${channelInfo && channelInfo.icon ?
                    `<img src="${channelInfo.icon}" alt="${displayName}" class="option-icon" onerror="this.style.display='none'">` :
                    ''
                }
                <span class="option-text">${displayName}</span>
                <span class="option-id">(${channelType})</span>
            `;
            
            // 添加点击事件
            optionDiv.addEventListener('click', () => {
                this.selectChannelOption(channelType, displayName, channelInfo);
            });
            
            this.channelFilterOptions.appendChild(optionDiv);
        });
        
        // 为默认选项添加点击事件
        const defaultOption = this.channelFilterOptions.querySelector('[data-value=""]');
        defaultOption.addEventListener('click', () => {
            this.selectChannelOption('', '所有渠道类型', null);
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
        
        // 帮助页面内容已直接嵌入HTML，无需动态加载
    }
    
    // 移除了 loadHelpContent 和 markdownToHtml 方法，因为帮助内容已直接嵌入HTML
    
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
                const channelInfo = this.ownedByData[channelId];
                const displayName = channelInfo ? channelInfo.name : `渠道 ${channelId}`;
                this.selectChannelOption(channelId, displayName, channelInfo);
            });
            
            this.channelsGrid.appendChild(channelCard);
        });
    }
    
    // 自定义下拉组件控制方法
    toggleChannelDropdown() {
        this.channelFilter.classList.toggle('open');
    }
    
    closeChannelDropdown() {
        this.channelFilter.classList.remove('open');
    }
    
    selectChannelOption(value, displayName, channelInfo) {
        this.selectedChannelValue = value;
        
        // 更新显示文本
        if (channelInfo && channelInfo.icon) {
            this.channelFilterText.innerHTML = `
                <img src="${channelInfo.icon}" alt="${displayName}" class="option-icon" onerror="this.style.display='none'">
                <span>${displayName}</span>
            `;
        } else {
            this.channelFilterText.textContent = displayName;
        }
        
        // 更新选中状态
        this.channelFilterOptions.querySelectorAll('.select-option').forEach(option => {
            option.classList.remove('selected');
            if (option.dataset.value === value) {
                option.classList.add('selected');
            }
        });
        
        // 关闭下拉菜单
        this.closeChannelDropdown();
        
        // 执行搜索
        this.performSearch();
    }
    
    performSearch() {
        const searchTerm = this.searchInput.value.toLowerCase().trim();
        const channelFilter = this.selectedChannelValue;
        const typeFilter = this.typeFilter.value;
        
        this.filteredData = this.data.filter(item => {
            const matchesSearch = !searchTerm ||
                this.fuzzyMatch(item.model.toLowerCase(), searchTerm);
            
            const matchesChannel = !channelFilter ||
                item.channel_type.toString() === channelFilter;
            
            const matchesType = !typeFilter ||
                item.type === typeFilter;
            
            return matchesSearch && matchesChannel && matchesType;
        });
        
        // Sort results by relevance if there's a search term
        if (searchTerm) {
            this.filteredData.sort((a, b) => {
                const scoreA = this.calculateMatchScore(a.model.toLowerCase(), searchTerm);
                const scoreB = this.calculateMatchScore(b.model.toLowerCase(), searchTerm);
                return scoreB - scoreA; // Higher score first
            });
        }
        
        this.renderTable();
        this.updateStats();
    }
    
    /**
     * Fuzzy matching algorithm that supports multiple matching strategies
     * @param {string} text - The text to search in
     * @param {string} query - The search query
     * @returns {boolean} - Whether the query matches the text
     */
    fuzzyMatch(text, query) {
        // Strategy 1: Direct substring match (highest priority)
        if (text.includes(query)) {
            return true;
        }
        
        // Strategy 2: Word-based matching
        const textWords = this.extractWords(text);
        const queryWords = this.extractWords(query);
        
        // Check if all query words have matches in text words
        const wordMatches = queryWords.every(queryWord => {
            return textWords.some(textWord => {
                // Exact word match
                if (textWord.includes(queryWord)) {
                    return true;
                }
                // Prefix match for abbreviations
                if (textWord.startsWith(queryWord) && queryWord.length >= 2) {
                    return true;
                }
                // Character sequence match for version numbers
                if (this.sequenceMatch(textWord, queryWord)) {
                    return true;
                }
                return false;
            });
        });
        
        if (wordMatches) {
            return true;
        }
        
        // Strategy 3: Character sequence matching (for cases like "deepseek v3" -> "deepseek-chat-v3")
        return this.advancedSequenceMatch(text, query);
    }
    
    /**
     * Extract meaningful words from text, handling various separators
     * @param {string} text - Input text
     * @returns {Array<string>} - Array of words
     */
    extractWords(text) {
        // Split by common separators and filter out empty strings
        return text.split(/[\s\-_\/\.\:]+/)
                  .filter(word => word.length > 0)
                  .map(word => word.toLowerCase());
    }
    
    /**
     * Check if characters in query appear in sequence in text
     * @param {string} text - Text to search in
     * @param {string} query - Query string
     * @returns {boolean} - Whether sequence matches
     */
    sequenceMatch(text, query) {
        if (query.length === 0) return true;
        if (text.length === 0) return false;
        
        let queryIndex = 0;
        for (let i = 0; i < text.length && queryIndex < query.length; i++) {
            if (text[i] === query[queryIndex]) {
                queryIndex++;
            }
        }
        
        return queryIndex === query.length;
    }
    
    /**
     * Advanced sequence matching with word boundary awareness
     * @param {string} text - Text to search in
     * @param {string} query - Query string
     * @returns {boolean} - Whether advanced sequence matches
     */
    advancedSequenceMatch(text, query) {
        const queryWords = this.extractWords(query);
        const textWords = this.extractWords(text);
        
        // Try to match query words in order within text words
        let queryWordIndex = 0;
        
        for (let textWord of textWords) {
            if (queryWordIndex >= queryWords.length) break;
            
            const currentQueryWord = queryWords[queryWordIndex];
            
            // Check various matching strategies for this word
            if (textWord.includes(currentQueryWord) ||
                textWord.startsWith(currentQueryWord) ||
                this.sequenceMatch(textWord, currentQueryWord)) {
                queryWordIndex++;
            }
        }
        
        // Consider it a match if we matched most of the query words
        return queryWordIndex >= Math.max(1, queryWords.length * 0.7);
    }
    
    /**
     * Calculate match score for sorting results by relevance
     * @param {string} text - Text to score
     * @param {string} query - Query string
     * @returns {number} - Match score (higher is better)
     */
    calculateMatchScore(text, query) {
        let score = 0;
        
        // Exact match gets highest score
        if (text === query) {
            return 1000;
        }
        
        // Direct substring match gets high score
        if (text.includes(query)) {
            score += 500;
            // Bonus for match at beginning
            if (text.startsWith(query)) {
                score += 200;
            }
        }
        
        const textWords = this.extractWords(text);
        const queryWords = this.extractWords(query);
        
        // Score based on word matches
        let wordMatchScore = 0;
        queryWords.forEach(queryWord => {
            textWords.forEach(textWord => {
                if (textWord === queryWord) {
                    wordMatchScore += 100; // Exact word match
                } else if (textWord.includes(queryWord)) {
                    wordMatchScore += 50; // Partial word match
                } else if (textWord.startsWith(queryWord)) {
                    wordMatchScore += 30; // Prefix match
                } else if (this.sequenceMatch(textWord, queryWord)) {
                    wordMatchScore += 20; // Sequence match
                }
            });
        });
        
        score += wordMatchScore;
        
        // Bonus for shorter text (more specific matches)
        score += Math.max(0, 100 - text.length);
        
        // Bonus for matching more query words
        const matchedWords = queryWords.filter(queryWord =>
            textWords.some(textWord =>
                textWord.includes(queryWord) ||
                textWord.startsWith(queryWord) ||
                this.sequenceMatch(textWord, queryWord)
            )
        ).length;
        
        score += (matchedWords / queryWords.length) * 100;
        
        return score;
    }
    
    clearFilters() {
        this.searchInput.value = '';
        this.selectChannelOption('', '所有渠道类型', null);
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
        
        // 更新表头以显示当前价格模式
        this.updateTableHeaders();
        
        this.tableBody.innerHTML = '';
        
        this.filteredData.forEach(item => {
            const row = document.createElement('tr');
            
            // 模型名称
            const modelCell = document.createElement('td');
            const searchTerm = this.searchInput.value.toLowerCase().trim();
            const highlightedModel = searchTerm ?
                this.highlightMatches(item.model, searchTerm) :
                this.escapeHtml(item.model);
            modelCell.innerHTML = `<span class="model-name">${highlightedModel}</span>`;
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
                    .map(([key, value]) => {
                        // 计算相对于输入价格的实际费率
                        const actualRatio = item.input * value;
                        const formattedRatio = this.formatPrice(actualRatio);
                        return `<span class="ratio-item">${key}: ${formattedRatio} (${value}x)</span>`;
                    })
                    .join('');
                extraCell.innerHTML = `<div class="extra-ratios">${ratios}</div>`;
            } else {
                extraCell.innerHTML = '<span class="extra-ratios">-</span>';
            }
            row.appendChild(extraCell);
            
            this.tableBody.appendChild(row);
        });
    }
    
    // 价格模式切换方法
    switchPriceMode(mode) {
        this.priceMode = mode;
        
        // 更新按钮状态
        this.priceModeButtons.forEach(button => {
            button.classList.remove('active');
            if (button.dataset.mode === mode) {
                button.classList.add('active');
            }
        });
        
        // 重新渲染表格
        this.renderTable();
    }
    
    // 价格转换方法
    convertPrice(price, mode) {
        if (price === 0) {
            return '免费';
        }
        
        switch (mode) {
            case 'ratio':
                return price.toFixed(5);
            case 'cny':
                // 倍率转换为人民币：倍率 * SCALE_FACTOR_CNY * 1000 (因为原始倍率是基于1K tokens的)
                const cnyPrice = price * this.SCALE_FACTOR_CNY * 1000;
                return `¥${cnyPrice.toFixed(6)}`;
            case 'usd':
                // 倍率转换为美元：倍率 * SCALE_FACTOR_USD * 1000 (因为原始倍率是基于1K tokens的)
                const usdPrice = price * this.SCALE_FACTOR_USD * 1000;
                return `$${usdPrice.toFixed(6)}`;
            default:
                return price.toFixed(5);
        }
    }
    
    // 更新表头以显示当前价格模式
    updateTableHeaders() {
        const inputHeader = document.querySelector('th:nth-child(4)');
        const outputHeader = document.querySelector('th:nth-child(5)');
        const extraHeader = document.querySelector('th:nth-child(6)');
        
        if (inputHeader && outputHeader) {
            switch (this.priceMode) {
                case 'ratio':
                    inputHeader.textContent = '输入倍率';
                    outputHeader.textContent = '输出倍率';
                    break;
                case 'cny':
                    inputHeader.textContent = '输入价格 (¥/1M tokens)';
                    outputHeader.textContent = '输出价格 (¥/1M tokens)';
                    break;
                case 'usd':
                    inputHeader.textContent = '输入价格 ($/1M tokens)';
                    outputHeader.textContent = '输出价格 ($/1M tokens)';
                    break;
            }
        }
        
        // 更新额外费率表头，标注相对于输入价格
        if (extraHeader) {
            extraHeader.textContent = '额外费率 (相对输入价格)';
        }
    }
    
    formatPrice(price) {
        return this.convertPrice(price, this.priceMode);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Highlight matching parts in text based on search query
     * @param {string} text - Original text
     * @param {string} query - Search query
     * @returns {string} - HTML with highlighted matches
     */
    highlightMatches(text, query) {
        if (!query || !text) {
            return this.escapeHtml(text);
        }
        
        const escapedText = this.escapeHtml(text);
        const queryWords = this.extractWords(query);
        
        let result = escapedText;
        
        // Highlight direct substring matches first (highest priority)
        if (text.toLowerCase().includes(query.toLowerCase())) {
            const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
            result = result.replace(regex, '<mark class="search-highlight">$1</mark>');
            return result;
        }
        
        // Highlight individual word matches
        queryWords.forEach(queryWord => {
            if (queryWord.length >= 2) { // Only highlight words with 2+ characters
                const regex = new RegExp(`\\b(${this.escapeRegex(queryWord)})`, 'gi');
                result = result.replace(regex, '<mark class="search-highlight">$1</mark>');
            }
        });
        
        return result;
    }
    
    /**
     * Escape special regex characters
     * @param {string} string - String to escape
     * @returns {string} - Escaped string
     */
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
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