from flask import Blueprint, request, jsonify, send_file
from flask_cors import CORS
import json
from src.models.empresa import (
    db, Empresa, Regulamentacao, Certificacao, ModalidadeTransporte, 
    TipoCarga, AbrangenciaGeografica, Frota, Armazenagem, PortoTerminal,
    SeguroCobertura, Tecnologia, DesempenhoQualidade, ClienteSegmento,
    RecursoHumano, Sustentabilidade
)
from src.models.usuario import LogAuditoria
from datetime import datetime
from sqlalchemy import or_, and_
from flask_login import login_required, current_user

empresa_bp = Blueprint("empresa", __name__)
CORS(empresa_bp)

@empresa_bp.route("/empresas", methods=["GET"])
def get_empresas():
    """Listar todas as empresas com filtros opcionais"""
    try:
        # Parâmetros de filtro
        razao_social = request.args.get("razao_social")
        cnpj = request.args.get("cnpj")
        etiqueta = request.args.get("etiqueta")
        tipo_carga = request.args.get("tipo_carga")
        modalidade = request.args.get("modalidade")
        certificacao = request.args.get("certificacao")
        abrangencia = request.args.get("abrangencia")
        possui_armazem = request.args.get("possui_armazem")
        portos_atendidos = request.args.get("portos_atendidos")
        tipo_regulamentacao = request.args.get("tipo_regulamentacao")
        tipo_frota = request.args.get("tipo_frota")
        tipo_veiculo = request.args.get("tipo_veiculo")
        possui_seguro = request.args.get("possui_seguro")
        nome_tecnologia = request.args.get("nome_tecnologia")
        segmento_cliente = request.args.get("segmento_cliente")
        certificacao_ambiental = request.args.get("certificacao_ambiental")
        
        # Paginação
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        
        # Query base
        query = Empresa.query
        
        # Aplicar filtros
        if razao_social:
            query = query.filter(Empresa.razao_social.ilike(f"%{razao_social}%"))
        
        if cnpj:
            query = query.filter(Empresa.cnpj.like(f"%{cnpj}%"))
        
        if etiqueta:
            query = query.filter(Empresa.etiqueta == etiqueta)
        
        if tipo_carga:
            query = query.join(TipoCarga).filter(TipoCarga.tipo_carga.ilike(f"%{tipo_carga}%"))
        
        if modalidade:
            query = query.join(ModalidadeTransporte).filter(ModalidadeTransporte.modalidade.ilike(f"%{modalidade}%"))
        
        if certificacao:
            query = query.join(Certificacao).filter(Certificacao.nome_certificacao.ilike(f"%{certificacao}%"))
        
        if abrangencia:
            query = query.join(AbrangenciaGeografica).filter(
                or_(
                    AbrangenciaGeografica.tipo_abrangencia.ilike(f"%{abrangencia}%"),
                    AbrangenciaGeografica.detalhes.ilike(f"%{abrangencia}%")
                )
            )
        
        if possui_armazem:
            possui_armazem_bool = possui_armazem.lower() in ["true", "1", "sim"]
            query = query.join(Armazenagem).filter(Armazenagem.possui_armazem == possui_armazem_bool)
        
        if portos_atendidos:
            query = query.join(PortoTerminal).filter(PortoTerminal.nome_porto_terminal.ilike(f"%{portos_atendidos}%"))
        
        if tipo_regulamentacao:
            query = query.join(Regulamentacao).filter(Regulamentacao.tipo_regulamentacao.ilike(f"%{tipo_regulamentacao}%"))
        
        if tipo_frota:
            query = query.join(Frota).filter(Frota.tipo_frota.ilike(f"%{tipo_frota}%"))
        
        if tipo_veiculo:
            query = query.join(Frota).filter(Frota.tipo_veiculo.ilike(f"%{tipo_veiculo}%"))
        
        if possui_seguro:
            possui_seguro_bool = possui_seguro.lower() in ["true", "1", "sim"]
            if possui_seguro_bool:
                query = query.join(SeguroCobertura).filter(SeguroCobertura.tipo_seguro.isnot(None))
            else:
                # Empresas que não possuem nenhum registro de seguro
                query = query.outerjoin(SeguroCobertura).filter(SeguroCobertura.id.is_(None))
        
        if nome_tecnologia:
            query = query.join(Tecnologia).filter(Tecnologia.nome_tecnologia.ilike(f"%{nome_tecnologia}%"))
        
        if segmento_cliente:
            query = query.join(ClienteSegmento).filter(ClienteSegmento.segmento.ilike(f"%{segmento_cliente}%"))
        
        if certificacao_ambiental:
            query = query.join(Sustentabilidade).filter(Sustentabilidade.certificacao_ambiental.ilike(f"%{certificacao_ambiental}%"))
        # Executar query com paginação
        empresas = query.distinct().paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "empresas": [empresa.to_dict() for empresa in empresas.items],
            "total": empresas.total,
            "pages": empresas.pages,
            "current_page": page,
            "per_page": per_page
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@empresa_bp.route("/empresas/<int:empresa_id>", methods=["GET"])
def get_empresa(empresa_id):
    """Obter detalhes completos de uma empresa específica"""
    try:
        empresa = Empresa.query.get_or_404(empresa_id)
        return jsonify(empresa.to_dict_complete())
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@empresa_bp.route("/empresas", methods=["POST"])
@login_required
def create_empresa():
    """Criar uma nova empresa"""
    try:
        # Verificar permissão
        if not current_user.pode_acessar('criar_empresa'):
            return jsonify({"error": "Acesso negado"}), 403
            
        data = request.get_json()
        
        # Validar dados obrigatórios
        if not data.get("razao_social") or not data.get("cnpj"):
            return jsonify({"error": "Razão social e CNPJ são obrigatórios"}), 400
        
        # Verificar se CNPJ já existe
        if Empresa.query.filter_by(cnpj=data["cnpj"]).first():
            return jsonify({"error": "CNPJ já cadastrado"}), 400
        
        # Criar empresa
        empresa = Empresa(
            razao_social=data["razao_social"],
            nome_fantasia=data.get("nome_fantasia"),
            cnpj=data["cnpj"],
            inscricao_estadual=data.get("inscricao_estadual"),
            endereco_completo=data.get("endereco_completo"),
            telefone_comercial=data.get("telefone_comercial"),
            telefone_emergencial=data.get("telefone_emergencial"),
            email=data.get("email"),
            website=data.get("website"),
            link_cotacao=data.get("link_cotacao"),
            observacoes=data.get("observacoes"),
            etiqueta=data.get("etiqueta", "CADASTRADA"),
            data_fundacao=datetime.strptime(data["data_fundacao"], "%Y-%m-%d").date() if data.get("data_fundacao") else None
        )
        
        db.session.add(empresa)
        db.session.flush()  # Para obter o ID da empresa
        
        _add_related_data(empresa, data)        
        db.session.commit()
        
        # Registrar log de auditoria
        LogAuditoria.registrar_acao(
            usuario_id=current_user.id,
            acao='CRIAR_EMPRESA',
            recurso='EMPRESAS',
            detalhes=f'Empresa criada: {empresa.razao_social} (CNPJ: {empresa.cnpj})',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify(empresa.to_dict_complete()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



@empresa_bp.route("/empresas/<int:empresa_id>", methods=["PUT"])
@login_required
def update_empresa(empresa_id):
    """Atualizar empresa – sem apagar dados existentes"""
    try:
        # Verificar permissão
        if not current_user.pode_acessar('editar_empresa'):
            return jsonify({"error": "Acesso negado"}), 403
            
        empresa = Empresa.query.get_or_404(empresa_id)
        data = request.get_json()
        
        # Guardar dados originais para o log
        dados_originais = {
            'razao_social': empresa.razao_social,
            'cnpj': empresa.cnpj,
            'etiqueta': empresa.etiqueta
        }

        # ---------- campos simples ----------
        simple = [
            "razao_social", "nome_fantasia", "cnpj", "inscricao_estadual",
            "endereco_completo", "telefone_comercial", "telefone_emergencial",
            "email", "website", "link_cotacao", "observacoes", "etiqueta"
        ]
        for campo in simple:
            if campo in data:
                setattr(empresa, campo, data[campo])

        if "data_fundacao" in data:
            empresa.data_fundacao = (
                datetime.strptime(data["data_fundacao"], "%Y-%m-%d").date()
                if data["data_fundacao"] else None
            )

        empresa.updated_at = datetime.utcnow()

        # ---------- relacionamentos ----------
        if "portos_terminais" in data:
            _update_portos_terminais(empresa, data["portos_terminais"])
        if "regulamentacoes" in data:
            _update_regulamentacoes(empresa, data["regulamentacoes"])
        if "certificacoes" in data:
            _update_certificacoes(empresa, data["certificacoes"])
        if "modalidades_transporte" in data:
            _update_modalidades(empresa, data["modalidades_transporte"])
        if "tipos_carga" in data:
            _update_tipos_carga(empresa, data["tipos_carga"])
        if "abrangencia_geografica" in data:
            _update_abrangencia(empresa, data["abrangencia_geografica"])
        if "frota" in data:
            _update_frota(empresa, data["frota"])
        if "armazenagem" in data:
            _update_armazenagem(empresa, data["armazenagem"])
        if "seguros_coberturas" in data:
            _update_seguros(empresa, data["seguros_coberturas"])
        if "tecnologias" in data:
            _update_tecnologias(empresa, data["tecnologias"])
        if "desempenho_qualidade" in data:
            _update_desempenho(empresa, data["desempenho_qualidade"])
        if "clientes_segmentos" in data:
            _update_clientes(empresa, data["clientes_segmentos"])
        if "recursos_humanos" in data:
            _update_recursos(empresa, data["recursos_humanos"])
        if "sustentabilidade" in data:
            _update_sustentabilidade(empresa, data["sustentabilidade"])

        db.session.commit()
        
        # Registrar log de auditoria
        alteracoes = []
        if dados_originais['razao_social'] != empresa.razao_social:
            alteracoes.append(f"Razão Social: '{dados_originais['razao_social']}' → '{empresa.razao_social}'")
        if dados_originais['etiqueta'] != empresa.etiqueta:
            alteracoes.append(f"Etiqueta: '{dados_originais['etiqueta']}' → '{empresa.etiqueta}'")
        
        detalhes = f"Empresa editada: {empresa.razao_social}"
        if alteracoes:
            detalhes += f" - Alterações: {'; '.join(alteracoes)}"
        
        LogAuditoria.registrar_acao(
            usuario_id=current_user.id,
            acao='EDITAR_EMPRESA',
            recurso='EMPRESAS',
            detalhes=detalhes,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify(empresa.to_dict_complete())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500





@empresa_bp.route("/empresas/<int:empresa_id>", methods=["DELETE"])
@login_required
def delete_empresa(empresa_id):
    """Excluir uma empresa"""
    try:
        # Verificar permissão
        if not current_user.pode_acessar('excluir_empresa'):
            return jsonify({"error": "Acesso negado"}), 403
            
        empresa = Empresa.query.get_or_404(empresa_id)
        
        # Guardar dados para o log antes de excluir
        razao_social = empresa.razao_social
        cnpj = empresa.cnpj
        
        db.session.delete(empresa)
        db.session.commit()
        
        # Registrar log de auditoria
        LogAuditoria.registrar_acao(
            usuario_id=current_user.id,
            acao='EXCLUIR_EMPRESA',
            recurso='EMPRESAS',
            detalhes=f'Empresa excluída: {razao_social} (CNPJ: {cnpj})',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({"message": "Empresa excluída com sucesso"})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@empresa_bp.route("/empresas/search", methods=["POST"])
def search_empresas():
    """Busca avançada de empresas com múltiplos critérios"""
    try:
        data = request.get_json()
        
        # Query base
        query = Empresa.query
        
        # Filtros de texto
        if data.get("razao_social"):
            query = query.filter(Empresa.razao_social.ilike(f"%{data['razao_social']}%"))
        
        if data.get("cnpj"):
            query = query.filter(Empresa.cnpj.like(f"%{data['cnpj']}%"))
        
        # Filtros por relacionamentos
        if data.get("tipos_carga"):
            tipos_carga = data["tipos_carga"] if isinstance(data["tipos_carga"], list) else [data["tipos_carga"]]
            query = query.join(TipoCarga).filter(TipoCarga.tipo_carga.in_(tipos_carga))
        
        if data.get("modalidades"):
            modalidades = data["modalidades"] if isinstance(data["modalidades"], list) else [data["modalidades"]]
            query = query.join(ModalidadeTransporte).filter(ModalidadeTransporte.modalidade.in_(modalidades))
        
        if data.get("certificacoes"):
            certificacoes = data["certificacoes"] if isinstance(data["certificacoes"], list) else [data["certificacoes"]]
            query = query.join(Certificacao).filter(Certificacao.nome_certificacao.in_(certificacoes))
        
        if data.get("regioes"):
            regioes = data["regioes"] if isinstance(data["regioes"], list) else [data["regioes"]]
            conditions = []
            for regiao in regioes:
                conditions.append(AbrangenciaGeografica.tipo_abrangencia.ilike(f"%{regiao}%"))
                conditions.append(AbrangenciaGeografica.detalhes.ilike(f"%{regiao}%"))
            query = query.join(AbrangenciaGeografica).filter(or_(*conditions))
        
        if data.get("possui_armazem") is not None:
            query = query.join(Armazenagem).filter(Armazenagem.possui_armazem == data["possui_armazem"])
        
        # Paginação
        page = data.get("page", 1)
        per_page = data.get("per_page", 10)
        
        empresas = query.distinct().paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "empresas": [empresa.to_dict() for empresa in empresas.items],
            "total": empresas.total,
            "pages": empresas.pages,
            "current_page": page,
            "per_page": per_page
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _update_regulamentacoes(empresa, regulamentacoes_data):
    # Limpar regulamentações existentes
    Regulamentacao.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novas regulamentações
    if regulamentacoes_data:
        for reg_data in regulamentacoes_data:
            regulamentacao = Regulamentacao(
                empresa_id=empresa.id,
                tipo_regulamentacao=reg_data.get("tipo_regulamentacao"),
                numero_registro=reg_data.get("numero_registro"),
                data_emissao=datetime.strptime(reg_data["data_emissao"], "%Y-%m-%d").date() if reg_data.get("data_emissao") else None,
                data_validade=datetime.strptime(reg_data["data_validade"], "%Y-%m-%d").date() if reg_data.get("data_validade") else None,
                orgao_emissor=reg_data.get("orgao_emissor")
            )
            db.session.add(regulamentacao)

def _update_certificacoes(empresa, certificacoes_data):
    # Limpar certificações existentes
    Certificacao.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novas certificações
    if certificacoes_data:
        for cert_data in certificacoes_data:
            certificacao = Certificacao(
                empresa_id=empresa.id,
                nome_certificacao=cert_data.get("nome_certificacao"),
                numero_certificacao=cert_data.get("numero_certificacao"),
                data_emissao=datetime.strptime(cert_data["data_emissao"], "%Y-%m-%d").date() if cert_data.get("data_emissao") else None,
                data_validade=datetime.strptime(cert_data["data_validade"], "%Y-%m-%d").date() if cert_data.get("data_validade") else None,
                orgao_certificador=cert_data.get("orgao_certificador")
            )
            db.session.add(certificacao)

def _update_modalidades(empresa, modalidades_data):
    # Limpar modalidades existentes
    ModalidadeTransporte.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novas modalidades
    if modalidades_data:
        for modalidade_item in modalidades_data:
            modal = ModalidadeTransporte(
                empresa_id=empresa.id,
                modalidade=modalidade_item.get("modalidade") if isinstance(modalidade_item, dict) else modalidade_item
            )
            db.session.add(modal)
    
def _update_tipos_carga(empresa, tipos_carga_data):
    # Limpar tipos de carga existentes
    TipoCarga.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novos tipos de carga
    if tipos_carga_data:
        for tipo_item in tipos_carga_data:
            tipo_carga = TipoCarga(
                empresa_id=empresa.id,
                tipo_carga=tipo_item.get("tipo_carga") if isinstance(tipo_item, dict) else tipo_item
            )
            db.session.add(tipo_carga)
    
def _update_abrangencia(empresa, abrangencia_data):
    # Limpar abrangências existentes
    AbrangenciaGeografica.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novas abrangências
    if abrangencia_data:
        for abr_item in abrangencia_data:
            abrangencia = AbrangenciaGeografica(
                empresa_id=empresa.id,
                tipo_abrangencia=abr_item.get("tipo_abrangencia"),
                detalhes=abr_item.get("detalhes")
            )
            db.session.add(abrangencia)
    
def _update_frota(empresa, frota_data):
    # Limpar frota existente
    Frota.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar nova frota
    if frota_data:
        for frota_item in frota_data:
            frota = Frota(
                empresa_id=empresa.id,
                tipo_frota=frota_item.get("tipo_frota"),
                quantidade=frota_item.get("quantidade"),
                tipo_veiculo=frota_item.get("tipo_veiculo"),
                tipo_carroceria=frota_item.get("tipo_carroceria"),
                capacidade=frota_item.get("capacidade"),
                ano_medio=frota_item.get("ano_medio")
            )
            db.session.add(frota)

def _update_armazenagem(empresa, armazenagem_data):
    # Limpar armazenagens existentes
    Armazenagem.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novas armazenagens
    if armazenagem_data:
        for arm_item in armazenagem_data:
            armazenagem = Armazenagem(
                empresa_id=empresa.id,
                possui_armazem=arm_item.get("possui_armazem"),
                localizacao=arm_item.get("localizacao"),
                capacidade_m2=arm_item.get("capacidade_m2"),
                capacidade_m3=arm_item.get("capacidade_m3"),
                tipos_armazenagem=arm_item.get("tipos_armazenagem"),
                servicos_oferecidos=arm_item.get("servicos_oferecidos")
            )
            db.session.add(armazenagem)

def _update_portos_terminais(empresa, portos_data):
    # Limpar portos/terminais existentes
    PortoTerminal.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novos portos/terminais (eliminando duplicatas)
    if portos_data:
        # Usar set para eliminar duplicatas
        portos_unicos = set()
        for porto_data in portos_data:
            nome_porto = porto_data.get("nome_porto_terminal")
            tipo_terminal = porto_data.get("tipo_terminal")
            if nome_porto and tipo_terminal:
                chave = f"{nome_porto}|{tipo_terminal}"
                portos_unicos.add(chave)
        
        # Adicionar apenas portos únicos
        for chave in portos_unicos:
            nome_porto, tipo_terminal = chave.split('|')
            porto = PortoTerminal(
                empresa_id=empresa.id,
                nome_porto_terminal=nome_porto,
                tipo_terminal=tipo_terminal
            )
            db.session.add(porto)

def _update_seguros(empresa, seguros_data):
    # Limpar seguros existentes
    SeguroCobertura.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novos seguros
    if seguros_data:
        for seg_item in seguros_data:
            # Processar data de validade se fornecida
            data_validade = None
            if seg_item.get("data_validade"):
                try:
                    data_validade = datetime.strptime(seg_item.get("data_validade"), '%Y-%m-%d').date()
                except ValueError:
                    pass  # Manter como None se a data for inválida
            
            seguro = SeguroCobertura(
                empresa_id=empresa.id,
                tipo_seguro=seg_item.get("tipo_seguro"),
                valor_cobertura=seg_item.get("valor_cobertura"),
                seguradora=seg_item.get("seguradora"),
                data_validade=data_validade
            )
            db.session.add(seguro)

def _update_tecnologias(empresa, tecnologias_data):
    # Limpar tecnologias existentes
    Tecnologia.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novas tecnologias
    if tecnologias_data:
        for tec_item in tecnologias_data:
            tecnologia = Tecnologia(
                empresa_id=empresa.id,
                nome_tecnologia=tec_item.get("nome_tecnologia"),
                detalhes=tec_item.get("detalhes"),
            )
            db.session.add(tecnologia)

def _update_desempenho(empresa, desempenho_data):
    # Limpar desempenho existente
    DesempenhoQualidade.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novo desempenho
    if desempenho_data:
        for desemp_item in desempenho_data:
            desempenho = DesempenhoQualidade(
                empresa_id=empresa.id,

                prazo_medio_atendimento=desemp_item.get("prazo_medio_atendimento"),
                unidade_prazo=desemp_item.get("unidade_prazo"),
                indice_avarias_extravios=desemp_item.get("indice_avarias_extravios"),
                indice_entregas_prazo=desemp_item.get("indice_entregas_prazo")
            )
            db.session.add(desempenho)

def _update_clientes(empresa, clientes_data):
    # Limpar clientes existentes
    ClienteSegmento.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novos clientes
    if clientes_data:
        for cli_item in clientes_data:
            cliente = ClienteSegmento(
                empresa_id=empresa.id,
                segmento=cli_item.get("segmento"),

                principais_clientes=cli_item.get("principais_clientes")
            )
            db.session.add(cliente)

def _update_recursos(empresa, recursos_data):
    # Limpar recursos existentes
    RecursoHumano.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar novos recursos
    if recursos_data:
        for rec_item in recursos_data:
            recurso = RecursoHumano(
                empresa_id=empresa.id,
                total_funcionarios=rec_item.get("total_funcionarios"),
                funcionarios_operacionais=rec_item.get("funcionarios_operacionais"),
                funcionarios_administrativos=rec_item.get("funcionarios_administrativos"),
                terceirizados=rec_item.get("terceirizados"),
                programas_treinamento=rec_item.get("programas_treinamento")
            )
            db.session.add(recurso)

def _update_sustentabilidade(empresa, sustentabilidade_data):
    # Limpar sustentabilidade existente
    Sustentabilidade.query.filter_by(empresa_id=empresa.id).delete()
    # Adicionar nova sustentabilidade
    if sustentabilidade_data:
        for sust_item in sustentabilidade_data:
            sustentabilidade = Sustentabilidade(
                empresa_id=empresa.id,
                certificacao_ambiental=sust_item.get("certificacao_ambiental"),
                programas_reducao_emissoes=sust_item.get("programas_reducao_emissoes")
            )
            db.session.add(sustentabilidade)

def _add_related_data(empresa, data):
    """Função auxiliar para adicionar dados relacionados durante a criação"""
    if data.get("portos_terminais"):
        _update_portos_terminais(empresa, data["portos_terminais"])
    if data.get("regulamentacoes"):
        _update_regulamentacoes(empresa, data["regulamentacoes"])
    if data.get("certificacoes"):
        _update_certificacoes(empresa, data["certificacoes"])
    if data.get("modalidades_transporte"):
        _update_modalidades(empresa, data["modalidades_transporte"])
    if data.get("tipos_carga"):
        _update_tipos_carga(empresa, data["tipos_carga"])
    if data.get("abrangencia_geografica"):
        _update_abrangencia(empresa, data["abrangencia_geografica"])
    if data.get("frota"):
        _update_frota(empresa, data["frota"])
    if data.get("armazenagem"):
        _update_armazenagem(empresa, data["armazenagem"])
    if data.get("seguros_coberturas"):
        _update_seguros(empresa, data["seguros_coberturas"])
    if data.get("tecnologias"):
        _update_tecnologias(empresa, data["tecnologias"])
    if data.get("desempenho_qualidade"):
        _update_desempenho(empresa, data["desempenho_qualidade"])
    if data.get("clientes_segmentos"):
        _update_clientes(empresa, data["clientes_segmentos"])
    if data.get("recursos_humanos"):
        _update_recursos(empresa, data["recursos_humanos"])
    if data.get("sustentabilidade"):
        _update_sustentabilidade(empresa, data["sustentabilidade"])



@empresa_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Retorna dados analytics para o dashboard"""
    try:
        # Buscar todas as empresas
        empresas = Empresa.query.all()
        
        if not empresas:
            # Retornar dados de exemplo se não houver empresas
            return jsonify({
                'empresasPorRegiao': [
                    {'regiao': 'Não Informado', 'empresas': 0, 'porcentagem': 0},
                    {'regiao': 'Sudeste', 'empresas': 0, 'porcentagem': 0},
                    {'regiao': 'Sul', 'empresas': 0, 'porcentagem': 0},
                    {'regiao': 'Nordeste', 'empresas': 0, 'porcentagem': 0},
                    {'regiao': 'Centro-Oeste', 'empresas': 0, 'porcentagem': 0},
                    {'regiao': 'Norte', 'empresas': 0, 'porcentagem': 0}
                ],
                'tiposCarga': [],
                'crescimentoMensal': [],
                'certificacoes': [],
                'metricas_detalhadas': [
                    {'metrica': 'Total de Empresas', 'valor': 0},
                    {'metrica': 'Empresas Certificadas', 'valor': 0},
                    {'metrica': 'Empresas com Armazém', 'valor': 0},
                    {'metrica': 'Abrangência Nacional', 'valor': 0}
                ]
            })
        
        # Análise por região
        regioes_count = {}
        for empresa in empresas:
            endereco = empresa.endereco_completo if empresa.endereco_completo else 'Não informado'
            regiao = extrair_regiao_do_endereco(endereco)
            regioes_count[regiao] = regioes_count.get(regiao, 0) + 1
        
        total_empresas = len(empresas)
        empresas_por_regiao = []
        for regiao, count in regioes_count.items():
            porcentagem = round((count / total_empresas) * 100, 1)
            empresas_por_regiao.append({
                'regiao': regiao,
                'empresas': count,
                'porcentagem': porcentagem
            })
        
        # Análise de tipos de carga
        tipos_carga_count = {}
        for empresa in empresas:
            for tipo_carga in empresa.tipos_carga:
                tipo = tipo_carga.tipo_carga if tipo_carga.tipo_carga else 'Não informado'
                tipos_carga_count[tipo] = tipos_carga_count.get(tipo, 0) + 1
        
        tipos_carga = []
        for tipo, count in sorted(tipos_carga_count.items(), key=lambda x: x[1], reverse=True)[:6]:
            tipos_carga.append({
                'tipo': tipo,
                'quantidade': count
            })
        
        # Análise de certificações
        certificacoes_count = {}
        for empresa in empresas:
            for certificacao in empresa.certificacoes:
                nome = certificacao.nome_certificacao if certificacao.nome_certificacao else 'Não informado'
                certificacoes_count[nome] = certificacoes_count.get(nome, 0) + 1
        
        certificacoes = []
        for cert, count in sorted(certificacoes_count.items(), key=lambda x: x[1], reverse=True)[:6]:
            certificacoes.append({
                'certificacao': cert,
                'quantidade': count
            })
        
        # Crescimento mensal (simulado baseado no número atual de empresas)
        import datetime
        hoje = datetime.date.today()
        crescimento_mensal = []
        
        for i in range(6):
            mes_data = hoje.replace(day=1) - datetime.timedelta(days=30*i)
            mes_nome = mes_data.strftime('%b')
            # Simular crescimento gradual
            empresas_no_mes = max(1, total_empresas - (5-i) * 2)
            crescimento_mensal.insert(0, {
                'mes': mes_nome,
                'empresas': empresas_no_mes
            })
        
        # Métricas detalhadas para a tabela
        empresas_certificadas = len(set(empresa.id for empresa in empresas for cert in empresa.certificacoes))
        empresas_com_armazem = len([empresa for empresa in empresas for arm in empresa.armazenagem if arm.possui_armazem])
        empresas_abrangencia_nacional = len([empresa for empresa in empresas for abr in empresa.abrangencia_geografica if 'nacional' in abr.tipo_abrangencia.lower()])
        
        metricas_detalhadas = [
            {'metrica': 'Total de Empresas', 'valor': total_empresas},
            {'metrica': 'Empresas Certificadas', 'valor': empresas_certificadas},
            {'metrica': 'Empresas com Armazém', 'valor': empresas_com_armazem},
            {'metrica': 'Abrangência Nacional', 'valor': empresas_abrangencia_nacional}
        ]
        
        return jsonify({
            'empresasPorRegiao': empresas_por_regiao,
            'tiposCarga': tipos_carga,
            'crescimentoMensal': crescimento_mensal,
            'certificacoes': certificacoes,
            'metricas_detalhadas': metricas_detalhadas
        })
        
    except Exception as e:
        print(f"Erro ao gerar analytics: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

def extrair_regiao_do_endereco(endereco):
    """Extrai a região do endereço completo baseado em palavras-chave"""
    if not endereco or endereco == 'Não informado' or endereco.strip() == '':
        return 'Não Informado'
    
    endereco_upper = endereco.upper()
    
    # Mapeamento de estados e cidades para regiões
    regioes_keywords = {
        'Sudeste': ['SP', 'SÃO PAULO', 'RJ', 'RIO DE JANEIRO', 'MG', 'MINAS GERAIS', 'BELO HORIZONTE', 'ES', 'ESPÍRITO SANTO', 'VITÓRIA'],
        'Sul': ['RS', 'RIO GRANDE DO SUL', 'PORTO ALEGRE', 'SC', 'SANTA CATARINA', 'FLORIANÓPOLIS', 'PR', 'PARANÁ', 'CURITIBA'],
        'Nordeste': ['BA', 'BAHIA', 'SALVADOR', 'PE', 'PERNAMBUCO', 'RECIFE', 'CE', 'CEARÁ', 'FORTALEZA', 'PB', 'PARAÍBA', 'JOÃO PESSOA', 'RN', 'RIO GRANDE DO NORTE', 'NATAL', 'AL', 'ALAGOAS', 'MACEIÓ', 'SE', 'SERGIPE', 'ARACAJU', 'MA', 'MARANHÃO', 'SÃO LUÍS', 'PI', 'PIAUÍ', 'TERESINA'],
        'Centro-Oeste': ['MT', 'MATO GROSSO', 'CUIABÁ', 'MS', 'MATO GROSSO DO SUL', 'CAMPO GRANDE', 'GO', 'GOIÁS', 'GOIÂNIA', 'DF', 'DISTRITO FEDERAL', 'BRASÍLIA'],
        'Norte': ['AM', 'AMAZONAS', 'MANAUS', 'PA', 'PARÁ', 'BELÉM', 'AC', 'ACRE', 'RIO BRANCO', 'RR', 'RORAIMA', 'BOA VISTA', 'RO', 'RONDÔNIA', 'PORTO VELHO', 'AP', 'AMAPÁ', 'MACAPÁ', 'TO', 'TOCANTINS', 'PALMAS']
    }
    
    for regiao, keywords in regioes_keywords.items():
        for keyword in keywords:
            if keyword in endereco_upper:
                return regiao
    
    return 'Não Informado'

def mapear_estado_para_regiao(estado):
    """Mapeia estado brasileiro para região"""
    if not estado or estado.strip() == '':
        return 'Não Informado'
        
    regioes = {
        'Sudeste': ['SP', 'RJ', 'MG', 'ES', 'São Paulo', 'Rio de Janeiro', 'Minas Gerais', 'Espírito Santo'],
        'Sul': ['RS', 'SC', 'PR', 'Rio Grande do Sul', 'Santa Catarina', 'Paraná'],
        'Nordeste': ['BA', 'PE', 'CE', 'PB', 'RN', 'AL', 'SE', 'MA', 'PI', 'Bahia', 'Pernambuco', 'Ceará', 'Paraíba', 'Rio Grande do Norte', 'Alagoas', 'Sergipe', 'Maranhão', 'Piauí'],
        'Centro-Oeste': ['MT', 'MS', 'GO', 'DF', 'Mato Grosso', 'Mato Grosso do Sul', 'Goiás', 'Distrito Federal'],
        'Norte': ['AM', 'PA', 'AC', 'RR', 'RO', 'AP', 'TO', 'Amazonas', 'Pará', 'Acre', 'Roraima', 'Rondônia', 'Amapá', 'Tocantins']
    }
    
    for regiao, estados in regioes.items():
        if estado in estados:
            return regiao
    
    return 'Não Informado'

@empresa_bp.route('/metricas-avancadas', methods=['GET'])
def get_metricas_avancadas():
    """Retorna métricas avançadas para relatórios"""
    try:
        empresas = Empresa.query.all()
        total_empresas = len(empresas)
        
        if total_empresas == 0:
            return jsonify({
                'total_empresas': 0,
                'empresas_certificadas': 0,
                'cobertura_nacional': 0,
                'empresas_armazenagem': 0,
                'diversificacao_carga': 0,
                'taxa_crescimento': 0
            })
        
        # Calcular métricas
        empresas_certificadas = sum(1 for e in empresas if len(e.certificacoes) > 0)
        taxa_certificacao = round((empresas_certificadas / total_empresas) * 100, 1)
        
        # Estados únicos cobertos
        estados_cobertos = set()
        for empresa in empresas:
            if empresa.endereco_estado:
                estados_cobertos.add(empresa.endereco_estado)
        cobertura_nacional = round((len(estados_cobertos) / 27) * 100, 1)  # 26 estados + DF
        
        # Empresas com armazenagem
        empresas_armazenagem = sum(1 for e in empresas if any(s.possui_armazenagem for s in e.servicos))
        taxa_armazenagem = round((empresas_armazenagem / total_empresas) * 100, 1)
        
        # Diversificação de carga (média de tipos de carga por empresa)
        total_tipos_carga = sum(len(set(s.tipo_carga for s in e.servicos if s.tipo_carga)) for e in empresas)
        diversificacao = round(total_tipos_carga / total_empresas, 1) if total_empresas > 0 else 0
        
        return jsonify({
            'total_empresas': total_empresas,
            'taxa_certificacao': taxa_certificacao,
            'cobertura_nacional': cobertura_nacional,
            'taxa_armazenagem': taxa_armazenagem,
            'diversificacao_carga': diversificacao,
            'empresas_certificadas': empresas_certificadas,
            'empresas_armazenagem': empresas_armazenagem,
            'estados_cobertos': len(estados_cobertos)
        })
        
    except Exception as e:
        print(f"Erro ao calcular métricas avançadas: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500






@empresa_bp.route("/empresas/export", methods=["GET"])
def export_empresas():
    """Exportar todos os dados das empresas em formato JSON"""
    try:
        # Buscar todas as empresas com dados completos
        empresas = Empresa.query.all()
        
        # Preparar dados para exportação
        export_data = {
            "metadata": {
                "export_date": datetime.utcnow().isoformat(),
                "total_empresas": len(empresas),
                "version": "1.0"
            },
            "empresas": [empresa.to_dict_complete() for empresa in empresas]
        }
        
        # Retornar dados como JSON para download
        response = jsonify(export_data)
        response.headers["Content-Disposition"] = f"attachment; filename=brccsis_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        response.headers["Content-Type"] = "application/json"
        
        return response
    
    except Exception as e:
        return jsonify({"error": f"Erro ao exportar dados: {str(e)}"}), 500


@empresa_bp.route("/empresas/import", methods=["POST"])
@login_required
def import_empresas():
    """Importar dados das empresas a partir de arquivo JSON"""
    try:
        # Verificar se foi enviado um arquivo
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo foi enviado"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
        # Verificar se é um arquivo JSON
        if not file.filename.lower().endswith('.json'):
            return jsonify({"error": "Arquivo deve ser do tipo JSON"}), 400
        
        # Ler e processar o arquivo JSON
        try:
            import_data = json.loads(file.read().decode('utf-8'))
        except json.JSONDecodeError:
            return jsonify({"error": "Arquivo JSON inválido"}), 400
        
        # Validar estrutura do arquivo
        if 'empresas' not in import_data:
            return jsonify({"error": "Estrutura do arquivo inválida. Campo 'empresas' não encontrado"}), 400
        
        empresas_data = import_data['empresas']
        if not isinstance(empresas_data, list):
            return jsonify({"error": "Campo 'empresas' deve ser uma lista"}), 400
        
        # Estatísticas da importação
        stats = {
            "total_processadas": 0,
            "criadas": 0,
            "atualizadas": 0,
            "erros": 0,
            "detalhes_erros": []
        }
        
        # Processar cada empresa
        for empresa_data in empresas_data:
            try:
                stats["total_processadas"] += 1
                
                # Verificar se empresa já existe (por CNPJ)
                cnpj = empresa_data.get('cnpj')
                if not cnpj:
                    stats["erros"] += 1
                    stats["detalhes_erros"].append(f"Empresa sem CNPJ: {empresa_data.get('razao_social', 'N/A')}")
                    continue
                
                empresa_existente = Empresa.query.filter_by(cnpj=cnpj).first()
                
                if empresa_existente:
                    # Atualizar empresa existente
                    _update_empresa_from_import(empresa_existente, empresa_data)
                    stats["atualizadas"] += 1
                else:
                    # Criar nova empresa
                    _create_empresa_from_import(empresa_data)
                    stats["criadas"] += 1
                
            except Exception as e:
                stats["erros"] += 1
                stats["detalhes_erros"].append(f"Erro ao processar empresa {empresa_data.get('razao_social', 'N/A')}: {str(e)}")
                continue
        
        # Confirmar transação
        db.session.commit()
        
        return jsonify({
            "message": "Importação concluída com sucesso",
            "estatisticas": stats
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro durante a importação: {str(e)}"}), 500


def _create_empresa_from_import(empresa_data):
    """Criar nova empresa a partir dos dados de importação"""
    # Criar empresa principal
    empresa = Empresa(
        razao_social=empresa_data.get("razao_social"),
        nome_fantasia=empresa_data.get("nome_fantasia"),
        cnpj=empresa_data.get("cnpj"),
        inscricao_estadual=empresa_data.get("inscricao_estadual"),
        endereco_completo=empresa_data.get("endereco_completo"),
        telefone_comercial=empresa_data.get("telefone_comercial"),
        telefone_emergencial=empresa_data.get("telefone_emergencial"),
        email=empresa_data.get("email"),
        website=empresa_data.get("website"),
        etiqueta=empresa_data.get("etiqueta", "CADASTRADA"),
        data_fundacao=datetime.strptime(empresa_data["data_fundacao"], "%Y-%m-%d").date() if empresa_data.get("data_fundacao") else None
    )
    
    db.session.add(empresa)
    db.session.flush()  # Para obter o ID da empresa
    
    # Adicionar dados relacionados
    _add_related_data(empresa, empresa_data)


def _update_empresa_from_import(empresa, empresa_data):
    """Atualizar empresa existente com dados de importação"""
    # Atualizar campos básicos
    empresa.razao_social = empresa_data.get("razao_social", empresa.razao_social)
    empresa.nome_fantasia = empresa_data.get("nome_fantasia", empresa.nome_fantasia)
    empresa.inscricao_estadual = empresa_data.get("inscricao_estadual", empresa.inscricao_estadual)
    empresa.endereco_completo = empresa_data.get("endereco_completo", empresa.endereco_completo)
    empresa.telefone_comercial = empresa_data.get("telefone_comercial", empresa.telefone_comercial)
    empresa.telefone_emergencial = empresa_data.get("telefone_emergencial", empresa.telefone_emergencial)
    empresa.email = empresa_data.get("email", empresa.email)
    empresa.website = empresa_data.get("website", empresa.website)
    empresa.etiqueta = empresa_data.get("etiqueta", empresa.etiqueta)
    empresa.updated_at = datetime.utcnow()
    
    if empresa_data.get("data_fundacao"):
        empresa.data_fundacao = datetime.strptime(empresa_data["data_fundacao"], "%Y-%m-%d").date()
    
    # Atualizar dados relacionados (substituindo os existentes)
    _clear_related_data(empresa)
    _add_related_data(empresa, empresa_data)


def _clear_related_data(empresa):
    """Limpar todos os dados relacionados de uma empresa"""
    Regulamentacao.query.filter_by(empresa_id=empresa.id).delete()
    Certificacao.query.filter_by(empresa_id=empresa.id).delete()
    ModalidadeTransporte.query.filter_by(empresa_id=empresa.id).delete()
    TipoCarga.query.filter_by(empresa_id=empresa.id).delete()
    AbrangenciaGeografica.query.filter_by(empresa_id=empresa.id).delete()
    Frota.query.filter_by(empresa_id=empresa.id).delete()
    Armazenagem.query.filter_by(empresa_id=empresa.id).delete()
    PortoTerminal.query.filter_by(empresa_id=empresa.id).delete()
    SeguroCobertura.query.filter_by(empresa_id=empresa.id).delete()
    Tecnologia.query.filter_by(empresa_id=empresa.id).delete()
    DesempenhoQualidade.query.filter_by(empresa_id=empresa.id).delete()
    ClienteSegmento.query.filter_by(empresa_id=empresa.id).delete()
    RecursoHumano.query.filter_by(empresa_id=empresa.id).delete()
    Sustentabilidade.query.filter_by(empresa_id=empresa.id).delete()



@empresa_bp.route("/empresas/import-excel", methods=["POST"])
def import_empresas_excel():
    """Importar dados das empresas a partir de arquivo Excel"""
    try:
        # Verificar se foi enviado um arquivo
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo foi enviado"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nenhum arquivo selecionado"}), 400
        
        # Verificar se é um arquivo Excel
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({"error": "Arquivo deve ser do tipo Excel (.xlsx ou .xls)"}), 400
        
        # Importar pandas e openpyxl para processar Excel
        try:
            import pandas as pd
        except ImportError:
            return jsonify({"error": "Biblioteca pandas não está instalada"}), 500
        
        # Ler o arquivo Excel
        try:
            excel_data = pd.read_excel(file, sheet_name=None)  # Lê todas as abas
        except Exception as e:
            return jsonify({"error": f"Erro ao ler arquivo Excel: {str(e)}"}), 400
        
        # Verificar se existe a aba "Empresas"
        if 'Empresas' not in excel_data:
            return jsonify({"error": "Aba 'Empresas' não encontrada no arquivo Excel"}), 400
        
        # Estatísticas da importação
        stats = {
            "total_processadas": 0,
            "criadas": 0,
            "atualizadas": 0,
            "erros": 0,
            "detalhes_erros": []
        }
        
        # Processar aba de empresas
        empresas_df = excel_data['Empresas']
        
        # Validar colunas obrigatórias
        colunas_obrigatorias = ['razao_social', 'cnpj']
        for coluna in colunas_obrigatorias:
            if coluna not in empresas_df.columns:
                return jsonify({"error": f"Coluna obrigatória '{coluna}' não encontrada na aba Empresas"}), 400
        
        # Processar cada empresa
        for index, row in empresas_df.iterrows():
            try:
                stats["total_processadas"] += 1
                
                # Limpar e validar CNPJ
                cnpj = str(row['cnpj']).strip()
                if pd.isna(row['cnpj']) or cnpj == '' or cnpj == 'nan':
                    stats["erros"] += 1
                    stats["detalhes_erros"].append(f"Linha {index + 2}: CNPJ vazio ou inválido")
                    continue
                
                # Remover formatação do CNPJ
                cnpj = ''.join(filter(str.isdigit, cnpj))
                if len(cnpj) != 14:
                    stats["erros"] += 1
                    stats["detalhes_erros"].append(f"Linha {index + 2}: CNPJ deve ter 14 dígitos")
                    continue
                
                # Verificar se empresa já existe
                empresa_existente = Empresa.query.filter_by(cnpj=cnpj).first()
                
                # Preparar dados da empresa
                empresa_data = {
                    'razao_social': str(row['razao_social']).strip() if pd.notna(row['razao_social']) else None,
                    'nome_fantasia': str(row['nome_fantasia']).strip() if pd.notna(row['nome_fantasia']) else None,
                    'cnpj': cnpj,
                    'inscricao_estadual': str(row['inscricao_estadual']).strip() if pd.notna(row['inscricao_estadual']) else None,
                    'endereco_completo': str(row['endereco_completo']).strip() if pd.notna(row['endereco_completo']) else None,
                    'telefone_comercial': str(row['telefone_comercial']).strip() if pd.notna(row['telefone_comercial']) else None,
                    'telefone_emergencial': str(row['telefone_emergencial']).strip() if pd.notna(row['telefone_emergencial']) else None,
                    'email': str(row['email']).strip() if pd.notna(row['email']) else None,
                    'website': str(row['website']).strip() if pd.notna(row['website']) else None,
                    'etiqueta': str(row['etiqueta']).strip() if pd.notna(row['etiqueta']) else 'CADASTRADA'
                }
                
                # Processar data de fundação
                if pd.notna(row['data_fundacao']):
                    try:
                        if isinstance(row['data_fundacao'], str):
                            empresa_data['data_fundacao'] = row['data_fundacao']
                        else:
                            empresa_data['data_fundacao'] = row['data_fundacao'].strftime('%Y-%m-%d')
                    except:
                        pass
                
                if empresa_existente:
                    # Atualizar empresa existente
                    _update_empresa_from_excel(empresa_existente, empresa_data, excel_data, cnpj)
                    stats["atualizadas"] += 1
                else:
                    # Criar nova empresa
                    _create_empresa_from_excel(empresa_data, excel_data, cnpj)
                    stats["criadas"] += 1
                
            except Exception as e:
                stats["erros"] += 1
                stats["detalhes_erros"].append(f"Linha {index + 2}: {str(e)}")
                continue
        
        # Confirmar transação
        db.session.commit()
        
        return jsonify({
            "message": "Importação de planilha concluída com sucesso",
            "estatisticas": stats
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro durante a importação: {str(e)}"}), 500


def _create_empresa_from_excel(empresa_data, excel_data, cnpj):
    """Criar nova empresa a partir dos dados da planilha Excel"""
    # Criar empresa principal
    empresa = Empresa(
        razao_social=empresa_data.get("razao_social"),
        nome_fantasia=empresa_data.get("nome_fantasia"),
        cnpj=empresa_data.get("cnpj"),
        inscricao_estadual=empresa_data.get("inscricao_estadual"),
        endereco_completo=empresa_data.get("endereco_completo"),
        telefone_comercial=empresa_data.get("telefone_comercial"),
        telefone_emergencial=empresa_data.get("telefone_emergencial"),
        email=empresa_data.get("email"),
        website=empresa_data.get("website"),
        etiqueta=empresa_data.get("etiqueta", "CADASTRADA"),
        data_fundacao=datetime.strptime(empresa_data["data_fundacao"], "%Y-%m-%d").date() if empresa_data.get("data_fundacao") else None
    )
    
    db.session.add(empresa)
    db.session.flush()  # Para obter o ID da empresa
    
    # Adicionar dados relacionados das outras abas
    _add_related_data_from_excel(empresa, excel_data, cnpj)


def _update_empresa_from_excel(empresa, empresa_data, excel_data, cnpj):
    """Atualizar empresa existente com dados da planilha Excel"""
    # Atualizar campos básicos
    empresa.razao_social = empresa_data.get("razao_social", empresa.razao_social)
    empresa.nome_fantasia = empresa_data.get("nome_fantasia", empresa.nome_fantasia)
    empresa.inscricao_estadual = empresa_data.get("inscricao_estadual", empresa.inscricao_estadual)
    empresa.endereco_completo = empresa_data.get("endereco_completo", empresa.endereco_completo)
    empresa.telefone_comercial = empresa_data.get("telefone_comercial", empresa.telefone_comercial)
    empresa.telefone_emergencial = empresa_data.get("telefone_emergencial", empresa.telefone_emergencial)
    empresa.email = empresa_data.get("email", empresa.email)
    empresa.website = empresa_data.get("website", empresa.website)
    empresa.etiqueta = empresa_data.get("etiqueta", empresa.etiqueta)
    empresa.updated_at = datetime.utcnow()
    
    if empresa_data.get("data_fundacao"):
        empresa.data_fundacao = datetime.strptime(empresa_data["data_fundacao"], "%Y-%m-%d").date()
    
    # Limpar dados relacionados existentes
    _clear_related_data(empresa)
    
    # Adicionar novos dados relacionados das outras abas
    _add_related_data_from_excel(empresa, excel_data, cnpj)


def _add_related_data_from_excel(empresa, excel_data, cnpj):
    """Adicionar dados relacionados das outras abas da planilha Excel"""
    import pandas as pd
    
    # Processar Regulamentações
    if 'Regulamentações' in excel_data or 'Regulamentacoes' in excel_data:
        sheet_name = 'Regulamentações' if 'Regulamentações' in excel_data else 'Regulamentacoes'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                regulamentacao = Regulamentacao(
                    empresa_id=empresa.id,
                    tipo_regulamentacao=str(row['tipo_regulamentacao']) if pd.notna(row['tipo_regulamentacao']) else None,
                    numero_registro=str(row['numero_registro']) if pd.notna(row['numero_registro']) else None,
                    data_emissao=pd.to_datetime(row['data_emissao']).date() if pd.notna(row['data_emissao']) else None,
                    data_validade=pd.to_datetime(row['data_validade']).date() if pd.notna(row['data_validade']) else None,
                    orgao_emissor=str(row['orgao_emissor']) if pd.notna(row['orgao_emissor']) else None
                )
                db.session.add(regulamentacao)
    
    # Processar Certificações
    if 'Certificações' in excel_data or 'Certificacoes' in excel_data:
        sheet_name = 'Certificações' if 'Certificações' in excel_data else 'Certificacoes'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                certificacao = Certificacao(
                    empresa_id=empresa.id,
                    nome_certificacao=str(row['nome_certificacao']) if pd.notna(row['nome_certificacao']) else None,
                    numero_certificacao=str(row['numero_certificacao']) if pd.notna(row['numero_certificacao']) else None,
                    data_emissao=pd.to_datetime(row['data_emissao']).date() if pd.notna(row['data_emissao']) else None,
                    data_validade=pd.to_datetime(row['data_validade']).date() if pd.notna(row['data_validade']) else None,
                    orgao_certificador=str(row['orgao_certificador']) if pd.notna(row['orgao_certificador']) else None
                )
                db.session.add(certificacao)
    
    # Processar Modalidades de Transporte
    if 'Modalidades de Transporte' in excel_data or 'Modalidades' in excel_data:
        sheet_name = 'Modalidades de Transporte' if 'Modalidades de Transporte' in excel_data else 'Modalidades'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                modalidade = ModalidadeTransporte(
                    empresa_id=empresa.id,
                    modalidade=str(row['modalidade']) if pd.notna(row['modalidade']) else None
                )
                db.session.add(modalidade)
    
    # Processar Tipos de Carga
    if 'Tipos de Carga' in excel_data or 'Tipos_Carga' in excel_data:
        sheet_name = 'Tipos de Carga' if 'Tipos de Carga' in excel_data else 'Tipos_Carga'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                tipo_carga = TipoCarga(
                    empresa_id=empresa.id,
                    tipo_carga=str(row['tipo_carga']) if pd.notna(row['tipo_carga']) else None
                )
                db.session.add(tipo_carga)
    
    # Processar Abrangência Geográfica
    if 'Abrangência Geográfica' in excel_data or 'Abrangencia' in excel_data:
        sheet_name = 'Abrangência Geográfica' if 'Abrangência Geográfica' in excel_data else 'Abrangencia'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                abrangencia = AbrangenciaGeografica(
                    empresa_id=empresa.id,
                    tipo_abrangencia=str(row['tipo_abrangencia']) if pd.notna(row['tipo_abrangencia']) else None,
                    detalhes=str(row['detalhes']) if pd.notna(row['detalhes']) else None
                )
                db.session.add(abrangencia)
    
    # Processar Frota
    if 'Frota' in excel_data:
        df = excel_data['Frota']
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                frota = Frota(
                    empresa_id=empresa.id,
                    tipo_frota=str(row['tipo_frota']) if pd.notna(row['tipo_frota']) else None,
                    quantidade=int(row['quantidade']) if pd.notna(row['quantidade']) else None,
                    tipo_veiculo=str(row['tipo_veiculo']) if pd.notna(row['tipo_veiculo']) else None,
                    tipo_carroceria=str(row['tipo_carroceria']) if pd.notna(row['tipo_carroceria']) else None,
                    capacidade=float(row['capacidade']) if pd.notna(row['capacidade']) else None,
                    ano_medio=int(row['ano_medio']) if pd.notna(row['ano_medio']) else None
                )
                db.session.add(frota)
    
    # Processar Armazenagem
    if 'Armazenagem' in excel_data:
        df = excel_data['Armazenagem']
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                possui_armazem = str(row['possui_armazem']).lower() in ['sim', 'yes', 'true', '1'] if pd.notna(row['possui_armazem']) else False
                armazenagem = Armazenagem(
                    empresa_id=empresa.id,
                    possui_armazem=possui_armazem,
                    localizacao=str(row['localizacao']) if pd.notna(row['localizacao']) else None,
                    capacidade_m2=float(row['capacidade_m2']) if pd.notna(row['capacidade_m2']) else None,
                    capacidade_m3=float(row['capacidade_m3']) if pd.notna(row['capacidade_m3']) else None,
                    tipos_armazenagem=str(row['tipos_armazenagem']) if pd.notna(row['tipos_armazenagem']) else None,
                    servicos_oferecidos=str(row['servicos_oferecidos']) if pd.notna(row['servicos_oferecidos']) else None
                )
                db.session.add(armazenagem)
    
    # Processar Portos e Terminais
    if 'Portos e Terminais' in excel_data or 'Portos' in excel_data:
        sheet_name = 'Portos e Terminais' if 'Portos e Terminais' in excel_data else 'Portos'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                porto = PortoTerminal(
                    empresa_id=empresa.id,
                    nome_porto_terminal=str(row['nome_porto_terminal']) if pd.notna(row['nome_porto_terminal']) else None,
                    tipo_terminal=str(row['tipo_terminal']) if pd.notna(row['tipo_terminal']) else None
                )
                db.session.add(porto)
    
    # Processar Seguros e Coberturas
    if 'Seguros e Coberturas' in excel_data or 'Seguros' in excel_data:
        sheet_name = 'Seguros e Coberturas' if 'Seguros e Coberturas' in excel_data else 'Seguros'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                seguro = SeguroCobertura(
                    empresa_id=empresa.id,
                    tipo_seguro=str(row['tipo_seguro']) if pd.notna(row['tipo_seguro']) else None,
                    numero_apolice=str(row['numero_apolice']) if pd.notna(row['numero_apolice']) else None,
                    data_validade=pd.to_datetime(row['data_validade']).date() if pd.notna(row['data_validade']) else None,
                    seguradora=str(row['seguradora']) if pd.notna(row['seguradora']) else None,
                    valor_cobertura=str(row['valor_cobertura']) if pd.notna(row['valor_cobertura']) else None
                )
                db.session.add(seguro)
    
    # Processar Tecnologias
    if 'Tecnologias' in excel_data:
        df = excel_data['Tecnologias']
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                tecnologia = Tecnologia(
                    empresa_id=empresa.id,
                    nome_tecnologia=str(row['nome_tecnologia']) if pd.notna(row['nome_tecnologia']) else None,
                    detalhes=str(row['detalhes']) if pd.notna(row['detalhes']) else None
                )
                db.session.add(tecnologia)
    
    # Processar Desempenho e Qualidade
    if 'Desempenho e Qualidade' in excel_data or 'Desempenho' in excel_data:
        sheet_name = 'Desempenho e Qualidade' if 'Desempenho e Qualidade' in excel_data else 'Desempenho'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                desempenho = DesempenhoQualidade(
                    empresa_id=empresa.id,
                    prazo_medio_atendimento=str(row['prazo_medio_atendimento']) if pd.notna(row['prazo_medio_atendimento']) else None,
                    unidade_prazo=str(row['unidade_prazo']) if pd.notna(row['unidade_prazo']) else 'dias',
                    indice_avarias_extravios=float(row['indice_avarias_extravios']) if pd.notna(row['indice_avarias_extravios']) else None,
                    indice_entregas_prazo=float(row['indice_entregas_prazo']) if pd.notna(row['indice_entregas_prazo']) else None
                )
                db.session.add(desempenho)
    
    # Processar Clientes e Segmentos
    if 'Clientes e Segmentos' in excel_data or 'Clientes' in excel_data:
        sheet_name = 'Clientes e Segmentos' if 'Clientes e Segmentos' in excel_data else 'Clientes'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                cliente = ClienteSegmento(
                    empresa_id=empresa.id,
                    segmento=str(row['segmento']) if pd.notna(row['segmento']) else None,
                    principais_clientes=str(row['principais_clientes']) if pd.notna(row['principais_clientes']) else None
                )
                db.session.add(cliente)
    
    # Processar Recursos Humanos
    if 'Recursos Humanos' in excel_data or 'RH' in excel_data:
        sheet_name = 'Recursos Humanos' if 'Recursos Humanos' in excel_data else 'RH'
        df = excel_data[sheet_name]
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                rh = RecursoHumano(
                    empresa_id=empresa.id,
                    numero_funcionarios=int(row['numero_funcionarios']) if pd.notna(row['numero_funcionarios']) else None,
                    programas_treinamento=str(row['programas_treinamento']) if pd.notna(row['programas_treinamento']) else None
                )
                db.session.add(rh)
    
    # Processar Sustentabilidade
    if 'Sustentabilidade' in excel_data:
        df = excel_data['Sustentabilidade']
        for _, row in df.iterrows():
            if pd.notna(row['cnpj_empresa']) and str(row['cnpj_empresa']).replace('.', '').replace('/', '').replace('-', '') == cnpj:
                sustentabilidade = Sustentabilidade(
                    empresa_id=empresa.id,
                    certificacao_ambiental=str(row['certificacao_ambiental']) if pd.notna(row['certificacao_ambiental']) else None,
                    programas_reducao_emissoes=str(row['programas_reducao_emissoes']) if pd.notna(row['programas_reducao_emissoes']) else None
                )
                db.session.add(sustentabilidade)


@empresa_bp.route("/empresas/template-excel", methods=["GET"])
def download_template_excel():
    """Gerar e baixar template da planilha Excel para importação"""
    try:
        import pandas as pd
        from io import BytesIO
        
        # Criar um buffer em memória
        output = BytesIO()
        
        # Criar o arquivo Excel com múltiplas abas
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Aba 1: Empresas (obrigatória)
            empresas_template = pd.DataFrame({
                'razao_social': ['Exemplo Transportes Ltda'],
                'nome_fantasia': ['Exemplo Transportes'],
                'cnpj': ['12.345.678/0001-90'],
                'inscricao_estadual': ['123456789'],
                'endereco_completo': ['Rua Exemplo, 123 - Centro - São Paulo/SP'],
                'telefone_comercial': ['(11) 1234-5678'],
                'telefone_emergencial': ['(11) 9876-5432'],
                'email': ['contato@exemplo.com.br'],
                'website': ['www.exemplo.com.br'],
                'data_fundacao': ['2020-01-15'],
                'etiqueta': ['CADASTRADA']
            })
            empresas_template.to_excel(writer, sheet_name='Empresas', index=False)
            
            # Aba 2: Regulamentações
            regulamentacoes_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'tipo_regulamentacao': ['RNTRC'],
                'numero_registro': ['123456789'],
                'data_emissao': ['2020-01-01'],
                'data_validade': ['2025-01-01'],
                'orgao_emissor': ['ANTT']
            })
            regulamentacoes_template.to_excel(writer, sheet_name='Regulamentações', index=False)
            
            # Aba 3: Certificações
            certificacoes_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'nome_certificacao': ['ISO 9001'],
                'numero_certificacao': ['ISO9001-2020-001'],
                'data_emissao': ['2020-01-01'],
                'data_validade': ['2023-01-01'],
                'orgao_certificador': ['Bureau Veritas']
            })
            certificacoes_template.to_excel(writer, sheet_name='Certificações', index=False)
            
            # Aba 4: Modalidades de Transporte
            modalidades_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90', '12.345.678/0001-90'],
                'modalidade': ['Rodoviário', 'Multimodal']
            })
            modalidades_template.to_excel(writer, sheet_name='Modalidades', index=False)
            
            # Aba 5: Tipos de Carga
            tipos_carga_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90', '12.345.678/0001-90'],
                'tipo_carga': ['Carga Geral', 'Carga Refrigerada']
            })
            tipos_carga_template.to_excel(writer, sheet_name='Tipos_Carga', index=False)
            
            # Aba 6: Abrangência Geográfica
            abrangencia_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'tipo_abrangencia': ['Regional'],
                'detalhes': ['Sudeste e Sul']
            })
            abrangencia_template.to_excel(writer, sheet_name='Abrangencia', index=False)
            
            # Aba 7: Frota
            frota_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'tipo_frota': ['Própria'],
                'quantidade': [25],
                'tipo_veiculo': ['Carreta'],
                'tipo_carroceria': ['Baú'],
                'capacidade': [30.0],
                'ano_medio': [2018]
            })
            frota_template.to_excel(writer, sheet_name='Frota', index=False)
            
            # Aba 8: Armazenagem
            armazenagem_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'possui_armazem': ['Sim'],
                'localizacao': ['São Paulo/SP'],
                'capacidade_m2': [5000.0],
                'capacidade_m3': [15000.0],
                'tipos_armazenagem': ['Seca, Refrigerada'],
                'servicos_oferecidos': ['Cross-docking, Picking, Packing']
            })
            armazenagem_template.to_excel(writer, sheet_name='Armazenagem', index=False)
            
            # Aba 9: Portos e Terminais
            portos_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90', '12.345.678/0001-90'],
                'nome_porto_terminal': ['Porto de Santos', 'Porto de Paranaguá'],
                'tipo_terminal': ['Marítimo', 'Marítimo']
            })
            portos_template.to_excel(writer, sheet_name='Portos', index=False)
            
            # Aba 10: Seguros e Coberturas
            seguros_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'tipo_seguro': ['RCTR-C'],
                'numero_apolice': ['123456789'],
                'data_validade': ['2024-12-31'],
                'seguradora': ['Seguradora Exemplo'],
                'valor_cobertura': ['R$ 200.000,00']
            })
            seguros_template.to_excel(writer, sheet_name='Seguros', index=False)
            
            # Aba 11: Tecnologias
            tecnologias_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90', '12.345.678/0001-90'],
                'nome_tecnologia': ['GPS', 'TMS'],
                'detalhes': ['Rastreamento em tempo real', 'Sistema de gestão de transporte']
            })
            tecnologias_template.to_excel(writer, sheet_name='Tecnologias', index=False)
            
            # Aba 12: Desempenho e Qualidade
            desempenho_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'prazo_medio_atendimento': ['3'],
                'unidade_prazo': ['dias'],
                'indice_avarias_extravios': [0.5],
                'indice_entregas_prazo': [98.5]
            })
            desempenho_template.to_excel(writer, sheet_name='Desempenho', index=False)
            
            # Aba 13: Clientes e Segmentos
            clientes_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'segmento': ['Varejo'],
                'principais_clientes': ['Cliente A, Cliente B, Cliente C']
            })
            clientes_template.to_excel(writer, sheet_name='Clientes', index=False)
            
            # Aba 14: Recursos Humanos
            rh_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'numero_funcionarios': [150],
                'programas_treinamento': ['Direção defensiva, Produtos perigosos']
            })
            rh_template.to_excel(writer, sheet_name='RH', index=False)
            
            # Aba 15: Sustentabilidade
            sustentabilidade_template = pd.DataFrame({
                'cnpj_empresa': ['12.345.678/0001-90'],
                'certificacao_ambiental': ['ISO 14001'],
                'programas_reducao_emissoes': ['Frota Euro 6, Biodiesel']
            })
            sustentabilidade_template.to_excel(writer, sheet_name='Sustentabilidade', index=False)
        
        # Preparar o arquivo para download
        output.seek(0)
        
        # Criar resposta com o arquivo
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=template_importacao_empresas.xlsx"
        response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        return response
    
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar template: {str(e)}"}), 500

