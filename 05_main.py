"""
05_main.py — Demonstração do MVP Parte 1 (AV 03) | Projeto Aplicado I | Schulz S.A.

Fluxo demonstrado:
  1. cria o banco SQLite e as três tabelas;
  2. instancia Tecnico, Equipamento e Medicao (dados do certificado modelo 00091/2026);
  3. insere os registros de teste;
  4. executa consulta relacional com JOIN e imprime o relatório de calibração;
  5. atualiza uma medição e mostra o status recalculado;
  6. provoca erros de propósito para mostrar o tratamento (dado inválido,
     TAG duplicada, chave estrangeira inexistente).

Execução:  python 05_main.py
(O nome 04_classes.py começa com número, por isso a importação usa importlib.)
"""

import importlib
import os

classes = importlib.import_module("04_classes")
Tecnico = classes.Tecnico
Equipamento = classes.Equipamento
Medicao = classes.Medicao
BancoDados = classes.BancoDados
ErroBancoDados = classes.ErroBancoDados

ARQUIVO_BANCO = "calibracao_schulz.db"
INCERTEZA_EXPANDIDA = 0.002          # mm, conforme o certificado modelo (item 5)
DATA_CALIBRACAO = "2026-08-26"

# (parâmetro, nominal, tol+, tol-, valor obtido) — certificado nº 00091/2026
PARAMETROS_CERTIFICADO = [
    ("PLANICIDADE_REF",    0.000, 0.050,  0.000,  0.002),
    ("ENTRE CENTROS_REF",  0.000, 0.040,  0.000,  0.027),
    ("62P_DIÂMETRO 1",     6.075, 0.010, -0.010,  6.079),
    ("62P_POSIÇÃO 1",      0.000, 0.100,  0.000,  0.430),
    ("62P_DIÂMETRO 2",     6.075, 0.010, -0.010,  6.078),
    ("62P_POSIÇÃO 2",      0.000, 0.100,  0.000,  0.245),
    ("13P_DIÂMETRO 1",    16.964, 0.010, -0.010, 16.968),
    ("13P_POSIÇÃO 1",      0.000, 0.100,  0.000,  0.959),
    ("13P_DIÂMETRO 2",    16.964, 0.010, -0.010, 16.970),
    ("13P_POSIÇÃO 2",      0.000, 0.100,  0.000,  0.236),
    ("106P_DIÂMETRO 1",    6.345, 0.010, -0.010,  6.346),
    ("106P_POSIÇÃO 1",     0.000, 0.100,  0.000,  0.132),
    ("106P_DIÂMETRO 2",    6.345, 0.010, -0.010,  6.349),
    ("106P_POSIÇÃO 2",     0.000, 0.100,  0.000,  0.868),
]


def titulo(texto: str) -> None:
    print("\n" + "=" * 78)
    print(texto)
    print("=" * 78)


def imprimir_relatorio(linhas) -> None:
    if not linhas:
        print("Nenhuma medição encontrada.")
        return
    cab = linhas[0]
    print(f"Equipamento : {cab['codigo_tag']} - {cab['descricao']} (fabricante: {cab['fabricante']})")
    print(f"Técnico     : {cab['tecnico']} (matrícula {cab['matricula']})")
    print(f"Data        : {cab['data_calibracao']}    Unidade: mm")
    print("-" * 78)
    print(f"{'ID':>3}  {'PARÂMETRO':<20}{'NOMINAL':>9}{'TOL+':>8}{'TOL-':>8}"
          f"{'OBTIDO':>9}{'ERRO':>8}  STATUS")
    print("-" * 78)
    for l in linhas:
        print(f"{l['id_medicao']:>3}  {l['parametro']:<20}{l['valor_nominal']:>9.3f}"
              f"{l['tol_superior']:>8.3f}{l['tol_inferior']:>8.3f}"
              f"{l['valor_obtido']:>9.3f}{l['erro']:>8.3f}  {l['status']}")
    print("-" * 78)
    aprovados = sum(1 for l in linhas if l["status"] == "APROVADO")
    print(f"Total: {len(linhas)} parâmetros | aprovados: {aprovados} | "
          f"reprovados: {len(linhas) - aprovados}")


def main() -> None:
    if os.path.exists(ARQUIVO_BANCO):          # demonstração repetível
        os.remove(ARQUIVO_BANCO)

    with BancoDados(ARQUIVO_BANCO) as banco:
        # 1. Estrutura -----------------------------------------------------
        titulo("1. Criação do banco e das tabelas (tecnicos, equipamentos, medicoes)")
        banco.criar_tabelas()
        print("Tabelas criadas com sucesso.")

        # 2 e 3. Instanciação e inserção -------------------------------------
        titulo("2. Instanciação dos objetos e inserção dos registros de teste")
        tecnico = banco.inserir_tecnico(
            Tecnico("mat-0001", "  Jose Alcides   Rosa Junior ", "Metrologia"))
        print("Inserido:", tecnico, f"-> id {tecnico.id_tecnico}")

        outro = banco.inserir_tecnico(Tecnico("MAT-0002", "Cleocir de Souza", "Metrologia"))
        print("Inserido:", outro, f"-> id {outro.id_tecnico}")

        equipamento = banco.inserir_equipamento(
            Equipamento("703.1208", "Dispositivo de controle"))     # fabricante: "Não consta"
        print("Inserido:", equipamento, f"-> id {equipamento.id_equipamento}")

        for param, nominal, tol_sup, tol_inf, obtido in PARAMETROS_CERTIFICADO:
            banco.inserir_medicao(Medicao(
                equipamento.id_equipamento, tecnico.id_tecnico, param,
                nominal, tol_sup, tol_inf, obtido,
                incerteza_expandida=INCERTEZA_EXPANDIDA,
                data_calibracao=DATA_CALIBRACAO))
        print(f"Inseridas {len(PARAMETROS_CERTIFICADO)} medições do certificado 00091/2026.")

        # 4. Consulta relacional (JOIN) ----------------------------------------
        titulo("3. Relatório de calibração (consulta com JOIN entre as 3 tabelas)")
        imprimir_relatorio(banco.relatorio_calibracao("703.1208"))

        # 5. UPDATE --------------------------------------------------------------
        titulo("4. UPDATE: correção do valor obtido de 62P_POSIÇÃO 1 (0,430 -> 0,090)")
        medicoes = banco.listar_medicoes_do_equipamento(equipamento.id_equipamento)
        alvo = next(m for m in medicoes if m.parametro == "62P_POSIÇÃO 1")
        print("Antes :", alvo)
        alvo.valor_obtido = "0,090"                 # aceita vírgula decimal (RH18)
        banco.atualizar_medicao(alvo)
        recarregada = next(m for m in banco.listar_medicoes_do_equipamento(
            equipamento.id_equipamento) if m.id_medicao == alvo.id_medicao)
        print("Depois:", recarregada, f"| erro recalculado = {recarregada.calcular_erro():.3f}")

        # 6. Tratamento de erros -----------------------------------------------------
        titulo("5. Tratamento de erros")
        testes = [
            ("Valor não numérico",
             lambda: Medicao(1, 1, "TESTE", 1.0, 0.1, -0.1, "abc")),
            ("Parâmetro vazio",
             lambda: Medicao(1, 1, "   ", 1.0, 0.1, -0.1, 1.0)),
            ("Data inválida",
             lambda: Medicao(1, 1, "TESTE", 1.0, 0.1, -0.1, 1.0, data_calibracao="26/08/2026")),
            ("TAG duplicada",
             lambda: banco.inserir_equipamento(Equipamento("703.1208", "Outro dispositivo"))),
            ("Equipamento inexistente (FK)",
             lambda: banco.inserir_medicao(
                 Medicao(999, tecnico.id_tecnico, "TESTE", 1.0, 0.1, -0.1, 1.0))),
            ("UPDATE em id inexistente",
             lambda: banco.atualizar_medicao(
                 Medicao(1, 1, "TESTE", 1.0, 0.1, -0.1, 1.0, id_medicao=9999))),
        ]
        for nome, acao in testes:
            try:
                acao()
                print(f"[FALHA NO TESTE] {nome}: nenhum erro foi levantado")
            except (ValueError, ErroBancoDados) as erro:
                print(f"[OK] {nome:<30} -> {type(erro).__name__}: {erro}")

        # Conferência final ------------------------------------------------------------
        titulo("6. Relatório final após a correção")
        imprimir_relatorio(banco.relatorio_calibracao("703.1208"))


if __name__ == "__main__":
    main()
