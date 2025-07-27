from django.urls import path
from . import views

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.home_redirect),

    # تسجيل الدخول وتسجيل الخروج
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # لوحة التحكم
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # صفحات الإضافة
    path('add_user/', views.add_user_view, name='add_user'),
    path('add_classroom/', views.add_classroom_view, name='add_classroom'),
    path('add_teacher/', views.add_teacher_view, name='add_teacher'),
    path('add_parent/', views.add_paraent_view, name='add_parent'),
    path('add_student/', views.add_student_view, name='add_student'),

    # ربط المدرس بالصف
    path('assign_teacher/', views.assign_teacher_view, name='assign_teacher'),

    # إضافة مادة دراسية
    path('add_subject/', views.add_subject_view, name='add_subject'),

    # عرض الصفوف
    path('all_classrooms/', views.all_classrooms_view, name='all_classrooms'),

    # عرض المدرسين والطلاب في الصف
    path('classroom/<int:classroom_id>/teachers/', views.classroom_teachers_view, name='classroom_teachers'),
    path('classroom/<int:classroom_id>/students/', views.classroom_students_view, name='classroom_students'),

    # عرض المواد الخاصة بصف معين
    path('classroom/<int:classroom_id>/subjects/', views.classroom_subjects_view, name='classroom_subjects'),

    # عرض الجدول الأسبوعي لصف معين
    path('classroom/<int:classroom_id>/schedule/', views.weekly_schedule_view, name='weekly_schedule'),

    # واجهة المحادثة مع أولياء الأمور
    path('messages/', views.chat_with_parent_view, name='chat_with_parents'),
    path('messages/parents/', views.parent_list_view, name='parent_list'),
    path('messages/<int:parent_id>/', views.chat_detail_view, name='chat_detail'),


    # صفحات داشبورد الأدوار
    path('student/dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('teacher/dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('parent/dashboard/', views.parent_dashboard_view, name='parent_dashboard'),

    path('teacher/classrooms/', views.teacher_classrooms_view, name='teacher_classrooms'),
    path('teacher/classrooms/<int:classroom_id>/send/', views.send_broadcast_view, name='send_broadcast'),
    path('student/broadcasts/', views.student_broadcasts_view, name='student_broadcasts'),

    path("teacher/classrooms/", views.teacher_classrooms_view, name="teacher_classrooms"),
    path("teacher/classroom/<int:classroom_id>/subjects/", views.teacher_subjects_view, name="teacher_subjects"),
    path("teacher/classroom/<int:classroom_id>/students/", views.teacher_students_view, name="teacher_students"),
    path("teacher/classroom/<int:classroom_id>/student/<int:student_id>/add_grade/", views.add_grade_view, name="add_grade"),



    
] 