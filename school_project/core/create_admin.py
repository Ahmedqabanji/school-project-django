import sqlite3
import bcrypt

# إعداد البيانات
username = "admin"
password = "admin123"
role = "admin"

# تشفير كلمة السر باستخدام bcrypt
hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# الاتصال بقاعدة البيانات (ارجع خطوة للخلف من مجلد core)
conn = sqlite3.connect("../db.sqlite3")
cursor = conn.cursor()

# التحقق هل المستخدم موجود
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
if cursor.fetchone():
    print("❗ الحساب موجود مسبقًا.")
else:
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   (username, hashed_password.decode(), role))
    conn.commit()
    print("✅ تم إنشاء حساب الأدمن بنجاح.")

conn.close()
