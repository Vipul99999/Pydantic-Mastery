"""Tests for @computed_field behavior."""
import pytest
from datetime import date, datetime
from app.models.computed import UserProfileComputed

class TestComputedFields:
    def test_full_name(self):
        p = UserProfileComputed(
            id=1, username="u", email="e@e.com",
            first_name="John", last_name="Doe", date_of_birth=date(1990, 1, 1)
        )
        assert p.full_name == "John Doe"

    def test_age_calculation(self):
        p = UserProfileComputed(
            id=1, username="u", email="e@e.com",
            first_name="A", last_name="B", date_of_birth=date(2000, 1, 1),
            account_created=datetime.utcnow()
        )
        current_year = datetime.utcnow().year
        assert p.age == current_year - 2000

    def test_premium_badge_conditional(self):
        p_free = UserProfileComputed(
            id=1, username="u", email="e@e.com", first_name="A", last_name="B",
            date_of_birth=date(1990, 1, 1), is_premium=False,
            account_created=datetime.utcnow()
        )
        p_prem = p_free.model_copy(update={"is_premium": True})
        
        assert p_free.premium_badge is None
        assert "Premium" in p_prem.premium_badge