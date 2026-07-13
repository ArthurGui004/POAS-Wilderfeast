# Wilderfeast API (FastAPI)

API do RPG Wilderfeast — sistema de fichas Feral e Bestiário.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

A API sobe em `http://localhost:8000`. Documentação interativa em `/docs`.

## Estrutura

```
app/
  main.py          # instância FastAPI, CORS, arquivos estáticos, rotas
  config.py        # configurações (settings via pydantic-settings)
  database.py      # engine assíncrono SQLAlchemy + Base + get_db
  security.py      # hashing de senha e JWT
  deps.py          # dependências de autenticação (get_current_user)
  seed.py          # condições padrão inseridas na primeira execução
  models/          # Feral, Utensilio, FeralEstilo, FeralHabilidade, Traco,
                    #   Monstro, Condicao, User
  schemas/         # Pydantic — validação de entrada/saída
  routers/
    auth.py        # POST /auth/register, /auth/login, GET /auth/me
    feral.py       # CRUD de fichas de personagem (Feral)
    bestiario.py   # CRUD do bestiário (Monstro)
static/uploads/     # imagens enviadas por upload (fichas e bestas)
```

## Autenticação

JWT (Bearer token). Após login/registro, envie o token no header:
`Authorization: Bearer <token>`.

## Variáveis de ambiente (opcional)

Crie um `.env` na pasta `backend/` se quiser sobrescrever os padrões:

```
SECRET_KEY=troque-por-um-segredo-forte
DATABASE_URL=sqlite+aiosqlite:///./wilderfeast.db
```
