from fastapi import FastAPI, HTTPException, Query
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from collections import defaultdict
# Routers
from routers.buyback_router import router as buyback_router
from routers.device_router import router as device_router
from routers.master_router import router as master_router
from routers.item_router import router as item_router
from routers.question_router import router as question_router
from routers.customer_router import router as customer_router
# -------------------------------------------------
# LOAD ENV
# -------------------------------------------------
load_dotenv()

app = FastAPI(title="GoStack FastAPI", version="2.0")

# -------------------------------------------------
# DB CONFIG FROM ENV
# -------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
    "connect_timeout": 5,
}

# -------------------------------------------------
# DB CONNECTION
# -------------------------------------------------
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        yield conn
    finally:
        if conn:
            conn.close()

# -------------------------------------------------
# ROOT
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "FastAPI server is running"}


app.include_router(buyback_router)
app.include_router(master_router)
app.include_router(device_router)
app.include_router(item_router)
app.include_router(question_router)
app.include_router(customer_router)
# -------------------------------------------------
# HEALTH
# -------------------------------------------------
@app.get("/health")
def health():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
                result = cursor.fetchone()
        return {"status": "ok", "db": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
        

    # =================================================
#  APPOINTMENT TYPE LIST API
# =================================================
@app.get("/api/v1/GetAppointmentTypesBuyback")
def get_appointment_types():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        name,
                        appoinment_id,
                        appoinmnet_type_name,
                        is_active,
                        creation,
                        modified
                    FROM `tabAppoinment Type Master`
                    WHERE is_active = 1
                    ORDER BY appoinment_id
                    """
                )
                data = cursor.fetchall()

        return {
            "success": True,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


