"""
Import questions from LaTeX files in ETL/QuestoesProvas into QuestionFromCSV.
Uses clean_latex for frontend-compatible rendering (KaTeX).
"""
import os
import re
import glob
import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from api_rest.models import QuestionFromCSV
from api_rest.utils.latex_utils import clean_latex

# Regex for extraction. Two formats supported:
# (1) One Solution block at end of file (banco-provas style): use REGEX_ENUNCIADOS + REGEX_SOLUCAO once.
# (2) Each \item has Question then Solution inside it: use REGEX_ITEM_QUESTION to get full blocks, then split each at \textbf{Solution}.
REGEX_ENUNCIADOS = re.compile(
    r'\\item\s*\\textbf\{Question\}(.*?)(?=\\item\s*\\textbf\{Question\}|\s*\\textbf\{Solution\})',
    re.DOTALL | re.IGNORECASE,
)
REGEX_SOLUCAO = re.compile(
    r'\\textbf\{Solution\}(.*?)(?=\\item\s*\\textbf\{Question\}|\Z)',
    re.DOTALL | re.IGNORECASE,
)
# Full block per item: from \item \textbf{Question} until next \item \textbf{Question} or end
REGEX_ITEM_QUESTION = re.compile(
    r'\\item\s*\\textbf\{Question\}(.*?)(?=\\item\s*\\textbf\{Question\}|\Z)',
    re.DOTALL | re.IGNORECASE,
)
REGEX_SOLUCAO_IN_BLOCK = re.compile(
    r'\\textbf\{Solution\}(.*?)(?=\\item\s*\\textbf\{Question\}|\Z)',
    re.DOTALL | re.IGNORECASE,
)

# Alternatives: optional ")}" separator then "AltA. AltB. ..." or \item[(a)] ... \item[(b)] ...
SEP_ALTERNATIVAS = ')}'
LABELS_ALTERNATIVAS = ['A', 'B', 'C', 'D', 'E']


def parse_filename(nome_arquivo: str):
    """
    Parse filename convention: {conteudo}_{materia}_{modelo}.tex or .latex
    Returns (conteudo, materia, modelo) or None on failure.
    """
    nome = nome_arquivo.replace('.latex', '').replace('.tex', '')
    partes = nome.split('_')
    if len(partes) < 2:
        return None
    try:
        conteudo = int(partes[0])
        modelo = int(partes[-1])
        materia = '_'.join(partes[1:-1])
        return conteudo, materia, modelo
    except (ValueError, IndexError):
        return None


def infer_prova_from_path(file_path: str) -> int:
    """Infer prova number from path (Prova1, Prova2, Prova3). Default 1."""
    path_lower = file_path.replace('\\', '/').lower()
    if 'prova3' in path_lower:
        return 3
    if 'prova2' in path_lower:
        return 2
    if 'prova1' in path_lower:
        return 1
    return 1


def extract_alternatives_from_enunciado(raw_enunciado: str):
    """
    Extract 5 alternatives from question block.
    Option A: ")} AltA. AltB. AltC. AltD. AltE." (split by ". ").
    Option B: \\item[(a)] ... \\item[(b)] ... (regex).
    Option C: first \\begin{enumerate}...\\end{enumerate} with 5 plain \\item (no bracket).
    Returns list of 5 strings (raw LaTeX); if not 5, returns list of 5 empty strings.
    """
    out = ['', '', '', '', '']
    # Option A: after ")}" we have "AltA. AltB. AltC. AltD. AltE." (plain text with ". " separator).
    # Do NOT use this when ")}" comes from \def\labelenumii{(\alph{enumii})} and the rest is
    # LaTeX \item content (would wrongly split at "vs. " etc.).
    if SEP_ALTERNATIVAS in raw_enunciado:
        idx = raw_enunciado.rfind(SEP_ALTERNATIVAS) + len(SEP_ALTERNATIVAS)
        after = raw_enunciado[idx:].strip()
        # Skip Option A if what follows looks like enumerate items (e.g. "\item" or "\n  \item")
        if '\\item' not in after[:80]:
            parts = re.split(r'\.\s+', after, maxsplit=5)
            if len(parts) >= 5:
                for i in range(5):
                    out[i] = parts[i].strip()
                    if out[i] and not out[i].endswith('.'):
                        out[i] += '.'
                return out

    # Option B: \item[(a)] ... \item[(b)] ...
    subitem_pattern = re.compile(
        r'\\item\[\s*\(?([a-e])\)?\s*\](?P<content>.*?)(?=\s*\\item\[|\s*\\end\{itemize\}|\Z)',
        re.DOTALL | re.IGNORECASE,
    )
    matches = list(subitem_pattern.finditer(raw_enunciado))
    if len(matches) >= 5:
        for m in matches[:5]:
            letter = m.group(1).lower()
            idx_letter = ord(letter) - ord('a')
            if 0 <= idx_letter < 5:
                out[idx_letter] = m.group('content').strip()
        return out

    # Option C: inner enumerate with 5 plain \item (e.g. \def\labelenumii{(\alph{enumii})} then \item ... \item ...)
    inner_enum = re.search(
        r'\\begin\{enumerate\}\s*(?P<content>.*?)\\end\{enumerate\}',
        raw_enunciado,
        re.DOTALL,
    )
    if inner_enum:
        inner = inner_enum.group('content')
        # Match \item optionally followed by [...] then content until next \item or end
        plain_items = re.findall(
            r'\\item\s*(?:\[.*?\])?\s*(?P<content>.*?)(?=\s*\\item\s*(?:\[.*?\])?\s*|\s*\\end\{enumerate\}|\Z)',
            inner,
            re.DOTALL,
        )
        if len(plain_items) >= 5:
            for i in range(5):
                out[i] = plain_items[i].strip()
            return out

    return out


def _remove_first_enumerate_block(text: str) -> str:
    """
    Remove the first \\begin{enumerate}...\\end{enumerate} block from text.
    Aligns with listas: enunciado should not contain the alternatives block (no \\def\\labelenumii).
    """
    return re.sub(
        r'\\begin\{enumerate\}\s*.*?\\end\{enumerate\}',
        '',
        text,
        count=1,
        flags=re.DOTALL,
    ).strip()


def split_statement_and_alternatives(raw_enunciado: str):
    """
    Split raw question block into statement (without alternatives block) and list of 5 alternative texts.
    Statement is the part before ")}" only when that ")}" is the Option A separator (plain "AltA. AltB. ...");
    otherwise use full text and remove the first \\begin{enumerate}...\\end{enumerate} so the stored
    enunciado never contains \\def\\labelenumii or the alternatives LaTeX.
    """
    alternativas_raw = extract_alternatives_from_enunciado(raw_enunciado)
    statement_raw = raw_enunciado
    if SEP_ALTERNATIVAS in raw_enunciado:
        idx = raw_enunciado.rfind(SEP_ALTERNATIVAS)
        after = raw_enunciado[idx + len(SEP_ALTERNATIVAS):].strip()
        # Only treat ")}" as statement end when it's Option A format (no \item after ")}")
        if '\\item' not in after[:80]:
            parts = re.split(r'\.\s+', after, maxsplit=5)
            if len(parts) >= 5:
                statement_raw = raw_enunciado[:idx].strip()
    statement_without_alternatives_block = _remove_first_enumerate_block(statement_raw)
    return statement_without_alternatives_block, alternativas_raw


def normalize_gabarito_solucao(solucao_raw: str, alternativas_list: list) -> tuple:
    """
    Detect the gabarito (correct letter) from a ")} Falso ... Verdadeiro ..." answer-key
    marker left over from the exam source's alternative-selector markup, wherever that
    marker appears in the extracted text.
    Returns (solucao_normalized, gabarito_letra) where solucao_normalized never contains
    the raw marker - it is answer-key bookkeeping, not part of the solution explanation,
    and was otherwise leaking verbatim into what students read and what gets sent as
    context to the AI tutor.
    """
    if not solucao_raw or not solucao_raw.strip():
        return "", None

    # Already has the pattern (check explicitly for ")} Falso" or ")} Verdadeiro" to avoid matching \labelenumii)
    if ')} Falso' in solucao_raw or ')} Verdadeiro' in solucao_raw:
        head, _, tail = solucao_raw.rpartition(')}')
        partes_solucao = tail.strip().split()
        gabarito = None
        for idx, word in enumerate(partes_solucao):
            if "Verdadeiro" in word:
                gabarito = chr(65 + idx)
                break
        return head.strip(), gabarito

    # Detect last enumerate in solution with \item Falso / \item Verdadeiro (order = A..E)
    all_enums = re.findall(
        r'\\begin\{enumerate\}(.*?)\\end\{enumerate\}',
        solucao_raw,
        re.DOTALL | re.IGNORECASE,
    )
    if all_enums:
        last_enum = all_enums[-1]
        items = re.findall(
            r'\\item\s*(.*?)(?=\s*\\item\s*|\s*\\end\{enumerate\}|\Z)',
            last_enum,
            re.DOTALL | re.IGNORECASE,
        )
        if len(items) >= 5:
            gabarito = None
            for idx, t in enumerate(items[:5]):
                if 'Verdadeiro' in t:
                    gabarito = chr(65 + idx)
                    break
            if gabarito:
                return solucao_raw.strip(), gabarito

    # Try to detect "letra [A-E]" or "alternativa [A-E]" or "(A)" etc.
    letra_match = re.search(
        r'(?:letra|alternativa)\s*(?:correta)?\s*[:\s]*\(?([A-Ea-e])\)?',
        solucao_raw,
        re.IGNORECASE,
    )
    if letra_match:
        letter = letra_match.group(1).upper()
        return solucao_raw.strip(), letter

    # Unknown format: keep original; backend may not infer gabarito
    return solucao_raw.strip(), None


class Command(BaseCommand):
    help = (
        'Imports questions from LaTeX files in ETL/QuestoesProvas into QuestionFromCSV. '
        'Uses clean_latex for enunciado, alternativas, and solucao.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete all QuestionFromCSV records before importing. Existing simulados may reference orphaned question_id.',
        )

    def load_dificuldade_map(self, base_dir: str):
        """
        Load optional dificuldade.csv: rows with filename or index, columns prova, dificuldade.
        Returns dict: key = (file_basename or index), value = (prova, dificuldade).
        """
        path = os.path.join(base_dir, 'dificuldade.csv')
        if not os.path.isfile(path):
            return {}
        result = {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fn = row.get('filename') or row.get('file') or row.get('arquivo')
                    if not fn and reader.fieldnames:
                        fn = row.get(reader.fieldnames[0], '')
                    try:
                        prova = int(row.get('prova', 1))
                    except (TypeError, ValueError):
                        prova = 1
                    try:
                        dificuldade = float(row.get('dificuldade', 0.5))
                    except (TypeError, ValueError):
                        dificuldade = 0.5
                    result[fn.strip()] = (prova, dificuldade)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not load dificuldade.csv: {e}'))
        return result

    def load_matriz_dificuldades(self, base_dir: str):
        """
        Load matrix CSV (e.g. matriz.dificuldades.NOVA.final.csv): separator ";",
        columns Nome.questao, percentual. Returns dict: key = filename with .Rnw -> .latex,
        value = dificuldade (float). Prova is NOT from CSV; it is set by file index in handle().
        """
        for name in ('matriz.dificuldades.NOVA.final.csv', 'matriz.dificuldades.csv'):
            path = os.path.join(base_dir, name)
            if not os.path.isfile(path):
                continue
            result = {}
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                    f.seek(0)
                    sep = ';' if ';' in first_line else ','
                    reader = csv.DictReader(f, delimiter=sep)
                    for row in reader:
                        nome = (row.get('Nome.questao') or row.get('nome') or row.get('Nome') or '').strip()
                        if not nome:
                            continue
                        nome_latex = nome.replace('.Rnw', '.latex').replace('.rnw', '.latex').strip()
                        raw_percentual = (row.get('percentual') or row.get('dificuldade') or '0.5').strip()
                        try:
                            result[nome_latex] = float(raw_percentual.replace(',', '.'))
                        except (TypeError, ValueError):
                            result[nome_latex] = 0.5
                if result:
                    self.stdout.write(self.style.SUCCESS(f'Loaded dificuldade for {len(result)} files from {name}'))
                return result
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not load {name}: {e}'))
        return {}

    def _prova_from_file_index(self, file_index: int) -> int:
        """Same as banco-provas: first 100 files -> prova 1, 101-200 -> 2, 201+ -> 3."""
        if file_index < 100:
            return 1
        if file_index < 200:
            return 2
        return 3

    def handle(self, *args, **options):
        # ETL/QuestoesProvas relative to CWD (same as import_questions uses ETL/Data)
        base_dir = os.path.join('ETL', 'QuestoesProvas')
        if not os.path.isdir(base_dir):
            self.stdout.write(
                self.style.ERROR(f'Directory not found: {base_dir}. Create it and add .tex/.latex files.')
            )
            return

        if options['clean']:
            self.stdout.write(self.style.WARNING('Cleaning QuestionFromCSV...'))
            count = QuestionFromCSV.objects.count()
            QuestionFromCSV.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} records. Existing simulados may have orphan question_id.'))

        dificuldade_map = self.load_dificuldade_map(base_dir)  # key -> (prova, dificuldade)
        matriz_map = self.load_matriz_dificuldades(base_dir)   # key -> dificuldade
        default_dificuldade = 0.5

        # Glob .tex and .latex recursively
        patterns = [
            os.path.join(base_dir, '**', '*.tex'),
            os.path.join(base_dir, '**', '*.latex'),
            os.path.join(base_dir, '*.tex'),
            os.path.join(base_dir, '*.latex'),
        ]
        seen_paths = set()
        all_files = []
        for p in patterns:
            for path in glob.glob(p):
                path = os.path.normpath(path)
                if path not in seen_paths:
                    seen_paths.add(path)
                    all_files.append(path)

        if not all_files:
            self.stdout.write(self.style.WARNING(f'No .tex or .latex files found under {base_dir}'))
            return

        total_saved = 0
        with transaction.atomic():
            for file_index, file_path in enumerate(sorted(all_files)):
                nome_arquivo = os.path.basename(file_path)
                parsed = parse_filename(nome_arquivo)
                if not parsed:
                    self.stdout.write(self.style.WARNING(f'Skipping (invalid filename): {nome_arquivo}'))
                    continue

                conteudo, materia, modelo = parsed
                # Prova by sorted file index (same as banco-provas: 1-100 -> 1, 101-200 -> 2, 201+ -> 3)
                prova = self._prova_from_file_index(file_index)
                if nome_arquivo in dificuldade_map:
                    _, dificuldade = dificuldade_map[nome_arquivo]
                elif nome_arquivo in matriz_map:
                    dificuldade = matriz_map[nome_arquivo]
                else:
                    dificuldade = default_dificuldade

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    try:
                        with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error reading {nome_arquivo}: {e}'))
                        continue

                # Detect format: each \item has its own \textbf{Solution} vs one Solution block at end
                full_blocks = REGEX_ITEM_QUESTION.findall(content)
                if not full_blocks:
                    self.stdout.write(self.style.WARNING(f'No Question blocks in {nome_arquivo}'))
                    continue

                per_item_solution = '\\textbf{Solution}' in full_blocks[0] or '\\textbf{solution}' in full_blocks[0]
                if per_item_solution:
                    # Format 2: each block = question + \textbf{Solution} + solution text
                    enunciado_blocks = []
                    solucao_blocks = []
                    for block in full_blocks:
                        sol_in_block = REGEX_SOLUCAO_IN_BLOCK.search(block)
                        if sol_in_block:
                            solucao_blocks.append(sol_in_block.group(1).strip())
                            # Question part is before \textbf{Solution}
                            idx = block.lower().find('\\textbf{solution}')
                            if idx >= 0:
                                enunciado_blocks.append(block[:idx].strip())
                            else:
                                enunciado_blocks.append(block)
                        else:
                            enunciado_blocks.append(block)
                            solucao_blocks.append('')
                else:
                    # Format 1: separate Solution block at end
                    enunciado_blocks = REGEX_ENUNCIADOS.findall(content)
                    solucao_match = REGEX_SOLUCAO.search(content)
                    one_solucao = (solucao_match.group(1).strip() if solucao_match else '').strip()
                    if not one_solucao:
                        one_solucao = 'SOLUCAO_NAO_ENCONTRADA'
                    solucao_blocks = [one_solucao] * len(enunciado_blocks)

                for i, block in enumerate(enunciado_blocks):
                    versao = i + 1
                    statement_raw, alternativas_raw = split_statement_and_alternatives(block)
                    solucao_raw = solucao_blocks[i] if i < len(solucao_blocks) else ''
                    if not solucao_raw:
                        solucao_raw = 'SOLUCAO_NAO_ENCONTRADA'
                    solucao_normalized, gabarito_letra = normalize_gabarito_solucao(solucao_raw, alternativas_raw)

                    enunciado_clean = clean_latex(statement_raw.strip())
                    alternativas_clean = [clean_latex(a or '').strip() for a in alternativas_raw]
                    if len(alternativas_clean) != 5:
                        alternativas_clean = (alternativas_clean + [''] * 5)[:5]
                    solucao_clean = clean_latex(solucao_normalized)

                    question_id = f"v_{versao}pr_{prova}_p_{conteudo}_m_{modelo}({materia})"

                    QuestionFromCSV.objects.update_or_create(
                        id=question_id,
                        defaults={
                            'prova': prova,
                            'conteudo': conteudo,
                            'modelo': modelo,
                            'versao': versao,
                            'dificuldade': dificuldade,
                            'materia': materia,
                            'enunciado': enunciado_clean,
                            'alternativas': alternativas_clean,
                            'solucao': solucao_clean,
                            'gabarito': gabarito_letra,
                        },
                    )
                    total_saved += 1

                self.stdout.write(self.style.SUCCESS(f'  {nome_arquivo}: {len(enunciado_blocks)} questions'))

        self.stdout.write(self.style.SUCCESS(f'Import completed. Total questions saved: {total_saved}.'))
