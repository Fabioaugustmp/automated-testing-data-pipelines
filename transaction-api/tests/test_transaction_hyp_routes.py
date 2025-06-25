from hypothesis import given, strategies as st

@given(
    nome=st.text(min_size=1, max_size=50),
    mcc=st.text(min_size=4, max_size=4),
    valor=st.floats(min_value=0.01, max_value=100000, allow_nan=False, allow_infinity=False)
)
def test_post_transaction_hypothesis(client, nome, mcc, valor):
    payload = {
        "nome": nome,
        "mcc": mcc,
        "valor": valor
    }
    response = client.post("/transacoes/", json=payload)
    # Accepts 201 (created) or 409 (duplicate), both are valid for property-based testing
    assert response.status_code in (201, 409)
    if response.status_code == 201:
        data = response.json()
        assert data["nome"] == nome
        assert data["mcc"] == mcc
        assert data["valor"] == valor

def test_get_transactions_returns_list(client):
    response = client.get("/transacoes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@given(
    nome=st.text(min_size=0, max_size=0),  # Invalid: empty string
    mcc=st.text(min_size=0, max_size=3),   # Invalid: too short
    valor=st.floats(max_value=0, allow_nan=False, allow_infinity=False)  # Invalid: zero or negative
)
def test_post_transaction_invalid_data(client, nome, mcc, valor):
    payload = {
        "nome": nome,
        "mcc": mcc,
        "valor": valor
    }
    response = client.post("/transacoes/", json=payload)
    assert response.status_code == 422