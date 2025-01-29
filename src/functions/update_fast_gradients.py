def update_fast_gradients(self, new_fast_gradient):
    """
    Atualiza a lista de gradientes rápidos, mantendo apenas os mais recentes.

    Args:
        new_fast_gradient (float): Novo valor do gradiente rápido.

    Returns:
        None
    """
    max_gradients_to_store = 10  # Número máximo de gradientes a armazenar
    self.fast_gradients.append(new_fast_gradient)

    # Remover o gradiente mais antigo se exceder o tamanho máximo
    if len(self.fast_gradients) > max_gradients_to_store:
        self.fast_gradients.pop(0)
