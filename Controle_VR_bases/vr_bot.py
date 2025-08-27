import os
import pandas as pd

def processar_vr(ano, mes, nome_saida=None):
    print(f"Iniciando processamento de VR para {mes}/{ano}...")

    pasta_dados = "dados"
    arquivos = os.listdir(pasta_dados)
    arquivos_xlsx = [f for f in arquivos if f.lower().endswith(".xlsx")]

    print(f"{len(arquivos_xlsx)} arquivos XLSX encontrados na pasta 'dados'.")

    planilhas = {}

    nomes_esperados = {
        "afastados": "Afastados",
        "aprendiz": "Aprendiz",
        "ativos": "Ativos",
        "dias_uteis": "Dias_Uteis",
        "sindicatos": "Sindicatos",
        "desligados": "Desligados",
        "estagio": "Estagio",
        "exterior": "Exterior",
        "ferias": "Ferias",
        "admissoes": "Admissoes",
    }

    for arquivo in arquivos_xlsx:
        caminho_arquivo = os.path.join(pasta_dados, arquivo)
        nome_base = os.path.splitext(os.path.basename(arquivo))[0].lower().replace(" ", "_")
        for chave_normalizada, nome_amigavel in nomes_esperados.items():
            if chave_normalizada in nome_base:
                try:
                    df = pd.read_excel(caminho_arquivo)
                    planilhas[chave_normalizada] = df
                    print(f"📘 Lendo arquivo: {caminho_arquivo}")
                except Exception as e:
                    print(f"❌ Erro ao ler {arquivo}: {e}")
                break

    obrigatorios = ["ativos", "dias_uteis", "sindicatos"]
    for nome in obrigatorios:
        if nome not in planilhas:
            print(f"❌ ERRO: Planilha obrigatória '{nome}' não encontrada.")
            return

    df_final = planilhas["ativos"].copy()

    try:
        dias_uteis_dict = dict(
            zip(
                planilhas["dias_uteis"].iloc[:, 0].astype(str).str.strip(),
                planilhas["dias_uteis"].iloc[:, 1]
            )
        )
    except Exception as e:
        print(f"❌ Erro ao montar dicionário de dias úteis: {e}")
        return

    df_final["Sindicato"] = df_final["Sindicato"].astype(str).str.strip()
    df_final["Dias_VR"] = df_final["Sindicato"].map(dias_uteis_dict).fillna(0)

    # Zera quem está afastado
    if "afastados" in planilhas:
        afastados_matriculas = planilhas["afastados"]["Matricula"].astype(str).unique()
        df_final.loc[df_final["Matricula"].astype(str).isin(afastados_matriculas), "Dias_VR"] = 0

    # Zera dias de quem está no exterior ou estagiando ou aprendiz
    for chave in ["exterior", "estagio", "aprendiz"]:
        if chave in planilhas:
            mats = planilhas[chave]["Matricula"].astype(str).unique()
            df_final.loc[df_final["Matricula"].astype(str).isin(mats), "Dias_VR"] = 0

    # Tratamento férias: subtrai dias de férias
    if "ferias" in planilhas:
        df_ferias = planilhas["ferias"]
        df_ferias["Matricula"] = df_ferias["Matricula"].astype(str)
        df_ferias["Dias_Comprados"] = df_ferias["Dias_Comprados"].fillna(0)
        df_ferias["Dias_Ferias"] = df_ferias["Dias_Ferias"].fillna(0)
        df_ferias["Dias_Descontar"] = df_ferias["Dias_Ferias"] - df_ferias["Dias_Comprados"]
        df_ferias["Dias_Descontar"] = df_ferias["Dias_Descontar"].clip(lower=0)

        ferias_dict = df_ferias.groupby("Matricula")["Dias_Descontar"].sum().to_dict()
        df_final["Matricula"] = df_final["Matricula"].astype(str)
        df_final["Dias_VR"] = df_final.apply(
            lambda row: max(row["Dias_VR"] - ferias_dict.get(row["Matricula"], 0), 0), axis=1
        )

    valor_dia_vr = 50
    df_final["VR_Total"] = df_final["Dias_VR"] * valor_dia_vr
    df_final["%_Empresa"] = df_final["VR_Total"] * 0.8
    df_final["%_Colaborador"] = df_final["VR_Total"] * 0.2

    df_resumo = df_final.groupby("Sindicato")[
        ["Dias_VR", "VR_Total", "%_Empresa", "%_Colaborador"]
    ].sum().reset_index()

    # Validações
    validacoes = []
    for _, row in df_final.iterrows():
        matricula = row["Matricula"]
        dias = row["Dias_VR"]
        problema = "ok"
        if dias == 0 and row["VR_Total"] > 0:
            problema = "Dias zerados com valor > 0"
        elif row["VR_Total"] == 0 and row["Dias_VR"] > 0:
            problema = "Sem valor mesmo com dias"
        elif row["Dias_VR"] > 22:
            problema = "Dias maiores que possível"
        validacoes.append({
            "Matricula": matricula,
            "Problema": problema
        })

    df_validacoes = pd.DataFrame(validacoes)

    # Também gerar planilha detalhada por pessoa
    df_detalhado = df_final[[
    "Matricula", "Sindicato", "Dias_VR", "VR_Total", "%_Empresa", "%_Colaborador"
    ]]

    if nome_saida is None:
        nome_saida = f"VR_{ano}_{mes:02d}_Processado.xlsx"

    raiz = os.path.dirname(os.path.abspath(__file__))
    pasta_output = os.path.join(raiz, "output")
    os.makedirs(pasta_output, exist_ok=True)
    caminho_saida = os.path.join(raiz, nome_saida)

    try:
        with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
            df_detalhado.to_excel(writer, sheet_name="VR_Mensal", index=False)
            df_resumo.to_excel(writer, sheet_name="resumo_sindicato", index=False)
            df_validacoes.to_excel(writer, sheet_name="validações", index=False)
            df_final.to_excel(writer, sheet_name="VR_Dia", index=False)
        print(f"✅ Arquivo final salvo em: {caminho_saida}")
    except Exception as e:
        print(f"❌ Erro ao salvar o arquivo final: {e}")
