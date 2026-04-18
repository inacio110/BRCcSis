from flask import Blueprint, request, jsonify
from flask_cors import CORS
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, desc
from datetime import datetime, date
import re

from src.models import db
from src.models.cotacao import Cotacao, HistoricoCotacao, StatusCotacao, EmpresaCotacao
from src.models.usuario import Usuario, TipoUsuario, LogAuditoria

cotacao_bp = Blueprint("cotacao", __name__)
CORS(cotacao_bp)

def validar_cnpj(cnpj):
    """Valida CNPJ usando algoritmo oficial"""
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se não são todos iguais
    if cnpj == cnpj[0] * 14:
        return False
    
    # Calcula primeiro dígito verificador
    soma = 0
    peso = 5
    for i in range(12):
        soma += int(cnpj[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    # Calcula segundo dígito verificador
    soma = 0
    peso = 6
    for i in range(13):
        soma += int(cnpj[i]) * peso
        peso -= 1
        if peso < 2:
            peso = 9
    
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    # Verifica se os dígitos calculados conferem
    return cnpj[12] == str(digito1) and cnpj[13] == str(digito2)

def validar_cep(cep):
    """Valida formato do CEP"""
    cep = re.sub(r'[^0-9]', '', cep)
    return len(cep) == 8 and cep.isdigit()

@cotacao_bp.route("/cotacoes", methods=["GET"])
@login_required
def listar_cotacoes():
    """Lista cotações baseado no tipo de usuário"""
    try:
        # Parâmetros de filtro
        status = request.args.get("status")
        cliente_nome = request.args.get("cliente_nome")
        cliente_cnpj = request.args.get("cliente_cnpj")
        origem_cidade = request.args.get("origem_cidade")
        destino_cidade = request.args.get("destino_cidade")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")
        consultor_id = request.args.get("consultor_id")
        operador_id = request.args.get("operador_id")
        empresa_transporte = request.args.get("empresa_transporte")
        
        # Paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        
        # Query base dependendo do tipo de usuário
        if current_user.tipo_usuario == TipoUsuario.CONSULTOR:
            # Consultores só veem suas próprias cotações
            query = Cotacao.query.filter(Cotacao.consultor_id == current_user.id)
        else:
            # Operadores, gerentes e administradores veem todas
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
        
        if cliente_cnpj:
            cnpj_limpo = re.sub(r'[^0-9]', '', cliente_cnpj)
            query = query.filter(Cotacao.cliente_cnpj.like(f"%{cnpj_limpo}%"))
        
        if origem_cidade:
            query = query.filter(Cotacao.origem_cidade.ilike(f"%{origem_cidade}%"))
        
        if destino_cidade:
            query = query.filter(Cotacao.destino_cidade.ilike(f"%{destino_cidade}%"))
        
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
        
        # Filtros específicos para operadores/administradores
        if current_user.tipo_usuario != TipoUsuario.CONSULTOR:
            if consultor_id:
                query = query.filter(Cotacao.consultor_id == consultor_id)
            
            if operador_id:
                query = query.filter(Cotacao.operador_id == operador_id)
        
        if empresa_transporte:
            try:
                empresa_enum = EmpresaCotacao(empresa_transporte)
                query = query.filter(Cotacao.empresa_transporte == empresa_enum)
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
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao listar cotações: {str(e)}'
        }), 500

@cotacao_bp.route("/cotacoes", methods=["POST"])
@login_required
def criar_cotacao():
    """Cria uma nova cotação (apenas consultores)"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario != TipoUsuario.CONSULTOR:
            return jsonify({
                'success': False,
                'message': 'Apenas consultores podem criar cotações'
            }), 403
        
        data = request.get_json()
        
        # Validações obrigatórias básicas
        campos_obrigatorios_basicos = ['cliente_nome', 'cliente_cnpj', 'carga_descricao', 'carga_peso_kg']
        
        for campo in campos_obrigatorios_basicos:
            if not data.get(campo):
                return jsonify({
                    'success': False,
                    'message': f'Campo obrigatório: {campo}'
                }), 400
        
        # Validações específicas por tipo de transporte
        empresa_transporte = data.get('empresa_transporte', 'brcargo_rodoviario')
        
        if empresa_transporte == 'brcargo_maritimo':
            # Para transporte marítimo, não exigir endereços detalhados
            # Apenas verificar se há informações mínimas
            if not data.get('origem_endereco') and not data.get('destino_endereco'):
                return jsonify({
                    'success': False,
                    'message': 'Para transporte marítimo, informe pelo menos porto de origem e destino'
                }), 400
        else:
            # Para outros tipos de transporte, exigir campos completos
            campos_obrigatorios_endereco = [
                'origem_cep', 'origem_endereco', 'origem_cidade', 'origem_estado',
                'destino_cep', 'destino_endereco', 'destino_cidade', 'destino_estado'
            ]
            
            for campo in campos_obrigatorios_endereco:
                if not data.get(campo):
                    return jsonify({
                        'success': False,
                        'message': f'Campo obrigatório: {campo}'
                    }), 400
        
        # Validar CNPJ
        if not validar_cnpj(data['cliente_cnpj']):
            return jsonify({
                'success': False,
                'message': 'CNPJ inválido'
            }), 400
        
        # Validar CEPs apenas para transporte não marítimo
        if empresa_transporte != 'brcargo_maritimo':
            if not validar_cep(data['origem_cep']):
                return jsonify({
                    'success': False,
                    'message': 'CEP de origem inválido'
                }), 400
            
            if not validar_cep(data['destino_cep']):
                return jsonify({
                    'success': False,
                    'message': 'CEP de destino inválido'
                }), 400
        
        # Validar peso
        try:
            peso = float(data['carga_peso_kg'])
            if peso <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Peso da carga deve ser um número positivo'
            }), 400
        
        # Criar cotação
        cotacao = Cotacao(
            consultor_id=current_user.id,
            empresa_transporte=EmpresaCotacao(data.get('empresa_transporte', 'brcargo_rodoviario')),
            cliente_nome=data['cliente_nome'],
            cliente_cnpj=re.sub(r'[^0-9]', '', data['cliente_cnpj']),
            cliente_contato_telefone=data.get('cliente_contato_telefone'),
            cliente_contato_email=data.get('cliente_contato_email'),
            origem_cep=re.sub(r'[^0-9]', '', data.get('origem_cep', '00000000')),
            origem_endereco=data.get('origem_endereco', ''),
            origem_cidade=data.get('origem_cidade', ''),
            origem_estado=data.get('origem_estado', ''),
            destino_cep=re.sub(r'[^0-9]', '', data.get('destino_cep', '00000000')),
            destino_endereco=data.get('destino_endereco', ''),
            destino_cidade=data.get('destino_cidade', ''),
            destino_estado=data.get('destino_estado', ''),
            carga_descricao=data['carga_descricao'],
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
            servicos_complementares=data.get('servicos_complementares')
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
        return jsonify({
            'success': False,
            'message': f'Erro ao criar cotação: {str(e)}'
        }), 500

@cotacao_bp.route("/cotacoes/<int:cotacao_id>", methods=["GET"])
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
        historico = HistoricoCotacao.query.filter_by(cotacao_id=cotacao_id)\
            .order_by(HistoricoCotacao.timestamp.desc()).all()
        
        cotacao_data = cotacao.to_dict()
        cotacao_data['historico'] = [h.to_dict() for h in historico]
        
        return jsonify({
            'success': True,
            'cotacao': cotacao_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter cotação: {str(e)}'
        }), 500

@cotacao_bp.route("/cotacoes/<int:cotacao_id>/aceitar", methods=["POST"])
@login_required
def aceitar_cotacao(cotacao_id):
    """Aceita uma cotação (operadores, gerentes, administradores)"""
    try:
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        
        # Verificar se pode aceitar
        if not cotacao.pode_ser_aceita_por(current_user):
            return jsonify({
                'success': False,
                'message': 'Você não pode aceitar esta cotação'
            }), 403
        
        cotacao.aceitar(current_user)
        db.session.commit()
        
        # Registrar log de auditoria
        LogAuditoria.registrar_acao(
            usuario_id=current_user.id,
            acao='ACEITAR',
            recurso='COTACAO',
            detalhes=f'Cotação {cotacao.numero_cotacao} aceita'
        )
        
        return jsonify({
            'success': True,
            'message': 'Cotação aceita com sucesso',
            'cotacao': cotacao.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao aceitar cotação: {str(e)}'
        }), 500

@cotacao_bp.route("/cotacoes/<int:cotacao_id>/responder", methods=["POST"])
@login_required
def responder_cotacao(cotacao_id):
    """Responde uma cotação com valores"""
    try:
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        data = request.get_json()
        
        # Verificar se pode responder
        if not cotacao.pode_ser_respondida_por(current_user):
            return jsonify({
                'success': False,
                'message': 'Você não pode responder esta cotação'
            }), 403
        
        # Validar dados obrigatórios
        if not data.get('valor_frete') or not data.get('prazo_entrega'):
            return jsonify({
                'success': False,
                'message': 'Valor do frete e prazo de entrega são obrigatórios'
            }), 400
        
        try:
            valor_frete = float(data['valor_frete'])
            prazo_entrega = int(data['prazo_entrega'])
            
            if valor_frete <= 0 or prazo_entrega <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Valor do frete e prazo devem ser números positivos'
            }), 400
        
        cotacao.responder(
            operador=current_user,
            valor_frete=valor_frete,
            prazo_entrega=prazo_entrega,
            observacoes=data.get('observacoes')
        )
        db.session.commit()
        
        # Registrar log de auditoria
        LogAuditoria.registrar_acao(
            usuario_id=current_user.id,
            acao='RESPONDER',
            recurso='COTACAO',
            detalhes=f'Cotação {cotacao.numero_cotacao} respondida com valor R$ {valor_frete}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Cotação respondida com sucesso',
            'cotacao': cotacao.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao responder cotação: {str(e)}'
        }), 500

@cotacao_bp.route("/cotacoes/<int:cotacao_id>/finalizar", methods=["POST"])
@login_required
def finalizar_cotacao(cotacao_id):
    """Finaliza uma cotação"""
    try:
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        data = request.get_json()
        
        # Verificar se pode finalizar
        if not cotacao.pode_ser_finalizada_por(current_user):
            return jsonify({
                'success': False,
                'message': 'Você não pode finalizar esta cotação'
            }), 403
        
        acao = data.get('acao')  # 'aprovar', 'recusar', 'marcar_finalizada'
        
        if acao == 'aprovar':
            cotacao.finalizar(current_user, aprovada=True, observacoes=data.get('observacoes'))
        elif acao == 'recusar':
            cotacao.finalizar(current_user, aprovada=False, observacoes=data.get('observacoes'))
        elif acao == 'marcar_finalizada':
            cotacao.marcar_finalizada(current_user, observacoes=data.get('observacoes'))
        else:
            return jsonify({
                'success': False,
                'message': 'Ação inválida. Use: aprovar, recusar ou marcar_finalizada'
            }), 400
        
        db.session.commit()
        
        # Registrar log de auditoria
        LogAuditoria.registrar_acao(
            usuario_id=current_user.id,
            acao='FINALIZAR',
            recurso='COTACAO',
            detalhes=f'Cotação {cotacao.numero_cotacao} finalizada - {acao}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Cotação finalizada com sucesso',
            'cotacao': cotacao.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao finalizar cotação: {str(e)}'
        }), 500

@cotacao_bp.route("/cotacoes/<int:cotacao_id>/reatribuir", methods=["POST"])
@login_required
def reatribuir_cotacao(cotacao_id):
    """Reatribui uma cotação para outro operador (apenas administradores/gerentes)"""
    try:
        cotacao = Cotacao.query.get_or_404(cotacao_id)
        data = request.get_json()
        
        # Verificar se pode reatribuir
        if not cotacao.pode_ser_reatribuida_por(current_user):
            return jsonify({
                'success': False,
                'message': 'Você não tem permissão para reatribuir cotações'
            }), 403
        
        novo_operador_id = data.get('operador_id')
        if not novo_operador_id:
            return jsonify({
                'success': False,
                'message': 'ID do operador é obrigatório'
            }), 400
        
        novo_operador = Usuario.query.get(novo_operador_id)
        if not novo_operador or novo_operador.tipo_usuario not in [TipoUsuario.OPERADOR, TipoUsuario.GERENTE, TipoUsuario.ADMINISTRADOR]:
            return jsonify({
                'success': False,
                'message': 'Operador inválido'
            }), 400
        
        cotacao.reatribuir(current_user, novo_operador)
        db.session.commit()
        
        # Registrar log de auditoria
        LogAuditoria.registrar_acao(
            usuario_id=current_user.id,
            acao='REATRIBUIR',
            recurso='COTACAO',
            detalhes=f'Cotação {cotacao.numero_cotacao} reatribuída para {novo_operador.nome_completo}'
        )
        
        return jsonify({
            'success': True,
            'message': 'Cotação reatribuída com sucesso',
            'cotacao': cotacao.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao reatribuir cotação: {str(e)}'
        }), 500

@cotacao_bp.route("/cotacoes/estatisticas", methods=["GET"])
@login_required
def obter_estatisticas():
    """Obtém estatísticas das cotações"""
    try:
        # Query base dependendo do tipo de usuário
        if current_user.tipo_usuario == TipoUsuario.CONSULTOR:
            base_query = Cotacao.query.filter(Cotacao.consultor_id == current_user.id)
        else:
            base_query = Cotacao.query
        
        # Estatísticas gerais
        total_cotacoes = base_query.count()
        
        # Por status
        stats_por_status = {}
        for status in StatusCotacao:
            count = base_query.filter(Cotacao.status == status).count()
            stats_por_status[status.value] = count
        
        # Por empresa de transporte
        stats_por_empresa = {}
        for empresa in EmpresaCotacao:
            count = base_query.filter(Cotacao.empresa_transporte == empresa).count()
            stats_por_empresa[empresa.value] = count
        
        # Estatísticas específicas para operadores/administradores
        stats_operadores = {}
        if current_user.tipo_usuario != TipoUsuario.CONSULTOR:
            # Cotações por operador
            operadores = Usuario.query.filter(
                Usuario.tipo_usuario.in_([TipoUsuario.OPERADOR, TipoUsuario.GERENTE, TipoUsuario.ADMINISTRADOR])
            ).all()
            
            for operador in operadores:
                count = Cotacao.query.filter(Cotacao.operador_id == operador.id).count()
                if count > 0:
                    stats_operadores[operador.nome_completo] = count
        
        return jsonify({
            'success': True,
            'estatisticas': {
                'total_cotacoes': total_cotacoes,
                'por_status': stats_por_status,
                'por_empresa': stats_por_empresa,
                'por_operador': stats_operadores
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        }), 500

@cotacao_bp.route("/operadores", methods=["GET"])
@login_required
def listar_operadores():
    """Lista operadores disponíveis (para reatribuição)"""
    try:
        # Verificar permissão
        if current_user.tipo_usuario not in [TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]:
            return jsonify({
                'success': False,
                'message': 'Acesso negado'
            }), 403
        
        operadores = Usuario.query.filter(
            Usuario.tipo_usuario.in_([TipoUsuario.OPERADOR, TipoUsuario.GERENTE, TipoUsuario.ADMINISTRADOR]),
            Usuario.ativo == True
        ).all()
        
        operadores_data = [{
            'id': op.id,
            'nome_completo': op.nome_completo,
            'username': op.username,
            'tipo_usuario': op.tipo_usuario.value
        } for op in operadores]
        
        return jsonify({
            'success': True,
            'operadores': operadores_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao listar operadores: {str(e)}'
        }), 500

