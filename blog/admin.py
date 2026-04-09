from django.contrib import admin
from .models import StudentProfile, Post, Comment, Department

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'year', 'enrollment_no', 'is_faculty', 'is_university_admin')
    list_filter = ('department', 'year', 'is_faculty', 'is_university_admin')
    search_fields = ('user__username', 'enrollment_no')
    list_editable = ('is_faculty', 'is_university_admin')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'department', 'post_type', 'status', 'approved_by', 'created_at', 'is_announcement')
    list_filter = ('status', 'department', 'post_type', 'is_announcement')
    search_fields = ('title', 'content', 'author__username')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'slug')
    raw_id_fields = ('author', 'approved_by')
    date_hierarchy = 'created_at'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at', 'active')
    list_filter = ('active',)
    search_fields = ('author__username', 'content')
    list_editable = ('active',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}