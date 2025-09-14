import os
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import sys
import asyncpg
sys.path.append(os.path.dirname(__file__))
from Deuda import pago
import datetime
import aiohttp

app = FastAPI()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

@app.post("/pago_deuda")
async def telegram_webhook(req: Request):
    try:
        data = await req.json()
        logger.info(f"Received webhook data: {data}")
        message = data.get("message")
        if not message:
            return JSONResponse({"status": "no_message"})

        if message.get("text"):
            values = message["text"].split()
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                row = await conn.fetchrow(
                    "SELECT deuda_uf, deuda_dolares_sin_interes, deuda_dolares_con_interes, fecha_ultimo_pago "
                    "FROM deudas WHERE deudor = $1 ORDER BY fecha_ultimo_pago DESC LIMIT 1",
                    values[0]
                )
                if row:
                    logger.error(f"{row[0]} {type(row[0])} {row[1]} {type(row[1])} {row[3]} {type(row[3])}")
                    ultimo_pago_formato, nueva_deuda_uf, nueva_deuda_usd_sin_interes, nueva_deuda_usd_con_interes, string = pago(
                        row[3],
                        row,
                        float(row[0]),
                        float(row[1]),
                        float(row[2]),
                        float(values[1]),
                        float(values[2]),
                        float(values[3])
                    )

                    # Insert new row
                    await conn.execute(
                        """
                        INSERT INTO deudas (fecha, deudor, deuda_uf, deuda_dolares_sin_interes, deuda_dolares_con_interes)
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        datetime.datetime.now(),  # fecha
                        values[0],                # deudor
                        nueva_deuda_uf,           # deuda_uf
                        nueva_deuda_usd_sin_interes,   # deuda_dolares_sin_interes
                        nueva_deuda_usd_con_interes    # deuda_dolares_con_interes
                    )
                    
                    async with aiohttp.ClientSession() as session:
                        response = await session.post(
                            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                            json={"chat_id": message["chat"]["id"], "text": string},
                        )
                        if response.status != 200:
                            logger.error(f"Failed to send Telegram message: {response.status}")
                    
                    return JSONResponse({"status": "success", "message": string})
                
            finally:
                await conn.close()
        return JSONResponse({"status": "no_text"})
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse({"status": "error", "error": str(e)})


@app.get("/favicon.ico")
async def faviconico():
    return Response(status_code=204)


@app.get("/favicon.png")
async def faviconpng():
    return Response(status_code=204)


@app.get("/")
def read_root():
    return {"message": "Hello World from FastAPI on Vercel!"}


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/test-hf")
async def test_hf():
    try:
        logger.info("Testing Hugging Face client")
        return {"status": "hf_client_initialized", "provider": "fal-ai"}
    except Exception as e:
        logger.error(f"HF client test failed: {str(e)}")
        return {"status": "error", "error": str(e)}
