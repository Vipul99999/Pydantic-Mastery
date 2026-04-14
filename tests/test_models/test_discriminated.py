"""Tests for Field(discriminator=...) unions."""
import pytest
from app.models.discriminated_unions import PaymentProfile, WebhookPayload

class TestDiscriminatedUnions:
    def test_credit_card_validation(self):
        payload = {
            "user_id": 1,
            "primary_method": {
                "type": "credit_card",
                "card_brand": "visa",
                "last_four": "4242",
                "expiry_month": 12,
                "expiry_year": 2028
            }
        }
        obj = PaymentProfile(**payload)
        assert obj.primary_method.type == "credit_card"
        assert hasattr(obj.primary_method, "card_brand")

    def test_invalid_discriminator_value(self):
        with pytest.raises(Exception, match="discriminator"):
            PaymentProfile(
                user_id=1,
                primary_method={"type": "paypal", "account": "test"}
            )