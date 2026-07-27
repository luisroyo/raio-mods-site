"""
Payment Service (Stub)
Preparado para futura integração com APIs de Pagamento (PIX / Mercado Pago).
"""

class PaymentService:
    
    @staticmethod
    def generate_pix_payment(product_id: str, plan_duration: str):
        """
        Futuramente irá gerar código PIX Copia e Cola via API do Mercado Pago.
        """
        pass

    @staticmethod
    def verify_payment_status(payment_id: str):
        """
        Futuramente consultará se o pagamento foi concluído.
        """
        pass
