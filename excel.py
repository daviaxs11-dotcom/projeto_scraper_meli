from __future__ import annotations

import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, Alignment
from PIL import Image as PILImage

from config import (
    ALTURA_IMAGEM,
    HEADLESS,
    MAX_PAGINAS,
    PAUSA_ENTRE_CONSULTAS,
    QTD_RESULTADOS,
    TIMEOUT_MS,
)
from scraper import buscar_produtos


def celula_destacada(celula):
    """Equivale à função VBA CelulaDestacada."""
    fill = celula.fill
    if fill is None:
        return False

    # Ignora células sem preenchimento real.
    if fill.fill_type is None:
        return False

    # Preserva a ideia da macro: qualquer preenchimento conta como destaque.
    return True


def _baixar_imagem(url):
    if not url:
        return None

    try:
        resposta = requests.get(
            url,
            timeout=max(10, TIMEOUT_MS / 1000),
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resposta.raise_for_status()

        arquivo = NamedTemporaryFile(delete=False, suffix=".img")
        arquivo.write(resposta.content)
        arquivo.close()

        # Converte para PNG para evitar problemas com WebP no Excel.
        origem = PILImage.open(arquivo.name).convert("RGB")
        png = NamedTemporaryFile(delete=False, suffix=".png")
        origem.save(png.name, "PNG")
        png.close()

        Path(arquivo.name).unlink(missing_ok=True)
        return png.name
    except Exception as exc:
        print(f"    Aviso: não foi possível baixar imagem: {exc}")
        return None


def _inserir_imagem(ws, url, linha, coluna=2):
    caminho = _baixar_imagem(url)
    if not caminho:
        return

    try:
        img = XLImage(caminho)

        celula = ws.cell(linha, coluna)
        # Aproximação da largura da coluna B.
        largura_px = 105
        altura_px = ALTURA_IMAGEM * 1.33

        img.width = min(img.width, largura_px)
        img.height = min(img.height, altura_px)

        # Mantém proporção.
        if img.width > largura_px:
            fator = largura_px / img.width
            img.width *= fator
            img.height *= fator
        if img.height > altura_px:
            fator = altura_px / img.height
            img.width *= fator
            img.height *= fator

        ws.add_image(img, celula.coordinate)
    except Exception as exc:
        print(f"    Aviso: erro ao inserir imagem: {exc}")
    finally:
        Path(caminho).unlink(missing_ok=True)


def _anuncio_ja_existe(ws, url):
    if not url:
        return False

    for row in ws.iter_rows(min_row=2, min_col=9, max_col=9, values_only=True):
        existente = str(row[0] or "").strip()
        if existente.lower() == url.strip().lower():
            return True

    return False


def _abrir_workbook(caminho):
    extensao = caminho.suffix.lower()

    if extensao == ".xlsm":
        # Mantém o projeto VBA existente, caso o usuário ainda o tenha no arquivo.
        return load_workbook(caminho, keep_vba=True)

    return load_workbook(caminho)


def executar_consulta(caminho_excel: Path):
    caminho_excel = Path(caminho_excel)
    wb = _abrir_workbook(caminho_excel)

    try:
        if "PRODUTOS" not in wb.sheetnames:
            raise RuntimeError("A aba PRODUTOS não foi encontrada.")

        ws_produtos = wb["PRODUTOS"]

        if "RESULTADO MELI" in wb.sheetnames:
            ws_resultado = wb["RESULTADO MELI"]
            # Remove imagens existentes antes de limpar.
            ws_resultado._images = []
            for row in ws_resultado.iter_rows():
                for cell in row:
                    cell.value = None
        else:
            ws_resultado = wb.create_sheet("RESULTADO MELI")

        cabecalhos = [
            "Código", "Imagem", "Produto", "Marca", "Preço",
            "Vendedor", "Frete Grátis", "Avaliação", "Link"
        ]

        for col, valor in enumerate(cabecalhos, start=1):
            ws_resultado.cell(1, col, valor)

        for cell in ws_resultado[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        linha = 2
        total_consultados = 0
        total_encontrados = 0
        total_gravados = 0
        total_erros = 0

        ultima_linha = ws_produtos.max_row

        for i in range(2, ultima_linha + 1):
            celula = ws_produtos.cell(i, 1)

            if not celula_destacada(celula):
                continue

            codigo = str(celula.value or "").strip()
            if not codigo:
                continue

            total_consultados += 1

            print()
            print("=" * 70)
            print(f"CONSULTANDO: {codigo}")
            print(f"LINHA PRODUTOS: {i}")
            print("ORDENAÇÃO: MENOR PREÇO")
            print("=" * 70)

            try:
                produtos = buscar_produtos(
                    codigo=codigo,
                    max_paginas=MAX_PAGINAS,
                    qtd_resultados=QTD_RESULTADOS,
                    timeout_ms=TIMEOUT_MS,
                    headless=HEADLESS,
                )
            except Exception as exc:
                total_erros += 1
                ws_resultado.cell(linha, 1, codigo)
                ws_resultado.cell(linha, 3, f"Erro na consulta: {exc}")
                linha += 1
                print(f"ERRO: {type(exc).__name__}: {exc}")
                time.sleep(PAUSA_ENTRE_CONSULTAS)
                continue

            print(f"PRODUTOS IDENTIFICADOS: {len(produtos)}")
            total_encontrados += len(produtos)

            if not produtos:
                ws_resultado.cell(linha, 1, codigo)
                ws_resultado.cell(linha, 3, "Nenhum produto encontrado")
                linha += 1
                time.sleep(PAUSA_ENTRE_CONSULTAS)
                continue

            for item in produtos:
                url = item.get("url", "")

                if _anuncio_ja_existe(ws_resultado, url):
                    continue

                ws_resultado.cell(linha, 1, codigo)
                ws_resultado.cell(linha, 2, item.get("image", ""))
                ws_resultado.cell(linha, 3, item.get("title", ""))
                ws_resultado.cell(linha, 4, item.get("brand", ""))
                ws_resultado.cell(linha, 5, item.get("price", 0))
                ws_resultado.cell(linha, 6, item.get("seller", ""))
                ws_resultado.cell(
                    linha, 7,
                    "Sim" if item.get("freeShipping") else "Não"
                )
                ws_resultado.cell(linha, 8, item.get("rating", 0))
                ws_resultado.cell(linha, 9, url)

                ws_resultado.row_dimensions[linha].height = ALTURA_IMAGEM
                _inserir_imagem(
                    ws_resultado,
                    item.get("image", ""),
                    linha,
                    coluna=2,
                )

                linha += 1
                total_gravados += 1

            time.sleep(PAUSA_ENTRE_CONSULTAS)

        # Formatação equivalente à macro.
        larguras = {
            "A": 15, "B": 15, "C": 60, "D": 25, "E": 14,
            "F": 30, "G": 15, "H": 12, "I": 70,
        }

        for coluna, largura in larguras.items():
            ws_resultado.column_dimensions[coluna].width = largura

        for row in range(2, ws_resultado.max_row + 1):
            ws_resultado.cell(row, 5).number_format = '"R$" #,##0.00'
            ws_resultado.cell(row, 8).number_format = '0.00'

        ws_resultado.auto_filter.ref = (
            f"A1:I{max(1, ws_resultado.max_row)}"
        )
        ws_resultado.freeze_panes = "A2"

        # Salva no próprio arquivo, preservando VBA quando for XLSM.
        wb.save(caminho_excel)

        print()
        print("=" * 70)
        print("CONSULTA CONCLUÍDA")
        print("=" * 70)
        print(f"Produtos destacados consultados: {total_consultados}")
        print(f"Produtos encontrados: {total_encontrados}")
        print(f"Produtos gravados: {total_gravados}")
        print(f"Consultas com erro: {total_erros}")
        print("Pesquisa realizada por menor preço.")
        print(f"Arquivo salvo: {caminho_excel}")

    finally:
        wb.close()
