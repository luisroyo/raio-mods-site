import os
from dotenv import load_dotenv
import mercadopago

load_dotenv()
token = os.getenv('MP_ACCESS_TOKEN')
sdk = mercadopago.SDK(token)

res = sdk.payment().search({"external_reference": "teste"})
print("With dict:", res)
