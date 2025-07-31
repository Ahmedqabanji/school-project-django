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
    #path('add_classroom/', views.add_classroom_view, name='add_classroom'),
    path('add_teacher/', views.add_teacher_view, name='add_teacher'),
   # path('add_parent/', views.add_paraent_view, name='add_parent'),
    path('add_student/', views.add_student_view, name='add_student'),

    # ربط المدرس بالصف
  
   path('classrooms/add/', views.add_classroom, name='add_classroom'),

   path('classrooms/', views.all_classrooms, name='all_classrooms'),

    
] 