from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Core
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # User Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('my-posts/', views.my_posts, name='my_posts'),

    # Posts (CRUD)
    path('post/new/', views.post_create, name='post_create'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/edit/', views.post_update, name='post_update'),
    path('post/<slug:slug>/delete/', views.post_delete, name='post_delete'),
    path('post/<slug:slug>/upvote/', views.upvote_post, name='upvote_post'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),

    # Departments
    path('departments/', views.departments_list, name='departments'),
    path('department/<str:dept_code>/', views.department_posts, name='department_posts'),

    # Moderation (Faculty + Admin)
    path('moderation/', views.moderation_dashboard, name='moderation_dashboard'),
    path('moderation/<slug:slug>/approve/', views.approve_post, name='approve_post'),
    path('moderation/<slug:slug>/reject/', views.reject_post, name='reject_post'),

    # Admin Panel
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/toggle-faculty/<int:user_id>/', views.toggle_faculty, name='toggle_faculty'),
    path('admin-panel/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
]