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
