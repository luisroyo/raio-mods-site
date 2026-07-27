"""
User Service (Stub)
Preparado para futura integração com banco de dados para controle de usuários.
"""

class UserService:
    
    @staticmethod
    def register_or_update_user(telegram_id: int, username: str, first_name: str):
        """
        Futuramente, salvará no DB e atualizará o campo 'last_interaction'.
        """
        pass

    @staticmethod
    def get_user_history(telegram_id: int):
        """
        Consultar histórico futuro do usuário.
        """
        return []
