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