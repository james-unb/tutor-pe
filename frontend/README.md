# TutorPE - Frontend

SPA em React + TypeScript que serve de interface para o tutor de IA e para os simulados do TutorPE. Consome a API descrita em [`../backend/README.md`](../backend/README.md).

## 🛠️ Stack

- **React 19** + **TypeScript**, com build via **Vite**.
- **React Router** para as rotas (`/simulados`, `/simulados/:id/play`, `/simulados/:id/performance`, `/chat/:id`).
- **SCSS Modules** para estilo, com tema claro/escuro.
- **Axios** para chamadas HTTP.
- **KaTeX** / **react-katex** para renderizar fórmulas em LaTeX.
- **@react-oauth/google** para o login com Google.

## 🚀 Como rodar

```bash
npm install
npm run dev
```

Crie um `.env` com:

```
VITE_BACKEND_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=<client id do Google OAuth>
```

Outros scripts: `npm run build` (typecheck + build), `npm run lint`, `npm run preview`.

## 📁 Estrutura

```
src/
├── pages/           # Login, Chat, Simulados, SimuladoPlayer, SimuladoPerformance
├── components/      # QuestionCard, QuestionChat, Sidebar, CreateSimuladoModal, Logo
├── layouts/          # MainLayout (sidebar + área de conteúdo)
├── contexts/         # AuthContext, ChatContext, ThemeContext
├── services/         # api.ts (axios) e simuladosApi.ts
├── lib/               # parseEnunciado.ts e utils.tsx (renderização de LaTeX)
└── types/             # tipos compartilhados (ex.: simulado.ts)
```
