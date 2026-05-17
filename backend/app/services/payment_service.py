import razorpay
import stripe
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class PaymentService:
    """Payment service for handling payments via Razorpay and Stripe"""
    
    def __init__(self):
        # Initialize Razorpay
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self.razorpay_client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )
        else:
            self.razorpay_client = None
            logger.warning("Razorpay credentials not configured")
        
        # Initialize Stripe
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self.stripe_enabled = True
        else:
            self.stripe_enabled = False
            logger.warning("Stripe credentials not configured")
    
    # ==================== RAZORPAY METHODS ====================
    
    def create_razorpay_order(self, amount: float, currency: str = "INR", receipt: str = None):
        """Create a Razorpay order"""
        if not self.razorpay_client:
            raise Exception("Razorpay not configured")
        
        try:
            order_data = {
                "amount": int(amount * 100),  # Convert to paise
                "currency": currency,
                "receipt": receipt or f"receipt_{int(amount)}",
                "payment_capture": 1  # Auto capture
            }
            
            order = self.razorpay_client.order.create(data=order_data)
            logger.info(f"Razorpay order created: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {str(e)}")
            raise
    
    def verify_razorpay_signature(self, order_id: str, payment_id: str, signature: str):
        """Verify Razorpay payment signature"""
        if not self.razorpay_client:
            raise Exception("Razorpay not configured")
        
        try:
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            self.razorpay_client.utility.verify_payment_signature(params_dict)
            logger.info(f"Razorpay signature verified for payment: {payment_id}")
            return True
            
        except razorpay.errors.SignatureVerificationError as e:
            logger.error(f"Razorpay signature verification failed: {str(e)}")
            return False
    
    def fetch_razorpay_payment(self, payment_id: str):
        """Fetch Razorpay payment details"""
        if not self.razorpay_client:
            raise Exception("Razorpay not configured")
        
        try:
            payment = self.razorpay_client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            logger.error(f"Failed to fetch Razorpay payment: {str(e)}")
            raise
    
    def create_razorpay_refund(self, payment_id: str, amount: float = None):
        """Create a Razorpay refund"""
        if not self.razorpay_client:
            raise Exception("Razorpay not configured")
        
        try:
            refund_data = {}
            if amount:
                refund_data["amount"] = int(amount * 100)  # Convert to paise
            
            refund = self.razorpay_client.payment.refund(payment_id, refund_data)
            logger.info(f"Razorpay refund created: {refund['id']}")
            return refund
            
        except Exception as e:
            logger.error(f"Failed to create Razorpay refund: {str(e)}")
            raise
    
    # ==================== STRIPE METHODS ====================
    
    def create_stripe_payment_intent(self, amount: float, currency: str = "inr", metadata: dict = None):
        """Create a Stripe payment intent"""
        if not self.stripe_enabled:
            raise Exception("Stripe not configured")
        
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to smallest currency unit
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            
            logger.info(f"Stripe payment intent created: {payment_intent['id']}")
            return payment_intent
            
        except Exception as e:
            logger.error(f"Failed to create Stripe payment intent: {str(e)}")
            raise
    
    def retrieve_stripe_payment_intent(self, payment_intent_id: str):
        """Retrieve Stripe payment intent"""
        if not self.stripe_enabled:
            raise Exception("Stripe not configured")
        
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent
        except Exception as e:
            logger.error(f"Failed to retrieve Stripe payment intent: {str(e)}")
            raise
    
    def create_stripe_refund(self, payment_intent_id: str, amount: float = None):
        """Create a Stripe refund"""
        if not self.stripe_enabled:
            raise Exception("Stripe not configured")
        
        try:
            refund_data = {"payment_intent": payment_intent_id}
            if amount:
                refund_data["amount"] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_data)
            logger.info(f"Stripe refund created: {refund['id']}")
            return refund
            
        except Exception as e:
            logger.error(f"Failed to create Stripe refund: {str(e)}")
            raise
    
    # ==================== UTILITY METHODS ====================
    
    def calculate_platform_commission(self, amount: float, percentage: float = None):
        """Calculate platform commission"""
        if percentage is None:
            percentage = settings.PLATFORM_COMMISSION_PERCENT
        
        commission = (amount * percentage) / 100
        worker_payout = amount - commission
        
        return {
            "total_amount": amount,
            "commission": round(commission, 2),
            "worker_payout": round(worker_payout, 2),
            "commission_percentage": percentage
        }
    
    def validate_payment_amount(self, amount: float, min_amount: float = 1.0):
        """Validate payment amount"""
        if amount < min_amount:
            raise ValueError(f"Payment amount must be at least ₹{min_amount}")
        
        if amount > 500000:  # Max 5 lakh
            raise ValueError("Payment amount exceeds maximum limit of ₹5,00,000")
        
        return True