from __future__ import annotations

import re
import time
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def _texto(locator):
    try:
        return (locator.inner_text() or "").strip()
    except Exception:
        return ""


def _atributo(locator, nome):
    try:
        valor = locator.get_attribute(nome)
        return (valor or "").strip()
    except Exception:
        return ""


def _numero_preco(texto):
    if not texto:
        return 0.0

    # Ex.: "R$ 1.234,56" / "1234,56"
    m = re.search(r"R\$\s*([\d.]+,\d{2})", texto)
    if not m:
        m = re.search(r"([\d.]+,\d{2})", texto)
    if not m:
        return 0.0

    valor = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return 0.0


def _rating(texto):
    if not texto:
        return 0.0
    m = re.search(r"\b([0-5](?:[.,]\d{1,2})?)\b", texto)
    if not m:
        return 0.0
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return 0.0


def _extrair_vendedor(card):
    # O Mercado Livre muda classes ocasionalmente; tentamos vários caminhos.
    for seletor in (
        ".poly-component__seller",
        ".poly-component__seller a",
        ".poly-card__seller",
        "[class*='seller']",
    ):
        try:
            loc = card.locator(seletor).first
            valor = _texto(loc)
            if valor:
                return valor
        except Exception:
            pass

    texto = _texto(card)
    # Alguns cards exibem "MARCA por Vendedor".
    m = re.search(r"\bpor\s+(.+?)(?:\n|$)", texto, re.I)
    return m.group(1).strip() if m else ""


def _extrair_card(card):
    titulo = ""
    for seletor in (
        ".poly-component__title",
        "a.poly-component__title",
        "h2",
        "h3",
        "[class*='title']",
    ):
        try:
            loc = card.locator(seletor).first
            titulo = _texto(loc)
            if titulo:
                break
        except Exception:
            pass

    url = ""
    try:
        # Preferimos o link que contém o título.
        link = card.locator("a").filter(has_text=titulo).first if titulo else card.locator("a").first
        url = _atributo(link, "href")
    except Exception:
        pass

    if not url:
        try:
            url = _atributo(card.locator("a").first, "href")
        except Exception:
            pass

    imagem = ""
    try:
        img = card.locator("img").first
        imagem = (
            _atributo(img, "src")
            or _atributo(img, "data-src")
            or _atributo(img, "data-lazy")
        )
    except Exception:
        pass

    texto_card = _texto(card)

    preco = 0.0
    for seletor in (
        ".poly-price__current",
        ".andes-money-amount",
        "[class*='price']",
    ):
        try:
            preco = _numero_preco(_texto(card.locator(seletor).first))
            if preco:
                break
        except Exception:
            pass

    if not preco:
        preco = _numero_preco(texto_card)

    rating = 0.0
    for seletor in (
        ".poly-reviews__rating",
        "[class*='rating']",
        "[class*='review']",
    ):
        try:
            rating = _rating(_texto(card.locator(seletor).first))
            if rating:
                break
        except Exception:
            pass

    marca = ""
    try:
        # Alguns cards trazem marca/vendedor em uma linha antes da avaliação.
        for seletor in (
            ".poly-component__brand",
            "[class*='brand']",
        ):
            marca = _texto(card.locator(seletor).first)
            if marca:
                break
    except Exception:
        pass

    frete = bool(re.search(r"frete\s+gr[aá]tis", texto_card, re.I))

    return {
        "productId": "",
        "title": titulo,
        "brand": marca,
        "price": preco,
        "originalPrice": 0.0,
        "seller": _extrair_vendedor(card),
        "freeShipping": frete,
        "rating": rating,
        "reviewCount": 0,
        "image": imagem,
        "url": url,
    }


def buscar_produtos(codigo: str, max_paginas: int = 10, qtd_resultados: int = 0,
                    timeout_ms: int = 180_000, headless: bool = True):
    """
    Scraper direto do Mercado Livre, sem Apify.

    A busca é feita pela página pública de resultados, ordenada por menor preço.
    """
    resultados = []
    vistos = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()

        try:
            for pagina in range(1, max_paginas + 1):
                url = (
                    "https://lista.mercadolivre.com.br/"
                    f"{quote_plus(codigo.strip())}"
                    f"_Desde_{1 + (pagina - 1) * 48}"
                    "?sort=price_asc"
                )

                print(f"  Página {pagina}: {url}")

                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                    page.wait_for_timeout(1200)
                except PlaywrightTimeoutError:
                    print("  Aviso: tempo excedido ao carregar a página; tentando continuar.")

                # Estrutura atual usa poly-card; mantemos fallback para ui-search.
                cards = page.locator(
                    "li.ui-search-layout__item, "
                    "div.poly-card, "
                    "article.poly-card"
                )

                quantidade = cards.count()
                print(f"  Cards encontrados: {quantidade}")

                if quantidade == 0:
                    # Espera um pouco por conteúdo dinâmico.
                    page.wait_for_timeout(1800)
                    quantidade = cards.count()

                if quantidade == 0:
                    print("  Nenhum card nesta página.")
                    break

                adicionados_pagina = 0

                for i in range(quantidade):
                    produto = _extrair_card(cards.nth(i))

                    if not produto["title"] or produto["price"] <= 0:
                        continue

                    chave = produto["url"] or (
                        produto["title"].strip().lower(),
                        produto["price"],
                    )

                    if chave in vistos:
                        continue

                    vistos.add(chave)
                    resultados.append(produto)
                    adicionados_pagina += 1

                    if qtd_resultados > 0 and len(resultados) >= qtd_resultados:
                        break

                print(f"  Novos produtos: {adicionados_pagina}")

                if qtd_resultados > 0 and len(resultados) >= qtd_resultados:
                    break

                # Se a página não trouxe novos produtos, não há motivo para avançar.
                if adicionados_pagina == 0:
                    break

                time.sleep(0.5)

        finally:
            browser.close()

    resultados.sort(key=lambda x: x.get("price", 0))
    return resultados
