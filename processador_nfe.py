import os
import sqlite3
import yaml
import logging
import logging.handlers
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import xmltodict
from datetime import datetime

def carregar_configuracoes(arquivo_config=None):
    """
    Carrega todas as configurações do arquivo YAML unificado.

    Args:
        arquivo_config (str, optional): Caminho do arquivo de configuração

    Returns:
        dict: Dicionário com as configurações organizadas por seção
    """
    # Diretório base do script
    base_dir = Path(__file__).parent.resolve()

    if arquivo_config is None:
        arquivo_config = base_dir / 'config.yaml'
    else:
        arquivo_config = Path(arquivo_config)

    # Configurações padrão
    configuracoes_padrao = {
        'processador': {
            'pasta_xml': './xml_nfe',
            'pasta_processados': './processados',
            'pasta_erros': './erros',
            'banco_dados': './nfe_database.db',
            'busca_recursiva': True
        },
        'logging': {
            'nivel': 'INFO',
            'formato': '%(asctime)s | %(levelname)8s | %(message)s',
            'formato_data': '%Y-%m-%d %H:%M:%S',
            'pasta_log': './logs',
            'nome_arquivo': 'processador_nfe.log',
            'rotacao': {
                'when': 'D',
                'interval': 1,
                'backup_count': 7
            }
        }
    }

    try:
        if arquivo_config.exists():
            print(f'Carregando configurações de: {arquivo_config}')

            with open(arquivo_config, 'r', encoding='utf-8') as f:
                # Carregar todos os documentos YAML do arquivo
                documentos = list(yaml.safe_load_all(f))

            # Mesclar documentos em um único dicionário de configurações
            configuracoes = {}
            for doc in documentos:
                if doc is not None:
                    configuracoes.update(doc)

            # Verificar e completar configurações faltantes
            for secao, config_padrao in configuracoes_padrao.items():
                if secao not in configuracoes:
                    configuracoes[secao] = config_padrao
                else:
                    # Verificar sub-configurações
                    for chave, valor_padrao in config_padrao.items():
                        if chave not in configuracoes[secao]:
                            configuracoes[secao][chave] = valor_padrao
                        elif isinstance(valor_padrao, dict) and isinstance(configuracoes[secao][chave], dict):
                            # Verificar configurações aninhadas (como rotacao)
                            for sub_chave, sub_valor_padrao in valor_padrao.items():
                                if sub_chave not in configuracoes[secao][chave]:
                                    configuracoes[secao][chave][sub_chave] = sub_valor_padrao

            print('Configurações carregadas com sucesso')
            return configuracoes

        else:
            print(f"Arquivo 'config.yaml' não encontrado!")
            print('Por favor, copie o arquivo config.exemplo.yaml para config.yaml')
            print('e edite com suas preferências antes de executar o programa.')
            exit(1)

    except yaml.YAMLError as e:
        print(f'Erro ao interpretar YAML: {e}')
        print(f"Verifique a sintaxe do arquivo 'config.yaml'")
        exit(1)
    except Exception as e:
        print(f'Erro ao carregar configurações: {e}')
        exit(1)

def configurar_logging(config_log):
    """
    Configura o sistema de logging para arquivo e terminal.

    Args:
        config_log (dict): Configurações de logging
    """
    # Diretório base do script
    base_dir = Path(__file__).parent.resolve()

    # Criar pasta de logs se não existir
    pasta_log = (base_dir / config_log['pasta_log']).resolve() # Converte esse caminho em um caminho absoluto, eliminando possíveis referências relativas como . ou ...
    pasta_log.mkdir(parents=True, exist_ok=True)

    # Arquivo de log
    caminho_log = pasta_log / config_log['nome_arquivo']

    # Configurar nível de log
    nivel_log = getattr(logging, config_log['nivel'].upper(), logging.INFO)

    # Configurar logging
    logging.basicConfig(
        level=nivel_log,
        format=config_log['formato'],
        datefmt=config_log['formato_data'],
        handlers=[
            # Rotação do arquivo de log com base no tempo
            logging.handlers.TimedRotatingFileHandler(
                filename=str(caminho_log),
                when=config_log['rotacao']['when'],
                interval=config_log['rotacao']['interval'],
                backupCount=config_log['rotacao']['backup_count'],
                encoding='utf-8'
            ),
            logging.StreamHandler()
        ]
    )

    # Log inicial
    logging.info('=' * 60)
    logging.info('Sistema de logging configurado')
    logging.info(f'Pasta de logs: {pasta_log}')
    logging.info(f'Arquivo de log: {caminho_log}')
    logging.info(f'Rotação: {config_log["rotacao"]["when"]} - Intervalo: {config_log["rotacao"]["interval"]} - Backup: {config_log["rotacao"]["backup_count"]}')
    logging.info('=' * 60)

class ProcessadorNFe(FileSystemEventHandler):
    """
    Classe principal que gerencia o processamento de arquivos XML de NFe.
    Herda de FileSystemEventHandler para responder a eventos do sistema de arquivos.
    """


    def __init__(self, config_processador):
        """
        Inicializa o processador de NFe.

        Args:
            config_processador (dict): Configurações do processador
        """
        super().__init__() # Chamaro construtor da classe pai.

        # Diretório base do script
        self.base_dir = Path(__file__).parent.resolve()

        # Armazenar configurações
        self.config = config_processador

        # Resolver caminhos absolutos
        self.pasta_xml = (self.base_dir / self.config['pasta_xml']).resolve()
        self.pasta_processados = (self.base_dir / self.config['pasta_processados']).resolve()
        self.pasta_erros = (self.base_dir / self.config['pasta_erros']).resolve()
        self.banco_dados = (self.base_dir / self.config['banco_dados']).resolve()

        # Configuração de busca recursiva
        self.busca_recursiva = self.config.get('busca_recursiva', True)

        # Criar pastas necessárias
        self.criar_pastas()

        # Inicializar banco de dados
        self.inicializar_banco()

        logging.info('Processador de NFe inicializado')
        logging.info(f'Pasta XML: {self.pasta_xml}')
        logging.info(f'Pasta processados: {self.pasta_processados}')
        logging.info(f'Pasta erros: {self.pasta_erros}')
        logging.info(f'Banco de dados: {self.banco_dados}')
        logging.info(f'Busca recursiva: {"Ativada" if self.busca_recursiva else "Desativada"}')

    def criar_pastas(self):
        """Cria as pastas necessárias se não existirem"""
        pastas = [self.pasta_xml, self.pasta_processados, self.pasta_erros]

        for pasta in pastas:
            if not pasta.exists():
                pasta.mkdir(parents=True, exist_ok=True)
                logging.info(f'Pasta criada: {pasta}')

    def inicializar_banco(self):
        """Inicializa o banco de dados SQLite com as tabelas necessárias"""
        try:
            conn = sqlite3.connect(str(self.banco_dados))
            cursor = conn.cursor()

            # Tabela para cabeçalho da NFe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nfe_cabecalho (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave_acesso TEXT UNIQUE NOT NULL,
                    numero_nf TEXT,
                    serie TEXT,
                    data_emissao DATE,
                    data_saida_entrada DATE,
                    tipo_operacao TEXT,
                    cnpj_emitente TEXT,
                    nome_emitente TEXT,
                    cnpj_destinatario TEXT,
                    nome_destinatario TEXT,
                    valor_total REAL,
                    valor_icms REAL,
                    valor_pis REAL,
                    valor_cofins REAL,
                    arquivo_xml TEXT,
                    caminho_original TEXT,
                    data_processamento DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela para itens da NFe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS nfe_itens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chave_acesso TEXT NOT NULL,
                    numero_item INTEGER,
                    codigo_produto TEXT,
                    descricao_produto TEXT,
                    cfop TEXT,
                    unidade_comercial TEXT,
                    quantidade_comercial REAL,
                    valor_unitario_comercial REAL,
                    valor_total_produto REAL,
                    valor_icms REAL,
                    valor_pis REAL,
                    valor_cofins REAL,
                    FOREIGN KEY (chave_acesso) REFERENCES nfe_cabecalho (chave_acesso)
                )
            """)

            conn.commit()
            conn.close()
            logging.info('Banco de dados inicializado com sucesso')

        except Exception as e:
            logging.error(f'Erro ao inicializar banco de dados: {e}')
            exit(1)

    def extrair_dados_nfe(self, xml_dict):
        """Extrai dados da NFe do dicionário XML"""
        try:
            # Navegar pela estrutura do XML
            nfe = xml_dict.get('NFe', {})
            inf_nfe = nfe.get('infNFe', {})

            # Dados de identificação
            ide = inf_nfe.get('ide', {})

            # Dados do emitente
            emit = inf_nfe.get('emit', {})

            # Dados do destinatário
            dest = inf_nfe.get('dest', {})

            # Totais
            total = inf_nfe.get('total', {})
            icms_tot = total.get('ICMSTot', {})

            # Detalhes dos produtos
            det = inf_nfe.get('det', [])
            if not isinstance(det, list):
                det = [det] # Se houver apenas um item, transformar em lista

            # Extrair chave de acesso do ID
            chave_acesso = inf_nfe.get('@Id', '').replace('NFe', '')

            # Dados do cabeçalho
            cabecalho = {
                'chave_acesso': chave_acesso,
                'numero_nf': ide.get('nNF', ''),
                'serie': ide.get('serie', ''),
                'data_emissao': self.converter_data(ide.get('dEmi', '')),
                'data_saida_entrada': self.converter_data(ide.get('dSaiEnt', '')),
                'tipo_operacao': ide.get('natOp', ''),
                'cnpj_emitente': emit.get('CNPJ', ''),
                'nome_emitente': emit.get('xNome', ''),
                'cnpj_destinatario': dest.get('CNPJ', ''),
                'nome_destinatario': dest.get('xNome', ''),
                'valor_total': float(icms_tot.get('vNF', 0)),
                'valor_icms': float(icms_tot.get('vICMS', 0)),
                'valor_pis': float(icms_tot.get('vPIS', 0)),
                'valor_cofins': float(icms_tot.get('vCOFINS', 0))
            }

            # Dados dos itens
            itens = []
            for item in det:
                prod = item.get('prod', {})
                imposto = item.get('imposto', {})

                # Extrair impostos
                icms = imposto.get('ICMS', {})
                icms_tipo = next(iter(icms.values())) if icms else {}

                pis = imposto.get('PIS', {})
                pis_tipo = next(iter(pis.values())) if pis else {}

                cofins = imposto.get('COFINS', {})
                cofins_tipo = next(iter(cofins.values())) if cofins else {}

                item_data = {
                    'chave_acesso': chave_acesso,
                    'numero_item': int(item.get('@nItem', 0)),
                    'codigo_produto': prod.get('cProd', ''),
                    'descricao_produto': prod.get('xProd', ''),
                    'cfop': prod.get('CFOP', ''),
                    'unidade_comercial': prod.get('uCom', ''),
                    'quantidade_comercial': float(prod.get('qCom', 0)),
                    'valor_unitario_comercial': float(prod.get('vUnCom', 0)),
                    'valor_total_produto': float(prod.get('vProd', 0)),
                    'valor_icms': float(icms_tipo.get('vICMS', 0)),
                    'valor_pis': float(pis_tipo.get('vPIS', 0)),
                    'valor_cofins': float(cofins_tipo.get('vCOFINS', 0))
                }
                itens.append(item_data)

            return cabecalho, itens

        except Exception as e:
            logging.error(f'Erro ao extrair dados da NFe: {e}')
            raise # Relança a exceção, fazendo com que ela suba para a função processar_xml, que foi quem chamou extrair_dados_nfe.

    def converter_data(self, data_str):
        """Converte string de data para formato SQLite"""
        try:
            if data_str:
                return datetime.strptime(data_str, '%Y-%m-%d').date()
            return None
        except:
            return None

    def gerar_nome_unico(self, arquivo_original, pasta_destino):
        """
        Gera um nome único para o arquivo, evitando conflitos.

        Args:
            arquivo_original (Path): Arquivo original
            pasta_destino (Path): Pasta de destino

        Returns:
            Path: Caminho único para o arquivo
        """
        nome_base = arquivo_original.stem
        extensao = arquivo_original.suffix
        contador = 1

        # Começar com o nome original
        nome_destino = pasta_destino / arquivo_original.name

        # Se já existe, adicionar contador
        while nome_destino.exists():
            novo_nome = f'{nome_base}_{contador:03d}-{extensao}'
            nome_destino = pasta_destino / novo_nome
            contador += 1

        return nome_destino

    def salvar_no_banco(self, cabecalho, itens, nome_arquivo, caminho_original):
        """Salva os dados da NFe no banco de dados"""
        try:
            conn = sqlite3.connect(str(self.banco_dados))
            cursor = conn.cursor()

            # Adicionar informações do arquivo ao cabeçalho
            cabecalho['arquivo_xml'] = nome_arquivo
            cabecalho['caminho_original'] = str(caminho_original)

            # Inserir cabeçalho
            cursor.execute("""
                INSERT OR REPLACE INTO nfe_cabecalho (
                    chave_acesso, numero_nf, serie, data_emissao,
                    data_saida_entrada, tipo_operacao, cnpj_emitente, nome_emitente,
                    cnpj_destinatario, nome_destinatario, valor_total, valor_icms,
                    valor_pis, valor_cofins, arquivo_xml, caminho_original
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )

            """, (
                cabecalho['chave_acesso'], cabecalho['numero_nf'], cabecalho['serie'], cabecalho['data_emissao'],
                cabecalho['data_saida_entrada'], cabecalho['tipo_operacao'], cabecalho['cnpj_emitente'], cabecalho['nome_emitente'],
                cabecalho['cnpj_destinatario'], cabecalho['nome_destinatario'], cabecalho['valor_total'], cabecalho['valor_icms'],
                cabecalho['valor_pis'], cabecalho['valor_cofins'], cabecalho['arquivo_xml'], cabecalho['caminho_original']
            ))

            # Remover itens existentes para esta chave de acesso
            cursor.execute('DELETE FROM nfe_itens WHERE chave_acesso = ?', (cabecalho['chave_acesso'],))

            # Inserir itens
            for item in itens:
                cursor.execute("""
                    INSERT INTO nfe_itens (
                        chave_acesso, numero_item, codigo_produto, descricao_produto,
                        cfop, unidade_comercial, quantidade_comercial, valor_unitario_comercial,
                        valor_total_produto, valor_icms, valor_pis, valor_cofins
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    item['chave_acesso'], item['numero_item'], item['codigo_produto'], item['descricao_produto'],
                    item['cfop'], item['unidade_comercial'], item['quantidade_comercial'], item['valor_unitario_comercial'],
                    item['valor_total_produto'], item['valor_icms'], item['valor_pis'], item['valor_cofins']
                ))

            conn.commit()
            conn.close()

            logging.info(f'NFe salva no banco: {cabecalho["numero_nf"]} - {len(itens)} itens')

        except Exception as e:
            logging.error(f'Erro ao salvar no banco de dados: {e}')
            raise # Relança a exceção, fazendo com que ela suba para a função processar_xml, que foi quem chamou salvar_no_banco.

    def processar_xml(self, arquivo_xml):
        """Processa um arquivo XML de NFe"""
        try:
            # Obter caminho relativo à pasta base de XML para logging
            try:
                caminho_relativo = arquivo_xml.relative_to(self.pasta_xml)
            except ValueError:
                caminho_relativo = arquivo_xml.name

            logging.info(f'Processando arquivo: {caminho_relativo}')

            # Ler e processar XML
            with open(arquivo_xml, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            # Converter XML para dicionário
            xml_dict = xmltodict.parse(xml_content)

            # Extrair dados
            cabecalho, itens = self.extrair_dados_nfe(xml_dict)

            # Salvar no banco
            self.salvar_no_banco(cabecalho, itens, arquivo_xml.name, caminho_relativo)

            # Mover arquivo para pasta de processados com nome único
            destino = self.gerar_nome_unico(arquivo_xml, self.pasta_processados)
            shutil.move(str(arquivo_xml), str(destino))

            logging.info(f'Arquivo processado com sucesso: {arquivo_xml.name}')

        except Exception as e:
            try:
                caminho_relativo = arquivo_xml.relative_to(self.pasta_xml)
            except ValueError:
                caminho_relativo = arquivo_xml.name

            logging.error(f'Erro ao processar {caminho_relativo}: {e}')

            # Mover arquivo para pasta de erros
            try:
                destino_erro = self.gerar_nome_unico(arquivo_xml, self.pasta_erros)
                shutil.move(str(arquivo_xml), str(destino_erro))
                logging.info(f'Arquivo movido para pasta de erros: {arquivo_xml.name}')
            except Exception as e2:
                logging.error(f'Erro ao mover arquivo para pasta de erros: {e2}')

    def on_created(self, event):
        """Chamado quando um novo arquivo é criado"""
        if not event.is_directory:
            arquivo = Path(event.src_path)

            # Verificar se é arquivo XML
            if arquivo.suffix.lower() != '.xml':
                logging.debug(f'Arquivo ignorado (não é XML): {arquivo.name}')
                return

            # Verificar se o arquivo está dentro da pasta monitorada
            try:
                arquivo.relative_to(self.pasta_xml)
            except ValueError:
                logging.debug(f'Arquivo fora da pasta monitorada: {arquivo}')
                return

            # Aguardar um pouco para garantir que o arquivo foi completamente copiado
            time.sleep(1)

            # Verificar se arquivo ainda existe
            if not arquivo.exists():
                logging.debug(f'Arquivo não existe mais: {arquivo.name}')
                return

            try:
                caminho_relativo = arquivo.relative_to(self.pasta_xml)
                logging.info(f'Novo arquivo XML detectado: {caminho_relativo}')
            except ValueError:
                logging.info(f'Novo arquivo XML detectado: {arquivo.name}')

            self.processar_xml(arquivo)

    def processar_arquivos_existentes(self):
        """Processa arquivos XML que já estão na pasta"""
        logging.info('Processando arquivos XML existentes...')
        arquivos_processados = 0

        # Escolher método de busca baseado na configuração
        if self.busca_recursiva:
            # Busca recursiva em todas as subpastas
            arquivos_xml = list(self.pasta_xml.rglob('*.xml'))
        else:
            # Busca apenas na pasta raiz
            arquivos_xml = list(self.pasta_xml.glob('*xml'))

        for arquivo in arquivos_xml:
            if arquivo.is_file():
                try:
                    caminho_relativo = arquivo.relative_to(self.pasta_xml)
                    logging.info(f'Processando arquivo existente: {caminho_relativo}')
                except ValueError:
                    logging.info(f'Processando arquivo existente: {arquivo.name}')

                self.processar_xml(arquivo)
                arquivos_processados += 1

        logging.info(f'Processamento inicial concluído! {arquivos_processados} arquivos processados')

def main():
    try:
        # Carregar todas as configurações
        configuracoes = carregar_configuracoes()

        # Configurar logging usando as configurações carregadas
        configurar_logging(configuracoes['logging'])

        logging.info('Iniciando processador de NFe...')

        # Criar o processador
        processador = ProcessadorNFe(configuracoes['processador'])

        logging.info(f'Diretório base: {processador.base_dir}')
        logging.info(f'Monitorando pasta: {processador.pasta_xml}')
        logging.info(f'Pasta processados: {processador.pasta_processados}')
        logging.info(f'Pasta erros: {processador.pasta_erros}')
        logging.info(f'Banco de dados: {processador.banco_dados}')
        logging.info('=' * 60)

        # Processar arquivos existentes
        processador.processar_arquivos_existentes()
        logging.info('=' * 60)

        # Configurar o observer
        observer = Observer()

        # No método .schedule, você passa:
        # 1. A instância da sua classe personalizada (que herdou de FileSystemEventHandler), que define como reagir aos eventos de arquivos (criação, modificação, etc.).
        # 2. O diretório que deseja monitorar.
        # Assim, o Observer vai monitorar esse diretório e chamar os métodos da sua classe (on_created, on_modified, etc.) sempre que ocorrerem eventos de sistema de arquivos.
        observer.schedule(processador, str(processador.pasta_xml), recursive=True)

        observer.start()

        logging.info('Monitoramento ativo! Pressione Ctrl+C para parar.')
        logging.info('=' * 60)

        # Manter o programa rodando
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info('Interrupção detectada - Parando o monitoramento...')
        observer.stop()
    except Exception as e:
        logging.error(f'Erro inesperado: {str(e)}')
        # Verifica se a variável observer foi definida no escopo local da função main() antes de tentar usá-la.
        # Por quê?
        # Se ocorrer uma exceção antes da linha observer = Observer(), a variável observer não existirá ainda.
        # Se você tentar chamar observer.stop() ou observer.join() sem essa verificação, causaria outro erro (NameError).
        if 'observer' in locals(): # A função locals() retorna um dicionário contendo todas as variáveis locais (nomes e valores) definidas no escopo atual da função.
            observer.stop()

    # Aguardar finalização do observer
    # Garante que só vai tentar parar (stop()) ou aguardar (join()) o observer se ele realmente foi criado.
    # É uma forma segura de evitar erros caso o programa falhe antes de chegar na criação do observer.
    if 'observer' in locals(): # # A função locals() retorna um dicionário contendo todas as variáveis locais (nomes e valores) definidas no escopo atual da função.
        observer.join()
        # O Observer roda em uma thread separada.
        # Quando você chama observer.stop(), pede para o monitoramento parar.
        # Faz o programa principal esperar até que a thread do observer termine de fato, garantindo um encerramento limpo e seguro.

    logging.info('Processador de NFe finalizado com sucesso!')

if __name__ == '__main__':
    main()
