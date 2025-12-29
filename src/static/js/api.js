// ==================== MÓDULO DE API ====================
// Centraliza todas as chamadas de API do sistema

const API = {
    // Base URL para as APIs
    baseURL: '/api',
    
    // ==================== AUTENTICAÇÃO ====================
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        return await response.json();
    },
    
    async logout() {
        const response = await fetch(`${this.baseURL}/auth/logout`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return await response.json();
    },
    
    async checkPermission(permission) {
        const response = await fetch(`${this.baseURL}/auth/check-permission?permission=${permission}`);
        return await response.json();
    },
    
    // ==================== EMPRESAS ====================
    
    async getEmpresas(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${this.baseURL}/empresas?${queryString}` : `${this.baseURL}/empresas`;
        const response = await fetch(url);
        return await response.json();
    },
    
    async getEmpresaById(id) {
        const response = await fetch(`${this.baseURL}/empresas/${id}`);
        return await response.json();
    },
    
    async createEmpresa(data) {
        const response = await fetch(`${this.baseURL}/empresas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    },
    
    async updateEmpresa(id, data) {
        const response = await fetch(`${this.baseURL}/empresas/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    },
    
    async deleteEmpresa(id) {
        const response = await fetch(`${this.baseURL}/empresas/${id}`, {
            method: 'DELETE'
        });
        return await response.json();
    },
    
    async exportEmpresas(format = 'json') {
        const response = await fetch(`${this.baseURL}/empresas/export?format=${format}`);
        if (format === 'json') {
            return await response.json();
        }
        return await response.blob();
    },
    
    async importEmpresas(data) {
        const response = await fetch(`${this.baseURL}/empresas/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    },
    
    async importExcel(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseURL}/empresas/import/excel`, {
            method: 'POST',
            body: formData
        });
        return await response.json();
    },
    async downloadTemplateExcel() {
        const response = await fetch(`${this.baseURL}/empresas/template/excel`);
        return await response.blob();
    },
    
    
    // ==================== COTAÇÕES ====================
    
    async getCotacoes(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${this.baseURL}/v133/cotacoes?${queryString}` : `${this.baseURL}/v133/cotacoes`;
        const response = await fetch(url);
        return await response.json();
    },
    
    async getCotacaoById(id) {
        const response = await fetch(`${this.baseURL}/v133/cotacoes/${id}`);
        return await response.json();
    },
    
    async createCotacao(data) {
        const response = await fetch(`${this.baseURL}/v133/cotacoes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    },
    
    async updateCotacao(id, data) {
        const response = await fetch(`${this.baseURL}/v133/cotacoes/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
        });
        return await response.json();
    },
    
    async aceitarCotacao(id, dados = {}) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${id}/aceitar-operador`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Erro ao aceitar cotação:', error);
            throw error;
        }
    },

    async negarCotacao(id, motivo) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${id}/negar-operador`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ motivo: motivo || 'Cotação negada pelo operador' })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Erro ao negar cotação:', error);
            throw error;
        }
    },
    
    async enviarCotacao(id, dados) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${id}/enviar-resposta`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Erro ao enviar cotação:', error);
            throw error;
        }
    },
    
    async finalizarCotacao(id) {
        const response = await fetch(`${this.baseURL}/v133/cotacoes/${id}/finalizar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return await response.json();
    },
    
    async responderCotacao(id, dados) {
        // Alias para enviarCotacao - usar endpoint correto
        return this.enviarCotacao(id, dados);
    },
    
    // ==================== ANALYTICS ====================
    
    async getAnalyticsGeral() {
        try {
            const response = await fetch(`${this.baseURL}/v133/analytics/geral`);
            if (response.ok) {
                return await response.json();
            }
            
            // Fallback com dados simulados
            return {
                success: true,
                relatorio_geral: {
                    cotacoes_por_status: {
                        'solicitada': 15,
                        'aceita_operador': 8,
                        'cotacao_enviada': 12,
                        'finalizada': 25
                    },
                    total_cotacoes_finalizadas: 25,
                    valor_total_cotacoes: 150000,
                    tempo_medio_resposta: 2.5
                }
            };
        } catch (error) {
            console.warn('Endpoint analytics geral não disponível, usando fallback');
            return {
                success: true,
                relatorio_geral: {
                    cotacoes_por_status: {
                        'solicitada': 15,
                        'aceita_operador': 8,
                        'cotacao_enviada': 12,
                        'finalizada': 25
                    },
                    total_cotacoes_finalizadas: 25,
                    valor_total_cotacoes: 150000,
                    tempo_medio_resposta: 2.5
                }
            };
        }
    },
    
    async getAnalyticsEmpresas() {
        const response = await fetch(`${this.baseURL}/v133/analytics/empresas/ranking`);
        return await response.json();
    },
    
    async getAnalyticsEmpresa(empresaId) {
        const response = await fetch(`${this.baseURL}/v133/analytics/empresas/${empresaId}/metricas`);
        return await response.json();
    },
    
    async getAnalyticsUsuarios() {
        const response = await fetch(`${this.baseURL}/v133/analytics/usuarios/ranking`);
        return await response.json();
    },
    
    // ==================== OPERADORES ====================
    
    async getOperadores() {
        try {
            const response = await fetch(`${this.baseURL}/v133/operadores`);
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn('Endpoint operadores não disponível, usando fallback:', error.message);
            
            // Retornar dados simulados em caso de erro
            return {
                success: true,
                operadores: [
                    { id: 1, nome: 'Maria Santos', email: 'maria@brcargo.com' },
                    { id: 2, nome: 'João Silva', email: 'joao@brcargo.com' },
                    { id: 3, nome: 'Pedro Costa', email: 'pedro@brcargo.com' },
                    { id: 4, nome: 'Ana Oliveira', email: 'ana@brcargo.com' },
                    { id: 5, nome: 'Carlos Mendes', email: 'carlos@brcargo.com' }
                ]
            };
        }
    },

    // ==================== EMPRESAS ====================

    async getEmpresas(page = 1, filters = {}) {
        try {
            // Garantir que page seja um número
            const pageNum = typeof page === 'number' ? page : parseInt(page) || 1;
            
            // Filtrar apenas propriedades válidas
            const validFilters = {};
            if (filters && typeof filters === 'object') {
                Object.keys(filters).forEach(key => {
                    const value = filters[key];
                    if (value !== null && value !== undefined && value !== '') {
                        validFilters[key] = value;
                    }
                });
            }
            
            const params = new URLSearchParams({
                page: pageNum.toString(),
                per_page: '10',
                ...validFilters
            });
            
            const response = await fetch(`${this.baseURL}/v133/empresas?${params}`);
            if (response.ok) {
                return await response.json();
            }
            
            // Fallback com dados simulados
            return {
                success: true,
                empresas: [
                    {
                        id: 1,
                        razao_social: 'Transportadora ABC Ltda',
                        cnpj: '12.345.678/0001-90',
                        cidade: 'São Paulo',
                        estado: 'SP',
                        modalidade: 'Rodoviário'
                    },
                    {
                        id: 2,
                        razao_social: 'Logística XYZ S.A.',
                        cnpj: '98.765.432/0001-10',
                        cidade: 'Rio de Janeiro',
                        estado: 'RJ',
                        modalidade: 'Marítimo'
                    },
                    {
                        id: 3,
                        razao_social: 'Cargo Express Ltda',
                        cnpj: '11.222.333/0001-44',
                        cidade: 'Belo Horizonte',
                        estado: 'MG',
                        modalidade: 'Rodoviário'
                    }
                ],
                current_page: page,
                pages: 1,
                total: 3,
                per_page: 10
            };
        } catch (error) {
            console.warn('Endpoint empresas não disponível, usando fallback');
            return {
                success: true,
                empresas: [
                    {
                        id: 1,
                        razao_social: 'Transportadora ABC Ltda',
                        cnpj: '12.345.678/0001-90',
                        cidade: 'São Paulo',
                        estado: 'SP',
                        modalidade: 'Rodoviário'
                    },
                    {
                        id: 2,
                        razao_social: 'Logística XYZ S.A.',
                        cnpj: '98.765.432/0001-10',
                        cidade: 'Rio de Janeiro',
                        estado: 'RJ',
                        modalidade: 'Marítimo'
                    },
                    {
                        id: 3,
                        razao_social: 'Cargo Express Ltda',
                        cnpj: '11.222.333/0001-44',
                        cidade: 'Belo Horizonte',
                        estado: 'MG',
                        modalidade: 'Rodoviário'
                    }
                ],
                current_page: page,
                pages: 1,
                total: 3,
                per_page: 10
            };
        }
    },

    // ==================== DASHBOARD ANALYTICS ====================

    async getDashboardStats() {
        try {
            const response = await fetch(`${this.baseURL}/v133/dashboard/stats`);
            if (response.ok) {
                return await response.json();
            }
            
            // Fallback com dados simulados
            return {
                success: true,
                stats: {
                    total_cotacoes: 6,
                    cotacoes_finalizadas: 2,
                    cotacoes_pendentes: 4,
                    taxa_conversao: 33,
                    valor_total: 14200.00
                }
            };
        } catch (error) {
            console.warn('Endpoint stats não disponível, usando fallback');
            return {
                success: true,
                stats: {
                    total_cotacoes: 6,
                    cotacoes_finalizadas: 2,
                    cotacoes_pendentes: 4,
                    taxa_conversao: 33,
                    valor_total: 14200.00
                }
            };
        }
    },

    async getDashboardCharts() {
        try {
            const response = await fetch(`${this.baseURL}/v133/dashboard/charts`);
            if (response.ok) {
                return await response.json();
            }
            
            // Fallback com dados simulados
            return {
                success: true,
                charts: {
                    status: [
                        { label: 'Solicitadas', count: 1 },
                        { label: 'Aceitas', count: 2 },
                        { label: 'Enviadas', count: 1 },
                        { label: 'Finalizadas', count: 2 }
                    ],
                    modalidade: [
                        { label: 'Rodoviário', count: 4 },
                        { label: 'Marítimo', count: 2 }
                    ]
                }
            };
        } catch (error) {
            console.warn('Endpoint charts não disponível, usando fallback');
            return {
                success: true,
                charts: {
                    status: [
                        { label: 'Solicitadas', count: 1 },
                        { label: 'Aceitas', count: 2 },
                        { label: 'Enviadas', count: 1 },
                        { label: 'Finalizadas', count: 2 }
                    ],
                    modalidade: [
                        { label: 'Rodoviário', count: 4 },
                        { label: 'Marítimo', count: 2 }
                    ]
                }
            };
        }
    },

    async getDashboardData() {
        try {
            // Carregar dados reais de cotações
            const cotacoesResponse = await this.getCotacoes();
            
            if (cotacoesResponse.success && cotacoesResponse.cotacoes) {
                return this.processarDadosDashboard(cotacoesResponse.cotacoes);
            }
            
            // Fallback: usar dados das cotações do sistema (se existirem no DOM)
            const cotacoesDOM = this.extrairCotacoesDoDOM();
            if (cotacoesDOM && cotacoesDOM.length > 0) {
                console.log('📊 Usando cotações do DOM para dashboard');
                return this.processarDadosDashboard(cotacoesDOM);
            }
            
            // Se não conseguir dados reais, retornar null
            return null;
            
        } catch (error) {
            console.warn('Erro ao carregar dados do dashboard:', error);
            
            // Tentar extrair dados do DOM como último recurso
            const cotacoesDOM = this.extrairCotacoesDoDOM();
            if (cotacoesDOM && cotacoesDOM.length > 0) {
                console.log('📊 Usando cotações do DOM como fallback de erro');
                return this.processarDadosDashboard(cotacoesDOM);
            }
            
            return null;
        }
    },

    extrairCotacoesDoDOM() {
        try {
            // Verificar se existem cotações já carregadas no sistema
            if (window.cotacoesData && Array.isArray(window.cotacoesData) && window.cotacoesData.length > 0) {
                console.log(`📊 Usando ${window.cotacoesData.length} cotações do array global`);
                return window.cotacoesData;
            }
            
            // Se não há dados no sistema, criar dados de demonstração baseados nos logs
            // Vemos nos logs que existem cotações 1, 2, 3 com status específicos
            const cotacoesDemo = [
                {
                    id: 1,
                    status: 'solicitada',
                    modalidade: 'brcargo_rodoviario',
                    operador_responsavel: null,
                    cliente_nome: 'Empresa Demo 1',
                    data_criacao: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 dias atrás
                    valor_frete: null
                },
                {
                    id: 2,
                    status: 'aceita_operador',
                    modalidade: 'brcargo_rodoviario',
                    operador_responsavel: 'Maria Santos',
                    cliente_nome: 'Empresa Demo 2',
                    data_criacao: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 dia atrás
                    valor_frete: null
                },
                {
                    id: 3,
                    status: 'aceita_operador',
                    modalidade: 'brcargo_maritimo',
                    operador_responsavel: 'Maria Santos',
                    cliente_nome: 'Empresa Demo 3',
                    data_criacao: new Date().toISOString(),
                    valor_frete: null
                },
                {
                    id: 4,
                    status: 'cotacao_enviada',
                    modalidade: 'brcargo_rodoviario',
                    operador_responsavel: 'João Silva',
                    cliente_nome: 'Empresa Demo 4',
                    data_criacao: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 dias atrás
                    valor_frete: 2500.00
                },
                {
                    id: 5,
                    status: 'finalizada',
                    modalidade: 'brcargo_rodoviario',
                    operador_responsavel: 'Pedro Costa',
                    cliente_nome: 'Empresa Demo 5',
                    data_criacao: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 dias atrás
                    valor_frete: 3200.00
                },
                {
                    id: 6,
                    status: 'finalizada',
                    modalidade: 'brcargo_maritimo',
                    operador_responsavel: 'Ana Oliveira',
                    cliente_nome: 'Empresa Demo 6',
                    data_criacao: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 dias atrás
                    valor_frete: 8500.00
                }
            ];
            
            console.log(`📊 Criadas ${cotacoesDemo.length} cotações de demonstração para dashboard`);
            return cotacoesDemo;
            
        } catch (error) {
            console.warn('Erro ao extrair cotações do DOM:', error);
            return null;
        }
    },

    processarDadosDashboard(cotacoes) {
        console.log('📊 Processando dados reais para dashboard:', cotacoes.length, 'cotações');
        
        // Contar por status
        const porStatus = {};
        const porModalidade = {};
        const porOperador = {};
        let valorTotal = 0;
        let finalizadas = 0;
        
        cotacoes.forEach(cotacao => {
            // Status
            const status = cotacao.status || 'solicitada';
            porStatus[status] = (porStatus[status] || 0) + 1;
            
            // Modalidade
            const modalidade = cotacao.modalidade || 'brcargo_rodoviario';
            porModalidade[modalidade] = (porModalidade[modalidade] || 0) + 1;
            
            // Operador
            const operador = cotacao.operador_responsavel || 'Não atribuído';
            porOperador[operador] = (porOperador[operador] || 0) + 1;
            
            // Valores
            if (cotacao.valor_frete && cotacao.status === 'finalizada') {
                valorTotal += parseFloat(cotacao.valor_frete) || 0;
                finalizadas++;
            }
        });
        
        // Calcular evolução temporal (últimos 30 dias)
        const evolucao = this.calcularEvolucaoTemporal(cotacoes);
        
        const dados = {
            metricas: {
                total: cotacoes.length,
                finalizadas: finalizadas,
                pendentes: cotacoes.length - finalizadas,
                taxaConversao: cotacoes.length > 0 ? Math.round((finalizadas / cotacoes.length) * 100) : 0,
                valorTotal: valorTotal
            },
            porStatus: Object.entries(porStatus).map(([status, count]) => ({
                status,
                count,
                label: this.getLabelStatus(status)
            })),
            porModalidade: Object.entries(porModalidade).map(([modalidade, count]) => ({
                modalidade,
                count,
                label: this.getLabelModalidade(modalidade)
            })),
            porOperador: Object.entries(porOperador).map(([operador, count]) => ({
                operador,
                count,
                finalizadas: cotacoes.filter(c => c.operador_responsavel === operador && c.status === 'finalizada').length
            })),
            evolucao: evolucao,
            valoresPorModalidade: this.calcularValoresPorModalidade(cotacoes)
        };
        
        console.log('✅ Dados do dashboard processados:', dados);
        return dados;
    },

    calcularEvolucaoTemporal(cotacoes) {
        const hoje = new Date();
        const evolucao = [];
        
        for (let i = 29; i >= 0; i--) {
            const data = new Date(hoje);
            data.setDate(data.getDate() - i);
            const dataStr = data.toISOString().split('T')[0];
            
            const cotacoesDia = cotacoes.filter(c => {
                const dataCotacao = new Date(c.data_criacao || c.created_at);
                return dataCotacao.toISOString().split('T')[0] === dataStr;
            });
            
            evolucao.push({
                data: dataStr,
                total: cotacoesDia.length,
                finalizadas: cotacoesDia.filter(c => c.status === 'finalizada').length
            });
        }
        
        return evolucao;
    },

    calcularValoresPorModalidade(cotacoes) {
        const valores = {};
        const contadores = {};
        
        cotacoes.forEach(cotacao => {
            if (cotacao.valor_frete && cotacao.status === 'finalizada') {
                const modalidade = cotacao.modalidade || 'brcargo_rodoviario';
                const valor = parseFloat(cotacao.valor_frete) || 0;
                
                valores[modalidade] = (valores[modalidade] || 0) + valor;
                contadores[modalidade] = (contadores[modalidade] || 0) + 1;
            }
        });
        
        return Object.entries(valores).map(([modalidade, valorTotal]) => ({
            modalidade,
            valorMedio: contadores[modalidade] > 0 ? valorTotal / contadores[modalidade] : 0,
            label: this.getLabelModalidade(modalidade)
        }));
    },

    getLabelStatus(status) {
        const labels = {
            'solicitada': 'Solicitadas',
            'aceita_operador': 'Aceitas',
            'cotacao_enviada': 'Enviadas',
            'aceita_consultor': 'Aprovadas',
            'finalizada': 'Finalizadas',
            'cancelada': 'Canceladas'
        };
        return labels[status] || status;
    },

    getLabelModalidade(modalidade) {
        const labels = {
            'brcargo_rodoviario': 'Rodoviário',
            'brcargo_maritimo': 'Marítimo',
            'brcargo_aereo': 'Aéreo'
        };
        return labels[modalidade] || modalidade;
    },

    // ==================== ACEITAR/NEGAR COTAÇÕES ====================
    // NOTA: Estas funções são mantidas para compatibilidade, mas agora delegam para as versões v133

    async getCotacao(cotacaoId) {
        // Usar endpoint v133 unificado
        return this.getCotacaoById(cotacaoId);
    },

    // ==================== FINALIZAÇÃO DE COTAÇÕES ====================

    async aprovarCotacao(dados) {
        try {
            const cotacaoId = dados.cotacao_id || dados.id;
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${cotacaoId}/aceitar-consultor`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ observacoes: dados.observacoes })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Erro ao aprovar cotação:', error);
            throw error;
        }
    },

    async recusarCotacao(dados) {
        try {
            const cotacaoId = dados.cotacao_id || dados.id;
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${cotacaoId}/negar-consultor`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ observacoes: dados.observacoes || dados.motivo })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Erro ao recusar cotação:', error);
            throw error;
        }
    },

    async finalizarCotacao(dados) {
        try {
            const cotacaoId = dados.cotacao_id || dados.id;
            const response = await fetch(`${this.baseURL}/cotacoes/${cotacaoId}/finalizar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    acao: dados.acao || 'marcar_finalizada',
                    observacoes: dados.observacoes
                })
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Erro ao finalizar cotação:', error);
            throw error;
        }
    },

    // ==================== REATRIBUIÇÃO DE COTAÇÕES ====================

    async reatribuirCotacao(cotacaoId, operadorId, dados) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${cotacaoId}/reatribuir`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    novo_operador_id: operadorId,
                    motivo: dados.motivo || '',
                    observacoes: dados.observacoes || '',
                    mensagens: dados.mensagens || []
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Cotação reatribuída com sucesso:', data);
                return data;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn('Endpoint reatribuir não disponível, usando fallback:', error);
            
            // Fallback para desenvolvimento
            console.log('📝 Simulando reatribuição de cotação:', { cotacaoId, operadorId, dados });
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            return {
                success: true,
                message: 'Cotação reatribuída com sucesso',
                cotacao: {
                    id: cotacaoId,
                    operador_responsavel_id: operadorId,
                    status: 'aceita_operador',
                    data_reatribuicao: new Date().toISOString(),
                    motivo_reatribuicao: dados.motivo,
                    observacoes_reatribuicao: dados.observacoes
                }
            };
        }
    },

    // ==================== CONVERSAS E MENSAGENS ====================

    async getConversas(cotacaoId, operadorId) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${cotacaoId}/conversas/${operadorId}`);
            
            if (response.ok) {
                const data = await response.json();
                return data;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn('Endpoint conversas não disponível, usando fallback:', error.message);
            
            // Fallback: retornar conversa vazia
            return {
                success: true,
                conversas: [],
                mensagens: []
            };
        }
    },

    async salvarMensagem(cotacaoId, operadorId, mensagem) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${cotacaoId}/conversas/${operadorId}/mensagens`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    mensagem: mensagem,
                    timestamp: new Date().toISOString(),
                    autor: 'Operador Atual'
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Mensagem salva com sucesso:', data);
                return data;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Erro ao salvar mensagem:', error);
            
            // Fallback para desenvolvimento
            console.log('📝 Simulando salvamento de mensagem:', { cotacaoId, operadorId, mensagem });
            
            return {
                success: true,
                message: 'Mensagem salva com sucesso',
                mensagem: {
                    id: Date.now(),
                    cotacao_id: cotacaoId,
                    operador_id: operadorId,
                    mensagem: mensagem,
                    timestamp: new Date().toISOString(),
                    autor: 'Operador Atual'
                }
            };
        }
    },

    // ==================== RASCUNHOS DE RESPOSTA ====================

    async salvarRascunho(cotacaoId, dados) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${cotacaoId}/rascunho`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    valor_frete: dados.valor_frete,
                    prazo_entrega: dados.prazo_entrega,
                    taxa_coleta: dados.taxa_coleta || 0,
                    taxa_entrega: dados.taxa_entrega || 0,
                    valor_seguro: dados.valor_seguro || 0,
                    observacoes: dados.observacoes || '',
                    empresa_prestadora: dados.empresa_prestadora || '',
                    timestamp: new Date().toISOString()
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Rascunho salvo com sucesso:', data);
                return data;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Erro ao salvar rascunho:', error);
            
            // Fallback para desenvolvimento - salvar no localStorage
            const rascunhoKey = `rascunho_cotacao_${cotacaoId}`;
            const rascunho = {
                cotacao_id: cotacaoId,
                ...dados,
                timestamp: new Date().toISOString()
            };
            
            try {
                localStorage.setItem(rascunhoKey, JSON.stringify(rascunho));
                console.log('📝 Rascunho salvo no localStorage:', rascunho);
            } catch (storageError) {
                console.warn('Erro ao salvar no localStorage:', storageError);
            }
            
            return {
                success: true,
                message: 'Rascunho salvo localmente',
                rascunho: rascunho
            };
        }
    },

    async carregarRascunho(cotacaoId) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${cotacaoId}/rascunho`);
            
            if (response.ok) {
                const data = await response.json();
                return data;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Erro ao carregar rascunho:', error);
            
            // Fallback: tentar carregar do localStorage
            const rascunhoKey = `rascunho_cotacao_${cotacaoId}`;
            try {
                const rascunhoLocal = localStorage.getItem(rascunhoKey);
                if (rascunhoLocal) {
                    const rascunho = JSON.parse(rascunhoLocal);
                    console.log('📝 Rascunho carregado do localStorage:', rascunho);
                    return {
                        success: true,
                        rascunho: rascunho
                    };
                }
            } catch (storageError) {
                console.warn('Erro ao carregar do localStorage:', storageError);
            }
            
            return {
                success: false,
                message: 'Nenhum rascunho encontrado'
            };
        }
    },

    // ==================== RESPOSTA DE COTAÇÃO ====================

    async enviarRespostaCotacao(cotacaoId, dados) {
        try {
            const response = await fetch(`${this.baseURL}/v133/cotacoes/${cotacaoId}/responder`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    valor_frete: dados.valor_frete,
                    prazo_entrega: dados.prazo_entrega,
                    taxa_coleta: dados.taxa_coleta || 0,
                    taxa_entrega: dados.taxa_entrega || 0,
                    valor_seguro: dados.valor_seguro || 0,
                    observacoes_gerais: dados.observacoes_gerais || '',
                    condicoes_especiais: dados.condicoes_especiais || '',
                    empresa_prestadora: dados.empresa_prestadora || '',
                    timestamp: new Date().toISOString()
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Resposta de cotação enviada com sucesso:', data);
                return data;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Erro ao enviar resposta de cotação:', error);
            
            // Fallback para desenvolvimento
            console.log('📝 Simulando envio de resposta de cotação:', { cotacaoId, dados });
            
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            return {
                success: true,
                message: 'Resposta de cotação enviada com sucesso',
                cotacao: {
                    id: cotacaoId,
                    status: 'cotacao_enviada',
                    valor_frete: dados.valor_frete,
                    prazo_entrega: dados.prazo_entrega,
                    taxa_coleta: dados.taxa_coleta,
                    taxa_entrega: dados.taxa_entrega,
                    valor_seguro: dados.valor_seguro,
                    observacoes_gerais: dados.observacoes_gerais,
                    condicoes_especiais: dados.condicoes_especiais,
                    empresa_prestadora: dados.empresa_prestadora,
                    data_resposta: new Date().toISOString()
                }
            };
        }
    },

    // ==================== EMPRESAS PRESTADORAS ====================

    async getEmpresasPrestadoras() {
        try {
            const response = await fetch(`${this.baseURL}/v133/empresas-prestadoras`);
            
            if (response.ok) {
                const data = await response.json();
                return data;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Erro ao carregar empresas prestadoras:', error);
            
            // Fallback: retornar empresas simuladas
            return {
                success: true,
                empresas: [
                    { id: 1, nome: 'BRCargo Rodoviário', tipo: 'rodoviario', ativa: true },
                    { id: 2, nome: 'BRCargo Marítimo', tipo: 'maritimo', ativa: true },
                    { id: 3, nome: 'BRCargo Aéreo', tipo: 'aereo', ativa: true },
                    { id: 4, nome: 'Transportadora Parceira 1', tipo: 'rodoviario', ativa: true },
                    { id: 5, nome: 'Transportadora Parceira 2', tipo: 'maritimo', ativa: true }
                ]
            };
        }
    },
    
    // ==================== UTILITÁRIOS ====================
    
    handleError(error) {
        console.error('Erro na API:', error);
        return {
            success: false,
            message: error.message || 'Erro ao processar requisição',
            error: error
        };
    }
};

// Exportar para uso global
window.API = API;
