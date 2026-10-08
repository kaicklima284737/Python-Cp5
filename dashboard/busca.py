def quicksort(registros, chave):
    """Ordena uma lista de registros pelo valor retornado por chave(registro)."""
    if len(registros) < 2:
        return registros
    pivo = registros[0]
    valor_pivo = chave(pivo)
    menores = [r for r in registros[1:] if chave(r) <= valor_pivo]
    maiores = [r for r in registros[1:] if chave(r) > valor_pivo]
    return quicksort(menores, chave) + [pivo] + quicksort(maiores, chave)


def pesquisa_binaria(registros, item, chave):
    """Retorna o índice de um registro cuja chave seja igual a item, ou -1."""
    esquerda = 0
    direita = len(registros) - 1
    while esquerda <= direita:
        meio = (esquerda + direita) // 2
        valor = chave(registros[meio])
        if valor == item:
            return meio
        elif valor > item:
            direita = meio - 1
        else:  # valor < item
            esquerda = meio + 1
    return -1


def buscar_titulo(ordenados, titulo):
    """Busca binária por título exato. Retorna todos os registros com esse título."""
    alvo = titulo.strip().lower()
    chave = lambda r: r["titulo"].lower()

    meio = pesquisa_binaria(ordenados, alvo, chave)
    if meio == -1:
        return []

    # A busca binária acha um deles. Os repetidos ficam lado a lado.
    inicio = fim = meio
    while inicio > 0 and chave(ordenados[inicio - 1]) == alvo:
        inicio -= 1
    while fim < len(ordenados) - 1 and chave(ordenados[fim + 1]) == alvo:
        fim += 1
    return ordenados[inicio : fim + 1]