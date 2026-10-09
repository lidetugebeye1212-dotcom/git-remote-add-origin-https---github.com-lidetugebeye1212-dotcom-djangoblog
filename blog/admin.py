from django.contrib import admin
from .models import Category, Tag, Post
from django.contrib import admin
from .models import Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "author",
        "category",
        "status",
        "created_at",
    ]

    list_filter = [
        "status",
        "category",
        "created_at",
    ]

    search_fields = [
        "title",
        "content",
    ]

    prepopulated_fields = {
        "slug": ("title",)
    }

    filter_horizontal = ["tags"]



@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "post",
        "author",
        "created_at",
        "is_approved",
    )
    list_filter = ("is_approved", "created_at")
    search_fields = ("body", "author__username", "post__title")
    actions = ["approve_comments"]

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)