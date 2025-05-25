# Exemplo de config.py
LDAP_SERVER_URI = 'ldap://seu-servidor-ldap:389'
LDAP_BASE_DN = 'dc=example,dc=com'  # Seu Base DN principal
LDAP_USER_BASE_DN = 'ou=users,dc=example,dc=com'  # Onde os usuários estão
LDAP_GROUP_BASE_DN = 'ou=groups,dc=example,dc=com' # Onde os grupos estão

# Credenciais de um usuário LDAP com permissão para administrar
# ATENÇÃO: Não suba senhas para o repositório em produção! Use variáveis de ambiente.
LDAP_BIND_DN = 'cn=admin,dc=example,dc=com'
LDAP_BIND_PASSWORD = 'senha-do-admin-ldap'

# Credenciais para proteger a própria interface web de administração
# (Pode ser um usuário LDAP específico ou credenciais separadas)
ADMIN_USERNAME = 'admin_interface'
ADMIN_PASSWORD = 'senha_interface_segura'

# Chave secreta para o Flask (usada para sessões, flash messages, etc.)
SECRET_KEY = 'uma-chave-secreta-muito-forte-e-aleatoria'

# Outras configurações
# DEBUG = True # Apenas para desenvolvimento
