FROM python:3.11-slim

# ตั้งค่า Environment ไม่ให้สร้างไฟล์ .pyc และให้ log ออกมาทันที
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# กำหนดโฟลเดอร์ทำงานใน Container
WORKDIR /app

# ติดตั้ง Dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# ติดตั้ง Netcat (เผื่อไว้ใช้รอ DB start)
RUN apt-get update && apt-get install -y netcat-openbsd

# Copy โค้ดทั้งหมดเข้า Container
COPY . /app/

# สร้างโฟลเดอร์สำหรับ Static files (เพื่อให้ Nginx เข้าถึงได้)
RUN mkdir -p /app/static /app/media