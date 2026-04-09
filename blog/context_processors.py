from .models import DEPARTMENT_CHOICES, POST_TYPE_CHOICES

def categories_processor(request):
    """Provide departments and post types to all templates"""
    return {
        'departments': DEPARTMENT_CHOICES,
        'post_types': POST_TYPE_CHOICES,
    }