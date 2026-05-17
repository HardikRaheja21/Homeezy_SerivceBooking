import razorpay
from app.core.config import settings
import hmac
import hashlib

class RazorpayProvider:
    def __init__(self):
        self.client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    def create_order(self, amount: float, currency: str = "USD", receipt: str = None) -> dict:
        """
        Creates an order in Razorpay. Amount should be in decimal format (e.g., 10.50), 
        it will be converted to the smallest unit (e.g., cents).
        """
        data = {
            "amount": int(amount * 100),
            "currency": currency,
            "receipt": receipt
        }
        order = self.client.order.create(data=data)
        return order

    def verify_webhook_signature(self, body: str, signature: str) -> bool:
        """
        Verifies the Razorpay webhook signature.
        """
        try:
            expected_signature = hmac.new(
                bytes(settings.RAZORPAY_KEY_SECRET, 'latin-1'),
                msg=bytes(body, 'latin-1'),
                digestmod=hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False
