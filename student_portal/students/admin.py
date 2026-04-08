from django.contrib import admin
from .models import Student, Subject, Grade, AttendanceRecord, StudentStatistics

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'name', 'program', 'semester', 'current_cgpa', 'enrollment_date')
    list_filter = ('program', 'semester')
    search_fields = ('name', 'roll_number')
    readonly_fields = ('enrollment_date', 'current_cgpa', 'total_credits_earned', 'total_credits_attempted')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'roll_number', 'age', 'program', 'semester')
        }),
        ('Course Details', {
            'fields': ('course', 'enrollment_date')
        }),
        ('Academic Performance', {
            'fields': ('current_cgpa', 'total_credits_earned', 'total_credits_attempted', 'marks')
        }),
    )
    actions = ['recalculate_cgpa']
    
    def recalculate_cgpa(self, request, queryset):
        for student in queryset:
            student.calculate_cgpa()
        self.message_user(request, "CGPA recalculated for selected students.")
    recalculate_cgpa.short_description = "Recalculate CGPA for selected students"


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'semester', 'credits', 'subject_type')
    list_filter = ('semester', 'subject_type', 'credits')
    search_fields = ('code', 'name')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'semester', 'marks', 'grade', 'grade_point')
    list_filter = ('semester', 'grade')
    search_fields = ('student__name', 'subject__code')
    ordering = ('-semester', 'student')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'date', 'is_present', 'remarks')
    list_filter = ('date', 'is_present', 'subject')
    search_fields = ('student__name', 'subject__code')
    ordering = ('-date',)


@admin.register(StudentStatistics)
class StudentStatisticsAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'sgpa', 'attendance_percentage', 'average_marks')
    list_filter = ('semester',)
    search_fields = ('student__name', 'student__roll_number')
    readonly_fields = ('sgpa', 'attendance_percentage', 'average_marks', 'last_updated')
