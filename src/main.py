import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from src.models import db
from src.routes.empresa import empresa_bp
from src.routes.user import user_bp
from src.routes.seed import seed_bp
from src.routes.auth import auth_bp
from src.routes.cotacao_v133 import cotacao_v133_bp
from src.routes.dashboard_v133 import dashboard_v133_bp

from flask_migrate import Migrate

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configurar banco de dados ANTES de inicializar Migrate
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Agora inicializar Migrate
migrate = Migrate(app, db)

# Habilitar CORS para todas as rotas
CORS(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Configurar sessão para não ser permanente e expirar ao fechar navegador
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora (3600 segundos)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # True apenas em HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

@login_manager.user_loader
def load_user(user_id):
    from src.models.usuario import Usuario
    return Usuario.query.get(int(user_id))

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(empresa_bp, url_prefix='/api')
app.register_blueprint(seed_bp, url_prefix='/api')
app.register_blueprint(cotacao_v133_bp, url_prefix='/api/v133')
app.register_blueprint(dashboard_v133_bp, url_prefix='/api/v133')

# Criar diretório do banco se não existir
os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)

with app.app_context():
    db.create_all()
    
    # Criar usuário administrador padrão se não existir
    from src.models.usuario import Usuario, TipoUsuario
    admin_user = Usuario.query.filter_by(username='admin').first()
    if not admin_user:
        admin = Usuario(
            username='admin',
            email='admin@brchina.com',
            nome_completo='Administrador do Sistema',
            tipo_usuario=TipoUsuario.ADMINISTRADOR
        )
        admin.set_password('admin123')  # Senha padrão - DEVE SER ALTERADA
        db.session.add(admin)
        db.session.commit()
        print("Usuário administrador criado: admin / admin123")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
@login_required
def serve(path):
    # Não interceptar rotas da API e de autenticação
    if path.startswith('api/') or path.startswith('login'):
        return "Route not found", 404
    
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

