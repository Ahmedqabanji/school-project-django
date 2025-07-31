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
    if not is_admin(request):  # استخدام is_admin بدل الشرط اليدوي
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


# إضافة صف دراسي
def add_classroom_view(request):
    if request.session.get('role') != 'admin':
        return redirect('login')

    if request.method == 'POST':
        name = request.POST.get('name')
        year = request.POST.get('year')

        if name and year:
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO classrooms (name, year) VALUES (?, ?)", (name, year))
            conn.commit()
            conn.close()
            return redirect('dashboard')
        else:
            return render(request, 'add_classroom.html', {'error': 'يرجى ملء كل الحقول'})

    return render(request, 'add_classroom.html')

# دالة مساعدة لجلب الصفوف
def get_all_classrooms():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM classrooms")
    result = cursor.fetchall()
    conn.close()
    return result



# عرض كل الصفوف
def all_classrooms_view(request):
    if request.session.get("role") != "admin":
        return redirect('login')

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, year FROM classrooms")
    classrooms = cursor.fetchall()
    conn.close()

    return render(request, "all_classrooms.html", {"classrooms": classrooms})

# عرض المدرسين المرتبطين بصف
def classroom_teachers_view(request, classroom_id):
    if not is_admin(request):  
        return redirect('login')

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT users.username
        FROM users
        JOIN teacher_classrooms ON users.id = teacher_classrooms.teacher_id
        WHERE teacher_classrooms.classroom_id = ?
    """, (classroom_id,))
    teachers = cursor.fetchall()
    conn.close()

    return render(request, "classroom_teachers.html", {"teachers": teachers})


# عرض الطلاب وأولياء أمورهم في صف معين
def classroom_students_view(request, classroom_id):
    if not is_admin(request):  
        return redirect('login')

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, u.username AS student_name, p.username AS parent_name, p.id AS parent_id
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN users p ON s.parent_id = p.id
        WHERE s.classroom_id = ?
    """, (classroom_id,))
    students = cursor.fetchall()
    conn.close()

    return render(request, "classroom_students.html", {
        "students": students,
        "classroom_id": classroom_id
    })


# عرض قائمة أولياء الأمور لبدء محادثة
def chat_with_parent_view(request):
    if not is_admin(request):  
        return redirect('login')

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role = 'parent'")
    parents = cursor.fetchall()
    conn.close()

    return render(request, "chat_with_parents.html", {"parents": parents})



# صفحة تفاصيل المحادثة بين المدير وولي الأمر
def chat_detail_view(request, parent_id):
    if not is_admin(request):  
        return redirect('login')

    user_id = request.session["user_id"]
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    if request.method == "POST":
        content = request.POST.get("message")
        if content:
            cursor.execute("""
                INSERT INTO messages (sender_id, receiver_id, content)
                VALUES (?, ?, ?)
            """, (user_id, parent_id, content))
            conn.commit()

    cursor.execute("""
        SELECT messages.id, sender.username, content, timestamp, sender.id
        FROM messages
        JOIN users AS sender ON sender.id = messages.sender_id
        WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?)
        ORDER BY timestamp ASC
    """, (user_id, parent_id, parent_id, user_id))

    messages = cursor.fetchall()
    cursor.execute("SELECT username FROM users WHERE id = ?", (parent_id,))
    parent_name = cursor.fetchone()[0]
    conn.close()

    return render(request, "chat_detail.html", {
        "messages": messages,
        "parent_id": parent_id,
        "parent_name": parent_name,
        "my_id": user_id
    })



# عرض قائمة أولياء الأمور لبدء محادثة
def parent_list_view(request):
    if not is_admin(request):  
        return redirect('login')

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users WHERE role = 'parent'")
    parents = cursor.fetchall()

    conn.close()

    return render(request, "parent_list.html", {"parents": parents})




def assign_teacher_view(request):
    if not is_admin(request):  
        return redirect('login')
    
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    if request.method == "POST":
        teacher_id = request.POST.get("teacher_id")
        classroom_id  = request.POST.get("classroom_id")
        cursor.execute("INSERT OR IGNORE INTO teacher_classrooms (teacher_id, classroom_id) VALUES (?,?)", (teacher_id, classroom_id))

        conn.commit()
        conn.close()
        return redirect("dashboard")
    
    cursor.execute("SELECT id, username FROM users WHERE role = 'teacher'")
    teachers = cursor.fetchall()
    cursor.execute("SELECT id, name FROM classrooms")
    classrooms =cursor.fetchall()
    conn.close()

    return render(request, "assign_teacher.html", {
        "teachers":teachers,
        "classrooms":classrooms
    })


# إضافة مادة دراسية وربطها بمدرس وصف
def add_subject_view(request):
    if not is_admin(request):  
        return redirect('login')

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.POST.get('name')
        teacher_id = request.POST.get('teacher_id')
        classroom_id = request.POST.get('classroom_id')
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if name and teacher_id and classroom_id and day and start_time and end_time:
            cursor.execute("""
                INSERT INTO subjects (name, teacher_id, classroom_id, day, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, teacher_id, classroom_id, day, start_time, end_time))
            conn.commit()
            conn.close()
            return redirect('dashboard')
        else:
            return render(request, 'add_subject.html', {
                'error': 'يرجى ملء جميع الحقول',
                'teachers': get_all_teachers(),
                'classrooms': get_all_classrooms()
            })

    teachers = get_all_teachers()
    classrooms = get_all_classrooms()
    conn.close()
    return render(request, 'add_subject.html', {
        'teachers': teachers,
        'classrooms': classrooms
    })

def get_all_teachers():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role = 'teacher'")
    teachers = cursor.fetchall()
    conn.close()
    return teachers

def get_all_classrooms():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM classrooms")
    classrooms = cursor.fetchall()
    conn.close()
    return classrooms

# عرض المواد الدراسية المرتبطة بصف معين
def classroom_subjects_view(request, classroom_id):
    if not is_admin(request):  
        return redirect('login')
    
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subjects.name, users.username, subjects.day, subjects.start_time, subjects.end_time
        FROM subjects
        JOIN users ON subjects.teacher_id = users.id
        WHERE subjects.classroom_id = ?
    """, (classroom_id,))
    subjects = cursor.fetchall()
    conn.close()

    return render(request, "classroom_subjects.html", {
        "subjects": subjects,
        "classroom_id": classroom_id
    })



def weekly_schedule_view(request, classroom_id):
    if not is_admin(request):  
        return redirect('login')
    
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subjects.day, subjects.start_time, subjects.end_time, subjects.name, users.username
        FROM subjects
        JOIN users ON subjects.teacher_id = users.id
        WHERE subjects.classroom_id = ?
        ORDER BY 
            CASE day
                WHEN 'Sunday' THEN 1
                WHEN 'Monday' THEN 2
                WHEN 'Tuesday' THEN 3
                WHEN 'Wednesday' THEN 4
                WHEN 'Thursday' THEN 5
                WHEN 'Friday' THEN 6
                WHEN 'Saturday' THEN 7
            END,
            start_time
    """, (classroom_id,))

    subjects = cursor.fetchall()
    conn.close()

    return render(request, "weekly_schedule.html", {
        "subjects": subjects,
        "classroom_id": classroom_id
    })



def assign_teacher_view(request):
    if not is_admin(request):  
        return redirect('login')
    
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    if request.method == "POST":
        teacher_id = request.POST.get("teacher_id")
        classroom_id  = request.POST.get("classroom_id")
        cursor.execute("INSERT OR IGNORE INTO teacher_classrooms (teacher_id, classroom_id) VALUES (?,?)", (teacher_id, classroom_id))

        conn.commit()
        conn.close()
        return redirect("dashboard")
    
    cursor.execute("SELECT id, username FROM users WHERE role = 'teacher'")
    teachers = cursor.fetchall()
    cursor.execute("SELECT id, name FROM classrooms")
    classrooms =cursor.fetchall()
    conn.close()

    return render(request, "assign_teacher.html", {
        "teachers":teachers,
        "classrooms":classrooms
    })


# إضافة مادة دراسية وربطها بمدرس وصف
def add_subject_view(request):
    if not is_admin(request):  
        return redirect('login')

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.POST.get('name')
        teacher_id = request.POST.get('teacher_id')
        classroom_id = request.POST.get('classroom_id')
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if name and teacher_id and classroom_id and day and start_time and end_time:
            cursor.execute("""
                INSERT INTO subjects (name, teacher_id, classroom_id, day, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, teacher_id, classroom_id, day, start_time, end_time))
            conn.commit()
            conn.close()
            return redirect('dashboard')
        else:
            return render(request, 'add_subject.html', {
                'error': 'يرجى ملء جميع الحقول',
                'teachers': get_all_teachers(),
                'classrooms': get_all_classrooms()
            })

    teachers = get_all_teachers()
    classrooms = get_all_classrooms()
    conn.close()
    return render(request, 'add_subject.html', {
        'teachers': teachers,
        'classrooms': classrooms
    })

def get_all_teachers():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role = 'teacher'")
    teachers = cursor.fetchall()
    conn.close()
    return teachers

def get_all_classrooms():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM classrooms")
    classrooms = cursor.fetchall()
    conn.close()
    return classrooms

# عرض المواد الدراسية المرتبطة بصف معين
def classroom_subjects_view(request, classroom_id):
    if not is_admin(request):  
        return redirect('login')
    
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subjects.name, users.username, subjects.day, subjects.start_time, subjects.end_time
        FROM subjects
        JOIN users ON subjects.teacher_id = users.id
        WHERE subjects.classroom_id = ?
    """, (classroom_id,))
    subjects = cursor.fetchall()
    conn.close()

    return render(request, "classroom_subjects.html", {
        "subjects": subjects,
        "classroom_id": classroom_id
    })



def weekly_schedule_view(request, classroom_id):
    if not is_admin(request):  
        return redirect('login')

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subjects.day, subjects.start_time, subjects.end_time, subjects.name, users.username
        FROM subjects
        JOIN users ON subjects.teacher_id = users.id
        WHERE subjects.classroom_id = ?
        ORDER BY 
            CASE day
                WHEN 'Sunday' THEN 1
                WHEN 'Monday' THEN 2
                WHEN 'Tuesday' THEN 3
                WHEN 'Wednesday' THEN 4
                WHEN 'Thursday' THEN 5
                WHEN 'Friday' THEN 6
                WHEN 'Saturday' THEN 7
            END,
            start_time
    """, (classroom_id,))

    subjects = cursor.fetchall()
    conn.close()

    return render(request, "weekly_schedule.html", {
        "subjects": subjects,
        "classroom_id": classroom_id
    })



def teacher_subjects_view(request, classroom_id):
    if request.session.get("role") != "teacher":
        return redirect('login')

    teacher_id = request.session.get("user_id")
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, day, start_time, end_time
        FROM subjects
        WHERE classroom_id = ? AND teacher_id = ?
    """, (classroom_id, teacher_id))
    subjects = cursor.fetchall()
    conn.close()

    return render(request, "teacher_subjects.html", {"subjects": subjects})


def teacher_students_view(request, classroom_id):
    if request.session.get("role") != "teacher":
        return redirect('login')

    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.id, u.username
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.classroom_id = ?
    """, (classroom_id,))
    students = cursor.fetchall()
    conn.close()

    return render(request, "teacher_students.html", {
        "students": students,
        "classroom_id": classroom_id
    })


def add_grade_view(request, classroom_id, student_id):
    if request.session.get("role") != "teacher":
        return redirect("login")

    teacher_id = request.session.get("user_id")
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()

    # جلب المواد التي يدرسها هذا المدرس داخل هذا الصف فقط
    cursor.execute("""
        SELECT id, name FROM subjects
        WHERE teacher_id = ? AND classroom_id = ?
    """, (teacher_id, classroom_id))
    subjects = cursor.fetchall()

    if request.method == "POST":
        subject_id = request.POST.get("subject_id")
        exam_score = request.POST.get("exam_score")
        evaluation = request.POST.get("evaluation")

        cursor.execute("""
            INSERT INTO grades (student_id, subject_id, exam_score, evaluation)
            VALUES (?, ?, ?, ?)
        """, (student_id, subject_id, exam_score, evaluation))

        conn.commit()
        conn.close()
        return redirect("teacher_students", classroom_id=classroom_id)

    conn.close()
    return render(request, "add_grade.html", {
        "subjects": subjects,
        "student_id": student_id,
        "classroom_id": classroom_id
    })


def student_dashboard_view(request):
    if request.session.get("role") != "student":
        return redirect("login")

    return render(request, "student_dashboard.html")


def teacher_dashboard_view(request):
    if request.session.get("role") != "teacher":
        return redirect("login")

    return render(request, "teacher_dashboard.html")

def parent_dashboard_view(request):
    if request.session.get("role") != "parent":
        return redirect("login")

    return render(request, "parent_dashboard.html")