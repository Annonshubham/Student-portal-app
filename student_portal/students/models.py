from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date

# Create your models here.
class Student(models.Model):
    SEMESTER_CHOICES = [
        (1, 'Semester 1'), (2, 'Semester 2'), (3, 'Semester 3'),
        (4, 'Semester 4'), (5, 'Semester 5'), (6, 'Semester 6'),
        (7, 'Semester 7'), (8, 'Semester 8'),
    ]
    
    PROGRAM_CHOICES = [
        ('B.Tech', 'Bachelor of Technology'),
        ('BCA', 'Bachelor of Computer Applications'),
        ('BA', 'Bachelor of Arts'),
        ('B.Sc', 'Bachelor of Science'),
        ('MBA', 'Master of Business Administration'),
    ]
    
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True, default='N/A')
    age = models.IntegerField(default=18, validators=[MinValueValidator(18), MaxValueValidator(60)])
    program = models.CharField(max_length=10, choices=PROGRAM_CHOICES, default='B.Tech')
    semester = models.IntegerField(choices=SEMESTER_CHOICES, default=1)
    enrollment_date = models.DateField(default='2024-01-01')
    
    # Legacy field for compatibility
    course = models.CharField(max_length=100, blank=True, null=True)
    marks = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # CGPA and overall stats
    current_cgpa = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    total_credits_earned = models.IntegerField(default=0)
    total_credits_attempted = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['roll_number']
        verbose_name_plural = "Students"
    
    def __str__(self):
        return f"{self.name} ({self.roll_number})"
    
    def calculate_cgpa(self):
        """Calculate CGPA based on all grades and their credits"""
        grades = Grade.objects.filter(student=self)
        if not grades.exists():
            self.current_cgpa = 0.0
            return 0.0
        
        total_grade_points = 0
        total_credits = 0
        
        for grade in grades:
            if grade.subject.credits > 0:
                total_grade_points += grade.grade_point * grade.subject.credits
                total_credits += grade.subject.credits
        
        if total_credits > 0:
            cgpa = total_grade_points / total_credits
            self.current_cgpa = round(cgpa, 2)
            self.total_credits_earned = total_credits
            self.total_credits_attempted = total_credits
            self.save()
            return self.current_cgpa
        
        return 0.0
    
    def get_attendance_percentage(self):
        """Calculate attendance percentage"""
        records = AttendanceRecord.objects.filter(student=self)
        if not records.exists():
            return 0
        
        present_count = records.filter(is_present=True).count()
        total_count = records.count()
        
        return round((present_count / total_count) * 100, 2) if total_count > 0 else 0
    
    def get_average_marks(self):
        """Get average marks from all grades"""
        grades = Grade.objects.filter(student=self)
        if not grades.exists():
            return 0
        
        avg_marks = grades.aggregate(models.Avg('marks'))['marks__avg']
        return round(avg_marks, 2) if avg_marks else 0


class Subject(models.Model):
    SUBJECT_TYPE_CHOICES = [
        ('Core', 'Core Subject'),
        ('Elective', 'Elective Subject'),
        ('Lab', 'Laboratory Subject'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    credits = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(6)])
    semester = models.IntegerField(choices=Student.SEMESTER_CHOICES)
    subject_type = models.CharField(max_length=20, choices=SUBJECT_TYPE_CHOICES, default='Core')
    
    class Meta:
        ordering = ['semester', 'code']
        verbose_name_plural = "Subjects"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Grade(models.Model):
    GRADE_CHOICES = [
        ('A+', 10), ('A', 9), ('B+', 8.5), ('B', 8),
        ('C+', 7.5), ('C', 7), ('D+', 6.5), ('D', 6),
        ('E', 5), ('F', 0),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades')
    semester = models.IntegerField(choices=Student.SEMESTER_CHOICES)
    marks = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade = models.CharField(max_length=3, choices=GRADE_CHOICES)
    grade_point = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    date_submitted = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'subject', 'semester')
        ordering = ['-semester', 'subject__code']
        verbose_name_plural = "Grades"
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.grade}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate grade based on marks"""
        if self.marks >= 90:
            self.grade = 'A+'
            self.grade_point = 10
        elif self.marks >= 85:
            self.grade = 'A'
            self.grade_point = 9
        elif self.marks >= 80:
            self.grade = 'B+'
            self.grade_point = 8.5
        elif self.marks >= 75:
            self.grade = 'B'
            self.grade_point = 8
        elif self.marks >= 70:
            self.grade = 'C+'
            self.grade_point = 7.5
        elif self.marks >= 65:
            self.grade = 'C'
            self.grade_point = 7
        elif self.marks >= 60:
            self.grade = 'D+'
            self.grade_point = 6.5
        elif self.marks >= 55:
            self.grade = 'D'
            self.grade_point = 6
        elif self.marks >= 50:
            self.grade = 'E'
            self.grade_point = 5
        else:
            self.grade = 'F'
            self.grade_point = 0
        
        super().save(*args, **kwargs)


class AttendanceRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    remarks = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Attendance Records"
        unique_together = ('student', 'subject', 'date')
    
    def __str__(self):
        return f"{self.student} - {self.subject} - {self.date} - {'Present' if self.is_present else 'Absent'}"


class StudentStatistics(models.Model):
    """Store student statistics for quick access and reporting"""
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='statistics')
    semester = models.IntegerField(choices=Student.SEMESTER_CHOICES)
    sgpa = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    attendance_percentage = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    average_marks = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    courses_passed = models.IntegerField(default=0)
    courses_failed = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Student Statistics"
    
    def __str__(self):
        return f"{self.student} - Semester {self.semester}"

