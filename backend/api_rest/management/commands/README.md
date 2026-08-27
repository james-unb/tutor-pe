# Question Import Command

The `import_questions` management command is responsible for parsing LaTeX files containing academic questions, sub-items, and solutions, and importing them into the project's database.

## Directory Structure requirements

The command expects a specific directory structure under `backend/ETL/Data/`:

- `Lista {X}/`: A folder for each list (Assignment).
  - `Lista {X}.tex`: The main LaTeX file containing questions and items.
  - `Solução/` (or similar prefix): A subdirectory containing the solution LaTeX file.
    - `Solução {X}.tex`: The LaTeX file containing the solutions.

## Main Functions

### 1. `parse_questions(file_path, list_num)`

- **Purpose**: Extracts the main question stems (enunciados) from the main `.tex` file.
- **Mechanism**:
  1.  Uses a regex to find the primary `\begin{enumerate} ... \end{enumerate}` block.
  2.  Identifies each `\item` that is not a sub-item (label-less `\item`).
  3.  **Recursive Cleaning**: If a question contains a sub-list (`itemize`), it uses a nested helper to remove the sub-items from this specific block. This ensures the "main question" text only contains the preamble and not the text of sub-questions (a, b, c).
  4.  Applies `clean_latex()` to convert tables and formatting into HTML.
- **Output**: A list of dictionaries containing IDs, numbers, and the processed text.

### 2. `parse_items(file_path, list_num)`

- **Purpose**: Extracts sub-questions (items like 'a', 'b', 'c') from the main `.tex` file.
- **Mechanism**:
  1.  Locates the same `enumerate` block as above.
  2.  Splits the content into the same main question items.
  3.  Inside each question block, it looks for `\item[label]` patterns where the label is a letter (e.g., `(a)` or `b)`).
  4.  Strips parentheses/brackets from the label to create a clean `item_code`.
  5.  Applies `clean_latex()` to the item's content.
- **Output**: A list of dictionaries linking each sub-item to its parent question number.

### 3. `parse_latex_solutions(file_path, list_num)`

- **Purpose**: Extracts solutions from the separate solution file.
- **Mechanism**:
  1.  Finds the main `enumerate` block in the solution file.
  2.  Assumes the order of `\item` entries in the solution file matches the order of questions in the main file.
  3.  Identifies sub-item solutions (e.g., `\item[a)]`) within each solution block.
  4.  If sub-items exist, it creates separate solution records linked to specific items.
  5.  If no sub-items are found, it creates a single solution linked directly to the question.
- **Output**: A list of solution dictionaries with text processed via `clean_latex()`.

### 4. `handle(*args, **options)` (Main Entry Point)

- **Purpose**: Orchestrates the scanning of directories and the database save/update process.
- **Flow**:
  1.  Iterates through possible list numbers (1 to 99).
  2.  Locates the directory and creates/retrieves an `Assignment` object.
  3.  Locates the question `.tex` file and calls `parse_questions` and `parse_items`.
  4.  Updates or creates `Question` and `Item` records in the database.
  5.  Locates the solution folder/file and calls `parse_latex_solutions`.
  6.  Updates or creates `Solution` records, ensuring they are linked to the correct `Question` and `Item` objects.
- **Safety**: Uses `transaction.atomic()` to ensure that if something fails, the database isn't left in a partial state for that specific run.

## Dependencies

- **`api_rest.utils.latex_utils.clean_latex`**: Critical utility that converts LaTeX tables (`tabular`), specific number grids (Lista 7 style), and basic formatting (bold/italic) into HTML for the frontend.
- **`glob` & `re`**: Used for flexible file path detection and complex text extraction.

## Usage

Run the command from the backend directory:

```bash
python manage.py import_questions
```

_(Add `--clean` if you have implemented that flag to wipe the DB before import)_.

---

# Simulado Questions Import Command (`import_sim_questions`)

The `import_sim_questions` command reads LaTeX files from `ETL/QuestoesProvas`, formats them with `clean_latex`, and saves records into `QuestionFromCSV` (used by simulados).

## Directory and file format

- **Base directory:** `ETL/QuestoesProvas` (relative to the directory from which you run `manage.py`, typically `backend/`).
- **File naming:** `{conteudo}_{materia}_{modelo}.tex` or `.latex` (e.g. `1_Algebra_2.tex` → conteudo=1, materia=Algebra, modelo=2).
- **Prova:** Inferred from path (e.g. subfolders `Prova1/`, `Prova2/`, `Prova3/`). Default is 1.
- **Optional:** `ETL/QuestoesProvas/dificuldade.csv` with columns such as `filename`, `prova`, `dificuldade` to override prova and difficulty per file.

## LaTeX structure expected

- **Questions:** Blocks matching `\item \textbf{Question}...` (multiple blocks = multiple versions, e.g. 1–10 per file).
- **Solution:** One block matching `\textbf{Solution}...` (reused for all versions of that file).
- **Alternatives:** Either (A) in the question text after ")}" as "AltA. AltB. AltC. AltD. AltE." or (B) as `\item[(a)] ... \item[(b)] ...` (five items).

All text (enunciado, each alternative, solucao) is processed with `clean_latex` for correct display in the frontend (KaTeX). The solution is normalized so the backend/frontend can derive the correct answer (e.g. ")} Falso Falso Verdadeiro Falso Falso") when applicable.

## Usage

From the backend directory:

```bash
python manage.py import_sim_questions
```

Use `--clean` to delete all `QuestionFromCSV` rows before importing (existing simulados may then reference missing questions).

For more detail on the folder layout and file conventions, see `ETL/QuestoesProvas/README.md`.
