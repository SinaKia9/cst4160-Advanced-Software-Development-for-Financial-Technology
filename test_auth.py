from core.auth import (
    hash_password,
    verify_password,
    is_valid_email,
    generate_code
)


def test_hash_password_changes_value():
    password = "SecurePass123"
    hashed = hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)


def test_verify_password_success():
    password = "SecurePass123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_failure():
    password = "SecurePass123"
    hashed = hash_password(password)

    assert verify_password("WrongPassword", hashed) is False


def test_valid_email():
    assert is_valid_email("john@example.com") is True


def test_invalid_email():
    assert is_valid_email("not-an-email") is False


def test_generate_code():
    code1 = generate_code()
    code2 = generate_code()

    assert isinstance(code1, str)
    assert isinstance(code2, str)
    assert len(code1) == 6
    assert len(code2) == 6
    assert code1 != code2