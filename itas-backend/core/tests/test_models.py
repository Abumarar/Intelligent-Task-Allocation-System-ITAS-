import pytest

from core.models import User


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(
        username="testuser",
        email="test@test.com",
        password="testpassword123",
        role="EMPLOYEE",
    )
    assert user.username == "testuser"
    assert user.role == "EMPLOYEE"
    assert user.check_password("testpassword123") is True
