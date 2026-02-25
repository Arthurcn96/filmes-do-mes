_DISCLAIMER: Esse texto foi gerado por IA_
# 🎬 Filmes do Mês

<p align="center">
  <img src="https://img.shields.io/github/last-commit/Arthurcn96/filmes-do-mes?logo=github&style=for-the-badge">
  <img src="https://img.shields.io/github/repo-size/Arthurcn96/filmes-do-mes?style=for-the-badge&logo=appveyor">
  <img src="https://img.shields.io/badge/Status-Finalizando-red?style=for-the-badge&logo=appveyor">
</p>

Lista os melhores filmes lançados no mês atual em cada ano desde 1960, ordenados por nota.  

O projeto é totalmente estático e atualizado automaticamente usando **TMDb API + GitHub Actions**.

É uma página web simples, os **20 melhores filmes lançados no mês atual** sempre atualizando pra cada novo mês

🔗 Link: https://arthurcn96.github.io/filmes-do-mes/

## 🛠️ Pré‑requisitos

Antes de rodar localmente, você precisa:

1. **Python 3.11+**
2. Conta no **TMDb** e uma **API Key**
3. Criar um arquivo `.env` com a API Key:


## 🔄 GitHub Actions — Atualização automatizada

O workflow em `.github/workflows/update-cache.yml` foi configurado para rodar em 2 vezes ao mês

Ele:

1. Executa `populate.py` que atualiza os dados dos filmes ultimos 3 anos (do mês atual).
2. Atualiza a lista de filmes`cache.json`
3. Faz commit automático no repo

Assim o site fica sempre com dados atualizados.

## 📄 Licença

Projeto de código aberto — sinta‑se à vontade para clonar, contribuir e aprender!
