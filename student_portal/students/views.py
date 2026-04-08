from .models import Student, Subject, Grade, AttendanceRecord, StudentStatistics
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Avg, Count, Q, Sum
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json

# ============= HOME & DASHBOARD =============

def home(request):
    """Enhanced home page with dashboard"""
    total_students = Student.objects.count()
    total_subjects = Subject.objects.count()
    
    # Get basic statistics
    avg_cgpa = Student.objects.aggregate(Avg('current_cgpa'))['current_cgpa__avg'] or 0
    
    data = {
        'title': 'Student Management Portal',
        'instructor': 'Admin',
        'total_students': total_students,
        'total_subjects': total_subjects,
        'average_cgpa': round(avg_cgpa, 2),
    }
    return render(request, 'home.html', data)


def dashboard(request):
    """Main dashboard with statistics and analytics"""
    students = Student.objects.all()
    total_students = students.count()
    
    # Academic statistics
    avg_cgpa = students.aggregate(Avg('current_cgpa'))['current_cgpa__avg'] or 0
    avg_attendance = students.aggregate(Avg('marks'))['marks__avg'] or 0
    
    # Top performers
    top_students = students.order_by('-current_cgpa')[:5]
    
    # Grade distribution
    grade_distribution = {
        'A+': Grade.objects.filter(grade='A+').count(),
        'A': Grade.objects.filter(grade='A').count(),
        'B+': Grade.objects.filter(grade='B+').count(),
        'B': Grade.objects.filter(grade='B').count(),
        'C+': Grade.objects.filter(grade='C+').count(),
        'C': Grade.objects.filter(grade='C').count(),
        'D+': Grade.objects.filter(grade='D+').count(),
        'D': Grade.objects.filter(grade='D').count(),
        'E': Grade.objects.filter(grade='E').count(),
        'F': Grade.objects.filter(grade='F').count(),
    }
    
    # Recent grades
    recent_grades = Grade.objects.select_related('student', 'subject').order_by('-date_submitted')[:10]
    
    # Recent attendance
    recent_attendance = AttendanceRecord.objects.select_related('student', 'subject').order_by('-date')[:10]
    
    context = {
        'total_students': total_students,
        'average_cgpa': round(avg_cgpa, 2),
        'average_marks': round(avg_attendance, 2),
        'top_students': top_students,
        'grade_distribution': grade_distribution,
        'recent_grades': recent_grades,
        'recent_attendance': recent_attendance,
    }
    
    return render(request, 'dashboard.html', context)


# ============= STUDENT MANAGEMENT =============

def students_page(request):
    """Show list of students with search and filtering"""
    q = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'roll_number')
    semester = request.GET.get('semester', '')
    program = request.GET.get('program', '')
    
    # Base query
    students = Student.objects.all()
    
    # Apply filters
    if q:
        students = students.filter(
            Q(name__icontains=q) | Q(roll_number__icontains=q)
        )
        not_found = not students.exists()
    else:
        not_found = False
    
    if semester:
        students = students.filter(semester=semester)
    
    if program:
        students = students.filter(program=program)
    
    # Sorting
    valid_sorts = ['roll_number', 'name', '-current_cgpa', 'marks', 'semester']
    if sort_by in valid_sorts:
        students = students.order_by(sort_by)
    else:
        students = students.order_by('roll_number')
    
    # Pagination
    paginator = Paginator(students, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get unique semesters and programs
    semesters = Student.SEMESTER_CHOICES
    programs = Student.PROGRAM_CHOICES
    
    return render(request, 'students.html', {
        'page_obj': page_obj,
        'students': page_obj.object_list,
        'query': q,
        'not_found': not_found,
        'sort_by': sort_by,
        'semester': semester,
        'program': program,
        'semesters': semesters,
        'programs': programs,
    })


def student_detail(request, student_id):
    """View detailed student profile"""
    student = get_object_or_404(Student, id=student_id)
    
    # Get student's grades
    grades = Grade.objects.filter(student=student).select_related('subject').order_by('-semester')
    
    # Get attendance
    attendance_records = AttendanceRecord.objects.filter(student=student).select_related('subject').order_by('-date')
    attendance_percentage = student.get_attendance_percentage()
    
    # Attendance by subject
    attendance_by_subject = {}
    for subject in Subject.objects.all():
        records = attendance_records.filter(subject=subject)
        if records.exists():
            present = records.filter(is_present=True).count()
            total = records.count()
            percentage = (present / total) * 100 if total > 0 else 0
            attendance_by_subject[subject.code] = {
                'present': present,
                'total': total,
                'percentage': round(percentage, 2)
            }
    
    context = {
        'student': student,
        'grades': grades,
        'attendance_records': attendance_records[:20],  # Last 20 records
        'attendance_percentage': attendance_percentage,
        'attendance_by_subject': attendance_by_subject,
        'average_marks': student.get_average_marks(),
    }
    
    return render(request, 'student_detail.html', context)


def add_student(request):
    """Add new student"""
    if request.method == "POST":
        name = request.POST.get('name')
        roll_number = request.POST.get('roll_number')
        age = request.POST.get('age')
        program = request.POST.get('program', 'B.Tech')
        semester = request.POST.get('semester', 1)
        course = request.POST.get('course', '')
        marks = request.POST.get('marks', 0)
        
        # Check if roll number already exists
        if Student.objects.filter(roll_number=roll_number).exists():
            return render(request, 'add_student.html', {
                'error': 'Roll number already exists!'
            })
        
        Student.objects.create(
            name=name,
            roll_number=roll_number,
            age=int(age),
            program=program,
            semester=int(semester),
            course=course,
            marks=int(marks)
        )
        
        return redirect('students')
    
    return render(request, 'add_student.html', {
        'programs': Student.PROGRAM_CHOICES,
        'semesters': Student.SEMESTER_CHOICES,
    })


def edit_student(request, student_id):
    """Edit student information"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        student.name = request.POST.get('name')
        student.roll_number = request.POST.get('roll_number')
        student.age = int(request.POST.get('age'))
        student.program = request.POST.get('program')
        student.semester = int(request.POST.get('semester'))
        student.course = request.POST.get('course')
        student.marks = int(request.POST.get('marks', 0))
        student.save()
        
        return redirect('student-detail', student_id=student.id)
    
    return render(request, 'add_student.html', {
        'student': student,
        'programs': Student.PROGRAM_CHOICES,
        'semesters': Student.SEMESTER_CHOICES,
    })


def delete_student(request, student_id):
    """Delete a student"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        student.delete()
        return redirect('students')
    
    return redirect('students')


# ============= CGPA & GRADES =============

def cgpa_calculator(request):
    """CGPA Calculator and Grade Viewer"""
    students = Student.objects.all()
    selected_student = None
    student_grades = []
    cgpa = 0
    
    if request.method == 'GET' and request.GET.get('student_id'):
        student_id = request.GET.get('student_id')
        selected_student = get_object_or_404(Student, id=student_id)
        
        # Get all grades for the student
        student_grades = Grade.objects.filter(student=selected_student).select_related('subject').order_by('-semester', 'subject__code')
        
        # Calculate CGPA
        cgpa = selected_student.calculate_cgpa()
    
    # Summary statistics
    total_grades = Grade.objects.count()
    avg_cgpa_all = Student.objects.aggregate(Avg('current_cgpa'))['current_cgpa__avg'] or 0
    
    context = {
        'students': students,
        'selected_student': selected_student,
        'student_grades': student_grades,
        'cgpa': cgpa,
        'total_grades': total_grades,
        'average_cgpa': round(avg_cgpa_all, 2),
    }
    
    return render(request, 'cgpa_calculator.html', context)


def grade_view(request, student_id=None):
    """Grade report and management"""
    if student_id:
        student = get_object_or_404(Student, id=student_id)
        grades = Grade.objects.filter(student=student).select_related('subject').order_by('-semester')
    else:
        student = None
        grades = Grade.objects.select_related('student', 'subject').order_by('-semester', 'student__roll_number')
    
    # Group by semester
    grades_by_semester = {}
    for grade in grades:
        sem = grade.semester
        if sem not in grades_by_semester:
            grades_by_semester[sem] = []
        grades_by_semester[sem].append(grade)
    
    # Grade statistics
    grade_stats = Grade.objects.values('grade').annotate(count=Count('id')).order_by('grade')
    
    context = {
        'student': student,
        'grades': grades,
        'grades_by_semester': grades_by_semester,
        'grade_stats': grade_stats,
    }
    
    return render(request, 'grade_view.html', context)


def add_grade(request, student_id):
    """Add grade for a student"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        semester = request.POST.get('semester')
        marks = int(request.POST.get('marks'))
        
        subject = get_object_or_404(Subject, id=subject_id)
        
        # Check if grade already exists
        grade, created = Grade.objects.update_or_create(
            student=student,
            subject=subject,
            semester=int(semester),
            defaults={'marks': marks}
        )
        
        # Recalculate CGPA
        student.calculate_cgpa()
        
        return redirect('student-detail', student_id=student.id)
    
    # Get available subjects for the student's semester
    subjects = Subject.objects.filter(semester=student.semester)
    existing_grades = Grade.objects.filter(student=student).values_list('subject_id', flat=True)
    available_subjects = subjects.exclude(id__in=existing_grades)
    
    return render(request, 'add_grade.html', {
        'student': student,
        'available_subjects': available_subjects,
        'semesters': Student.SEMESTER_CHOICES,
    })


# ============= ATTENDANCE =============

def attendance_viewer(request):
    """View and manage attendance records"""
    students = Student.objects.all()
    selected_student = None
    attendance_records = []
    attendance_percentage = 0
    
    if request.method == 'GET' and request.GET.get('student_id'):
        student_id = request.GET.get('student_id')
        selected_student = get_object_or_404(Student, id=student_id)
        
        # Get attendance records
        attendance_records = AttendanceRecord.objects.filter(
            student=selected_student
        ).select_related('subject').order_by('-date')
        
        # Calculate attendance percentage
        attendance_percentage = selected_student.get_attendance_percentage()
    
    # Attendance statistics
    total_records = AttendanceRecord.objects.count()
    present_count = AttendanceRecord.objects.filter(is_present=True).count()
    
    context = {
        'students': students,
        'selected_student': selected_student,
        'attendance_records': attendance_records,
        'attendance_percentage': attendance_percentage,
        'total_records': total_records,
        'present_count': present_count,
    }
    
    return render(request, 'attendance_viewer.html', context)


def mark_attendance(request, student_id):
    """Mark attendance for a student"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        date_str = request.POST.get('date')
        is_present = request.POST.get('is_present') == 'on'
        remarks = request.POST.get('remarks', '')
        
        subject = get_object_or_404(Subject, id=subject_id)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        record, created = AttendanceRecord.objects.update_or_create(
            student=student,
            subject=subject,
            date=date_obj,
            defaults={'is_present': is_present, 'remarks': remarks}
        )
        
        return redirect('student-detail', student_id=student.id)
    
    subjects = Subject.objects.all()
    
    return render(request, 'mark_attendance.html', {
        'student': student,
        'subjects': subjects,
    })


def attendance_report(request, student_id=None):
    """Detailed attendance report"""
    if student_id:
        student = get_object_or_404(Student, id=student_id)
        records = AttendanceRecord.objects.filter(student=student).select_related('subject')
    else:
        student = None
        records = AttendanceRecord.objects.select_related('student', 'subject')
    
    # Group by subject
    attendance_by_subject = {}
    for record in records:
        subject_code = record.subject.code
        if subject_code not in attendance_by_subject:
            attendance_by_subject[subject_code] = {
                'subject': record.subject,
                'present': 0,
                'absent': 0,
                'records': []
            }
        
        attendance_by_subject[subject_code]['records'].append(record)
        if record.is_present:
            attendance_by_subject[subject_code]['present'] += 1
        else:
            attendance_by_subject[subject_code]['absent'] += 1
    
    # Calculate percentages
    for subject_code, data in attendance_by_subject.items():
        total = data['present'] + data['absent']
        data['percentage'] = (data['present'] / total * 100) if total > 0 else 0
    
    context = {
        'student': student,
        'attendance_by_subject': attendance_by_subject,
    }
    
    return render(request, 'attendance_report.html', context)


# ============= STATISTICS & ANALYTICS =============

def statistics(request):
    """Overall statistics and analytics"""
    # Student statistics
    total_students = Student.objects.count()
    average_cgpa = Student.objects.aggregate(Avg('current_cgpa'))['current_cgpa__avg'] or 0
    
    # Grade distribution
    grades = Grade.objects.values('grade').annotate(count=Count('id')).order_by('-count')
    
    # Top performers
    top_students = Student.objects.order_by('-current_cgpa')[:10]
    
    # Semester-wise distribution
    semester_dist = Student.objects.values('semester').annotate(count=Count('id')).order_by('semester')
    
    # Program-wise distribution
    program_dist = Student.objects.values('program').annotate(count=Count('id')).order_by('program')
    
    # Attendance statistics
    total_attendance_records = AttendanceRecord.objects.count()
    present_records = AttendanceRecord.objects.filter(is_present=True).count()
    absent_records = AttendanceRecord.objects.filter(is_present=False).count()
    avg_attendance = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    context = {
        'total_students': total_students,
        'average_cgpa': round(average_cgpa, 2),
        'grades': list(grades),
        'top_students': top_students,
        'semester_dist': list(semester_dist),
        'program_dist': list(program_dist),
        'total_attendance_records': total_attendance_records,
        'present_records': present_records,
        'absent_records': absent_records,
        'average_attendance': round(avg_attendance, 2),
    }
    
    return render(request, 'statistics.html', context)

