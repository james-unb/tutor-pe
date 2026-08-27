import asyncio
import glob
import os
import re
import json
import pandas as pd
from typing import List
from pydantic import BaseModel, Field


# --- 1. DEFINIÇÃO DAS CLASSES DE MODELO (Pydantic) ---

class QuestionType(BaseModel):
    id_questao: str = Field(
        description="Identificação única da versão da questão.")
    prova: int = Field(description="Número da prova na questão")
    dificuldade: float = Field(
        description="Dificuldade da questão conforme a coluna percentual no arquivo CSV")
    materia: str = Field(description="Matéria da questão conforme o nome do arquivo")
    posicao_conteudo: int = Field(
        description="Posição do conteúdo (primeiro número do nome do arquivo)")
    modelo_questao: int = Field(
        description="Modelo da questão (segundo número no nome do arquivo)")
    versao: int = Field(description="Número da versão da questão (1 a 10)")
    enunciado: str = Field(description="Enunciado completo da questão.")
    solucao: str = Field(description="Solução completa da questão.")


# --- 2. EXPRESSÕES REGULARES PARA EXTRAÇÃO ---

REGEX_ENUNCIADOS = re.compile(
    r'\\item\s*\\textbf\{Question\}(.*?)(?=\\item\s*\\textbf\{Question\}|\s*\\textbf\{Solution\})',
    re.DOTALL | re.IGNORECASE
)

REGEX_SOLUCAO = re.compile(
    r'\\textbf\{Solution\}(.*?)(?=\\item\s*\\textbf\{Question\}|\Z)',
    # \Z garante que pegue até o final do arquivo se for o último
    re.DOTALL | re.IGNORECASE
)

# --- 3. FUNCAO QUE TIRA A FORMATACAO LATEX  ---

def limpar_latex(texto: str) -> str:

    texto = re.sub(r'\\(begin|end)\{(enumerate|itemize)\}', ' ', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\\def\\labelenumii\{.*?\}', '', texto, flags=re.DOTALL)
    texto = re.sub(r'\\item\s*', ' ', texto)
    texto = re.sub(r'\\textbf\{([^}]+)\}', r'\1', texto)
    texto = re.sub(r'\\textit\{([^}]+)\}', r'\1', texto)
    texto = re.sub(r'\\(hfil|vfil|centering|noindent)', '', texto)
    texto = re.sub(r'\\\((.*?)\\\)', r' \1 ', texto)
    texto = re.sub(r'\$(.*?)\$', r' \1 ', texto)
    texto = texto.replace(r'\c{c}', 'ç')  # ç
    texto = texto.replace(r'\'a', 'á').replace(r'\'e', 'é').replace(r'\'i', 'í').replace(r'\'o', 'ó').replace(r'\'u',
                                                                                                              'ú')
    texto = texto.replace(r'\~a', 'ã').replace(r'\~o', 'õ')
    texto = texto.replace(r'\`a', 'à')
    texto = texto.replace(r'\\', ' ')
    texto = re.sub(
        r'\\(alpha|beta|gamma|cdot|times|ldots|frac|sum|int|sqrt|left|right|label|caption|section|subsection|chapter|author|title|documentclass|usepackage)\{?.*?\}?',
        '', texto)
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto).strip()

    return texto


# --- 4. FUNCAO QUE ORGANIZA O BANCO  ---

def processar_latex_local(
        latex_content: str,
        nome_arquivo: str,
        prova: int,
        dificuldade: float,
) -> List[QuestionType]:
    questoes_extraidas: List[QuestionType] = []

    try:
        nome_sem_extensao = nome_arquivo.replace('.latex', '')
        partes = nome_sem_extensao.split('_')
        posicao_conteudo = int(partes[0])
        modelo_questao = int(partes[-1])
        partes_materia = partes[1:-1]
        materia = '_'.join(partes_materia)
    except Exception as e:
        print(f"❌ Erro de parsing no nome do arquivo {nome_arquivo}: {e}")
        return []

    solucao_match = REGEX_SOLUCAO.search(latex_content)
    solucao_texto_base = solucao_match.group(1).strip() if solucao_match else "SOLUCAO_NAO_ENCONTRADA_REGEX_FALHOU"
    solucao_limpa = limpar_latex(solucao_texto_base)

    enunciado_matches = REGEX_ENUNCIADOS.findall(latex_content)

    if len(enunciado_matches) != 10:
        print(f"⚠️ Aviso: Encontradas {len(enunciado_matches)} versões (Esperado: 10). Arquivo: {nome_arquivo}")

    for i, enunciado_texto in enumerate(enunciado_matches):
        versao_num = i + 1  # A versão é o índice (1 a 10)

        enunciado_limpo = limpar_latex(enunciado_texto)

        id_completo = f"v_{versao_num}pr_{prova}_p_{posicao_conteudo}_m_{modelo_questao}({materia})"

        q = QuestionType(
            id_questao=id_completo,
            prova=prova,
            dificuldade=dificuldade,
            materia=materia,
            posicao_conteudo=posicao_conteudo,
            modelo_questao=modelo_questao,
            versao=versao_num,
            enunciado=enunciado_limpo,
            solucao=solucao_limpa,  # Solução é a mesma para todas as 10 versões
        )
        questoes_extraidas.append(q)

    return questoes_extraidas


# --- 5. FUNCAO QUE COVERTE O JSON PARA CSV  ---

def converter_json_para_csv(json_filename="questoes-teste-local.json", csv_filename="questoes-final.csv"):

    if not os.path.exists(json_filename):
        print(f"❌ Erro: O arquivo JSON '{json_filename}' não foi encontrado.")
        return

    print(f"⏳ Carregando dados do JSON: {json_filename}...")

    try:
        with open(json_filename, "r", encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        print(f"❌ Erro ao ler o JSON: {e}")
        return

    df = pd.DataFrame(data)

    print(f"✅ JSON carregado com {len(df)} linhas.")

    try:
        df.to_csv(csv_filename, index=False, sep=';', encoding='utf-8')
        print(f"🎉 Sucesso! O arquivo CSV foi salvo como: {csv_filename}")
    except Exception as e:
        print(f"❌ Erro ao salvar o CSV: {e}")

# --- 6. FUNCAO PRINCIPAL ASSINCRONA  ---

async def main():

    dificuldade_file_path = "/dados/unb/8oSemestre/james/dificuldade/matriz.csv"
    try:
        df_dificuldades = pd.read_csv(dificuldade_file_path, encoding="latin-1")
        print("✅ Arquivo de dificuldades carregado com sucesso pelo Pandas.")
    except Exception as e:
        print(f"🚨 Erro ao carregar o CSV: {e}")
        return

    caminho_questoes = "/dados/unb/8oSemestre/james/questoes/*.latex"
    arquivos_latex = sorted(glob.glob(caminho_questoes))
    num_total_arquivos = len(arquivos_latex)

    print(f"Iniciando o processamento PARALELO (Puro Python) de {num_total_arquivos} arquivos...")

    CONCURRENCY_LIMIT = 50
    sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def task_wrapper(i, arquivo_path):
        async with sem:
            indice_arquivo = i + 1
            nome_arquivo = os.path.basename(arquivo_path)

            try:
                dificuldade_percentual = df_dificuldades.loc[i, 'percentual'].item()
            except KeyError:
                dificuldade_percentual = 0

            if indice_arquivo <= 100:
                prova_atual = 1
            elif indice_arquivo <= 200:
                prova_atual = 2
            else:
                prova_atual = 3

            try:
                with open(arquivo_path, "r", encoding="utf-8", errors='ignore') as file:
                    latex_content = file.read()
            except UnicodeDecodeError:
                try:
                    with open(arquivo_path, "r", encoding="latin-1", errors='ignore') as file:
                        latex_content = file.read()
                except Exception as e:
                    print(f"❌ Erro final ao ler {nome_arquivo}: {e}")
                    return []
                except Exception as e:
                    print(f"❌ Erro ao ler {nome_arquivo}: {e}")
                    return []

            questoes = processar_latex_local(
                latex_content,
                nome_arquivo,
                prova_atual,
                dificuldade_percentual
            )

            if questoes:
                print(
                    f"✅ Sucesso ({indice_arquivo}/{num_total_arquivos}): {nome_arquivo} - {len(questoes)} questões extraídas.")
            return questoes


    tasks = [task_wrapper(i, arquivo_path) for i, arquivo_path in enumerate(arquivos_latex)]


    resultados_agrupados = await asyncio.gather(*tasks)


    todas_as_questoes: List[QuestionType] = []
    for lista_questoes in resultados_agrupados:
        todas_as_questoes.extend(lista_questoes)

    print("\n✅ Processamento Completo!")
    print(f"Total de questões extraídas: {len(todas_as_questoes)}")


    output_data = [q.model_dump() for q in todas_as_questoes]

    output_filename = "questoes-teste-local.json"
    with open(output_filename, "w", encoding='utf-8') as file:
        json.dump(output_data, file, indent=2, ensure_ascii=False)

    print(f"Resultado final salvo em {output_filename}.")
    converter_json_para_csv(json_filename=output_filename, csv_filename="questoes-finais.csv")



# Execução do script
if __name__ == '__main__':
    asyncio.run(main())