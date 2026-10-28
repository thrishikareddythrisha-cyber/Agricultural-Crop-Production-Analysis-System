import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "crop_analysis"),
    )

def init_db():
    # Create the database once in MySQL Workbench or the MySQL command line:
    # CREATE DATABASE crop_analysis;
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS regions (
                region_id INT AUTO_INCREMENT PRIMARY KEY,
                region_name VARCHAR(120) NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crops (
                crop_id INT AUTO_INCREMENT PRIMARY KEY,
                crop_name VARCHAR(120) NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crop_records (
                record_id INT AUTO_INCREMENT PRIMARY KEY,
                crop_id INT NOT NULL,
                region_id INT NOT NULL,
                year SMALLINT NOT NULL,
                cultivated_area DECIMAL(16,4) NOT NULL,
                production DECIMAL(16,4) NOT NULL,
                rainfall_mm DECIMAL(10,2) NULL,
                area_unit VARCHAR(40) NOT NULL,
                production_unit VARCHAR(40) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_record_crop FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
                CONSTRAINT fk_record_region FOREIGN KEY (region_id) REFERENCES regions(region_id),
                INDEX idx_year_region_crop (year, region_id, crop_id)
            )
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()
