# TutorPE - Backend

Este é o backend do projeto TutorPE, desenvolvido com Django e Django REST Framework. Ele fornece uma API para o sistema de chat educativo e autenticação.

## 🚀 Como Rodar o Projeto

Este projeto utiliza **Docker** e **Docker Compose** para facilitar a configuração e execução do ambiente de desenvolvimento.

### Pré-requisitos

Certifique-se de ter instalado em sua máquina:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Passo a Passo

1. **Clone o repositório** (se ainda não o fez).

2. **Configuração do `.env`**  
   Crie um arquivo `.env` na raiz da pasta `backend` a partir do `.env.example`:

   ```bash
   cp .env.example .env
   ```

   Edite o `.env` e preencha as variáveis:

   | Variável | Descrição |
   |----------|-----------|
   | `GEMINI_KEY` | Chave da API do Google Gemini (IA) |
   | `GEMINI_MODEL` | Nome do modelo Gemini (ex.: `gemini-1.5-flash`) |
   | `GOOGLE_CLIENT_ID` | Client ID do Google (login com Google) |
   | `JWT_SECRET` | Chave secreta para assinatura dos tokens JWT |
   | `DATABASE_NAME` | Nome do banco (padrão: `database`) |
   | `DATABASE_USER` | Usuário do banco (padrão: `user`) |
   | `DATABASE_PASSWORD` | Senha do banco (padrão: `pass`) |
   | `DATABASE_HOST` | Deixe `localhost` no `.env`; o Compose sobrescreve com `database` no container |
   | `DATABASE_PORT` | Porta do PostgreSQL (padrão: `5432`) |

3. **Subir os containers**  
   Na raiz do `backend`, construa e inicie os serviços:

   ```bash
   docker-compose up --build
   ```

   O backend ficará em `http://localhost:8000`. O PostgreSQL sobe na porta `5432`.

4. **Extração/importação dos dados**  
   Com os containers em execução, rode **os dois** comandos de importação:

   **a) Questões educativas (LaTeX)** — base de questões do tutor:

   ```bash
   docker-compose exec tutor_pe_backend python manage.py import_questions
   ```

   **b) Questões de simulados** — provas em `ETL/QuestoesProvas`:

   ```bash
   docker-compose exec tutor_pe_backend python manage.py import_sim_questions
   ```

   Opcional: use `--clean` em cada comando para limpar as tabelas correspondentes antes de importar (ex.: `import_sim_questions --clean`).

---

## 📡 Documentação da API

Todas as rotas estão sob o prefixo `/api/`. Endpoints que exigem autenticação devem enviar o header `Authorization: Bearer <JWT_TOKEN>`.

### Autenticação

#### `POST /api/login/google/`

Login ou cadastro com credenciais do Google.

- **Body (JSON)**:
  ```json
  {
    "credential": "GOOGLE_JWT_TOKEN"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "user": {
      "email": "user@gmail.com",
      "name": "User Name",
      "photo_url": "https://..."
    },
    "token": "JWT_ACCESS_TOKEN"
  }
  ```

### Chat

#### `POST /api/chat/`

Envia uma mensagem para o agente de IA.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Body (JSON)**:
  ```json
  {
    "message": "Explique a questão 5",
    "session_id": "uuid-da-sessao"
  }
  ```
  `session_id` é opcional; se omitido, uma nova sessão é criada.
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "session_id": "uuid-da-sessao",
    "title": "Explique a questão 5...",
    "data": {
      "items": [
        { "type": "text", "content": "Explicação..." },
        { "type": "formula", "content": "x^2 + y" }
      ],
      "question_data": { ... }
    }
  }
  ```

#### `GET /api/chat/history/`

Lista os chats (sessões) do usuário.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200 OK)**:
  ```json
  [
    {
      "id": "uuid-da-sessao",
      "title": "Título do Chat",
      "timestamp": "14/12/2025 10:00"
    }
  ]
  ```

#### `GET /api/chat/<session_id>/`

Retorna o histórico de mensagens de uma sessão.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200 OK)**:
  ```json
  [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "Olá",
      "timestamp": "10:00"
    },
    {
      "id": "msg-uuid",
      "role": "assistant",
      "content": "Olá! Como posso ajudar?",
      "timestamp": "10:01",
      "question_data": { ... }
    }
  ]
  ```

### Simulados

#### `GET /api/simulados/`

Lista os simulados do usuário. Query opcional: `?prova=<id>` para filtrar por prova.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200 OK)**:
  ```json
  [
    {
      "id": "uuid",
      "prova": 1,
      "dificuldade_media": 2.5,
      "concluido": false,
      "nota": null,
      "tempo_segundos": null,
      "created_at": "2025-02-16T12:00:00Z"
    }
  ]
  ```

#### `POST /api/simulados/`

Cria um novo simulado a partir de uma prova.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Body (JSON)**:
  ```json
  {
    "prova": 1,
    "target_dificuldade": 2.5
  }
  ```
  `prova` é obrigatório; `target_dificuldade` é opcional.
- **Response (201 Created)**:
  ```json
  {
    "status": "success",
    "id": "uuid",
    "prova": 1,
    "dificuldade_media": 2.5,
    "concluido": false,
    "nota": null,
    "tempo_segundos": null,
    "created_at": "2025-02-16T12:00:00Z",
    "questions": [
      {
        "id": 123,
        "conteudo": "...",
        "dificuldade": 2,
        "order": 1
      }
    ]
  }
  ```

#### `GET /api/simulados/<id>/`

Retorna um simulado específico com as questões e a resposta do usuário em cada uma.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200 OK)**:
  ```json
  {
    "id": "uuid",
    "prova": 1,
    "dificuldade_media": 2.5,
    "concluido": false,
    "nota": null,
    "tempo_segundos": null,
    "created_at": "2025-02-16T12:00:00Z",
    "questions": [
      {
        "id": 123,
        "conteudo": "...",
        "dificuldade": 2,
        "order": 1,
        "resposta_usuario": "A"
      }
    ]
  }
  ```

#### `GET /api/simulados/<id>/questoes/`

Retorna as questões do simulado com enunciado, alternativas e (se concluído) solução.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 123,
      "order": 1,
      "conteudo": "...",
      "materia": "...",
      "enunciado": "LaTeX limpo",
      "dificuldade": 2,
      "resposta_usuario": "A",
      "alternativas": ["A) ...", "B) ...", "C) ...", "D) ...", "E) ..."],
      "solucao": "..."
    }
  ]
  ```
  O campo `solucao` só é retornado quando o simulado está concluído.

#### `POST /api/simulados/<id>/submeter/`

Registra a resposta do usuário para uma questão.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Body (JSON)**:
  ```json
  {
    "question_id": 123,
    "resposta": "A"
  }
  ```
  `resposta`: alternativa (ex.: `"A"`, `"B"`).
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Resposta salva."
  }
  ```
- **Erros**: 400 se o simulado já foi finalizado; 404 se o simulado ou a questão não existir.

#### `POST /api/simulados/<id>/finalizar/`

Finaliza o simulado, calcula a nota e retorna acertos/total.

- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Body (JSON)** (opcional):
  ```json
  {
    "tempo_segundos": 3600
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "status": "success",
    "nota": 7.5,
    "acertos": 15,
    "total": 20,
    "tempo_segundos": 3600
  }
  ```
- **Erros**: 400 se o simulado já tiver sido finalizado; 404 se o simulado não existir.

---

## 🛠️ Tecnologias

- **Python 3.11**
- **Django & Django REST Framework**
- **PostgreSQL**
- **Docker & Docker Compose**
