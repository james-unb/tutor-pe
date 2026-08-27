import os
import glob
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from api_rest.models import Assignments, Question, Item, Solution
from api_rest.utils.latex_utils import clean_latex

class Command(BaseCommand):
    help = 'Imports questions, items, and solutions directly from LaTeX files in ETL/Data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete all existing questions, items, and solutions before importing.',
        )

    def parse_questions(self, file_path, list_num):
        """
        Parses the main questions from a LaTeX file.
        Extracts the 'enumerate' block and identifies individual \item blocks as questions.
        Cleans the question text using clean_latex utility.
        """
        questions_data = []
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                full_content = f.read()

            # Find the main enumerate block which contains the questions
            enumerate_block = re.search(r'\\begin{enumerate}(.*?)\\end{enumerate}', full_content, re.DOTALL)

            if not enumerate_block:
                self.stdout.write(self.style.WARNING(f"Enumerate block not found in {file_path}"))
                return []

            clean_content = enumerate_block.group(1)

            # Pattern to match main items (questions), looking ahead to the next \item or end of string
            item_pattern = re.compile(
                r'\\item(.*?)(?=\s*\\item(?!\[)|$)',
                re.DOTALL
            )

            all_items = item_pattern.findall(clean_content)
            
            # Sub-patterns to handle itemize/sub-items within a question
            itemize_pattern = re.compile(r'\\begin\{itemize\}(.*?)\\end\{itemize\}', re.DOTALL)
            labeled_subitem_pattern = re.compile(
                r'\\item\[\s*(?:\([a-z]\)|[a-z]\))\s*\].*?(?=(?:\\item\[|\\item\b|\\end\{itemize\}|$))',
                re.DOTALL
            )

            for i, item_text in enumerate(all_items):
                question_id = f'l{list_num}q{i+1:02}'

                def _remove_subitems_from_header(match):
                    inner = match.group(1)
                    # Removing sub-items to keep only the main question preamble/text
                    cleaned_inner = labeled_subitem_pattern.sub('', inner)
                    
                    if not re.search(r'\\item\b', cleaned_inner):
                        return ''
                    return r'\begin{itemize}' + cleaned_inner + r'\end{itemize}'

                # Clean the question text by removing sub-item blocks for the main enunciado
                question_without_subitems = itemize_pattern.sub(_remove_subitems_from_header, item_text)
                final_question_text = clean_latex(question_without_subitems.strip())

                questions_data.append({
                    'question_id': question_id,
                    'list_num': list_num,
                    'question_num': i + 1,
                    'question_enunciado': final_question_text
                })

            return questions_data

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: File '{file_path}' was not found."))
            return []
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while parsing questions in {file_path}: {e}"))
            return []

    def parse_items(self, file_path, list_num):
        """
        Parses the sub-items (a, b, c...) for each question from the same LaTeX file.
        Uses regex to find \item[label] patterns within the question blocks.
        """
        items_data = []
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                full_content = f.read()

            enumerate_block = re.search(r'\\begin{enumerate}(.*?)\\end{enumerate}', full_content, re.DOTALL)

            if not enumerate_block:
                return []

            content_body = enumerate_block.group(1)

            main_item_pattern = re.compile(
                r'\\item(.*?)(?=\s*\\item(?!\[)|$)',
                re.DOTALL
            )
            all_main_items = main_item_pattern.findall(content_body)

            # Pattern for sub-items like (a), b), [a], etc.
            # Content must stop at next \item[, at \end{itemize} (avoid capturing table/trailing content), or end of string
            subitem_label_pattern = re.compile(
                r'\\item\[\s*(?P<label>\(?[a-z]\)?)\s*\](?P<content>.*?)(?=\s*\\item\[|\s*\\end\{itemize\}|\Z)',
                re.DOTALL
            )

            for i, item_text in enumerate(all_main_items):
                subitem_matches = subitem_label_pattern.finditer(item_text)
                for match in subitem_matches:
                    captured = match.groupdict()
                    raw_label = captured['label']
                    item_content = captured['content']
                    
                    # Clean label to get pure letter (e.g., 'a' instead of '(a)')
                    item_letter = raw_label.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
                    item_id = f'l{list_num}q{i+1:02}i{item_letter}'

                    items_data.append({
                        'item_id': item_id,
                        'list_num': list_num,
                        'question_num': i + 1,
                        'item_code': item_letter,
                        'item_enunciado': clean_latex(item_content.strip())
                    })
            return items_data

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while parsing items in {file_path}: {e}"))
            return []

    def parse_latex_solutions(self, file_path, list_num):
        """
        Parses solutions from a dedicated solution LaTeX file.
        Matches solutions to questions and specific items based on their order and labels.
        """
        solutions_data = []
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                full_content = f.read()

            enumerate_block = re.search(r'\\begin{enumerate}(.*?)\\end{enumerate}', full_content, re.DOTALL)
            if not enumerate_block:
                self.stdout.write(self.style.WARNING(f"Enumerate block not found in solution file {file_path}"))
                return []

            questions = re.findall(r'\\item(?!\[)(.*?)(?=\\item(?!\[)|\Z)', enumerate_block.group(1), re.DOTALL)

            for i, question_text in enumerate(questions):
                question_num = i + 1
                question_id = f'l{list_num}q{question_num:02}'

                subitems = re.findall(r'\\item\[([a-z])\)](.*?)(?=\\item\[|\Z)', question_text, re.DOTALL)
                if subitems:
                    for item_letter, solution_text in subitems:
                        id_sol = f'{question_id}i{item_letter}'
                        solutions_data.append({
                            'solution_id': id_sol,
                            'question_id': question_id,
                            'item_id': f'l{list_num}q{question_num:02}i{item_letter}',
                            'solution_text': clean_latex(solution_text.strip())
                        })
                else:
                    solutions_data.append({
                        'solution_id': question_id,
                        'question_id': question_id,
                        'item_id': None,
                        'solution_text': clean_latex(question_text.strip())
                    })

            return solutions_data

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Error: Solution file '{file_path}' was not found."))
            return []
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred while parsing solutions in {file_path}: {e}"))
            return []

    def handle(self, *args, **options):
        base_dir = os.path.join('ETL', 'Data')
        
        if not os.path.exists(base_dir):
            self.stdout.write(self.style.ERROR(f'Directory not found: {base_dir}'))
            return

        if options['clean']:
            self.stdout.write(self.style.WARNING('Cleaning database...'))
            Solution.objects.all().delete()
            Item.objects.all().delete()
            Question.objects.all().delete()
            Assignments.objects.all().delete()

        with transaction.atomic():
            # Scan directories named "Lista 1", "Lista 2", etc.
            for i in range(1, 100):
                list_dir_pattern = os.path.join(base_dir, f'Lista {i}')
                list_dirs = glob.glob(list_dir_pattern) 
                
                if not list_dirs:
                    if i > 10: # Safety break if no more lists are found
                        break
                    continue
                
                list_dir = list_dirs[0]
                self.stdout.write(self.style.SUCCESS(f'Processing List {i} in {list_dir}...'))
                
                # Create/Get Assignment object
                assignment_obj, _ = Assignments.objects.get_or_create(number=i)

                # Search for the main LaTeX file for the list
                tex_pattern = os.path.join(list_dir, f'Lista {i}.tex')
                tex_files = glob.glob(tex_pattern)
                
                if not tex_files:
                     tex_pattern = os.path.join(list_dir, f'Lista* {i}*.tex')
                     tex_files = glob.glob(tex_pattern)

                if tex_files:
                    question_file = tex_files[0]
                    self.stdout.write(f'  Parsing questions and items from: {question_file}')
                    
                    # 1. Parse and Save Questions
                    questions_data = self.parse_questions(question_file, i)
                    for q in questions_data:
                        Question.objects.update_or_create(
                            id=q['question_id'],
                            defaults={
                                'assignment': assignment_obj,
                                'number': q['question_num'],
                                'enunciado': q['question_enunciado']
                            }
                        )
                    self.stdout.write(f'    Parsed {len(questions_data)} questions.')

                    # 2. Parse and Save Items
                    items_data = self.parse_items(question_file, i)
                    for item in items_data:
                        try:
                            # Link item to the correct question
                            target_q_id = f"l{i}q{item['question_num']:02}"
                            question_obj = Question.objects.get(id=target_q_id)
                            Item.objects.update_or_create(
                                id=item['item_id'],
                                defaults={
                                    'question': question_obj,
                                    'codigo': item['item_code'],
                                    'enunciado': item['item_enunciado']
                                }
                            )
                        except Question.DoesNotExist:
                             self.stdout.write(self.style.WARNING(f"    Warning: Question not found for item {item['item_id']}"))
                    self.stdout.write(f'    Parsed {len(items_data)} items.')

                else:
                    self.stdout.write(self.style.WARNING(f'  Question LaTeX file not found for List {i}'))

                # 3. Handle Solutions
                solution_folder_pattern = os.path.join(list_dir, 'Solu*')
                solution_dirs = glob.glob(solution_folder_pattern)
                
                if solution_dirs:
                    sol_dir = solution_dirs[0]
                    sol_tex_pattern = os.path.join(sol_dir, f'Solu*.tex')
                    sol_files = glob.glob(sol_tex_pattern)
                    
                    if sol_files:
                        sol_file = sol_files[0]
                        self.stdout.write(f'  Parsing solutions from: {sol_file}')
                        
                        solutions_data = self.parse_latex_solutions(sol_file, i)
                        saved_sol_count = 0
                        for sol in solutions_data:
                            try:
                                question_obj = Question.objects.get(id=sol['question_id'])
                                item_obj = None
                                if sol['item_id']:
                                    try:
                                        item_obj = Item.objects.get(id=sol['item_id'])
                                    except Item.DoesNotExist:
                                        pass

                                Solution.objects.update_or_create(
                                    id=sol['solution_id'],
                                    defaults={
                                        'question': question_obj,
                                        'item': item_obj,
                                        'text': sol['solution_text']
                                    }
                                )
                                saved_sol_count += 1
                            except Question.DoesNotExist:
                                pass
                        self.stdout.write(f'    Parsed {saved_sol_count} solutions.')
                    else:
                        self.stdout.write(self.style.WARNING(f'  Solution LaTeX file not found in {sol_dir}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  Solution folder not found for List {i}'))
            
            self.stdout.write(self.style.SUCCESS(f'Import process completed successfully.'))
