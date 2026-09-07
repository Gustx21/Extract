from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import io

app = Flask(__name__)
CORS(app)

PORT = 5000

def tratar_colunas(cols, prefixo):
    """
    Trata colunas duplicadas e vazias.
    """
    vistos = {}
    resultado = []
    for i, c in enumerate(cols):
        nome = str(c).strip() if pd.notna(c) and str(c).strip() != '' else f"{prefixo}_vazia_{i}"
        if nome in vistos:
            vistos[nome] += 1
            resultado.append(f"{nome}_{vistos[nome]}")
        else:
            vistos[nome] = 0
            resultado.append(nome)
    return resultado

def encontrar_indice_cabecalho(df, palavra_chave):
    """
    Busca o índice da linha que contém a palavra-chave de forma segura.
    """
    mask = df.astype(str).apply(lambda col: col.str.contains(palavra_chave, case=False, na=False))
    linhas_com_palavra = mask.any(axis=1)
    
    if not linhas_com_palavra.any():
        raise ValueError(f"Cabeçalho com '{palavra_chave}' não encontrado no arquivo.")
    
    return linhas_com_palavra.idxmax()

def processar_arquivo(file, extensao):
    # 1. Leitura dinâmica usando match-case
    match extensao:
        case 'csv':
            df = pd.read_csv(file, header=None, low_memory=False)
        case 'xlsx' | 'xls':
            try:
                df = pd.read_excel(file, engine='calamine', header=None)
            except Exception as e:
                print(f"Aviso: Engine 'calamine' falhou, usando padrão. Erro: {e}")
                df = pd.read_excel(file, header=None)
        case 'parquet':
            # Nota: Parquet possui tipagem e cabeçalho estritos. 
            # A lógica abaixo assume que ele também está em formato bruto.
            df = pd.read_parquet(file)
        case _:
            raise ValueError(f"Formato de arquivo de entrada '{extensao}' não suportado.")

    idx_dt_devol = encontrar_indice_cabecalho(df, 'Dt Devol')
    idx_rca_item = encontrar_indice_cabecalho(df, 'Rca Item')

    cols_dt_devol = tratar_colunas(df.iloc[idx_dt_devol].values, "M")
    cols_rca_item = tratar_colunas(df.iloc[idx_rca_item].values, "D")

    overlap = set(cols_dt_devol).intersection(cols_rca_item)
    if overlap:
        cols_rca_item = [f"{c}_det" if c in overlap else c for c in cols_rca_item]

    dados_finais = []
    mestre_atual = {}

    for row in df.iloc[idx_dt_devol+1:].itertuples(index=False, name=None):
        val0 = str(row[0]).strip()

        if not val0 or not val0.isnumeric():
            continue

        val3 = row[3]

        if pd.notna(val3) and isinstance(val3, str) and len(val3) > 5:
            mestre_atual = dict(zip(cols_dt_devol, row))
        else:
            if mestre_atual:
                detalhe = dict(zip(cols_rca_item, row))
                linha_completa = {**mestre_atual, **detalhe}
                dados_finais.append(linha_completa)

    if not dados_finais:
        raise ValueError("Nenhum dado válido foi extraído. Verifique a estrutura do arquivo.")

    df_final = pd.DataFrame(dados_finais)

    # Remove colunas indesejadas por regex
    df_final = df_final.loc[:, ~df_final.columns.astype(str).str.contains('nan|Unnamed', case=False)]
    
    # Substitui strings vazias por NaN e remove colunas 100% vazias
    df_final = df_final.replace(r'^\s*$', np.nan, regex=True)
    df_final = df_final.dropna(axis=1, how='all')

    # Remove linha de totais
    mask_totais = df_final.astype(str).apply(
        lambda row: row.str.contains('Total do Rca :|Total :|Total Geral', case=False, na=False)
    ).any(axis=1)
    
    df_final = df_final[~mask_totais]

    colunas_para_remover = [
        'Nota_1', 'D_vazia_4', 'M_vazia_19', 'NumNota Orig.', 
        'Data NF Origem', 'Nr.Lote', 'D_vazia_23'
    ]
    df_final = df_final.drop(columns=colunas_para_remover, errors='ignore')

    # Renomear colunas
    df_final = df_final.rename(columns={
        'D_vazia_1': 'Cod Produto',
        'D_vazia_16': 'Vlr Item'
    })
    
    return df_final

@app.route('/processar', methods=['POST'])
def api_process_file():
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"erro": "Nenhum arquivo selecionado"}), 400

    # Descobre a extensão do arquivo de entrada
    extensao_entrada = file.filename.split('.')[-1].lower()
    
    # Formato desejado para a saída
    formato_saida = request.form.get('formato', 'xlsx').lower()

    try:
        # Passa a extensão como parâmetro
        df_final = processar_arquivo(file, extensao_entrada)
        
        buffer = io.BytesIO()
        
        # 2. Saída dinâmica usando match-case
        match formato_saida:
            case 'csv':
                df_final.to_csv(buffer, index=False)
                mimetype = 'text/csv'
                filename = 'relatorio.csv'
                
            case 'xlsx':
                df_final.to_excel(buffer, index=False, engine='openpyxl')
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = 'relatorio.xlsx'
                
            case 'parquet':
                df_final.to_parquet(buffer, index=False)
                mimetype = 'application/vnd.apache.parquet'
                filename = 'relatorio.parquet'
                
            case _:
                return jsonify({"erro": f"Formato de saída '{formato_saida}' não suportado"}), 400
            
        buffer.seek(0) 
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True, port=PORT)