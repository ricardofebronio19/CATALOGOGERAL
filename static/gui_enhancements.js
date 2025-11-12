// Melhorias JavaScript para a versão desktop (pywebview)

(function() {
    'use strict';
    
    // Verifica se está rodando na versão desktop
    const isDesktopApp = window.pywebview !== undefined;
    
    if (!isDesktopApp) {
        console.log('Versão browser detectada - enhancements desativados');
        return;
    }
    
    console.log('🖥️ Versão Desktop - Enhancements ativos');
    
    // 1. Adiciona indicador de status de conexão
    function createConnectionIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'connection-status';
        indicator.title = 'Conectado ao servidor local';
        document.body.appendChild(indicator);
        
        // Verifica conexão periodicamente
        setInterval(() => {
            fetch('/api/health-check', { method: 'HEAD' })
                .then(() => {
                    indicator.classList.remove('offline');
                    indicator.title = 'Conectado ao servidor local';
                })
                .catch(() => {
                    indicator.classList.add('offline');
                    indicator.title = 'Servidor offline';
                });
        }, 5000);
    }
    
    // 2. Atalhos de teclado customizados
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+R ou F5 - Recarregar
            if ((e.ctrlKey && e.key === 'r') || e.key === 'F5') {
                e.preventDefault();
                window.location.reload();
            }
            
            // Ctrl+Q - Fechar aplicação (se API disponível)
            if (e.ctrlKey && e.key === 'q') {
                e.preventDefault();
                if (window.pywebview && window.pywebview.api) {
                    window.close();
                }
            }
            
            // F11 - Tela cheia
            if (e.key === 'F11') {
                e.preventDefault();
                if (window.pywebview && window.pywebview.api) {
                    window.pywebview.api.maximize_window();
                }
            }
            
            // Ctrl+0 - Reset zoom
            if (e.ctrlKey && e.key === '0') {
                e.preventDefault();
                document.body.style.zoom = '100%';
            }
            
            // Ctrl+Plus - Zoom in
            if (e.ctrlKey && (e.key === '+' || e.key === '=')) {
                e.preventDefault();
                const currentZoom = parseFloat(document.body.style.zoom || '100');
                document.body.style.zoom = Math.min(currentZoom + 10, 200) + '%';
            }
            
            // Ctrl+Minus - Zoom out
            if (e.ctrlKey && e.key === '-') {
                e.preventDefault();
                const currentZoom = parseFloat(document.body.style.zoom || '100');
                document.body.style.zoom = Math.max(currentZoom - 10, 50) + '%';
            }
        });
    }
    
    // 3. Indicador de carregamento global
    function createLoadingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'loading-indicator';
        document.body.appendChild(indicator);
        
        // Mostra indicador durante navegação
        let isLoading = false;
        
        // Monitora fetch requests
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            if (!isLoading) {
                indicator.style.opacity = '1';
                isLoading = true;
            }
            
            return originalFetch.apply(this, args)
                .finally(() => {
                    setTimeout(() => {
                        indicator.style.opacity = '0';
                        isLoading = false;
                    }, 500);
                });
        };
        
        // Monitora XMLHttpRequest
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(...args) {
            this.addEventListener('loadstart', () => {
                indicator.style.opacity = '1';
                isLoading = true;
            });
            this.addEventListener('loadend', () => {
                setTimeout(() => {
                    indicator.style.opacity = '0';
                    isLoading = false;
                }, 500);
            });
            return originalOpen.apply(this, args);
        };
    }
    
    // 4. Previne comportamentos de navegador
    function preventBrowserBehaviors() {
        // Previne arrastar e soltar arquivos na janela (exceto em inputs)
        document.addEventListener('dragover', (e) => {
            if (e.target.tagName !== 'INPUT') {
                e.preventDefault();
            }
        });
        
        document.addEventListener('drop', (e) => {
            if (e.target.tagName !== 'INPUT') {
                e.preventDefault();
            }
        });
        
        // Previne context menu (botão direito) em produção
        // Descomente se quiser desabilitar:
        // document.addEventListener('contextmenu', e => e.preventDefault());
        
        // Previne seleção acidental com duplo clique
        document.addEventListener('selectstart', (e) => {
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') {
                e.preventDefault();
            }
        });
    }
    
    // 5. Smooth scroll global
    function enableSmoothScroll() {
        document.documentElement.style.scrollBehavior = 'smooth';
    }
    
    // 6. Detecta e mostra versão da aplicação
    function showAppVersion() {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_version) {
            window.pywebview.api.get_version().then(version => {
                console.log(`📦 Catálogo de Peças v${version}`);
                
                // Adiciona versão no título se não estiver
                if (!document.title.includes(version)) {
                    document.title = `${document.title} v${version}`;
                }
            });
        }
    }
    
    // 7. Transições suaves ao navegar
    function setupPageTransitions() {
        // Adiciona classe ao carregar
        document.body.classList.add('fade-enter');
        setTimeout(() => {
            document.body.classList.add('fade-enter-active');
        }, 10);
    }
    
    // 8. Toast notifications nativas (opcional)
    window.showToast = function(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        const styles = {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '15px 25px',
            borderRadius: '8px',
            background: type === 'success' ? '#4caf50' : 
                       type === 'error' ? '#f44336' : 
                       type === 'warning' ? '#ff9800' : '#2196f3',
            color: 'white',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: 10000,
            animation: 'slideInRight 0.3s ease-out',
            fontFamily: 'Segoe UI, sans-serif',
            fontSize: '14px'
        };
        
        Object.assign(toast.style, styles);
        document.body.appendChild(toast);
        
        // Animação de entrada
        const keyframes = `
            @keyframes slideInRight {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(400px); opacity: 0; }
            }
        `;
        
        if (!document.getElementById('toast-animations')) {
            const style = document.createElement('style');
            style.id = 'toast-animations';
            style.textContent = keyframes;
            document.head.appendChild(style);
        }
        
        // Remove após duração
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    };
    
    // Inicializa tudo quando DOM estiver pronto
    function init() {
        createConnectionIndicator();
        setupKeyboardShortcuts();
        createLoadingIndicator();
        preventBrowserBehaviors();
        enableSmoothScroll();
        showAppVersion();
        setupPageTransitions();
        
        console.log('✅ Desktop enhancements carregados com sucesso');
        
        // Notifica que está pronto (opcional)
        if (window.pywebview) {
            // showToast('Aplicação carregada!', 'success', 2000);
        }
    }
    
    // Executa quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
