# 🧾 Processador de NFe

Sistema automatizado para processamento de arquivos XML de Notas Fiscais Eletrônicas (NFe), com monitoramento em tempo real e armazenamento em banco de dados SQLite.

## 🚀 Funcionalidades

- **Monitoramento automático** de pasta para novos arquivos XML
- **Processamento recursivo** de XMLs em subpastas (configurável)
- **Processamento em tempo real** de NFe
- **Extração de dados** do cabeçalho e itens da NFe
- **Armazenamento** em banco de dados SQLite
- **Organização automática** de arquivos processados
- **Sistema de logs** com rotação automática
- **Tratamento de erros** com movimentação para pasta específica
- **Prevenção de conflitos** com nomes únicos para arquivos duplicados

## 📋 Requisitos

- Python 3.7+
- Dependências listadas em `requirements.txt`

## 🛠️ Instalação

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/luizelias8/processador-nfe.git
   cd processador-nfe
   ```

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o sistema:**
   ```bash
   cp config.exemplo.yaml config.yaml
   ```

   Edite o arquivo `config.yaml` com suas configurações personalizadas.

## ⚙️ Configuração

O arquivo `config.yaml` permite personalizar:

### Processador
- `pasta_xml`: Pasta monitorada para novos arquivos XML
- `pasta_processados`: Destino dos arquivos processados com sucesso
- `pasta_erros`: Destino dos arquivos com erro no processamento
- `banco_dados`: Caminho do arquivo do banco SQLite
- `busca_recursiva`: Processa XMLs em subpastas (true/false)

### Logging
- `nivel`: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `formato`: Formato das mensagens de log
- `pasta_log`: Pasta onde serão salvos os arquivos de log
- `rotacao`: Configurações de rotação automática de logs

### Exemplo de Configuração
```yaml
processador:
  pasta_xml: './xml_nfe'
  pasta_processados: './processados'
  pasta_erros: './erros'
  banco_dados: './nfe_database.db'
  busca_recursiva: true  # Processa XMLs em subpastas

logging:
  nivel: 'INFO'
  formato: '%(asctime)s | %(levelname)8s | %(message)s'
  pasta_log: './logs'
  nome_arquivo: 'processador_nfe.log'
```

## 🚀 Uso

### Execução
```bash
python processador_nfe.py
```

### Organização de Arquivos

O sistema suporta duas formas de organização:

#### 1. Pasta Simples (busca_recursiva: false)
```
xml_nfe/
├── arquivo1.xml
├── arquivo2.xml
└── arquivo3.xml
```

#### 2. Organização em Subpastas (busca_recursiva: true)
```
xml_nfe/
├── 2024/
│   ├── janeiro/
│   │   ├── nfe_001.xml
│   │   └── nfe_002.xml
│   └── fevereiro/
│       └── nfe_003.xml
├── fornecedor_a/
│   ├── nfe_a001.xml
│   └── nfe_a002.xml
└── fornecedor_b/
    └── nfe_b001.xml
```

### Fluxo de Processamento

1. O sistema monitora a pasta `xml_nfe/` (ou conforme configurado)
2. **Com busca recursiva ativada**, monitora também todas as subpastas
3. Quando um novo arquivo XML é detectado:
   - **Processa** e extrai dados da NFe
   - **Salva** no banco de dados SQLite com rastreamento do caminho original
   - **Move** para pasta `processados/` se bem-sucedido
   - **Move** para pasta `erros/` se houver problemas
   - **Gera nome único** se já existir arquivo com mesmo nome
4. Logs são gerados automaticamente com rotação diária

### Estrutura do Banco de Dados

**Tabela `nfe_cabecalho`:**
- Dados principais da NFe (chave, número, emitente, destinatário, valores)
- `arquivo_xml`: Nome do arquivo processado
- `caminho_original`: Caminho original do arquivo (para rastreabilidade)

**Tabela `nfe_itens`:**
- Detalhes dos produtos/serviços da NFe

## 📁 Estrutura de Pastas

```
processador-nfe/
├── processador_nfe.py      # Script principal
├── config.exemplo.yaml     # Exemplo de configuração
├── config.yaml            # Configuração personalizada (criada pelo usuário)
├── requirements.txt        # Dependências Python
├── xml_nfe/               # Pasta monitorada (criada automaticamente)
│   ├── subpasta1/         # Subpastas opcionais (se busca_recursiva=true)
│   └── subpasta2/
├── processados/           # Arquivos processados (criada automaticamente)
├── erros/                 # Arquivos com erro (criada automaticamente)
├── logs/                  # Arquivos de log (criada automaticamente)
└── nfe_database.db        # Banco SQLite (criado automaticamente)
```

## 🔧 Recursos Avançados

### Busca Recursiva
- **Ativada**: Processa XMLs em todas as subpastas
- **Desativada**: Processa apenas XMLs na pasta raiz
- Configurável via `busca_recursiva` no arquivo de configuração

### Prevenção de Conflitos
- Gera nomes únicos automaticamente quando arquivos têm o mesmo nome
- Exemplo: `nfe.xml` → `nfe_001.xml`, `nfe_002.xml`

### Rastreabilidade
- Campo `caminho_original` no banco registra de onde veio cada arquivo
- Útil para organização por período, fornecedor, etc.

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request
