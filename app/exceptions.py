class InvalidAIResponseError(Exception):
    """Erro emitido quando o provedor de IA retorna uma resposta inutilizável."""

    def __init__(self, repair_feedback: str = "response failed parsing or validation") -> None:
        self.repair_feedback = repair_feedback
        super().__init__("O provedor de IA retornou uma resposta inválida.")
