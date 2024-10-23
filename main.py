import requests
import paramiko
from zipfile import ZipFile
import io
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Configurando logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurações de autenticação e SFTP
GRAPHQL_URL = 'https://graphql.intelipost.com.br/'
SFTP_HOST = "edi-prd-v1.intelipost.com.br"
SFTP_PORT = 22
SFTP_PATH = "/client67224/RODONAVES/NOTFIS"  # Caminho fixo no FTP
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
SFTP_USERNAME = os.getenv('SFTP_USERNAME')
SFTP_PASSWORD = os.getenv('SFTP_PASSWORD')

# ID fixo da transportadora
TRANSPORTADORA_ID = '31'

def pegar_data_atual():
    """Define automaticamente o intervalo de datas como a data corrente."""
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    logging.info(f"Usando a data corrente: {data_hoje} para ambos início e fim do intervalo.")
    return data_hoje, data_hoje

def autenticar():
    """Autentica no GraphQL usando as credenciais do .env."""
    if not EMAIL or not PASSWORD:
        logging.error("Credenciais não definidas. Verifique o arquivo .env.")
        exit(1)

    query = """
    query ($email: String!, $password: String!) {
      login(email: $email, password: $password) {
        authf2
        user {
          token
          access_token
        }
      }
    }
    """

    variaveis = {
        "email": EMAIL,
        "password": PASSWORD
    }

    payload = {
        'operationName': None,
        'query': query,
        'variables': variaveis
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept-Language': 'pt-BR,pt;q=0.9',
    }

    try:
        resposta = requests.post(GRAPHQL_URL, json=payload, headers=headers)
        resposta.raise_for_status()
        dados_autenticacao = resposta.json().get('data', {}).get('login')

        if dados_autenticacao and 'user' in dados_autenticacao:
            token_acesso = dados_autenticacao['user'].get('access_token')
            if token_acesso:
                logging.info("Autenticado com sucesso.")
                return token_acesso
            else:
                logging.error("Token de acesso não encontrado.")
        else:
            logging.error("Erro na estrutura de resposta da autenticação.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro na autenticação via GraphQL: {e}")
        exit(1)

    return None

def obter_url_download(token_acesso, data_inicial, data_final):
    """Faz a requisição para o GraphQL e retorna o link para download do arquivo ZIP."""
    headers = {
        'Authorization': f'Bearer {token_acesso}',
        'Content-Type': 'application/json',
        'Accept-Language': 'pt-BR,pt;q=0.9',
    }

    query = """
    query($logistic_provider_id: String, $file_type: String, $date_range_start: String, $date_range_end: String, $order_status: [String]) {
        generatePslBatchDownloadUrl(logistic_provider_id: $logistic_provider_id, file_type: $file_type, date_range_start: $date_range_start, date_range_end: $date_range_end, order_status: $order_status) {
            download_url
        }
    }
    """

    variaveis = {
        'logistic_provider_id': TRANSPORTADORA_ID,
        'file_type': 'txt',
        'date_range_start': data_inicial,
        'date_range_end': data_final,
        'order_status': [],
    }

    payload = {
        'query': query,
        'variables': variaveis,
    }

    try:
        resposta = requests.post(GRAPHQL_URL, json=payload, headers=headers)
        resposta.raise_for_status()
        url_download = resposta.json()['data']['generatePslBatchDownloadUrl']['download_url']
        logging.info(f"URL de download obtido: {url_download}")
        return url_download
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro na requisição GraphQL: {e}")
        exit(1)
    except KeyError:
        logging.error("Erro ao parsear a resposta do GraphQL.")
        logging.error(resposta.text)
        exit(1)

def baixar_arquivo_zip(url_download):
    """Baixa o arquivo ZIP usando a URL fornecida."""
    try:
        resposta = requests.get(url_download)
        resposta.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao baixar o arquivo: {e}")
        exit(1)

    if resposta.headers.get('Content-Type') != 'application/zip':
        logging.error("Erro: o arquivo baixado não é um ZIP válido.")
        exit(1)

    return io.BytesIO(resposta.content)

def conectar_sftp():
    """Estabelece a conexão SFTP com os detalhes fixos do .env."""
    try:
        transporte = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transporte.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
        sftp = paramiko.SFTPClient.from_transport(transporte)
        logging.info("Conexão SFTP estabelecida com sucesso.")
        return sftp, transporte
    except paramiko.ssh_exception.SSHException as e:
        logging.error(f"Erro ao conectar no SFTP: {e}")
        exit(1)

def extrair_e_enviar_arquivos(zip_file, sftp, caminho_sftp, data_atual):
    with ZipFile(zip_file, 'r') as zip_ref:
        for nome_arquivo in zip_ref.namelist():
            if nome_arquivo.endswith('.txt'):
                f"{nome_arquivo.rsplit('.', 1)[0]}-{data_atual}.txt"
                logging.info(f"Extraindo e enviando {nome_arquivo} para o SFTP...")

                # Lê o arquivo diretamente do ZIP
                with zip_ref.open(nome_arquivo) as arquivo:
                    # Faz o upload diretamente do conteúdo do arquivo
                    with sftp.open(f"{caminho_sftp}/{nome_arquivo}", 'wb') as arquivo_sftp:
                        arquivo_sftp.write(arquivo.read())

                logging.info(f"Arquivo {nome_arquivo} enviado para o SFTP com sucesso!")


def main():
    # Define o intervalo de datas automaticamente para o dia corrente
    data_inicial, data_final = pegar_data_atual()

    # Autentica no GraphQL
    token_acesso = autenticar()

    # Obter a URL para download
    logging.info("Obtendo o link de download...")
    url_download = obter_url_download(token_acesso, data_inicial, data_final)

    # Baixar o arquivo ZIP
    logging.info("Baixando o arquivo ZIP...")
    zip_file = baixar_arquivo_zip(url_download)

    # Conectar ao SFTP
    logging.info("Conectando ao SFTP...")
    sftp, transporte = conectar_sftp()

    # Extrair e enviar os arquivos diretamente para o SFTP
    extrair_e_enviar_arquivos(zip_file, sftp, SFTP_PATH, data_inicial)

    # Fechar a conexão SFTP
    sftp.close()
    transporte.close()

if __name__ == "__main__":
    main()
