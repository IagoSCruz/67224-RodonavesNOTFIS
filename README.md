# 67224-RodonavesNOTFIS
 Este script foi criado para automatizar uma rotina diária do time operacional da Stihl, que antes precisava baixar manualmente os arquivos EDI da transportadora Rodonaves pelo TMS e enviar por e-mail. Agora, com o script, esse processo é todo automatizado: ele acessa o TMS, baixa e extrai os arquivos referentes ao dia corrente, e deposita diretamente na pasta SFTP da Rodonaves, sem precisar de intervenção manual.

## Aplicação de Processamento EDI com Docker

Este projeto faz o download de arquivos EDI em formato `.zip` via uma requisição GraphQL, extrai os arquivos `.txt` e envia para um servidor SFTP. Cada arquivo extraído recebe um sufixo com a data do processamento antes de ser enviado. O projeto foi dockerizado para garantir consistência no ambiente de execução.

## Funcionalidades

- Download de arquivos `.zip` via GraphQL.
- Extração de arquivos `.txt` sem modificação de conteúdo.
- Adição de um sufixo com a data no nome dos arquivos.
- Envio dos arquivos para um servidor SFTP.
- Dockerização para facilitar a execução em qualquer ambiente.

---

## Como rodar localmente

### 1. Requisitos

- **Python 3.10+**
- **Docker** (para quem quiser rodar via container)
- Conta com acesso ao SFTP e GraphQL

### 2. Variáveis de ambiente

Crie um arquivo `.env` com suas configurações:

```bash
EMAIL=seu-email@example.com
PASSWORD=sua-senha
SFTP_USERNAME=usuario-sftp
SFTP_PASSWORD=senha-sftp
SFTP_HOST=edi-prd-v1.intelipost.com.br
GRAPHQL_URL=https://graphql.intelipost.com.br/

