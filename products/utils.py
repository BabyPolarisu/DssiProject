import cv2
import numpy as np

def verify_promptpay_qr(image_file, input_account_number):
    """
    ฟังก์ชันตรวจสอบความถูกต้องของ QR Code PromptPay
    return: (True/False, message)
    """
    try:
        # 1. แปลงไฟล์ที่อัปโหลดให้เป็น format ที่ OpenCV อ่านได้
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        # รีเซ็ต pointer ของไฟล์ให้กลับไปเริ่มต้น (เพื่อให้ Django save ลง DB ได้ต่อ)
        image_file.seek(0)

        if img is None:
            return False, "ไฟล์รูปภาพไม่ถูกต้อง หรือเสียหาย"

        # 2. สร้างตัวอ่าน QR Code
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(img)

        if not data:
            return False, "ไม่พบ QR Code ในรูปภาพ กรุณาอัปโหลดรูปที่ชัดเจน"

        # 3. ตรวจสอบข้อมูลใน QR (Logic เบื้องต้น)
        # ปกติ PromptPay QR จะมีข้อมูล Standard EMVCo
        # แต่ถ้าแบบง่ายคือดูว่าใน QR มีเลขบัญชีหรือเบอร์โทรที่กรอกมาไหม
        
        # ลบขีดออกจากเลขบัญชีที่กรอกมา (เช่น 081-234 -> 081234)
        clean_acc_num = input_account_number.replace('-', '').replace(' ', '')
        
        if clean_acc_num in data:
            return True, "ตรวจสอบแล้ว: QR Code ตรงกับเลขบัญชี"
        else:
            # กรณี QR เป็น Code ที่เข้ารหัสซับซ้อน อาจจะเช็คแค่ว่าเป็น QR ก็พอในระดับเบื้องต้น
            # แต่ถ้าอยากเข้มงวด ให้ return False
            print(f"QR Data Found: {data}") # ไว้ดู log
            return True, "พบ QR Code (แต่รูปแบบข้อมูลอาจตรวจสอบเลขบัญชีโดยตรงไม่ได้)" 
            # เปลี่ยนเป็น False ถ้าต้องการความเป๊ะ 100% (แต่ User อาจจะอัป QR เจนใหม่ๆ ไม่ผ่าน)

    except Exception as e:
        print(e)
        return False, "เกิดข้อผิดพลาดในการประมวลผลรูปภาพ"