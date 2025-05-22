import ldap
import ldap.modlist as modlist # Para construir listas de modificação
# from ldap.controls import PasswordPolicyControl # Para políticas de senha, se aplicável


def connect_ldap(config):
    conn = ldap.initialize(config['LDAP_SERVER_URI'])
    conn.simple_bind_s(config['LDAP_BIND_DN'], config['LDAP_BIND_PASSWORD'])
    return conn

def get_all_users(conn, base_dn, attributes=['uid', 'cn', 'mail']):
    # Cuidado: O filtro '(objectClass=inetOrgPerson)' pode variar conforme seu schema
    search_filter = "(objectClass=inetOrgPerson)" # Ou person, posixAccount, etc.
    try:
        results = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, attributes)
        users = []
        for dn, entry in results:
            user_data = {attr.decode(): entry[attr][0].decode() for attr in entry if entry[attr]}
            user_data['dn'] = dn.decode() # Pode ser útil
            users.append(user_data)
        return users
    except ldap.LDAPError as e:
        print(f"LDAP Error: {e}")
        return []

def get_all_groups(conn, group_base_dn, attributes=['cn', 'dn']):
    # Ajuste o filtro conforme o objectClass dos seus grupos (groupOfNames, posixGroup, group, etc.)
    search_filter = "(objectClass=groupOfNames)" # Ou groupOfUniqueNames, posixGroup
    try:
        # Pedir o DN implicitamente com None na lista de atributos se não for especificado
        # ou explicitamente se sua biblioteca/config exigir.
        # 'dn' não é um atributo real, é a identificação da entrada.
        # Para obter o DN, ele geralmente já vem na tupla (dn, entry) do search_s.
        results = conn.search_s(group_base_dn, ldap.SCOPE_SUBTREE, search_filter, attributes)
        groups = []
        for dn, entry in results:
            group_data = {attr.decode(): [val.decode() for val in entry[attr]] for attr in entry if entry[attr]}
            group_data['dn'] = dn.decode() # Adiciona o DN ao dicionário do grupo
            groups.append(group_data)
        return groups
    except ldap.LDAPError as e:
        print(f"LDAP Error ao buscar grupos: {e}")
        raise # Re-lança a exceção para ser tratada pela rota

def get_user_details_by_uid(conn, user_base_dn, uid, attributes=None):
    """Busca detalhes de um usuário pelo UID."""
    search_filter = f"(uid={ldap.filter.escape_filter_chars(uid)})"
    try:
        # Se attributes for None, busca todos os atributos do usuário
        result = conn.search_s(user_base_dn, ldap.SCOPE_SUBTREE, search_filter, attributes)
        if result:
            dn, entry = result[0]
            # Decodifica atributos e valores
            decoded_entry = {
                k.decode('utf-8'): [v.decode('utf-8') for v in entry[k]]
                for k in entry
            }
            return {'dn': dn.decode('utf-8'), 'attributes': decoded_entry}
        return None
    except ldap.LDAPError as e:
        print(f"LDAP Error ao buscar usuário {uid}: {e}")
        raise

def get_user_group_dns(conn, user_dn, group_base_dn):
    """Retorna uma lista de DNs dos grupos aos quais um usuário pertence."""
    # O atributo de membro pode ser 'member', 'uniqueMember', etc.
    # Ajuste conforme seu schema de grupo.
    member_attr = 'member' 
    search_filter = f"(& (objectClass=groupOfNames) ({member_attr}={ldap.filter.escape_filter_chars(user_dn)}) )"
    group_dns = []
    try:
        results = conn.search_s(group_base_dn, ldap.SCOPE_SUBTREE, search_filter, ['dn']) # Só precisamos do DN do grupo
        for dn, _ in results:
            group_dns.append(dn.decode('utf-8'))
        return group_dns
    except ldap.LDAPError as e:
        print(f"LDAP Error ao buscar grupos do usuário {user_dn}: {e}")
        # Em caso de erro, poderia retornar lista vazia ou relançar
        return []


def add_user_to_group(conn, user_dn, group_dn):
    """Adiciona um usuário (pelo seu DN) a um grupo (pelo seu DN)."""
    # O atributo de membro pode ser 'member', 'uniqueMember', etc.
    # Ajuste conforme seu schema de grupo.
    member_attr = 'member' 
    # Certifique-se que user_dn e group_dn são strings. LDAP geralmente espera bytes.
    mod_attrs = [(ldap.MOD_ADD, member_attr.encode('utf-8'), [user_dn.encode('utf-8')])]
    try:
        conn.modify_s(group_dn.encode('utf-8'), mod_attrs)
        print(f"Usuário {user_dn} adicionado ao grupo {group_dn}")
    except ldap.ALREADY_EXISTS:
        print(f"Usuário {user_dn} já é membro do grupo {group_dn}") # Não é um erro crítico
    except ldap.LDAPError as e:
        print(f"Erro ao adicionar usuário {user_dn} ao grupo {group_dn}: {e}")
        raise # Re-lança para tratamento na rota

def remove_user_from_group(conn, user_dn, group_dn):
    """Remove um usuário (pelo seu DN) de um grupo (pelo seu DN)."""
    member_attr = 'member'
    mod_attrs = [(ldap.MOD_DELETE, member_attr.encode('utf-8'), [user_dn.encode('utf-8')])]
    try:
        conn.modify_s(group_dn.encode('utf-8'), mod_attrs)
        print(f"Usuário {user_dn} removido do grupo {group_dn}")
    except ldap.NO_SUCH_ATTRIBUTE:
        print(f"Usuário {user_dn} não era membro (ou atributo {member_attr} não existe) do grupo {group_dn}") # Não é um erro crítico
    except ldap.LDAPError as e:
        print(f"Erro ao remover usuário {user_dn} do grupo {group_dn}: {e}")
        raise
