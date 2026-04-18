with open("src/routes/cotacao_v133.py", "r") as f:
    content = f.read()

route_code = """
@cotacao_v133_bp.route("/operadores", methods=["GET"])
@login_required
def obter_operadores():
    \"\"\"Obtém lista de operadores disponíveis\"\"\"
    try:
        operadores = Usuario.query.filter(
            or_(
                Usuario.tipo_usuario == TipoUsuario.OPERADOR,
                Usuario.tipo_usuario == TipoUsuario.ADMINISTRADOR,
                Usuario.tipo_usuario == TipoUsuario.GERENTE
            ),
            Usuario.ativo == True
        ).all()
        
        return jsonify({
            'success': True,
            'operadores': [{
                'id': op.id,
                'nome': op.nome_completo,
                'departamento': 'Operações',
                'status': 'online'
            } for op in operadores]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }), 500
"""

if "/operadores" not in content and "def obter_operadores()" not in content:
    # Append to the end
    with open("src/routes/cotacao_v133.py", "a") as f:
        f.write(route_code)
    print("Added /operadores route")
else:
    print("Route already exists or script needs adjustment")
