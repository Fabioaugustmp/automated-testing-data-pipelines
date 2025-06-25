# app/schemas/transaction.py
import datetime
from pydantic import BaseModel, Field, ConfigDict

class TransactionBase(BaseModel):
    nome: str = Field(..., description="Nome da transação")
    mcc: str = Field(..., description="Código MCC")
    valor: float = Field(..., gt=0, description="Valor da transação")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "Restaurante Comida Boa",
                    "mcc": "5812",
                    "valor": 99.90
                }
            ]
        }
    )

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    data: datetime.datetime

    model_config = ConfigDict(from_attributes=True)