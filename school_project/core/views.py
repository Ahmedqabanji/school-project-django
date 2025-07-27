from django.shortcuts import render, redirect
from django.http import HttpResponse
import sqlite3
from .helpers import hash_password, check_password, is_admin 

# تحويل الزائر إلى صفحة تسجيل الدخول
def home_redirect(request):
    return redirect('login')

# صفحة تسجيل الدخول
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()
        cursor.execute("SELECT id, password, role, is_active FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id, hashed_pw, role, is_active = user
            if not is_active:
                return render(request, "login.html", {"error": "المستخدم غير مفعل. يرجى التواصل مع الإدارة."})
            if check_password(password, hashed_pw):  # ✅ استخدام الدالة المشتركة
                request.session["user_id"] = user_id
                request.session["role"] = role
                if role == "admin":
                    return redirect("dashboard")
                elif role == "student":
                    return redirect("student_dashboard")
                elif role == "teacher":
                    return redirect("teacher_dashboard")
                elif role == "parent":
                    return redirect("parent_dashboard")
        return render(request, "login.html", {"error": "اسم المستخدم أو كلمة المرور غير صحيحة."})

    return render(request, "login.html")

# تسجيل الخروج
def logout_view(request):
    request.session.flush()
    return redirect('login')

def add_user_view(request):
    if not is_admin(request):
        return redirect('login')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if username and password and role:
            conn = sqlite3.connect("db.sqlite3")
            c = conn.cursor()

            c.execute("SELECT id FROM users WHERE username = ?", (username,))
            if c.fetchone():
                conn.close()
                return render(request, 'add_user.html', {'error': 'اسم المستخدم موجود مسبقاً'})

            hashed_pw = hash_password(password)

            c.execute("""
                INSERT INTO users (username, password, role, is_active)
                VALUES (?, ?, ?, 1)
            """, (username, hashed_pw, role))
            conn.commit()

            user_id = c.lastrowid
            conn.close()

            if role == 'student':
                return redirect(f'/add_student/?user_id={user_id}')
            elif role == 'teacher':
                return redirect(f'/add_teacher/?user_id={user_id}')
            elif role == 'parent':
                return redirect(f'/add_parent/?user_id={user_id}')
            else:
                return redirect('dashboard')

    return render(request, 'add_user.html')



def add_student_view(request):
    if not is_admin(request):
        return redirect('login')

    user_id = request.GET.get('user_id')

    if request.method == 'POST':
        parent_id = request.POST.get('parent_id')
        class_id = request.POST.get('class_id')

        if parent_id and class_id:
            conn = sqlite3.connect('db.sqlite3')
            c = conn.cursor()
            c.execute("""
                INSERT INTO students (user_id, parent_id, class_id)
                VALUES (?, ?, ?)
            """, (user_id, parent_id, class_id))
            conn.commit()
            conn.close()
            return redirect('dashboard')

    # جلب أولياء الأمور
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("""
        SELECT p.id, u.username FROM parents p
        JOIN users u ON p.user_id = u.id
    """)
    parents = c.fetchall()

    c.execute("SELECT id, name FROM classrooms")
    classrooms = c.fetchall()
    conn.close()

    return render(request, 'add_student.html', {
        'user_id': user_id,
        'parents': parents,
        'classrooms': classrooms
    })


# دالة مساعدة: جلب الصفوف الدراسية
def get_all_classrooms():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM classrooms")
    result = cursor.fetchall()
    conn.close()
    return result

# دالة مساعدة: جلب المعلمين
def get_all_teachers():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role = 'teacher'")
    result = cursor.fetchall()
    conn.close()
    return result

# إضافة معلم وربطه بصف دراسي
def add_teacher_view(request):
    if not is_admin(request):  # ✅ استخدام الدالة is_admin
        return redirect('login')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        classroom_id = request.POST.get('classroom_id')

        if username and password and classroom_id:
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return render(request, 'add_teacher.html', {
                    'error': 'اسم المستخدم موجود بالفعل',
                    'classrooms': get_all_classrooms()
                })
            hashed_pw = hash_password(password)  # ✅ استخدام الدالة hash_password
            cursor.execute("""
                INSERT INTO users (username, password, role, is_active)
                VALUES (?, ?, 'teacher', 1)
            """, (username, hashed_pw))
            teacher_id = cursor.lastrowid
            cursor.execute("INSERT INTO teacher_classrooms (teacher_id, classroom_id) VALUES (?, ?)", (teacher_id, classroom_id))
            conn.commit()
            conn.close()
            return redirect('dashboard')
        else:
            return render(request, 'add_teacher.html', {
                'error': 'يرجى ملء جميع الحقول',
                'classrooms': get_all_classrooms()
            })

    classrooms = get_all_classrooms()
    return render(request, 'add_teacher.html', {'classrooms': classrooms})

# إضافة ولي أمر
def add_parent_view(request):
    if not is_admin(request):  # ✅ استخدام is_admin بدل الشرط اليدوي
        return redirect('login')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return render(request, 'add_parent.html', {'error': 'أسم المستخدم موجود بالفعل'})
            hashed_pw = hash_password(password)  # ✅ استخدام hash_password
            cursor.execute("""
                INSERT INTO users (username, password, role, is_active)
                VALUES (?, ?, 'parent', 0)
            """, (username, hashed_pw))
            conn.commit()
            conn.close()
            return redirect('dashboard')
        else:
            return render(request, 'add_parent.html', {'error': 'يرجى ملء جميع الحقول'})

    return render(request, 'add_parent.html')

# لوحة تحكم المدير
def dashboard_view(request):
    if not is_admin(request) or 'user_id' not in request.session:
        return redirect('login')
    return render(request, 'dashboard.html')
