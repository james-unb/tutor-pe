# ETL/QuestoesProvas – Questões de provas (simulados)

Esta pasta contém os arquivos LaTeX das questões de provas usadas pelo comando `import_sim_questions` para popular a tabela `QuestionFromCSV` (simulados).

## Estrutura sugerida

- **Arquivos:** `.tex` ou `.latex` na raiz ou em subpastas.
- **Nome do arquivo:** `{conteudo}_{materia}_{modelo}.tex`  
  Exemplos:
  - `1_Algebra_2.tex` → conteudo=1, materia=Algebra, modelo=2  
  - `14_distribuicao_exponencial_03.latex` → conteudo=14, materia=distribuicao_exponencial, modelo=3  

- **Prova (1, 2 ou 3):**  
  - Se os arquivos estiverem em subpastas `Prova1/`, `Prova2/`, `Prova3/`, o número da prova é inferido pelo caminho.  
  - Caso contrário, usa-se prova 1 por padrão.  
  - Opcional: use o CSV `dificuldade.csv` nesta pasta para definir `prova` e `dificuldade` por arquivo.

## Formato do conteúdo LaTeX

- **Questões:** Vários blocos no formato  
  `\item \textbf{Question}` ... texto do enunciado ...  
  Cada bloco corresponde a uma versão (1 a 10) da mesma questão; o comando gera um registro por versão.

- **Solução:** Um único bloco  
  `\textbf{Solution}` ... texto da solução ...  
  Esse texto é associado a todas as versões do arquivo.

- **Alternativas (A–E):**  
  - **Opção A:** No enunciado, após o marcador `)}`, as cinco alternativas em sequência, separadas por ponto e espaço (ex.: ")} AltA. AltB. AltC. AltD. AltE.").  
  - **Opção B:** No enunciado, uso de itens numerados por letra: `\item[(a)] ...`, `\item[(b)] ...`, até (e).

## Dificuldade (opcional)

Crie `dificuldade.csv` nesta pasta com colunas, por exemplo:

- `filename` (ou `file` / `arquivo`): nome do arquivo .tex/.latex  
- `prova`: 1, 2 ou 3  
- `dificuldade`: número (ex.: 0.0–1.0)  

Se não existir o CSV, usa-se prova inferida pelo caminho e dificuldade padrão 0.5.

## Comando de importação

A partir do diretório `backend/`:

```bash
python manage.py import_sim_questions
```

Com `--clean` para apagar todas as questões em `QuestionFromCSV` antes de importar (simulados já criados podem ficar com questões inexistentes).
