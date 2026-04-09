from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Post, Comment, StudentProfile
from .forms import RegistrationForm, PostForm, CommentForm, StudentProfileForm

from .models import DEPARTMENT_CHOICES, POST_TYPE_CHOICES


def _get_role(user):
    """Returns (is_admin, is_faculty, profile) for a user."""
    if not user.is_authenticated:
        return False, False, None
    profile = getattr(user, 'student_profile', None)
    is_admin = user.is_superuser or (profile and profile.is_university_admin)
    is_faculty = profile and profile.is_faculty
    return is_admin, is_faculty, profile


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Assign role based on selection
            role = form.cleaned_data.get('role')
            profile = user.student_profile
            if role == 'FACULTY':
                profile.is_faculty = True
                profile.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Registration successful.')
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})


def home(request):
    query = request.GET.get('q')
    dept_filter = request.GET.get('dept')
    type_filter = request.GET.get('type')

    posts = Post.objects.filter(status='APPROVED')

    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    if dept_filter:
        posts = posts.filter(department=dept_filter)
    if type_filter:
        posts = posts.filter(post_type=type_filter)

    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'departments': DEPARTMENT_CHOICES,
        'post_types': POST_TYPE_CHOICES,
        'current_dept': dept_filter,
        'current_type': type_filter,
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug)
    is_admin, is_faculty, profile = _get_role(request.user)
    is_moderator = is_admin or is_faculty

    # Access control for non-approved posts
    if post.status != 'APPROVED':
        if not request.user.is_authenticated:
            messages.error(request, 'This post is pending approval.')
            return redirect('home')
        if not (request.user == post.author or is_moderator):
            messages.error(request, 'This post is pending approval and is not visible yet.')
            return redirect('home')

    comments = post.comments.filter(parent=None, active=True)

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass
            comment.save()
            messages.success(request, 'Comment added!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = CommentForm()

    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'is_moderator': is_moderator,
        'is_admin': is_admin,
    })


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = 'PENDING'
            post.save()
            messages.success(request, 'Post submitted! It will appear after faculty review.')
            return redirect('my_posts')
    else:
        form = PostForm()
    return render(request, 'post_form.html', {'form': form, 'title': 'Create Post'})


@login_required
def post_update(request, slug):
    post = get_object_or_404(Post, slug=slug)
    is_admin, is_faculty, profile = _get_role(request.user)

    if post.author != request.user and not is_admin:
        messages.error(request, 'You are not authorized to edit this post.')
        return redirect('home')

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            updated = form.save(commit=False)
            # Re-submit for approval if it was approved and author edits it
            if post.author == request.user and not is_admin:
                updated.status = 'PENDING'
                updated.approved_by = None
                messages.info(request, 'Post re-submitted for approval after edit.')
            updated.save()
            messages.success(request, 'Post updated!')
            return redirect('post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
    return render(request, 'post_form.html', {'form': form, 'title': 'Edit Post'})


@login_required
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)
    is_admin, is_faculty, profile = _get_role(request.user)

    if post.author != request.user and not is_admin:
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('home')

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully.')
        return redirect('home')
    return render(request, 'post_confirm_delete.html', {'post': post})


@login_required
def delete_comment(request, comment_id):
    is_admin, is_faculty, profile = _get_role(request.user)
    if not is_admin:
        messages.error(request, 'Access denied. Admins only can delete comments.')
        return redirect('home')
    
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        post_slug = comment.post.slug
        comment.delete()
        messages.success(request, 'Comment deleted successfully.')
        return redirect('post_detail', slug=post_slug)
    return redirect('home')


@login_required
def my_posts(request):
    """Author's own post list with status badges."""
    user_posts = request.user.posts.all().order_by('-created_at')
    return render(request, 'my_posts.html', {'user_posts': user_posts})


@login_required
def profile(request):
    is_admin, is_faculty, profile = _get_role(request.user)
    user_posts = request.user.posts.all().order_by('-created_at')
    return render(request, 'profile.html', {
        'user_posts': user_posts,
        'is_admin': is_admin,
        'is_faculty': is_faculty,
        'student_profile': profile,
    })


@login_required
def edit_profile(request):
    profile = request.user.student_profile
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})


@login_required
def upvote_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if post.status != 'APPROVED':
        messages.error(request, 'Cannot upvote a pending post.')
        return redirect('home')
    if request.user in post.upvotes.all():
        post.upvotes.remove(request.user)
        messages.info(request, 'Upvote removed.')
    else:
        post.upvotes.add(request.user)
        messages.success(request, 'Upvoted!')
    return redirect('post_detail', slug=post.slug)


def department_posts(request, dept_code):
    posts = Post.objects.filter(department=dept_code, status='APPROVED')
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    dept_name = dict(DEPARTMENT_CHOICES).get(dept_code, dept_code)
    return render(request, 'department_posts.html', {
        'page_obj': page_obj,
        'department': {'code': dept_code, 'name': dept_name}
    })


def departments_list(request):
    departments = [{'code': code, 'name': name} for code, name in DEPARTMENT_CHOICES]
    return render(request, 'departments.html', {'departments': departments})


# --- MODERATION VIEWS ---────────────

@login_required
def moderation_dashboard(request):
    is_admin, is_faculty, profile = _get_role(request.user)
    if not (is_admin or is_faculty):
        messages.error(request, 'Access denied. Moderators only.')
        return redirect('home')

    pending_posts = Post.objects.filter(status='PENDING').order_by('-created_at')
    rejected_posts = Post.objects.filter(status='REJECTED').order_by('-created_at')[:10]
    return render(request, 'moderation.html', {
        'pending_posts': pending_posts,
        'rejected_posts': rejected_posts,
        'is_admin': is_admin,
    })


@login_required
def approve_post(request, slug):
    is_admin, is_faculty, profile = _get_role(request.user)
    if not (is_admin or is_faculty):
        messages.error(request, 'Access denied.')
        return redirect('home')

    post = get_object_or_404(Post, slug=slug)
    post.status = 'APPROVED'
    post.approved_by = request.user
    post.save()
    messages.success(request, f'✅ Post "{post.title}" has been approved and is now live!')
    return redirect('moderation_dashboard')


@login_required
def reject_post(request, slug):
    is_admin, is_faculty, profile = _get_role(request.user)
    if not (is_admin or is_faculty):
        messages.error(request, 'Access denied.')
        return redirect('home')

    post = get_object_or_404(Post, slug=slug)
    post.status = 'REJECTED'
    post.approved_by = request.user
    post.save()
    messages.warning(request, f'❌ Post "{post.title}" has been rejected.')
    return redirect('moderation_dashboard')


# --- ADMIN USER MANAGEMENT ---────────

@login_required
def admin_panel(request):
    is_admin, is_faculty, profile = _get_role(request.user)
    if not is_admin:
        messages.error(request, 'Access denied. Admins only.')
        return redirect('home')

    from django.contrib.auth.models import User
    all_users = User.objects.select_related('student_profile').order_by('username')
    return render(request, 'admin_panel.html', {
        'all_users': all_users,
        'is_admin': is_admin,
    })


@login_required
def toggle_faculty(request, user_id):
    is_admin, is_faculty, profile = _get_role(request.user)
    if not is_admin:
        messages.error(request, 'Access denied.')
        return redirect('home')

    from django.contrib.auth.models import User
    target_user = get_object_or_404(User, id=user_id)
    target_profile = getattr(target_user, 'student_profile', None)
    if target_profile:
        target_profile.is_faculty = not target_profile.is_faculty
        target_profile.save()
        status = 'granted faculty privileges to' if target_profile.is_faculty else 'removed faculty privileges from'
        messages.success(request, f'Successfully {status} {target_user.username}.')
    return redirect('admin_panel')


@login_required
def delete_user(request, user_id):
    is_admin, is_faculty, profile = _get_role(request.user)
    if not is_admin:
        messages.error(request, 'Access denied. Admins only.')
        return redirect('home')

    from django.contrib.auth.models import User
    target_user = get_object_or_404(User, id=user_id)

    if target_user.is_superuser and not request.user.is_superuser:
        messages.error(request, 'You cannot delete a superuser.')
        return redirect('admin_panel')
        
    if target_user == request.user:
        messages.error(request, 'You cannot delete yourself.')
        return redirect('admin_panel')

    target_user.delete()
    messages.success(request, f'Successfully deleted user {target_user.username}.')
    return redirect('admin_panel')