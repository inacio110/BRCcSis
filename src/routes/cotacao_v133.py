"""
Rotas adicionais para BRCcSis v1.3.3
Sistema completo de fluxo de cotações
"""

from flask import Blueprint, request, jsonify
from flask_cors import CORS
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc, func
from datetime import datetime, date
import re

from src.models import db
from src.models.cotacao import Cotacao, HistoricoCotacao, StatusCotacao, EmpresaCotacao
from src.models.usuario import Usuario, TipoUsuario
from src.models.notificacao import Notificacao, TipoNotificacao
from src.models.empresa import Empresa

cotacao_v133_bp = Blueprint("cotacao_v133", __name__)
CORS(cotacao_v133_bp)

# ==================== ROTAS GERAIS ====================

@cotacao_v133_bp.route("/cotacoes", methods=["GET"])
@login_required
def listar_cotacoes():
    """Lista cotações baseado no tipo de usuário (endpoint unificado)"""
    try:
        # Parâmetros de filtro
        status = request.args.get("status")
        cliente_nome = request.args.get("cliente_nome")
        empresa_transporte = request.args.get("empresa_transporte")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        
        # Paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # Query base dependendo do tipo de usuário
        if current_user.tipo_usuario == TipoUsuario.CONSULTOR:
            # Consultores só veem suas próprias cotações
            query = Cotacao.query.filter(Cotacao.consultor_id == current_user.id)
        elif current_user.tipo_usuario == TipoUsuario.OPERADOR:
            # Operadores veem cotações disponíveis OU suas próprias
            query = Cotacao.query.filter(
                or_(
                    Cotacao.status == StatusCotacao.SOLICITADA,
                    Cotacao.operador_id == current_user.id
                )
            )
        else:
            # Administradores e gerentes veem todas
            query = Cotacao.query
        
        # Aplicar filtros
        if status:
            try:
                status_enum = StatusCotacao(status)
                query = query.filter(Cotacao.status == status_enum)
            except ValueError:
                pass
        
        if cliente_nome:
            query = query.filter(Cotacao.cliente_nome.ilike(f"%{cliente_nome}%"))
        
        if empresa_transporte:
            try:
                empresa_enum = EmpresaCotacao(empresa_transporte)
                query = query.filter(Cotacao.empresa_transporte == empresa_enum)
            except ValueError:
                pass
        
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(Cotacao.data_solicitacao >= data_inicio_dt)
            except ValueError:
                pass
        
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                query = query.filter(Cotacao.data_solicitacao <= data_fim_dt)
            except ValueError:
                pass
        
        # Ordenar por data de solicitação (mais recentes primeiro)
        query = query.order_by(desc(Cotacao.data_solicitacao))
        
        # Paginação
        cotacoes_paginadas = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Converter para dicionário
        cotacoes_data = [cotacao.to_dict() for cotacao in cotacoes_paginadas.items]
        
        return jsonify({
            'success': True,
            'cotacoes': cotacoes_data,
            'total': cotacoes_paginadas.total,
            'pages': cotacoes_paginadas.pages,
            'current_page': page,
            'per_page': per_page,
            'has_next': cotacoes_paginadas.has_next,
            'has_prev': cotacoes_paginadas.has_prev
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao listar cotações: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes", methods=["POST"])
@login_required
def criar_cotacao():
    """Cria uma nova cotação (implementação completa)"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.CONSULTOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Apenas consultores, gerentes e administradores podem criar cotações'
            }), 403
        
        data = request.get_json()
        
        # Obter modalidade de transporte
        empresa_transporte = data.get('empresa_transporte', '').lower()
        
        # Validações obrigatórias básicas (para todas as modalidades)
        campos_basicos_obrigatorios = [
            'cliente_nome', 'cliente_cnpj', 'numero_cliente'
        ]
        
        # Campos específicos por modalidade
        if empresa_transporte == 'brcargo_rodoviario':
            tipo_origem = data.get('tipo_origem', 'endereco')
            if tipo_origem == 'porto':
                campos_obrigatorios = campos_basicos_obrigatorios + [
                    'origem_porto', 'destino_cep', 'destino_endereco', 'destino_cidade', 'destino_estado',
                    'carga_descricao', 'carga_peso_kg', 'carga_valor_mercadoria', 'carga_cubagem'
                ]
            else:
                campos_obrigatorios = campos_basicos_obrigatorios + [
                    'origem_cep', 'origem_endereco', 'origem_cidade', 'origem_estado',
                    'destino_cep', 'destino_endereco', 'destino_cidade', 'destino_estado',
                    'carga_descricao', 'carga_peso_kg', 'carga_valor_mercadoria', 'carga_cubagem'
                ]
        elif empresa_transporte == 'brcargo_maritimo':
            campos_obrigatorios = campos_basicos_obrigatorios + [
                'porto_origem', 'porto_destino', 'net_weight', 'gross_weight', 
                'cubagem', 'incoterm', 'tipo_carga_maritima', 'carga_valor_mercadoria'
            ]
        elif empresa_transporte == 'frete_aereo':
            campos_obrigatorios = campos_basicos_obrigatorios + [
                'aeroporto_origem', 'aeroporto_destino', 'tipo_servico_aereo',
                'carga_descricao', 'carga_peso_kg', 'carga_valor_mercadoria', 'carga_cubagem'
            ]
        else:
            campos_obrigatorios = campos_basicos_obrigatorios + [
                'origem_cep', 'origem_endereco', 'origem_cidade', 'origem_estado',
                'destino_cep', 'destino_endereco', 'destino_cidade', 'destino_estado',
                'carga_descricao', 'carga_peso_kg', 'carga_valor_mercadoria', 'carga_cubagem'
            ]
        
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório: {campo}'
                }), 400
        
        # Validar CNPJ
        from src.routes.cotacao import validar_cnpj
        if not validar_cnpj(data['cliente_cnpj']):
            return jsonify({
                'success': False,
                'message': 'CNPJ inválido'
            }), 400
        
        # Validar CEPs apenas para transporte rodoviário com origem endereço
        if empresa_transporte == 'brcargo_rodoviario':
            tipo_origem = data.get('tipo_origem', 'endereco')
            from src.routes.cotacao import validar_cep
            
            if tipo_origem == 'endereco' and not validar_cep(data.get('origem_cep', '')):
                return jsonify({
                    'success': False,
                    'message': 'CEP de origem inválido'
                }), 400
            
            if not validar_cep(data.get('destino_cep', '')):
                return jsonify({
                    'success': False,
                    'message': 'CEP de destino inválido'
                }), 400
        
        # Validar peso
        if empresa_transporte != 'brcargo_maritimo':
            try:
                peso = float(data['carga_peso_kg'])
                if peso <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'Peso da carga deve ser um número positivo'
                }), 400
        else:
            try:
                peso = float(data.get('gross_weight', 0))
                if peso <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'Gross Weight deve ser um número positivo'
                }), 400
        
        # Validar empresa de transporte
        empresa_transporte_str = data.get('empresa_transporte', 'brcargo_rodoviario')
        try:
            empresa_transporte_enum = EmpresaCotacao(empresa_transporte_str)
        except ValueError:
            return jsonify({
                'success': False,
                'message': f'Empresa de transporte inválida: {empresa_transporte_str}'
            }), 400
        
        # Validações específicas para transporte marítimo
        if empresa_transporte_enum == EmpresaCotacao.BRCARGO_MARITIMO:
            campos_maritimos_obrigatorios = [
                'net_weight', 'gross_weight', 'cubagem', 'incoterm', 
                'tipo_carga_maritima', 'porto_origem', 'porto_destino'
            ]
            
            for campo in campos_maritimos_obrigatorios:
                if not data.get(campo):
                    return jsonify({
                        'success': False,
                        'message': f'Campo obrigatório para transporte marítimo: {campo}'
                    }), 400
            
            try:
                net_weight = float(data['net_weight'])
                gross_weight = float(data['gross_weight'])
                cubagem = float(data['cubagem'])
                
                if net_weight <= 0 or gross_weight <= 0 or cubagem <= 0:
                    raise ValueError()
                    
                if net_weight > gross_weight:
                    return jsonify({
                        'success': False,
                        'message': 'Net Weight não pode ser maior que Gross Weight'
                    }), 400
                    
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'message': 'Valores de peso e cubagem devem ser números positivos'
                }), 400
        
        # Preparar dados de origem baseado no tipo
        if empresa_transporte_enum == EmpresaCotacao.BRCARGO_RODOVIARIO:
            tipo_origem = data.get('tipo_origem', 'endereco')
            if tipo_origem == 'porto':
                origem_cep = '00000000'
                origem_endereco = f"Porto: {data.get('origem_porto', 'Porto não especificado')}"
                origem_cidade = data.get('origem_porto', 'Porto não especificado')
                origem_estado = 'SP'
            else:
                origem_cep = re.sub(r'[^0-9]', '', data.get('origem_cep', ''))
                origem_endereco = data.get('origem_endereco', '')
                origem_cidade = data.get('origem_cidade', '')
                origem_estado = data.get('origem_estado', '')
        elif empresa_transporte_enum == EmpresaCotacao.BRCARGO_MARITIMO:
            origem_cep = '00000000'
            origem_endereco = f"Porto: {data.get('porto_origem', 'Porto não especificado')}"
            origem_cidade = data.get('porto_origem', 'Porto não especificado')
            origem_estado = 'SP'
        else:
            origem_cep = re.sub(r'[^0-9]', '', data.get('origem_cep', ''))
            origem_endereco = data.get('origem_endereco', '')
            origem_cidade = data.get('origem_cidade', '')
            origem_estado = data.get('origem_estado', '')

        # Criar cotação
        cotacao = Cotacao(
            consultor_id=current_user.id,
            empresa_transporte=empresa_transporte_enum,
            cliente_nome=data['cliente_nome'],
            cliente_cnpj=re.sub(r'[^0-9]', '', data['cliente_cnpj']),
            cliente_contato_telefone=data.get('cliente_contato_telefone'),
            cliente_contato_email=data.get('cliente_contato_email'),
            origem_cep=origem_cep,
            origem_endereco=origem_endereco,
            origem_cidade=origem_cidade,
            origem_estado=origem_estado,
            destino_cep=re.sub(r'[^0-9]', '', data.get('destino_cep', '')),
            destino_endereco=data.get('destino_endereco', ''),
            destino_cidade=data.get('destino_cidade', ''),
            destino_estado=data.get('destino_estado', ''),
            carga_descricao=data.get('carga_descricao', ''),
            carga_peso_kg=peso,
            carga_comprimento_cm=data.get('carga_comprimento_cm'),
            carga_largura_cm=data.get('carga_largura_cm'),
            carga_altura_cm=data.get('carga_altura_cm'),
            carga_valor_mercadoria=data.get('carga_valor_mercadoria'),
            carga_tipo_embalagem=data.get('carga_tipo_embalagem'),
            servico_prazo_desejado=data.get('servico_prazo_desejado'),
            servico_tipo=data.get('servico_tipo'),
            servico_observacoes=data.get('servico_observacoes'),
            data_coleta_preferencial=datetime.strptime(data['data_coleta_preferencial'], '%Y-%m-%d').date() if data.get('data_coleta_preferencial') else None,
            instrucoes_manuseio=data.get('instrucoes_manuseio'),
            seguro_adicional=data.get('seguro_adicional', False),
            servicos_complementares=data.get('servicos_complementares'),
            numero_cliente=data.get('numero_cliente'),
            numero_net_weight=data.get('net_weight'),
            numero_gross_weight=data.get('gross_weight'),
            cubagem=data.get('cubagem') if empresa_transporte_enum == EmpresaCotacao.BRCARGO_MARITIMO else data.get('carga_cubagem'),
            incoterm=data.get('incoterm'),
            tipo_carga_maritima=data.get('tipo_carga_maritima'),
            tamanho_container=data.get('tamanho_container'),
            quantidade_containers=data.get('quantidade_containers'),
            porto_origem=data.get('porto_origem'),
            porto_destino=data.get('porto_destino')
        )
        
        db.session.add(cotacao)
        db.session.commit()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=cotacao.id,
            usuario_id=current_user.id,
            status_anterior=None,
            status_novo=StatusCotacao.SOLICITADA,
            observacoes=f"Cotação criada pelo consultor {current_user.nome_completo}"
        )
        
        # Registrar log de auditoria
        from src.models.usuario import LogAuditoria
        LogAuditoria.registrar_acao(
            usuario_id=current_user.id,
            acao='CRIAR',
            recurso='COTACAO',
            detalhes=f'Cotação {cotacao.numero_cotacao} criada para cliente {cotacao.cliente_nome}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Cotação criada com sucesso',
            'cotacao': cotacao.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Erro ao criar cotação: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Erro ao criar cotação: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/<int:cotacao_id>", methods=["GET"])
@login_required
def obter_cotacao(cotacao_id):
    """Obtém uma cotação específica"""
    try:
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        
        # Verificar permissão
        if (current_user.tipo_usuario == TipoUsuario.CONSULTOR and 
            cotacao.consultor_id != current_user.id):
            return jsonify({
                'success': False,
                'message': 'Acesso negado'
            }), 403
        
        # Buscar histórico
        historico = HistoricoCotacao.obter_historico_cotacao(cotacao_id)
        
        cotacao_data = cotacao.to_dict()
        cotacao_data['historico'] = historico
        
        return jsonify({
            'success': True,
            'cotacao': cotacao_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter cotação: {str(e)}'
        }), 500

# ==================== ROTAS PARA OPERADORES ====================

@cotacao_v133_bp.route("/cotacoes/disponiveis", methods=["GET"])
@login_required
def obter_cotacoes_disponiveis():
    """Obtém cotações disponíveis para operadores aceitarem"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.OPERADOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Acesso negado'
            }), 403
        
        # Buscar cotações com status SOLICITADA
        cotacoes = Cotacao.query.filter_by(
            status=StatusCotacao.SOLICITADA
        ).order_by(Cotacao.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'cotacoes': [cotacao.to_dict() for cotacao in cotacoes]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/<int:cotacao_id>/aceitar-operador", methods=["POST"])
@login_required
def aceitar_cotacao_operador(cotacao_id):
    """Operador aceita uma cotação"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.OPERADOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Apenas operadores podem aceitar cotações'
            }), 403
        
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        
        data = request.get_json() or {}
        observacoes = data.get('observacoes')
        
        # Aceitar cotação usando método do modelo
        cotacao.aceitar_por_operador(current_user.id, observacoes)
        
        return jsonify({
            'success': True,
            'message': 'Cotação aceita com sucesso',
            'cotacao': cotacao.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/<int:cotacao_id>/negar-operador", methods=["POST"])
@login_required
def negar_cotacao_operador(cotacao_id):
    """Operador nega uma cotação (marca como finalizada com status negada)"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.OPERADOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Apenas operadores podem negar cotações'
            }), 403
        
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        
        # Verificar se pode negar (apenas se estiver solicitada)
        if cotacao.status != StatusCotacao.SOLICITADA:
            return jsonify({
                'success': False,
                'message': 'Apenas cotações solicitadas podem ser negadas'
            }), 400
        
        data = request.get_json() or {}
        motivo = data.get('motivo') or data.get('observacoes')
        
        # Marcar como finalizada com observação de negação
        cotacao.marcar_finalizada(
            usuario=current_user,
            observacoes=f"Cotação negada pelo operador. Motivo: {motivo}" if motivo else "Cotação negada pelo operador"
        )
        
        return jsonify({
            'success': True,
            'message': 'Cotação negada com sucesso',
            'cotacao': cotacao.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/<int:cotacao_id>/enviar-resposta", methods=["POST"])
@login_required
def enviar_resposta_cotacao(cotacao_id):
    """Operador envia resposta da cotação"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.OPERADOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Apenas operadores podem responder cotações'
            }), 403
        
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        
        # Verificar se o operador é responsável pela cotação
        if cotacao.operador_id != current_user.id and current_user.tipo_usuario == TipoUsuario.OPERADOR:
            return jsonify({
                'success': False,
                'message': 'Você não é responsável por esta cotação'
            }), 403
        
        data = request.get_json()
        
        # Validações
        if not data.get('empresa_prestadora_id'):
            return jsonify({
                'success': False,
                'message': 'Empresa prestadora é obrigatória'
            }), 400
        
        # Verificar se a empresa existe
        empresa = Empresa.query.get(data['empresa_prestadora_id'])
        if not empresa:
            return jsonify({
                'success': False,
                'message': 'Empresa prestadora não encontrada'
            }), 400
        
        # Enviar cotação usando método do modelo
        cotacao.enviar_cotacao(
            valor_frete=data.get('valor_frete'),
            prazo_entrega=data.get('prazo_entrega'),
            observacoes=data.get('observacoes'),
            empresa_prestadora_id=data['empresa_prestadora_id']
        )
        
        return jsonify({
            'success': True,
            'message': 'Resposta enviada com sucesso',
            'cotacao': cotacao.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/minhas-operacoes", methods=["GET"])
@login_required
def obter_minhas_operacoes():
    """Obtém cotações que o operador está gerenciando"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.OPERADOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Acesso negado'
            }), 403
        
        # Para operadores, mostrar apenas suas cotações
        # Para admin/gerente, mostrar todas
        if current_user.tipo_usuario == TipoUsuario.OPERADOR:
            cotacoes = Cotacao.query.filter_by(
                operador_id=current_user.id
            ).order_by(Cotacao.updated_at.desc()).all()
        else:
            cotacoes = Cotacao.query.filter(
                Cotacao.operador_id.isnot(None)
            ).order_by(Cotacao.updated_at.desc()).all()
        
        return jsonify({
            'success': True,
            'cotacoes': [cotacao.to_dict() for cotacao in cotacoes]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

# ==================== ROTAS PARA CONSULTORES ====================

@cotacao_v133_bp.route("/cotacoes/<int:cotacao_id>/aceitar-consultor", methods=["POST"])
@login_required
def aceitar_cotacao_consultor(cotacao_id):
    """Consultor aceita uma cotação"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.CONSULTOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Apenas consultores podem aceitar cotações'
            }), 403
        
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        
        # Verificar se o consultor é dono da cotação
        if cotacao.consultor_id != current_user.id and current_user.tipo_usuario == TipoUsuario.CONSULTOR:
            return jsonify({
                'success': False,
                'message': 'Você não é responsável por esta cotação'
            }), 403
        
        data = request.get_json() or {}
        observacoes = data.get('observacoes')
        
        # Aceitar cotação usando método do modelo
        cotacao.aceitar_por_consultor(observacoes)
        
        return jsonify({
            'success': True,
            'message': 'Cotação aceita com sucesso',
            'cotacao': cotacao.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/<int:cotacao_id>/negar-consultor", methods=["POST"])
@login_required
def negar_cotacao_consultor(cotacao_id):
    """Consultor nega uma cotação"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.CONSULTOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Apenas consultores podem negar cotações'
            }), 403
        
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        
        # Verificar se o consultor é dono da cotação
        if cotacao.consultor_id != current_user.id and current_user.tipo_usuario == TipoUsuario.CONSULTOR:
            return jsonify({
                'success': False,
                'message': 'Você não é responsável por esta cotação'
            }), 403
        
        data = request.get_json() or {}
        observacoes = data.get('observacoes')
        
        # Negar cotação usando método do modelo
        cotacao.negar_por_consultor(observacoes)
        
        return jsonify({
            'success': True,
            'message': 'Cotação negada',
            'cotacao': cotacao.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/minhas-solicitacoes", methods=["GET"])
@login_required
def obter_minhas_solicitacoes():
    """Obtém cotações solicitadas pelo consultor"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.CONSULTOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Acesso negado'
            }), 403
        
        # Para consultores, mostrar apenas suas cotações
        # Para admin/gerente, mostrar todas
        if current_user.tipo_usuario == TipoUsuario.CONSULTOR:
            cotacoes = Cotacao.query.filter_by(
                consultor_id=current_user.id
            ).order_by(Cotacao.created_at.desc()).all()
        else:
            cotacoes = Cotacao.query.order_by(Cotacao.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'cotacoes': [cotacao.to_dict() for cotacao in cotacoes]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

# ==================== ROTAS PARA SEPARAÇÃO POR MODALIDADE ====================

@cotacao_v133_bp.route("/cotacoes/rodoviarias", methods=["GET"])
@login_required
def obter_cotacoes_rodoviarias():
    """Obtém cotações rodoviárias"""
    try:
        cotacoes = Cotacao.query.filter_by(
            empresa_transporte=EmpresaCotacao.BRCARGO_RODOVIARIO
        ).order_by(Cotacao.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'cotacoes': [cotacao.to_dict() for cotacao in cotacoes]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/maritimas", methods=["GET"])
@login_required
def obter_cotacoes_maritimas():
    """Obtém cotações marítimas"""
    try:
        cotacoes = Cotacao.query.filter_by(
            empresa_transporte=EmpresaCotacao.BRCARGO_MARITIMO
        ).order_by(Cotacao.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'cotacoes': [cotacao.to_dict() for cotacao in cotacoes]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/cotacoes/aereas", methods=["GET"])
@login_required
def obter_cotacoes_aereas():
    """Obtém cotações aéreas"""
    try:
        cotacoes = Cotacao.query.filter_by(
            empresa_transporte=EmpresaCotacao.FRETE_AEREO
        ).order_by(Cotacao.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'cotacoes': [cotacao.to_dict() for cotacao in cotacoes]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

# ==================== ROTAS PARA NOTIFICAÇÕES ====================

@cotacao_v133_bp.route("/notificacoes", methods=["GET"])
@login_required
def obter_notificacoes():
    """Obtém notificações do usuário"""
    try:
        # Parâmetros de consulta
        apenas_nao_lidas = request.args.get('apenas_nao_lidas', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 50))
        
        query = Notificacao.query.filter_by(usuario_id=current_user.id)
        
        if apenas_nao_lidas:
            query = query.filter_by(lida=False)
        
        notificacoes = query.order_by(
            Notificacao.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'success': True,
            'notificacoes': [notif.to_dict() for notif in notificacoes],
            'total_nao_lidas': Notificacao.contar_nao_lidas(current_user.id)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/notificacoes/<int:notificacao_id>/marcar-lida", methods=["POST"])
@login_required
def marcar_notificacao_lida(notificacao_id):
    """Marca uma notificação como lida"""
    try:
        sucesso = Notificacao.marcar_como_lida(notificacao_id, current_user.id)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Notificação marcada como lida'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Notificação não encontrada'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/notificacoes/marcar-todas-lidas", methods=["POST"])
@login_required
def marcar_todas_notificacoes_lidas():
    """Marca todas as notificações do usuário como lidas"""
    try:
        Notificacao.query.filter_by(
            usuario_id=current_user.id,
            lida=False
        ).update({'lida': True})
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Todas as notificações foram marcadas como lidas'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

# ==================== ROTAS PARA HISTÓRICO ====================

@cotacao_v133_bp.route("/cotacoes/<int:cotacao_id>/historico", methods=["GET"])
@login_required
def obter_historico_cotacao(cotacao_id):
    """Obtém histórico completo de uma cotação"""
    try:
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        
        # Verificar permissão de visualização
        pode_visualizar = (
            current_user.tipo_usuario in [TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE] or
            cotacao.consultor_id == current_user.id or
            cotacao.operador_id == current_user.id
        )
        
        if not pode_visualizar:
            return jsonify({
                'success': False,
                'message': 'Acesso negado'
            }), 403
        
        historico = HistoricoCotacao.obter_historico_cotacao(cotacao_id)
        
        return jsonify({
            'success': True,
            'historico': historico
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

# ==================== ENDPOINT TEMPORÁRIO PARA TESTES ====================

@cotacao_v133_bp.route("/cotacoes/test", methods=["GET"])
def obter_cotacoes_teste():
    """Endpoint temporário para testar dados reais (SEM AUTENTICAÇÃO)"""
    try:
        # Buscar todas as cotações para teste
        cotacoes = Cotacao.query.order_by(Cotacao.created_at.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'total': len(cotacoes),
            'cotacoes': [cotacao.to_dict() for cotacao in cotacoes],
            'message': 'Dados reais do banco de dados'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

@cotacao_v133_bp.route("/operadores/test", methods=["GET"])
def obter_operadores_teste():
    """Endpoint temporário para testar operadores reais (SEM AUTENTICAÇÃO)"""
    try:
        from src.models.usuario import Usuario, TipoUsuario
        
        # Buscar operadores reais
        operadores = Usuario.query.filter(
            Usuario.tipo_usuario.in_([TipoUsuario.OPERADOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE])
        ).all()
        
        return jsonify({
            'success': True,
            'operadores': [{
                'id': op.id,
                'nome': op.nome_completo,
                'email': op.email,
                'tipo': op.tipo_usuario.value
            } for op in operadores]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500

