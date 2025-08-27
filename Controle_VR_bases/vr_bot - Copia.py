import os
import pandas as pd

def processar_vr(ano, mes, nome_saida=None):
    print(f"Iniciando processamento de VR para {mes}/{ano}...")

    pasta_dados = "dados"
    arquivos = os.listdir(pasta_dados)
    arquivos_xlsx = [f for f in arquivos if f.lower().endswith(".xlsx")]

    print(f"{len(arquivos_xlsx)} arquivos XLSX encontrados na pasta 'dados'.")

    # Dicionário para armazenar os DataFrames nomeados
    planilhas = {}

    # Nomes esperados (sem acento e normalizados)
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

    # Leitura e atribuição aos nomes esperados
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

    # Confere obrigatórios
    obrigatorios = ["ativos", "dias_uteis", "sindicatos"]
    for nome in obrigatorios:
        if nome not in planilhas:
            print(f"❌ ERRO: Planilha obrigatória '{nome}' não encontrada.")
            return

    # Merge geral com ativos como base
    df_final = planilhas["ativos"].copy()

    # Dicionário de dias úteis por sindicato
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

    # Adiciona coluna Dias_VR com base no sindicato de cada colaborador
    df_final["Dias_VR"] = df_final["Sindicato"].astype(str).str.strip().map(dias_uteis_dict).fillna(0)

    # Cálculo de valores
    valor_dia_vr = 50  # valor por dia fictício
    df_final["VR_Total"] = df_final["Dias_VR"] * valor_dia_vr
    df_final["%_Empresa"] = df_final["VR_Total"] * 0.8
    df_final["%_Colaborador"] = df_final["VR_Total"] * 0.2

    # Cria resumo por sindicato
    df_resumo = df_final.groupby("Sindicato")[
        ["Dias_VR", "VR_Total", "%_Empresa", "%_Colaborador"]
    ].sum().reset_index()

   # --- Validações por colaborador ---
    validacoes = []

    # Verifica se coluna Matricula existe
    if "Matricula" not in df_final.columns:
        print("❌ ERRO: Coluna 'Matricula' não encontrada no df_final.")
        df_validacoes = pd.DataFrame(columns=["Matricula", "Problema"])
    else:
        for _, row in df_final.iterrows():
            problemas = []

            sindicato = str(row.get("Sindicato", "")).strip()
            dias_vr = row.get("Dias_VR", 0)
            vr_total = row.get("VR_Total", 0)

            if not sindicato:
                problemas.append("Sindicato ausente")
            if dias_vr == 0 or pd.isna(dias_vr):
                problemas.append("Dias de VR zerado")
            if vr_total == 0 or pd.isna(vr_total):
                problemas.append("Valor de VR zerado")

            status = "OK" if not problemas else "; ".join(problemas)

            validacoes.append({
                "Matricula": row["Matricula"],
                "Problema": status
            })

        df_validacoes = pd.DataFrame(validacoes)

        # Salvar arquivo final
        def salvar_arquivo_final(df_final, df_resumo, df_validacoes, mes, ano, nome_saida=None):
            if nome_saida is None:
                nome_saida = f"VR_{ano}_{mes:02d}_Processado.xlsx"

        # Corrigir caminho absoluto em relação ao script atual (evita output/output)
        raiz = os.path.dirname(os.path.abspath(__file__))
        pasta_output = os.path.join(raiz, "output")
        os.makedirs(pasta_output, exist_ok=True)
        caminho_saida = os.path.join(pasta_output, nome_saida)

        try:
            with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
                df_final.to_excel(writer, sheet_name="VR_Mensal", index=False)
                df_resumo.to_excel(writer, sheet_name="resumo_sindicato", index=False)
                df_validacoes.to_excel(writer, sheet_name="validações", index=False)
            print(f"✅ Arquivo final salvo em: {caminho_saida}")
        except Exception as e:
            print(f"❌ Erro ao salvar o arquivo final: {e}")

    salvar_arquivo_final(df_final, df_resumo, df_validacoes, mes, ano, nome_saida)


# Executa apenas se rodar diretamente
if __name__ == "__main__":
    processar_vr(ano=2025, mes=9)
