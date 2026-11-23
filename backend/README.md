# Wilderfeast API

A API FastAPI gerencia as fichas dos Ferais, seus inventários e atributos, e o bestiário. Execute os comandos abaixo a partir da pasta `backend`.

## Executar localmente

Use Python 3.13 ou 3.14. No Windows, prepare o ambiente com PowerShell.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-api.txt
```

Em Linux ou macOS, ative o ambiente com `source .venv/bin/activate`. O arquivo `requirements-api.txt` inclui as dependências do servidor, dos testes e da importação dos catálogos. O arquivo `requirements.txt` também inclui ferramentas usadas para extrair materiais de origem.

Para habilitar o envio de fotos dos Ferais, configure `CLOUDINARY_URL` no ambiente do backend ou no `.env` local, com o valor da sua conta Cloudinary no formato `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`. Reinicie a API após configurar. Os arquivos ficam na pasta `wilderfeast/ferais` do Cloudinary, e a ficha guarda a URL pública HTTPS da imagem.

Para usar SQLite, crie um arquivo `.env` nesta pasta.

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./wilderfeast.db
```

Para PostgreSQL, configure `DATABASE_URL` com o endereço do banco. A API aceita URLs `postgresql://` e `postgresql+asyncpg://`. Em produção, defina também `SECRET_KEY` com um segredo persistente, compartilhado pelos processos da mesma instância. Sem essa variável, cada processo gera sua própria chave e as sessões expiram ao reiniciar.

```sh
python -m uvicorn app.main:app --port 8000
```

A documentação interativa fica em [localhost:8000/docs](http://localhost:8000/docs).

## Publicar a API

Use um banco PostgreSQL persistente e configure `DATABASE_URL` e `SECRET_KEY` no ambiente do serviço. A partir da pasta `backend`, instale `requirements-api.txt` e inicie o Uvicorn. O comando abaixo lê a porta da variável `PORT` do serviço.

```sh
python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
```

A API aplica as migrações e preenche o Bestiário e os catálogos antes de receber tráfego. O banco novo recebe **40 monstros** e **seis utensílios oficiais**. Reiniciar a API adiciona os registros que faltam e conserva o vigor e a durabilidade atuais dos registros existentes, além das fichas e dos inventários dos jogadores. Se a preparação falhar, verifique os logs do serviço antes de reiniciar.

A inicialização grava as URLs públicas do Cloudinary em `imagem_url` nos registros padrão que ainda estão sem imagem. As consultas do bestiário, do catálogo e do inventário devolvem esse campo.

## Rotas do jogo

| Recurso | Operações |
| --- | --- |
| Conta | `POST /auth/registro`, `POST /auth/login` (formulário OAuth2) e `POST /auth/logout` |
| Fichas | `POST /feral/`, `GET /feral/meus`, `GET`, `PUT` e `DELETE /feral/{id}` |
| Bestiário | `GET /monstro/` lista as feras. `GET /monstro/{id}` inclui comportamento, estilos, habilidades, traços, partes, técnicas e efeitos de quebra. |
| Utensílios | `GET /utensilio/` lista os modelos comuns e, com autenticação, também os modelos pessoais do usuário. Os mesmos IDs podem ser escolhidos ao criar um Feral. |
| Inventário | `GET /feral/{id}/inventario` lista os itens da ficha. `PUT /feral/{id}/inventario/{item_id}` ajusta a durabilidade. |
| Atributos | `GET /feral/{id}/atributos` retorna os catálogos com os valores da ficha. `PUT` na mesma rota grava um atributo por vez. |

As operações da ficha exigem o token do proprietário no cabeçalho `Authorization: Bearer <token>`. Para criar um Feral, envie o ID escolhido em `utensilio_id` no corpo de `POST /feral/`. A API valida a opção e grava a ficha e seu utensílio inicial em uma única transação, com durabilidade máxima. Ao chegar a zero, o item fica quebrado. Ao reparar o item, ele volta a funcionar. Estilos e habilidades aceitam pontos inteiros a partir de zero. Traços e condições aceitam 0 (inativo) ou 1 (ativo).

A migração inclui Barbante, Cutelo, Espeto, Luvas, Maçarico e Panela com os dados revisados do catálogo inicial. Novos registros em `utensilio` ficam disponíveis assim que são salvos. Deixe `usuario_id` nulo para incluir o utensílio no catálogo de todos os jogadores.

## Testes

```sh
python -m unittest discover -s tests -v
```

Os testes criam contas, fichas e itens em bancos SQLite temporários.
