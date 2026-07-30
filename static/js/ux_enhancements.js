/**
 * Sistema de UX Enhancements para CGI
 * Gerencia notificações, feedback visual e interações
 */

class UXManager {
    constructor() {
        this.toasts = [];
        this.loadingOverlay = null;
        this.init();
    }

    init() {
        this.createToastContainer();
        this.createLoadingOverlay();
        this.createScrollToTop();
        this.initProgressIndicators();
        this.initCopyButtons();
        this.initDragAndDrop();
        this.initSearchSuggestions();
        this.initCollapsibles();
        this.bindEvents();
        
        // Converte todas as flash messages existentes em toasts
        this.convertFlashMessages();
    }

    // ===== SISTEMA DE TOAST NOTIFICATIONS =====

    createToastContainer() {
        if (!document.querySelector('.toast-container')) {
            const container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
    }

    showToast(message, type = 'info', title = null, duration = 5000) {
        const toastId = Date.now();
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('data-toast-id', toastId);

        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        const titles = {
            success: title || 'Sucesso!',
            error: title || 'Erro!',
            warning: title || 'Atenção!',
            info: title || 'Informação'
        };

        toast.innerHTML = `
            <div class="toast-header">
                <span class="toast-icon">${icons[type]}</span>
                <h6 class="toast-title">${titles[type]}</h6>
                <button type="button" class="toast-close" onclick="ux.hideToast(${toastId})">&times;</button>
            </div>
            <div class="toast-body">${message}</div>
        `;

        const container = document.querySelector('.toast-container');
        container.appendChild(toast);

        // Animação de entrada
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.hideToast(toastId);
            }, duration);
        }

        this.toasts.push({ id: toastId, element: toast });
        return toastId;
    }

    hideToast(toastId) {
        const toastIndex = this.toasts.findIndex(t => t.id === toastId);
        if (toastIndex === -1) return;

        const toast = this.toasts[toastIndex].element;
        toast.classList.add('hide');

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);

        this.toasts.splice(toastIndex, 1);
    }

    // ===== LOADING OVERLAY =====

    createLoadingOverlay() {
        if (!document.querySelector('.loading-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div>
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Carregando...</div>
                </div>
            `;
            document.body.appendChild(overlay);
            this.loadingOverlay = overlay;
        }
    }

    showLoading(message = 'Carregando...') {
        const textElement = this.loadingOverlay.querySelector('.loading-text');
        textElement.textContent = message;
        this.loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }

    // ===== BOTÕES COM FEEDBACK =====

    setupButtonFeedback(button, action) {
        const originalText = button.textContent;
        
        button.addEventListener('click', async (e) => {
            if (button.disabled) return;
            
            button.disabled = true;
            button.classList.add('loading');
            
            try {
                const result = await action(e);
                
                button.classList.remove('loading');
                button.classList.add('success');
                
                setTimeout(() => {
                    button.classList.remove('success');
                    button.disabled = false;
                    button.textContent = originalText;
                }, 1500);
                
                return result;
            } catch (error) {
                button.classList.remove('loading');
                button.classList.add('shake');
                button.disabled = false;
                button.textContent = originalText;
                
                setTimeout(() => {
                    button.classList.remove('shake');
                }, 500);
                
                throw error;
            }
        });
    }

    // ===== PROGRESS INDICATORS =====

    initProgressIndicators() {
        // Auto-setup para progress bars existentes
        document.querySelectorAll('.progress-bar').forEach(bar => {
            const fill = bar.querySelector('.progress-fill');
            if (fill && fill.dataset.progress) {
                this.updateProgress(bar, parseInt(fill.dataset.progress));
            }
        });
    }

    updateProgress(progressBar, percentage) {
        const fill = progressBar.querySelector('.progress-fill');
        fill.style.width = `${Math.min(Math.max(percentage, 0), 100)}%`;
    }

    animateProgress(progressBar, fromPercent, toPercent, duration = 1000) {
        const fill = progressBar.querySelector('.progress-fill');
        const startTime = Date.now();
        const difference = toPercent - fromPercent;

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const currentPercent = fromPercent + (difference * progress);
            
            fill.style.width = `${currentPercent}%`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    // ===== SCROLL TO TOP =====

    createScrollToTop() {
        if (!document.querySelector('.scroll-to-top')) {
            const button = document.createElement('button');
            button.className = 'scroll-to-top';
            button.innerHTML = '↑';
            button.title = 'Voltar ao topo';
            
            button.addEventListener('click', () => {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });

            document.body.appendChild(button);

            // Show/hide baseado no scroll
            window.addEventListener('scroll', () => {
                if (window.scrollY > 300) {
                    button.classList.add('show');
                } else {
                    button.classList.remove('show');
                }
            });
        }
    }

    // ===== COPY TO CLIPBOARD =====

    initCopyButtons() {
        document.querySelectorAll('[data-copy]').forEach(button => {
            button.classList.add('copy-button');
            button.addEventListener('click', () => {
                const textToCopy = button.dataset.copy;
                this.copyToClipboard(textToCopy, button);
            });
        });
    }

    async copyToClipboard(text, feedbackElement = null) {
        try {
            await navigator.clipboard.writeText(text);
            
            if (feedbackElement) {
                feedbackElement.classList.add('copied');
                setTimeout(() => {
                    feedbackElement.classList.remove('copied');
                }, 2000);
            }
            
            this.showToast('Texto copiado para a área de transferência!', 'success', null, 2000);
            return true;
        } catch (err) {
            // Fallback para navegadores mais antigos
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            
            try {
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showToast('Texto copiado!', 'success', null, 2000);
                return true;
            } catch (fallbackErr) {
                document.body.removeChild(textArea);
                this.showToast('Não foi possível copiar o texto', 'error');
                return false;
            }
        }
    }

    // ===== DRAG AND DROP =====

    initDragAndDrop() {
        document.querySelectorAll('.drop-zone').forEach(zone => {
            this.setupDropZone(zone);
        });
    }

    setupDropZone(zone) {
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', (e) => {
            if (!zone.contains(e.relatedTarget)) {
                zone.classList.remove('dragover');
            }
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            
            const files = Array.from(e.dataTransfer.files);
            const allowedTypes = zone.dataset.allowedTypes?.split(',') || [];
            
            if (allowedTypes.length > 0) {
                const validFiles = files.filter(file => 
                    allowedTypes.some(type => file.type.includes(type))
                );
                
                if (validFiles.length !== files.length) {
                    this.showToast('Alguns arquivos foram ignorados (tipo não suportado)', 'warning');
                }
                
                if (validFiles.length > 0) {
                    this.handleDroppedFiles(validFiles, zone);
                }
            } else {
                this.handleDroppedFiles(files, zone);
            }
        });
    }

    handleDroppedFiles(files, zone) {
        // Override this method or use data attributes para definir comportamento
        if (zone.dataset.onDrop) {
            const handlerName = zone.dataset.onDrop;
            if (window[handlerName] && typeof window[handlerName] === 'function') {
                window[handlerName](files, zone);
            }
        }
    }

    // ===== SEARCH SUGGESTIONS =====

    initSearchSuggestions() {
        document.querySelectorAll('[data-suggestions]').forEach(input => {
            this.setupSearchSuggestions(input);
        });
    }

    setupSearchSuggestions(input) {
        const container = input.parentNode;
        container.style.position = 'relative';

        const suggestionsList = document.createElement('div');
        suggestionsList.className = 'search-suggestions';
        container.appendChild(suggestionsList);

        let currentSuggestions = [];
        let selectedIndex = -1;

        input.addEventListener('input', async (e) => {
            const query = e.target.value.trim();
            
            if (query.length >= 2) {
                try {
                    const suggestions = await this.fetchSuggestions(query, input.dataset.suggestions);
                    this.showSuggestions(suggestions, suggestionsList, input);
                    currentSuggestions = suggestions;
                    selectedIndex = -1;
                } catch (error) {
                    console.error('Erro ao buscar sugestões:', error);
                }
            } else {
                suggestionsList.classList.remove('show');
            }
        });

        input.addEventListener('keydown', (e) => {
            if (!suggestionsList.classList.contains('show')) return;

            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    selectedIndex = Math.min(selectedIndex + 1, currentSuggestions.length - 1);
                    this.highlightSuggestion(suggestionsList, selectedIndex);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    selectedIndex = Math.max(selectedIndex - 1, -1);
                    this.highlightSuggestion(suggestionsList, selectedIndex);
                    break;
                case 'Enter':
                    if (selectedIndex >= 0) {
                        e.preventDefault();
                        input.value = currentSuggestions[selectedIndex];
                        suggestionsList.classList.remove('show');
                    }
                    break;
                case 'Escape':
                    suggestionsList.classList.remove('show');
                    break;
            }
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                suggestionsList.classList.remove('show');
            }
        });
    }

    async fetchSuggestions(query, endpoint) {
        const response = await fetch(`${endpoint}?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        return data.suggestions || [];
    }

    showSuggestions(suggestions, container, input) {
        container.innerHTML = '';
        
        suggestions.forEach((suggestion, index) => {
            const item = document.createElement('div');
            item.className = 'search-suggestion-item';
            item.textContent = suggestion;
            
            item.addEventListener('click', () => {
                input.value = suggestion;
                container.classList.remove('show');
            });
            
            container.appendChild(item);
        });

        container.classList.add('show');
    }

    highlightSuggestion(container, index) {
        container.querySelectorAll('.search-suggestion-item').forEach((item, i) => {
            item.classList.toggle('highlighted', i === index);
        });
    }

    // ===== COLLAPSIBLES =====

    initCollapsibles() {
        document.querySelectorAll('.collapsible').forEach(button => {
            button.addEventListener('click', () => {
                button.classList.toggle('active');
                const content = button.nextElementSibling;
                
                if (content && content.classList.contains('collapsible-content')) {
                    content.classList.toggle('active');
                }
            });
        });
    }

    // ===== UTILITY METHODS =====

    highlightElement(element, duration = 2000) {
        element.classList.add('highlight-new');
        setTimeout(() => {
            element.classList.remove('highlight-new');
        }, duration);
    }

    shakeElement(element) {
        element.classList.add('shake');
        setTimeout(() => {
            element.classList.remove('shake');
        }, 500);
    }

    pulseElement(element) {
        element.classList.add('pulse');
    }

    stopPulse(element) {
        element.classList.remove('pulse');
    }

    // Confetti effect para celebrar ações importantes
    createConfetti() {
        const colors = ['#ff6600', '#ff8533', '#ffaa66', '#ffc199', '#ffe5cc'];
        const confettiCount = 50;
        
        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = Math.random() * 3 + 's';
            confetti.style.animationDuration = (Math.random() * 2 + 1) + 's';
            
            document.body.appendChild(confetti);
            
            setTimeout(() => {
                if (confetti.parentNode) {
                    confetti.parentNode.removeChild(confetti);
                }
            }, 4000);
        }
    }

    // ===== CONVERSÃO DE FLASH MESSAGES =====

    convertFlashMessages() {
        const flashMessages = document.querySelectorAll('.alert, .flash-message');
        
        flashMessages.forEach(flash => {
            const text = flash.textContent.trim();
            let type = 'info';
            
            if (flash.classList.contains('alert-success') || flash.classList.contains('success')) {
                type = 'success';
            } else if (flash.classList.contains('alert-danger') || flash.classList.contains('error')) {
                type = 'error';
            } else if (flash.classList.contains('alert-warning') || flash.classList.contains('warning')) {
                type = 'warning';
            }
            
            if (text) {
                this.showToast(text, type);
            }
            
            // Remove flash message original
            flash.style.display = 'none';
        });
    }

    // ===== EVENT BINDING =====

    bindEvents() {
        // Auto-setup para tooltips
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            if (!element.classList.contains('tooltip')) {
                element.classList.add('tooltip');
            }
        });

        // Auto-setup para botões com feedback
        document.querySelectorAll('[data-async-action]').forEach(button => {
            this.setupButtonFeedback(button, async () => {
                const action = button.dataset.asyncAction;
                if (window[action] && typeof window[action] === 'function') {
                    return await window[action](button);
                }
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+K para focar na busca
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('input[type="search"], input[name="termo"]');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
            
            // Esc para fechar modais/overlays
            if (e.key === 'Escape') {
                this.hideLoading();
                document.querySelectorAll('.modal.show').forEach(modal => {
                    modal.classList.remove('show');
                });
            }
        });
    }

    // ===== API PÚBLICAS =====

    success(message, title = null, duration = 5000) {
        return this.showToast(message, 'success', title, duration);
    }

    error(message, title = null, duration = 7000) {
        return this.showToast(message, 'error', title, duration);
    }

    warning(message, title = null, duration = 6000) {
        return this.showToast(message, 'warning', title, duration);
    }

    info(message, title = null, duration = 5000) {
        return this.showToast(message, 'info', title, duration);
    }

    // Feedback rápido para operações AJAX
    async performAction(action, loadingMessage = 'Processando...') {
        this.showLoading(loadingMessage);
        
        try {
            const result = await action();
            this.hideLoading();
            return result;
        } catch (error) {
            this.hideLoading();
            this.error('Erro ao executar operação: ' + error.message);
            throw error;
        }
    }
}

// Instância global
const ux = new UXManager();

// Auto-inicialização quando DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // UXManager já foi inicializado no constructor
        console.log('UX Enhancements carregado');
    });
} else {
    console.log('UX Enhancements carregado (DOM já pronto)');
}

// Export para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UXManager;
}