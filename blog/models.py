from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse

# Department choices
DEPARTMENT_CHOICES = [
    ('CSE', 'Computer Science & Engineering'),
    ('ECE', 'Electronics & Communication'),
    ('ME', 'Mechanical Engineering'),
    ('CE', 'Civil Engineering'),
    ('EE', 'Electrical Engineering'),
    ('IT', 'Information Technology'),
    ('MCA', 'Master of Computer Applications'),
    ('MBA', 'Master of Business Administration'),
    ('OTHER', 'Other'),
]

YEAR_CHOICES = [
    ('1', '1st Year'),
    ('2', '2nd Year'),
    ('3', '3rd Year'),
    ('4', '4th Year'),
    ('PG', 'Post Graduate'),
]

POST_TYPE_CHOICES = [
    ('ACADEMIC', 'Academic Notes / Study Material'),
    ('EVENT', 'Campus Event'),
    ('PLACEMENT', 'Placement / Internship'),
    ('DOUBT', 'Question / Doubt'),
    ('GENERAL', 'General Discussion'),
]

STATUS_CHOICES = [
    ('PENDING', 'Pending Approval'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
]

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    enrollment_no = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='CSE')
    year = models.CharField(max_length=5, choices=YEAR_CHOICES, default='1')
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    is_faculty = models.BooleanField(default=False)
    is_university_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.department}"
    
    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"

class Department(models.Model):
    name = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_name_display())
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.get_name_display()

class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='CSE')
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='GENERAL')
    is_announcement = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For upvoting (simple)
    upvotes = models.ManyToManyField(User, related_name='upvoted_posts', blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def total_upvotes(self):
        return self.upvotes.count()
    
    def get_absolute_url(self):
        return reverse('post_detail', args=[self.slug])
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-is_announcement', '-created_at']

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f'Comment by {self.author} on {self.post}'