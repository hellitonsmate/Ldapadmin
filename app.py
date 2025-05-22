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

def get_ldap_connection():
    """Helper para obter conexão LDAP."""
    conn = ldap.initialize(app.config['LDAP_SERVER_URI'])
    # Recomenda-se usar STARTTLS para conexões seguras se não for LDAPS
    # conn.start_tls_s() 
    conn.simple_bind_s(app.config['LDAP_BIND_DN'], app.config['LDAP_BIND_PASSWORD'])
    return conn

@app.route('/users/new', methods=['GET'])
@requires_auth
def create_user_form_route():
    conn = None
    try:
        conn = get_ldap_connection()
        # Supondo que você tenha uma base DN para grupos em sua configuração
        group_base_dn = app.config.get('LDAP_GROUP_BASE_DN', 'ou=groups,' + app.config['LDAP_BASE_DN'])
        all_groups = ldap_utils.get_all_groups(conn, group_base_dn)
    except ldap.LDAPError as e:
        flash(f"Erro ao carregar grupos do LDAP: {str(e)}", "danger")
        all_groups = []
    finally:
        if conn:
            conn.unbind_s()
    return render_template('user_form.html', all_groups=all_groups, user_data=None, user_groups_dns=[])


@app.route('/users/edit/<username>', methods=['GET'])
@requires_auth
def edit_user_form_route(username):
    conn = None
    user_data = None
    all_groups = []
    user_groups_dns = []
    try:
        conn = get_ldap_connection()
        user_dn_base = app.config['LDAP_USER_BASE_DN']
        user_info = ldap_utils.get_user_details_by_uid(conn, user_dn_base, username) # Você precisará criar esta função

        if not user_info:
            flash(f"Usuário '{username}' não encontrado.", "warning")
            return redirect(url_for('list_users_route'))
        
        user_data = user_info['attributes'] # Ex: {'uid': ['testuser'], 'cn': ['Test User'], ...}
        user_dn = user_info['dn']

        group_base_dn = app.config.get('LDAP_GROUP_BASE_DN', 'ou=groups,' + app.config['LDAP_BASE_DN'])
        all_groups = ldap_utils.get_all_groups(conn, group_base_dn)
        
        # Obter os grupos atuais do usuário
        user_groups_dns = ldap_utils.get_user_group_dns(conn, user_dn, group_base_dn) # Você precisará criar esta função

    except ldap.LDAPError as e:
        flash(f"Erro ao carregar dados para edição: {str(e)}", "danger")
        # Poderia redirecionar ou apenas mostrar o formulário com menos dados
    finally:
        if conn:
            conn.unbind_s()
    
    return render_template('user_form.html', user_data=user_data, all_groups=all_groups, user_groups_dns=user_groups_dns)

if __name__ == '__main__':
    app.run(debug=True) # debug=True SÓ para desenvolvimento
