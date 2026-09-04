class InvalidAIResponseError(Exception):
    """Erro emitido quando o provedor de IA retorna uma resposta inutilizável."""

    def __init__(self) -> None:
        super().__init__("O provedor de IA retornou uma resposta inválida.")
