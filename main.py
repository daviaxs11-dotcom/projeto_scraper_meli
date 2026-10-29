from pathlib import Path
from config import EXCEL_PATH
from excel import executar_consulta


def main():
    print("=" * 70)
    print("SCRAPER MERCADO LIVRE - PYTHON")
    print("=" * 70)
    print(f"Excel: {EXCEL_PATH}")
    print()

    if not EXCEL_PATH.exists():
        print(f"ERRO: arquivo Excel não encontrado: {EXCEL_PATH}")
        input("\nPressione ENTER para sair...")
        return

    try:
        executar_consulta(EXCEL_PATH)
    except KeyboardInterrupt:
        print("\nExecução interrompida pelo usuário.")
    except Exception as exc:
        print(f"\nERRO FATAL: {type(exc).__name__}: {exc}")

    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()
