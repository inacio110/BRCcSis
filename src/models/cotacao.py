from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pytz
from enum import Enum
from . import db
from .usuario import get_brasilia_time, Usuario

class StatusCotacao(Enum):
    SOLICITADA = "solicitada"  # Consultor solicitou
    ACEITA_OPERADOR = "aceita_operador"  # Operador aceitou
    COTACAO_ENVIADA = "cotacao_enviada"  # Operador enviou cotação
    ACEITA_CONSULTOR = "aceita_consultor"  # Consultor aceitou
    NEGADA_CONSULTOR = "negada_consultor"  # Consultor negou
    FINALIZADA = "finalizada"  # Processo finalizado

class EmpresaCotacao(Enum):
    BRCARGO_RODOVIARIO = "brcargo_rodoviario"
    BRCARGO_MARITIMO = "brcargo_maritimo"
    FRETE_AEREO = "frete_aereo"

class Cotacao(db.Model):
    __tablename__ = 'cotacoes'
    
    # Identificação
    id = db.Column(db.Integer, primary_key=True)
    numero_cotacao = db.Column(db.String(20), unique=True, nullable=False)
    
    # Relacionamentos
    consultor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    operador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    empresa_prestadora_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)  # Empresa que forneceu o serviço
    
    # Empresa de transporte
    empresa_transporte = db.Column(db.Enum(EmpresaCotacao), nullable=False, default=EmpresaCotacao.BRCARGO_RODOVIARIO)
    
    # Status e controle
    status = db.Column(db.Enum(StatusCotacao), nullable=False, default=StatusCotacao.SOLICITADA)
    data_solicitacao = db.Column(db.DateTime, default=get_brasilia_time)
    data_aceite_operador = db.Column(db.DateTime)
    data_cotacao_enviada = db.Column(db.DateTime)
    data_resposta_cliente = db.Column(db.DateTime)
    data_finalizacao = db.Column(db.DateTime)
    
    # Dados do cliente
    cliente_nome = db.Column(db.String(255), nullable=False)
    cliente_cnpj = db.Column(db.String(18), nullable=False)
    cliente_contato_telefone = db.Column(db.String(20))
    cliente_contato_email = db.Column(db.String(100))
    
    # Origem
    origem_cep = db.Column(db.String(9), nullable=False)
    origem_endereco = db.Column(db.String(500), nullable=False)
    origem_cidade = db.Column(db.String(100), nullable=False)
    origem_estado = db.Column(db.String(2), nullable=False)
    
    # Destino
    destino_cep = db.Column(db.String(9), nullable=False)
    destino_endereco = db.Column(db.String(500), nullable=False)
    destino_cidade = db.Column(db.String(100), nullable=False)
    destino_estado = db.Column(db.String(2), nullable=False)
    
    # Carga
    carga_descricao = db.Column(db.Text, nullable=False)
    carga_peso_kg = db.Column(db.Numeric(10, 2), nullable=False)
    carga_comprimento_cm = db.Column(db.Numeric(8, 2))
    carga_largura_cm = db.Column(db.Numeric(8, 2))
    carga_altura_cm = db.Column(db.Numeric(8, 2))
    carga_valor_mercadoria = db.Column(db.Numeric(12, 2))
    carga_tipo_embalagem = db.Column(db.String(100))
    
    # Serviço
    servico_prazo_desejado = db.Column(db.Integer)  # dias
    servico_tipo = db.Column(db.String(50))  # expresso, econômico, etc.
    servico_observacoes = db.Column(db.Text)
    
    # Dados opcionais
    data_coleta_preferencial = db.Column(db.Date)
    instrucoes_manuseio = db.Column(db.Text)
    seguro_adicional = db.Column(db.Boolean, default=False)
    servicos_complementares = db.Column(db.Text)
    
    # Campos específicos para transporte marítimo
    numero_cliente = db.Column(db.String(50))  # Obrigatório para marítimo
    numero_net_weight = db.Column(db.Numeric(10, 2))  # Obrigatório para marítimo
    numero_gross_weight = db.Column(db.Numeric(10, 2))  # Obrigatório para marítimo
    cubagem = db.Column(db.Numeric(10, 3))  # Obrigatório para marítimo
    incoterm = db.Column(db.String(10))  # Obrigatório para marítimo
    tipo_carga_maritima = db.Column(db.String(50))  # FCL ou LCL
    tamanho_container = db.Column(db.String(20))  # Para FCL
    quantidade_containers = db.Column(db.Integer)  # Para FCL
    porto_origem = db.Column(db.String(100))  # Obrigatório para marítimo
    porto_destino = db.Column(db.String(100))  # Obrigatório para marítimo
    
    # Resposta da cotação
    cotacao_valor_frete = db.Column(db.Numeric(12, 2))
    cotacao_prazo_entrega = db.Column(db.Integer)  # dias
    cotacao_observacoes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=get_brasilia_time)
    updated_at = db.Column(db.DateTime, default=get_brasilia_time, onupdate=get_brasilia_time)
    
    # Relacionamentos
    consultor = db.relationship('Usuario', foreign_keys=[consultor_id], backref='cotacoes_solicitadas')
    operador = db.relationship('Usuario', foreign_keys=[operador_id], backref='cotacoes_gerenciadas')
    empresa_prestadora = db.relationship('Empresa', foreign_keys=[empresa_prestadora_id], backref='cotacoes_prestadas')
    
    def __init__(self, **kwargs):
        super(Cotacao, self).__init__(**kwargs)
        if not self.numero_cotacao:
            self.numero_cotacao = self.gerar_numero_cotacao()
    
    @staticmethod
    def gerar_numero_cotacao():
        """Gera um número único para a cotação no formato COT-YYYYMMDD-NNNN"""
        hoje = datetime.now().strftime('%Y%m%d')
        
        # Buscar o último número do dia
        ultimo_numero = db.session.query(Cotacao.numero_cotacao)\
            .filter(Cotacao.numero_cotacao.like(f'COT-{hoje}-%'))\
            .order_by(Cotacao.numero_cotacao.desc())\
            .first()
        
        if ultimo_numero:
            # Extrair o número sequencial e incrementar
            seq = int(ultimo_numero[0].split('-')[-1]) + 1
        else:
            seq = 1
        
        return f'COT-{hoje}-{seq:04d}'
    
    def pode_ser_aceita_por(self, usuario):
        """Verifica se a cotação pode ser aceita pelo usuário"""
        from .usuario import TipoUsuario
        return (self.status == StatusCotacao.SOLICITADA and 
                usuario.tipo_usuario in [TipoUsuario.OPERADOR, TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE])
    
    def pode_ser_respondida_por(self, usuario):
        """Verifica se a cotação pode ser respondida pelo usuário"""
        from .usuario import TipoUsuario
        return (self.status == StatusCotacao.ACEITA_OPERADOR and 
                (self.operador_id == usuario.id or 
                 usuario.tipo_usuario in [TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]))
    
    def pode_ser_finalizada_por(self, usuario):
        """Verifica se a cotação pode ser finalizada pelo usuário"""
        from .usuario import TipoUsuario
        return (self.status in [StatusCotacao.COTACAO_ENVIADA, StatusCotacao.ACEITA_CONSULTOR, StatusCotacao.NEGADA_CONSULTOR] and 
                (self.operador_id == usuario.id or 
                 usuario.tipo_usuario in [TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]))
    
    def pode_ser_reatribuida_por(self, usuario):
        """Verifica se a cotação pode ser reatribuída pelo usuário"""
        from .usuario import TipoUsuario
        return usuario.tipo_usuario in [TipoUsuario.ADMINISTRADOR, TipoUsuario.GERENTE]
    
    def aceitar(self, operador):
        """Aceita a cotação e atribui ao operador"""
        if not self.pode_ser_aceita_por(operador):
            raise ValueError("Cotação não pode ser aceita por este usuário")
        
        self.operador_id = operador.id
        self.status = StatusCotacao.ACEITA_OPERADOR
        self.data_aceite_operador = get_brasilia_time()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=operador.id,
            status_anterior=StatusCotacao.SOLICITADA,
            status_novo=StatusCotacao.ACEITA_OPERADOR,
            observacoes=f"Cotação aceita pelo operador {operador.nome_completo}"
        )
    
    def responder(self, operador, valor_frete, prazo_entrega, observacoes=None):
        """Responde a cotação com valores"""
        if not self.pode_ser_respondida_por(operador):
            raise ValueError("Cotação não pode ser respondida por este usuário")
        
        self.cotacao_valor_frete = valor_frete
        self.cotacao_prazo_entrega = prazo_entrega
        self.cotacao_observacoes = observacoes
        self.status = StatusCotacao.COTACAO_ENVIADA
        self.data_cotacao_enviada = get_brasilia_time()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=operador.id,
            status_anterior=StatusCotacao.ACEITA_OPERADOR,
            status_novo=StatusCotacao.COTACAO_ENVIADA,
            observacoes=f"Cotação respondida com valor R$ {valor_frete} e prazo {prazo_entrega} dias"
        )
    
    def finalizar(self, usuario, aprovada=True, observacoes=None):
        """Finaliza a cotação"""
        if not self.pode_ser_finalizada_por(usuario):
            raise ValueError("Cotação não pode ser finalizada por este usuário")
        
        status_anterior = self.status
        if aprovada:
            self.status = StatusCotacao.ACEITA_CONSULTOR
        else:
            self.status = StatusCotacao.NEGADA_CONSULTOR
        
        self.data_resposta_cliente = get_brasilia_time()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=usuario.id,
            status_anterior=status_anterior,
            status_novo=self.status,
            observacoes=observacoes or f"Cotação {'aprovada' if aprovada else 'recusada'} pelo cliente"
        )
    
    def marcar_finalizada(self, usuario, observacoes=None):
        """Marca a cotação como finalizada"""
        if not self.pode_ser_finalizada_por(usuario):
            raise ValueError("Cotação não pode ser marcada como finalizada por este usuário")
        
        status_anterior = self.status
        self.status = StatusCotacao.FINALIZADA
        self.data_finalizacao = get_brasilia_time()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=usuario.id,
            status_anterior=status_anterior,
            status_novo=StatusCotacao.FINALIZADA,
            observacoes=observacoes or "Cotação marcada como finalizada"
        )
    
    def reatribuir(self, admin, novo_operador):
        """Reatribui a cotação para outro operador"""
        if not self.pode_ser_reatribuida_por(admin):
            raise ValueError("Usuário não tem permissão para reatribuir cotações")
        
        operador_anterior = self.operador
        self.operador_id = novo_operador.id
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=admin.id,
            status_anterior=self.status,
            status_novo=self.status,
            observacoes=f"Cotação reatribuída de {operador_anterior.nome_completo if operador_anterior else 'N/A'} para {novo_operador.nome_completo}"
        )
    
    def get_status_display(self):
        """Retorna o status em formato legível"""
        status_map = {
            StatusCotacao.SOLICITADA: "Solicitada",
            StatusCotacao.ACEITA_OPERADOR: "Aceita pelo Operador",
            StatusCotacao.COTACAO_ENVIADA: "Cotação Enviada",
            StatusCotacao.ACEITA_CONSULTOR: "Aceita pelo Consultor",
            StatusCotacao.NEGADA_CONSULTOR: "Negada pelo Consultor",
            StatusCotacao.FINALIZADA: "Finalizada"
        }
        return status_map.get(self.status, self.status.value)
    
    def get_status_color(self):
        """Retorna a cor CSS para o status"""
        color_map = {
            StatusCotacao.SOLICITADA: "bg-yellow-100 text-yellow-800",
            StatusCotacao.ACEITA_OPERADOR: "bg-blue-100 text-blue-800",
            StatusCotacao.COTACAO_ENVIADA: "bg-purple-100 text-purple-800",
            StatusCotacao.ACEITA_CONSULTOR: "bg-green-100 text-green-800",
            StatusCotacao.NEGADA_CONSULTOR: "bg-red-100 text-red-800",
            StatusCotacao.FINALIZADA: "bg-gray-100 text-gray-800"
        }
        return color_map.get(self.status, "bg-gray-100 text-gray-800")
    
    def to_dict(self):
        """Converte a cotação para dicionário"""
        return {
            'id': self.id,
            'numero_cotacao': self.numero_cotacao,
            'consultor_id': self.consultor_id,
            'consultor_nome': self.consultor.nome_completo if self.consultor else None,
            'operador_id': self.operador_id,
            'operador_nome': self.operador.nome_completo if self.operador else None,
            'empresa_transporte': self.empresa_transporte.value,
            'status': self.status.value,
            'status_display': self.get_status_display(),
            'status_color': self.get_status_color(),
            'data_solicitacao': self.data_solicitacao.isoformat() if self.data_solicitacao else None,
            'data_aceite_operador': self.data_aceite_operador.isoformat() if self.data_aceite_operador else None,
            'data_cotacao_enviada': self.data_cotacao_enviada.isoformat() if self.data_cotacao_enviada else None,
            'data_resposta_cliente': self.data_resposta_cliente.isoformat() if self.data_resposta_cliente else None,
            'data_finalizacao': self.data_finalizacao.isoformat() if self.data_finalizacao else None,
            'cliente_nome': self.cliente_nome,
            'cliente_cnpj': self.cliente_cnpj,
            'cliente_contato_telefone': self.cliente_contato_telefone,
            'cliente_contato_email': self.cliente_contato_email,
            'origem_cep': self.origem_cep,
            'origem_endereco': self.origem_endereco,
            'origem_cidade': self.origem_cidade,
            'origem_estado': self.origem_estado,
            'destino_cep': self.destino_cep,
            'destino_endereco': self.destino_endereco,
            'destino_cidade': self.destino_cidade,
            'destino_estado': self.destino_estado,
            'carga_descricao': self.carga_descricao,
            'carga_peso_kg': float(self.carga_peso_kg) if self.carga_peso_kg else None,
            'carga_comprimento_cm': float(self.carga_comprimento_cm) if self.carga_comprimento_cm else None,
            'carga_largura_cm': float(self.carga_largura_cm) if self.carga_largura_cm else None,
            'carga_altura_cm': float(self.carga_altura_cm) if self.carga_altura_cm else None,
            'carga_valor_mercadoria': float(self.carga_valor_mercadoria) if self.carga_valor_mercadoria else None,
            'carga_tipo_embalagem': self.carga_tipo_embalagem,
            'servico_prazo_desejado': self.servico_prazo_desejado,
            'servico_tipo': self.servico_tipo,
            'servico_observacoes': self.servico_observacoes,
            'data_coleta_preferencial': self.data_coleta_preferencial.isoformat() if self.data_coleta_preferencial else None,
            'instrucoes_manuseio': self.instrucoes_manuseio,
            'seguro_adicional': self.seguro_adicional,
            'servicos_complementares': self.servicos_complementares,
            'cotacao_valor_frete': float(self.cotacao_valor_frete) if self.cotacao_valor_frete else None,
            'cotacao_prazo_entrega': self.cotacao_prazo_entrega,
            'cotacao_observacoes': self.cotacao_observacoes,
            # Campos específicos para transporte marítimo
            'numero_cliente': self.numero_cliente,
            'numero_net_weight': float(self.numero_net_weight) if self.numero_net_weight else None,
            'numero_gross_weight': float(self.numero_gross_weight) if self.numero_gross_weight else None,
            # Aliases para compatibilidade com frontend
            'net_weight': float(self.numero_net_weight) if self.numero_net_weight else None,
            'gross_weight': float(self.numero_gross_weight) if self.numero_gross_weight else None,
            'cubagem': float(self.cubagem) if self.cubagem else (float(self.carga_comprimento_cm * self.carga_largura_cm * self.carga_altura_cm / 6000) if self.carga_comprimento_cm and self.carga_largura_cm and self.carga_altura_cm else None),
            'incoterm': self.incoterm,
            'tipo_carga_maritima': self.tipo_carga_maritima,
            'tamanho_container': self.tamanho_container,
            'quantidade_containers': self.quantidade_containers,
            'porto_origem': self.porto_origem,
            'porto_destino': self.porto_destino,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    # Métodos para integração com sistema de notificações e fluxo completo
    def aceitar_por_operador(self, operador_id, observacoes=None):
        """Operador aceita a cotação"""
        if self.status != StatusCotacao.SOLICITADA:
            raise ValueError("Cotação não está disponível para aceitação")
        
        status_anterior = self.status
        self.operador_id = operador_id
        self.status = StatusCotacao.ACEITA_OPERADOR
        self.data_aceite_operador = get_brasilia_time()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=operador_id,
            status_anterior=status_anterior,
            status_novo=self.status,
            observacoes=observacoes
        )
        
        # Notificar consultor
        from .notificacao import Notificacao
        Notificacao.notificar_cotacao_aceita(self)
        
        db.session.commit()
        return True
    
    def enviar_cotacao(self, valor_frete=None, prazo_entrega=None, observacoes=None, empresa_prestadora_id=None):
        """Operador envia cotação respondida"""
        if self.status != StatusCotacao.ACEITA_OPERADOR:
            raise ValueError("Cotação não está em status adequado para envio")
        
        status_anterior = self.status
        self.cotacao_valor_frete = valor_frete
        self.cotacao_prazo_entrega = prazo_entrega
        self.cotacao_observacoes = observacoes
        self.empresa_prestadora_id = empresa_prestadora_id
        self.status = StatusCotacao.COTACAO_ENVIADA
        self.data_cotacao_enviada = get_brasilia_time()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=self.operador_id,
            status_anterior=status_anterior,
            status_novo=self.status,
            observacoes=f"Valor: R$ {valor_frete}, Prazo: {prazo_entrega} dias. {observacoes or ''}"
        )
        
        # Notificar consultor
        from .notificacao import Notificacao
        Notificacao.notificar_cotacao_respondida(self)
        
        db.session.commit()
        return True
    
    def aceitar_por_consultor(self, observacoes=None):
        """Consultor aceita a cotação"""
        if self.status != StatusCotacao.COTACAO_ENVIADA:
            raise ValueError("Cotação não está disponível para aceitação pelo consultor")
        
        status_anterior = self.status
        self.status = StatusCotacao.ACEITA_CONSULTOR
        self.data_resposta_cliente = get_brasilia_time()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=self.consultor_id,
            status_anterior=status_anterior,
            status_novo=self.status,
            observacoes=observacoes
        )
        
        # Notificar operador
        from .notificacao import Notificacao
        Notificacao.notificar_cotacao_finalizada(self, aceita=True)
        
        db.session.commit()
        return True
    
    def negar_por_consultor(self, observacoes=None):
        """Consultor nega a cotação"""
        if self.status != StatusCotacao.COTACAO_ENVIADA:
            raise ValueError("Cotação não está disponível para negação pelo consultor")
        
        status_anterior = self.status
        self.status = StatusCotacao.NEGADA_CONSULTOR
        self.data_resposta_cliente = get_brasilia_time()
        
        # Registrar no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=self.id,
            usuario_id=self.consultor_id,
            status_anterior=status_anterior,
            status_novo=self.status,
            observacoes=observacoes
        )
        
        # Notificar operador
        from .notificacao import Notificacao
        Notificacao.notificar_cotacao_finalizada(self, aceita=False)
        
        db.session.commit()
        return True
    
    @staticmethod
    def criar_cotacao(dados, consultor_id):
        """Cria uma nova cotação e notifica operadores"""
        cotacao = Cotacao(
            consultor_id=consultor_id,
            **dados
        )
        
        db.session.add(cotacao)
        db.session.flush()  # Para obter o ID
        
        # Registrar criação no histórico
        HistoricoCotacao.registrar_mudanca(
            cotacao_id=cotacao.id,
            usuario_id=consultor_id,
            status_anterior=None,
            status_novo=cotacao.status,
            observacoes="Cotação criada"
        )
        
        # Notificar operadores
        from .notificacao import Notificacao
        Notificacao.notificar_nova_cotacao(cotacao)
        
        db.session.commit()
        return cotacao
    
    def __repr__(self):
        return f'<Cotacao {self.numero_cotacao}>'


class HistoricoCotacao(db.Model):
    __tablename__ = 'historico_cotacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    cotacao_id = db.Column(db.Integer, db.ForeignKey('cotacoes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    status_anterior = db.Column(db.Enum(StatusCotacao))
    status_novo = db.Column(db.Enum(StatusCotacao), nullable=False)
    observacoes = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=get_brasilia_time)
    
    cotacao = db.relationship('Cotacao', backref='historico')
    usuario = db.relationship('Usuario')
    
    @staticmethod
    def registrar_mudanca(cotacao_id, usuario_id, status_anterior, status_novo, observacoes=None):
        """Registra uma mudança no histórico da cotação"""
        historico = HistoricoCotacao(
            cotacao_id=cotacao_id,
            usuario_id=usuario_id,
            status_anterior=status_anterior,
            status_novo=status_novo,
            observacoes=observacoes
        )
        db.session.add(historico)
        db.session.commit()
        return historico
    
    @staticmethod
    def obter_historico_cotacao(cotacao_id):
        """Obtém o histórico completo de uma cotação"""
        try:
            historico_items = HistoricoCotacao.query.filter_by(cotacao_id=cotacao_id)\
                .order_by(HistoricoCotacao.timestamp.asc()).all()
            return [item.to_dict() for item in historico_items]
        except Exception as e:
            # Se houver problema com enum, fazer consulta raw e processar manualmente
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT id, cotacao_id, usuario_id, status_anterior, status_novo, 
                       observacoes, timestamp
                FROM historico_cotacoes 
                WHERE cotacao_id = :cotacao_id 
                ORDER BY timestamp ASC
            """), {'cotacao_id': cotacao_id})
            
            historico = []
            for row in result:
                # Buscar nome do usuário
                from .usuario import Usuario
                usuario = Usuario.query.get(row.usuario_id)
                
                historico.append({
                    'id': row.id,
                    'cotacao_id': row.cotacao_id,
                    'usuario_id': row.usuario_id,
                    'usuario_nome': usuario.nome_completo if usuario else None,
                    'status_anterior': row.status_anterior,
                    'status_novo': row.status_novo,
                    'observacoes': row.observacoes,
                    'timestamp': row.timestamp.isoformat() if hasattr(row.timestamp, 'isoformat') else str(row.timestamp)
                })
            
            return historico
    
    def to_dict(self):
        """Converte o histórico para dicionário"""
        # Lidar com dados históricos que podem ser strings ou enums
        def get_status_value(status):
            if status is None:
                return None
            if hasattr(status, 'value'):
                return status.value
            return str(status)
        
        return {
            'id': self.id,
            'cotacao_id': self.cotacao_id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario.nome_completo if self.usuario else None,
            'status_anterior': get_status_value(self.status_anterior),
            'status_novo': get_status_value(self.status_novo),
            'observacoes': self.observacoes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f'<HistoricoCotacao {self.cotacao_id} - {self.status_novo.value}>'

