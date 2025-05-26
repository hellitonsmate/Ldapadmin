from flask import Flask, render_template, request, redirect, url_for, flash

import ldap_utils # seu módulo de funções LDAP
import config # seu arquivo de configuração
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

def check_auth(username, password):
    return username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']

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
@app.route('/users/new', methods=['POST'])
@requires_auth
def create_user_route():
    # Obter dados do formulário
    uid = request.form.get('uid')
    given_name = request.form.get('givenName')
    sn = request.form.get('sn')
    cn = request.form.get('cn') # Ou gere a partir de givenName + sn
    mail = request.form.get('mail')
    password = request.form.get('userPassword')
    confirm_password = request.form.get('confirmPassword')
    selected_group_dns = request.form.getlist('groups') # Lista de DNs dos grupos selecionados

    if password != confirm_password:
        flash("As senhas não coincidem!", "danger")
        # Re-renderizar o formulário com os dados preenchidos e grupos
        conn_temp = None
        all_groups = []
        try:
            conn_temp = get_ldap_connection()
            group_base_dn = app.config.get('LDAP_GROUP_BASE_DN', 'ou=groups,' + app.config['LDAP_BASE_DN'])
            all_groups = ldap_utils.get_all_groups(conn_temp, group_base_dn)
        except ldap.LDAPError as e_grp:
             flash(f"Erro ao recarregar grupos: {str(e_grp)}", "warning")
        finally:
            if conn_temp: conn_temp.unbind_s()
        # Recria o user_data com o que foi submetido para repopular o formulário
        current_form_data_for_template = {
            'uid': [uid], 'givenName': [given_name], 'sn': [sn], 'cn': [cn], 'mail': [mail]
        }
        return render_template('user_form.html', all_groups=all_groups, user_data=current_form_data_for_template, user_groups_dns=selected_group_dns)


    # Construir DN do novo usuário
    # Ex: "uid=novo_usuario,ou=users,dc=example,dc=com"
    user_dn = f"uid={ldap.filter.escape_filter_chars(uid)},{app.config['LDAP_USER_BASE_DN']}"

    # Atributos do usuário
    # Ajuste os objectClass conforme seu schema (ex: inetOrgPerson, posixAccount, top)
    user_attrs = {
        'objectClass': [b'inetOrgPerson', b'organizationalPerson', b'person', b'top'],
        'uid': [uid.encode('utf-8')],
        'givenName': [given_name.encode('utf-8')],
        'sn': [sn.encode('utf-8')],
        'cn': [cn.encode('utf-8')],
        'userPassword': [password.encode('utf-8')] # O LDAP geralmente faz o hashing
    }
    if mail:
        user_attrs['mail'] = [mail.encode('utf-8')]

    # Converter para o formato que add_s espera (lista de tuplas)
    ldap_user_attrs = []
    for key, value in user_attrs.items():
        ldap_user_attrs.append((key.encode('utf-8'), value))
    
    conn = None
    try:
        conn = get_ldap_connection()
        
        # 1. Adicionar usuário
        conn.add_s(user_dn, ldap_user_attrs)
        flash(f"Usuário '{uid}' criado com sucesso!", "success")

        # 2. Adicionar usuário aos grupos selecionados
        if selected_group_dns:
            for group_dn in selected_group_dns:
                try:
                    ldap_utils.add_user_to_group(conn, user_dn, group_dn)
                    flash(f"Usuário '{uid}' adicionado ao grupo '{group_dn.split(',')[0].split('=')[1]}'.", "info") # Mostra o CN do grupo
                except ldap.LDAPError as e_group_add:
                    flash(f"Erro ao adicionar usuário ao grupo '{group_dn.split(',')[0].split('=')[1]}': {str(e_group_add)}", "danger")
        
        return redirect(url_for('list_users_route'))

    except ldap.ALREADY_EXISTS:
        flash(f"Erro: Usuário '{uid}' (DN: {user_dn}) já existe!", "danger")
    except ldap.LDAPError as e:
        flash(f"Erro LDAP ao criar usuário: {str(e)}", "danger")
    finally:
        if conn:
            conn.unbind_s()
    
    # Se chegou aqui, houve um erro na criação do usuário principal, recarregar o formulário
    all_groups_on_error = []
    try:
        conn_temp = get_ldap_connection() # Nova conexão para buscar grupos
        group_base_dn = app.config.get('LDAP_GROUP_BASE_DN', 'ou=groups,' + app.config['LDAP_BASE_DN'])
        all_groups_on_error = ldap_utils.get_all_groups(conn_temp, group_base_dn)
    except Exception as e_grp_load:
        flash(f"Erro crítico ao tentar recarregar grupos após falha: {str(e_grp_load)}", "warning")
    finally:
        if conn_temp: conn_temp.unbind_s()

    current_form_data_for_template_on_error = {
        'uid': [uid], 'givenName': [given_name], 'sn': [sn], 'cn': [cn], 'mail': [mail]
    }
    return render_template('user_form.html', all_groups=all_groups_on_error, user_data=current_form_data_for_template_on_error, user_groups_dns=selected_group_dns)

@app.route('/users/edit/<username>', methods=['POST'])
@requires_auth
def edit_user_route(username):
    conn = None
    try:
        conn = get_ldap_connection()
        user_dn_base = app.config['LDAP_USER_BASE_DN']
        
        # Obter o DN do usuário que está sendo editado
        user_info = ldap_utils.get_user_details_by_uid(conn, user_dn_base, username, attributes=['dn'])
        if not user_info:
            flash(f"Usuário '{username}' não encontrado para edição.", "danger")
            return redirect(url_for('list_users_route'))
        user_dn = user_info['dn']

        # Dados do formulário
        given_name = request.form.get('givenName')
        sn = request.form.get('sn')
        cn = request.form.get('cn')
        mail = request.form.get('mail')
        selected_group_dns_new = set(request.form.getlist('groups')) # DNs dos grupos selecionados no form

        # Modificar atributos básicos do usuário
        # ATENÇÃO: uid (username) geralmente não é modificado. Se for, o DN muda.
        # Se o uid for modificável, a lógica de user_dn e referências em grupos precisa ser MUITO cuidadosa (usar MOD_RDN).
        # Por simplicidade, assumimos que uid não muda.

        mods = []
        # Para cada atributo, prepare a modificação se o valor mudou ou foi fornecido
        # É importante pegar os valores antigos para comparar e só modificar se necessário,
        # ou se o atributo não existir e estiver sendo adicionado.
        # A biblioteca python-ldap.modlist.modifyModlist pode ser útil aqui para gerar 'mods'.
        # Exemplo simplificado:
        # (Este é um exemplo básico, para atributos multivalorados ou opcionais, refine)
        if given_name: mods.append((ldap.MOD_REPLACE, b'givenName', [given_name.encode('utf-8')]))
        if sn: mods.append((ldap.MOD_REPLACE, b'sn', [sn.encode('utf-8')]))
        if cn: mods.append((ldap.MOD_REPLACE, b'cn', [cn.encode('utf-8')]))
        
        # Para o email, se estiver vazio no form, podemos querer remover o atributo.
        if mail:
            mods.append((ldap.MOD_REPLACE, b'mail', [mail.encode('utf-8')]))
        else: # Se o campo email está vazio, e o usuário tinha um email, remove.
            current_user_details = ldap_utils.get_user_details_by_uid(conn, user_dn_base, username, attributes=['mail'])
            if current_user_details and 'mail' in current_user_details['attributes']:
                 mods.append((ldap.MOD_DELETE, b'mail', None)) # Remove todas as ocorrências do atributo mail

        if mods:
            conn.modify_s(user_dn.encode('utf-8'), mods)
            flash(f"Atributos do usuário '{username}' atualizados.", "success")

        # Gerenciar associações de grupo
        group_base_dn = app.config.get('LDAP_GROUP_BASE_DN', 'ou=groups,' + app.config['LDAP_BASE_DN'])
        current_user_group_dns = set(ldap_utils.get_user_group_dns(conn, user_dn, group_base_dn))

        groups_to_add_user_to = selected_group_dns_new - current_user_group_dns
        groups_to_remove_user_from = current_user_group_dns - selected_group_dns_new

        for group_dn in groups_to_add_user_to:
            try:
                ldap_utils.add_user_to_group(conn, user_dn, group_dn)
                flash(f"Usuário '{username}' adicionado ao grupo '{group_dn.split(',')[0].split('=')[1]}'.", "info")
            except ldap.LDAPError as e_add_grp:
                flash(f"Erro ao adicionar '{username}' ao grupo '{group_dn.split(',')[0].split('=')[1]}': {e_add_grp}", "danger")

        for group_dn in groups_to_remove_user_from:
            try:
                ldap_utils.remove_user_from_group(conn, user_dn, group_dn)
                flash(f"Usuário '{username}' removido do grupo '{group_dn.split(',')[0].split('=')[1]}'.", "info")
            except ldap.LDAPError as e_rem_grp:
                flash(f"Erro ao remover '{username}' do grupo '{group_dn.split(',')[0].split('=')[1]}': {e_rem_grp}", "danger")
        
        return redirect(url_for('edit_user_form_route', username=username)) # Volta para o form de edição

    except ldap.LDAPError as e:
        flash(f"Erro LDAP ao editar usuário '{username}': {str(e)}", "danger")
        # Pode redirecionar para lista ou tentar recarregar o form de edição com os dados atuais
        return redirect(url_for('edit_user_form_route', username=username))
    finally:
        if conn:
            conn.unbind_s()

# Não se esqueça da rota para alterar senha, que seria separada (POST para /users/<username>/change-password)
# ...

if __name__ == '__main__':
    app.run(debug=True) # debug=True SÓ para desenvolvimento
