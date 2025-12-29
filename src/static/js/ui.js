// ==================== MÓDULO DE UI ====================
// Gerencia a interface do usuário e navegação
//
// ⚠️  PADRÃO DO SISTEMA - MODAIS:
// - Todos os modais devem fechar APENAS pelo botão X
// - NUNCA implementar fechamento ao clicar fora do modal
// - Use UI.setupModalClose(modalId) para configurar corretamente
// - O sistema configura automaticamente todos os modais na inicialização

const UI = {
    // Estado atual da aplicação
    currentSection: 'dashboard',
    
    // ==================== NAVEGAÇÃO ====================
    
    /**
     * Inicializa os event listeners de navegação
     */
    init() {
        // Navegação principal
        document.getElementById('nav-dashboard')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showSection('dashboard');
        });
        
        document.getElementById('nav-empresas')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showSection('empresas');
        });
        
        document.getElementById('nav-cotacoes')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showSection('cotacoes');
        });
        
        document.getElementById('nav-analytics')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showSection('analytics');
        });
        
        document.getElementById('nav-cadastro')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showSection('cadastro');
        });
        
        // Botões de ação rápida
        document.getElementById('btn-cadastrar-nova')?.addEventListener('click', () => {
            this.showSection('cadastro');
        });
        
        document.getElementById('btn-buscar-empresas')?.addEventListener('click', () => {
            this.showSection('empresas');
        });
        
        document.getElementById('btn-solicitar-cotacao')?.addEventListener('click', (e) => {
            e.preventDefault();
            // Abrir modal de cotação diretamente
            if (typeof window.abrirModalCotacao === 'function') {
                window.abrirModalCotacao();
            } else if (typeof abrirModalCotacao === 'function') {
                abrirModalCotacao();
            } else {
                console.warn('Função abrirModalCotacao não encontrada ainda. Aguardando carregamento...');
                // Tentar novamente após um delay
                setTimeout(() => {
                    if (typeof window.abrirModalCotacao === 'function') {
                        window.abrirModalCotacao();
                    } else {
                        console.error('Função abrirModalCotacao ainda não disponível após delay');
                    }
                }, 500);
            }
        });
        
        // Logout
        document.getElementById('btn-logout')?.addEventListener('click', async () => {
            if (Utils.confirm('Deseja realmente sair do sistema?')) {
                try {
                    await API.logout();
                    window.location.href = '/login.html';
                } catch (error) {
                    console.error('Erro ao fazer logout:', error);
                    window.location.href = '/login.html';
                }
            }
        });

        // Configurar comportamento padrão de todos os modais
        setTimeout(() => {
            this.setupAllModals();
        }, 1000); // Aguardar carregamento completo
    },
    
    /**
     * Mostra uma seção específica
     * @param {string} section - Nome da seção
     */
    showSection(section) {
        // Ocultar todas as seções
        const sections = ['dashboard', 'empresas', 'cadastro', 'cotacoes', 'analytics'];
        sections.forEach(s => {
            const element = document.getElementById(s);
            if (element) {
                Utils.hide(element);
            }
        });
        
        // Ocultar seções especiais
        const secaoCotacoes = document.getElementById('secao-cotacoes');
        const secaoAnalytics = document.getElementById('secao-analytics-v133');
        if (secaoCotacoes) Utils.hide(secaoCotacoes);
        if (secaoAnalytics) Utils.hide(secaoAnalytics);
        // Mostrar seção selecionada
        this.currentSection = section;
        
        switch(section) {
            case 'dashboard':
                Utils.show('dashboard');
                if (Dashboard && typeof Dashboard.loadData === 'function') {
                    // Aguardar um pouco para garantir que a seção esteja visível
                    setTimeout(() => {
                        Dashboard.loadData();
                    }, 100);
                }
                break;
            case 'empresas':
                Utils.show('empresas');
                Empresas.load();
                break;
            case 'cadastro':
                Utils.show('cadastro');
                Empresas.resetForm();
                break;
            case 'cotacoes':
                if (secaoCotacoes) {
                    Utils.show(secaoCotacoes);
                    if (Cotacoes && typeof Cotacoes.render === 'function') {
                        Cotacoes.render();
                    }
                }
                break;
            case 'analytics':
                if (secaoAnalytics) {
                    Utils.show(secaoAnalytics);
                    Analytics.load();
                }
                break;
        }
        
        // Controlar visibilidade do rodapé
        this.updateFooterVisibility(section);
    },
    
    /**
     * Atualiza visibilidade do rodapé
     * @param {string} section - Seção atual
     */
    updateFooterVisibility(section) {
        const footers = document.querySelectorAll('footer');
        footers.forEach(footer => {
            if (section === 'analytics') {
                Utils.hide(footer);
            } else {
                Utils.show(footer);
            }
        });
    },
    
    // ==================== MODAIS ====================
    
    /**
     * Mostra modal
     * @param {string} modalId - ID do modal
     */
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
        }
    },
    
    /**
     * Oculta modal
     * @param {string} modalId - ID do modal
     */
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
        }
    },
    
    /**
     * Configura modal para fechar APENAS pelo botão X
     * @param {string} modalId - ID do modal
     * PADRÃO DO SISTEMA: Modal só deve fechar pelo botão X
     */
    setupModalClose(modalId) {
        // PADRÃO DO SISTEMA: Modal só fecha pelo botão X
        const modal = document.getElementById(modalId);
        if (modal) {
            // Remover qualquer event listener existente que feche ao clicar fora
            modal.removeEventListener('click', this._closeOnOutsideClick);
            console.log(`✅ Modal ${modalId} configurado para fechar APENAS pelo botão X`);
        }
    },

    /**
     * Função auxiliar para remover event listeners de clique fora
     * @private
     */
    _closeOnOutsideClick(e) {
        // Esta função não deve ser usada - mantida apenas para remoção
        if (e.target === e.currentTarget) {
            // Não fazer nada - modal não deve fechar
        }
    },

    /**
     * Configura todos os modais do sistema para o comportamento padrão
     */
    setupAllModals() {
        // Buscar todos os elementos com classe modal
        const modals = document.querySelectorAll('.modal, [id*="modal"]');
        modals.forEach(modal => {
            if (modal.id) {
                this.setupModalClose(modal.id);
            }
        });
        console.log(`✅ ${modals.length} modais configurados com comportamento padrão`);
    },
    
    // ==================== LOADING ====================
    
    /**
     * Mostra indicador de loading
     * @param {HTMLElement|string} element - Elemento ou ID
     */
    showLoading(element) {
        const el = typeof element === 'string' ? document.getElementById(element) : element;
        if (el) {
            const loading = Utils.createElement('div', { className: 'loading' });
            el.appendChild(loading);
        }
    },
    
    /**
     * Remove indicador de loading
     * @param {HTMLElement|string} element - Elemento ou ID
     */
    hideLoading(element) {
        const el = typeof element === 'string' ? document.getElementById(element) : element;
        if (el) {
            const loading = el.querySelector('.loading');
            if (loading) {
                loading.remove();
            }
        }
    },
    
    // ==================== FORMULÁRIOS ====================
    
    /**
     * Obtém dados de um formulário
     * @param {HTMLFormElement|string} form - Formulário ou ID
     * @returns {object} - Dados do formulário
     */
    getFormData(form) {
        const formElement = typeof form === 'string' ? document.getElementById(form) : form;
        const formData = new FormData(formElement);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            // Converter valores numéricos formatados
            const input = formElement.querySelector(`[name="${key}"]`);
            if (input && input.dataset.valorNumerico) {
                data[key] = parseFloat(input.dataset.valorNumerico);
            } else if (input && input.type === 'number') {
                data[key] = Utils.parseFormattedNumber(value);
            } else {
                data[key] = value;
            }
        }
        
        return data;
    },
    
    /**
     * Preenche formulário com dados
     * @param {HTMLFormElement|string} form - Formulário ou ID
     * @param {object} data - Dados para preencher
     */
    setFormData(form, data) {
        const formElement = typeof form === 'string' ? document.getElementById(form) : form;
        
        Object.keys(data).forEach(key => {
            const input = formElement.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = data[key];
                } else if (input.type === 'radio') {
                    const radio = formElement.querySelector(`[name="${key}"][value="${data[key]}"]`);
                    if (radio) radio.checked = true;
                } else {
                    input.value = data[key] || '';
                }
            }
        });
    },
    
    /**
     * Limpa formulário
     * @param {HTMLFormElement|string} form - Formulário ou ID
     */
    clearForm(form) {
        const formElement = typeof form === 'string' ? document.getElementById(form) : form;
        if (formElement) {
            formElement.reset();
            // Limpar erros de validação
            const errors = formElement.querySelectorAll('.text-red-500');
            errors.forEach(error => error.classList.add('hidden'));
        }
    },
    
    /**
     * Mostra erro de validação em campo
     * @param {string} fieldName - Nome do campo
     * @param {string} message - Mensagem de erro
     */
    showFieldError(fieldName, message) {
        const errorElement = document.getElementById(`${fieldName}_error`);
        if (errorElement) {
            Utils.setTextContent(errorElement, message);
            errorElement.classList.remove('hidden');
        }
    },
    
    /**
     * Oculta erro de validação em campo
     * @param {string} fieldName - Nome do campo
     */
    hideFieldError(fieldName) {
        const errorElement = document.getElementById(`${fieldName}_error`);
        if (errorElement) {
            errorElement.classList.add('hidden');
        }
    },
    
    // ==================== PAGINAÇÃO ====================
    
    /**
     * Atualiza informações de paginação
     * @param {object} paginationInfo - Informações de paginação
     */
    updatePagination(paginationInfo) {
        const { currentPage, totalPages, totalResults, itemsPerPage } = paginationInfo;
        
        const from = (currentPage - 1) * itemsPerPage + 1;
        const to = Math.min(currentPage * itemsPerPage, totalResults);
        
        Utils.setTextContent(document.getElementById('showing-from'), from);
        Utils.setTextContent(document.getElementById('showing-to'), to);
        Utils.setTextContent(document.getElementById('total-results'), totalResults);
        
        // Atualizar botões
        const btnPrev = document.getElementById('btn-prev');
        const btnNext = document.getElementById('btn-next');
        
        if (btnPrev) {
            btnPrev.disabled = currentPage === 1;
        }
        
        if (btnNext) {
            btnNext.disabled = currentPage === totalPages || totalPages === 0;
        }
    }
};

// Exportar para uso global
window.UI = UI;
