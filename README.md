# 🎬 Letterboxd Recommender

Um projeto de estudo para criar um sistema inteligente de recomendação de filmes baseado no perfil do Letterboxd do usuário.

## 📋 Status Atual

**Versão:** 1.0 - Sorteador Básico  
**Status:** ✅ Funcional

Atualmente o projeto funciona como um **sorteador aleatório** que:
- Recebe o username do Letterboxd
- Faz web scraping da watchlist do usuário
- Sorteia um filme aleatório da lista
- Exibe o resultado em uma interface web simples

## 🚀 Como Executar

### Pré-requisitos
- Python 3.7+
- pip

### Instalação
1. Clone o repositório:
```bash
git clone https://github.com/SEU_USUARIO/letterboxd-recommender.git
cd letterboxd-recommender
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute o servidor:
```bash
uvicorn main:app --reload
```

5. Acesse `http://127.0.0.1:8000` no seu navegador

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python, FastAPI, Uvicorn
- **Web Scraping:** Requests, BeautifulSoup4
- **Frontend:** HTML, CSS, JavaScript vanilla
- **Outras:** Lxml para parsing

## 📁 Estrutura do Projeto

```
letterboxd-recommender/
├── frontend/
│   ├── index.html          # Interface web
│   └── script.js           # Lógica do frontend
├── venv/                   # Ambiente virtual
├── main.py                 # API FastAPI
├── scraper.py              # Web scraping do Letterboxd
├── requirements.txt        # Dependências do projeto
└── README.md              # Este arquivo
```

## 🎯 Roadmap - Funcionalidades Futuras

### Versão 2.0 - Recomendador Inteligente
- [ ] Análise de padrões temporais (dias da semana, época do ano)
- [ ] Consideração de feriados e datas especiais
- [ ] Análise do histórico de filmes logados
- [ ] Sistema de categorias personalizáveis

### Versão 3.0 - IA e Análise Avançada
- [ ] Integração com APIs de IA para análise mais sofisticada
- [ ] Análise de sentimentos das reviews
- [ ] Recomendações baseadas em mood/contexto
- [ ] Sistema de filtros avançados

### Melhorias Técnicas
- [ ] Banco de dados para cache de dados
- [ ] Autenticação com Letterboxd
- [ ] API própria para outras aplicações
- [ ] Interface mais robusta (possivelmente React)
- [ ] Deploy em produção

## 🤝 Contribuições

Este é um projeto de estudo pessoal, mas sugestões e feedback são sempre bem-vindos! 

## 📝 Notas de Desenvolvimento

- **Objetivo:** Aprender programação através de um projeto prático
- **Metodologia:** Desenvolvimento incremental, começando simples e evoluindo
- **Aprendizados:** Web scraping, APIs, frontend/backend, estruturação de projetos

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**⚠️ Aviso:** Este projeto é apenas para fins educacionais. Respeite os termos de uso do Letterboxd.
**🍿 Me siga no Letterboxd:** [letterboxd.com/guickz](https://letterboxd.com/guickz/) 📽️