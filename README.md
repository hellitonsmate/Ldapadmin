# Gestor Web Simples para LDAP

Um projeto de interface web simples para facilitar o gerenciamento de usuários e grupos em um servidor LDAP. Desenvolvido com Python, Flask e a biblioteca `python-ldap`.

## 🎯 Visão Geral

Este projeto visa fornecer uma ferramenta administrativa básica e intuitiva para operações CRUD (Criar, Ler, Atualizar, Excluir) em usuários LDAP, bem como gerenciar a associação desses usuários a grupos, que por sua vez podem definir permissões de acesso em outros sistemas.

## ✨ Funcionalidades Principais

* **Listagem de Usuários:** Visualização de usuários existentes no LDAP.
* **Criação de Usuários:** Formulário para adicionar novos usuários com atributos essenciais (uid, nome, sobrenome, email, senha).
* **Edição de Usuários:** Modificação dos atributos de usuários existentes.
* **Exclusão de Usuários:** Remoção de usuários do diretório LDAP.
* **Alteração de Senha:** Interface para que o administrador defina uma nova senha para um usuário.
* **Gerenciamento de Grupos:**
    * Visualização de grupos existentes.
    * Associação de usuários a um ou mais grupos durante a criação ou edição do usuário.
    * (A criação de grupos em si pode ser uma funcionalidade futura ou gerenciada externamente).

## 🛠️ Tecnologias Utilizadas

* **Backend:**
    * Python 3.x
    * Flask (Microframework web)
    * `python-ldap` (Para interação com o servidor LDAP)
* **Frontend:**
    * HTML5
    * CSS (Exemplo: Bootstrap para estilização rápida)
    * JavaScript (Para interações básicas e validações no cliente)
    * Jinja2 (Mecanismo de template do Flask)
* **Servidor de Dados:**
    * Qualquer servidor LDAP compatível (OpenLDAP, 389 Directory Server, etc.)

## 📋 Pré-requisitos

Antes de começar, garanta que você tem os seguintes pré-requisitos instalados:

* Python 3.8 ou superior
* `pip` (Gerenciador de pacotes Python)
* Um servidor LDAP acessível e configurado.
* Bibliotecas de desenvolvimento LDAP e SASL (necessárias para compilar `python-ldap`):
    * No Debian/Ubuntu: `sudo apt-get install libldap2-dev libsasl2-dev`
    * No Fedora/CentOS: `sudo yum install openldap-devel cyrus-sasl-devel`

## ⚙️ Instalação e Configuração

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio-ldap-manager.git](https://github.com/seu-usuario/seu-repositorio-ldap-manager.git)
    cd seu-repositorio-ldap-manager
    ```

2.  **Crie e ative um ambiente virtual (recomendado):**
    ```bash
    python -m venv venv
    # No Windows
    # venv\Scripts\activate
    # No Linux/macOS
    # source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: Crie um arquivo `requirements.txt` com as bibliotecas Python, ex: `Flask`, `python-ldap`)*

4.  **Configure a Aplicação:**
    Copie o arquivo de exemplo `config.py.example` para `config.py` (ou configure via variáveis de ambiente, conforme sua implementação).
    ```bash
    cp config.py.example config.py
    ```
    Edite `config.py` com as informações do seu servidor LDAP e da aplicação:

    ```python
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
    ```

5.  **Schema LDAP:**
    Certifique-se de que seu schema LDAP suporta os `objectClass`es utilizados pela aplicação (ex: `inetOrgPerson`, `organizationalPerson`, `person` para usuários; e `groupOfNames` ou `posixGroup` para grupos) e os atributos correspondentes (`uid`, `cn`, `sn`, `givenName`, `mail`, `userPassword`, `member`).

## ▶️ Executando a Aplicação

Para iniciar o servidor de desenvolvimento Flask:

```bash
# Garanta que seu ambiente virtual está ativado
# flask run # Se você configurou o app via FLASK_APP=app.py
# OU
python app.py
