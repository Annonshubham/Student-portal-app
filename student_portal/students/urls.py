from django.urls import path
from . import views

urlpatterns = [
    # Home & Dashboard
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Student Management
    path('students/', views.students_page, name='students'),
    path('add/', views.add_student, name='add-student'),
    path('student/<int:student_id>/', views.student_detail, name='student-detail'),
    path('edit/<int:student_id>/', views.edit_student, name='edit-student'),
    path('delete/<int:student_id>/', views.delete_student, name='delete-student'),
    
    # CGPA & Grades
    path('cgpa/', views.cgpa_calculator, name='cgpa-calculator'),
    path('grades/', views.grade_view, name='grade-view'),
    path('grades/<int:student_id>/', views.grade_view, name='grade-view-student'),
    path('add-grade/<int:student_id>/', views.add_grade, name='add-grade'),
    
    # Attendance
    path('attendance/', views.attendance_viewer, name='attendance-viewer'),
    path('attendance/<int:student_id>/', views.mark_attendance, name='mark-attendance'),
    path('attendance-report/<int:student_id>/', views.attendance_report, name='attendance-report'),
    
    # Statistics
    path('statistics/', views.statistics, name='statistics'),
]