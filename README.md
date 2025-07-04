# 🧾 Processador de NFe

Sistema automatizado para processamento de arquivos XML de Notas Fiscais Eletrônicas (NFe), com monitoramento em tempo real e armazenamento em banco de dados SQLite.

## 🚀 Funcionalidades

- **Monitoramento automático** de pasta para novos arquivos XML
- **Processamento em tempo real** de NFe
- **Extração de dados** do cabeçalho e itens da NFe
- **Armazenamento** em banco de dados SQLite
- **Organização automática** de arquivos processados
- **Sistema de logs** com rotação automática
- **Tratamento de erros** com movimentação para pasta específica

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

### Logging
- `nivel`: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `formato`: Formato das mensagens de log
- `pasta_log`: Pasta onde serão salvos os arquivos de log
- `rotacao`: Configurações de rotação automática de logs

## 🚀 Uso

### Execução
```bash
python processador_nfe.py
```

### Fluxo de Processamento

1. O sistema monitora a pasta `xml_nfe/` (ou conforme configurado)
2. Quando um novo arquivo XML é detectado:
   - **Processa** e extrai dados da NFe
   - **Salva** no banco de dados SQLite
   - **Move** para pasta `processados/` se bem-sucedido
   - **Move** para pasta `erros/` se houver problemas
3. Logs são gerados automaticamente com rotação diária

### Estrutura do Banco de Dados

**Tabela `nfe_cabecalho`:**
- Dados principais da NFe (chave, número, emitente, destinatário, valores)

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
├── processados/           # Arquivos processados (criada automaticamente)
├── erros/                 # Arquivos com erro (criada automaticamente)
├── logs/                  # Arquivos de log (criada automaticamente)
└── nfe_database.db        # Banco SQLite (criado automaticamente)
```

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request
