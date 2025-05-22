from flask import Flask, render_template, request, redirect, url_for
import ldap_utils
import config # Seu arquivo de configuração

app = Flask(__name__)

# Carregar configuração (exemplo simples)
app.config.from_object(config) # Se config.py estiver no mesmo nível
# Ou diretamente:
# app.config['LDAP_SERVER_URI'] = 'ldap://localhost:389'
# app.config['LDAP_USER_BASE_DN'] = 'ou=users,dc=example,dc=com'
# app.config['LDAP_BIND_DN'] = 'cn=admin,dc=example,dc=com'
# app.config['LDAP_BIND_PASSWORD'] = 'admin_password'


# Autenticação básica (MUITO SIMPLES - para fins de exemplo)
# Em produção, use algo mais robusto!
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
            'Login Necessário.', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@requires_auth # Protege a rota
def list_users_route():
    try:
        conn = ldap_utils.connect_ldap(app.config)
        users = ldap_utils.get_all_users(conn, app.config['LDAP_USER_BASE_DN'])
        conn.unbind_s()
    except Exception as e:
        # Logar o erro e mostrar uma mensagem amigável
        print(f"Erro ao conectar ou buscar usuários: {e}")
        users = []
        # Você pode querer passar uma mensagem de erro para o template
    return render_template('list_users.html', users=users)

# ... outras rotas para criar, editar, deletar ...

if __name__ == '__main__':
    app.run(debug=True) # debug=True SÓ para desenvolvimento
