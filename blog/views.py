
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .models import Post
from .forms import PostForm, RegisterForm, ProfileUpdateForm, AuthorProfileForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from .models import AuthorProfile, Post
from .forms import CommentForm
from .models import Comment, Post
from django.contrib import messages
from django.contrib.auth import login
from .forms import RegisterForm, ProfileUpdateForm


from django.core.paginator import Paginator
from django.db.models import Q
from .models import Post, Category
from django.db import models
from django.contrib.auth import get_user_model



def post_list(request):
    # Show only published posts to public visitors.
    posts = (
        Post.objects
        .filter(status=Post.Status.PUBLISHED)
        .select_related("author", "category")
        .prefetch_related("tags")
    )

    # Read search and category filters from the URL.
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()

    # Search titles and content.
    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
        )

    # Filter by category ID.
    if selected_category.isdigit():
        posts = posts.filter(category_id=int(selected_category))

    # Paginate the filtered results.
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    categories = Category.objects.order_by("name")

    return render(
        request,
        "blog/post_list.html",
        {
            "page_obj": page_obj,
            "categories": categories,
            "query": query,
            "selected_category": selected_category,
        },
    )

def post_detail(request, slug):
    post = get_object_or_404(
        Post,
        slug=slug,
        status=Post.Status.PUBLISHED,
    )

    comments = post.comments.filter(is_approved=True)

    if request.user.is_authenticated:
        # Let users see their own pending comments too.
        comments = post.comments.filter(
            models.Q(is_approved=True)
            | models.Q(author=request.user)
        )

    return render(
        request,
        "blog/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "comment_form": CommentForm(),
        },
    )


@login_required
def post_create(request):
    # PostForm will be defined in blog/forms.py
    from .forms import PostForm

    if request.method == "POST":
        form = PostForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            form.save_m2m()

            return redirect(post.get_absolute_url())
    else:
        form = PostForm()

    return render(
        request,
        "blog/post_form.html",
        {"form": form, "title": "Create Post"},
    )


@login_required
def post_update(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if post.author != request.user:
        return HttpResponseForbidden("You cannot edit this post.")

    from .forms import PostForm

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)

        if form.is_valid():
            form.save()
            return redirect(post.get_absolute_url())
    else:
        form = PostForm(instance=post)

    return render(
        request,
        "blog/post_form.html",
        {"form": form, "title": "Edit Post"},
    )


@login_required
def post_delete(request, slug):
    post = get_object_or_404(Post, slug=slug)

    if post.author != request.user:
        return HttpResponseForbidden("You cannot delete this post.")

    if request.method == "POST":
        post.delete()
        return redirect("blog:post_list")

    return render(
        request,
        "blog/post_confirm_delete.html",
        {"post": post},
    )

@login_required
def post_preview(request, slug):
    post = get_object_or_404(
        Post,
        slug=slug,
        author=request.user,
        status=Post.Status.DRAFT,
    )

    return render(
        request,
        "blog/post_detail.html",
        {"post": post},
    )

def register(request):
    if request.user.is_authenticated:
        return redirect("blog:post_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your account was created successfully!")
            return redirect("profile")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def profile(request):
    posts = Post.objects.filter(
        author=request.user
    ).select_related("category").prefetch_related("tags")

    return render(
        request,
        "blog/profile.html",
        {"profile_user": request.user, "posts": posts},
    )



@login_required
def profile_edit(request):
    author_profile, _ = AuthorProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = ProfileUpdateForm(
            request.POST,
            instance=request.user,
        )

        author_form = AuthorProfileForm(
            request.POST,
            instance=author_profile,
        )

        if form.is_valid() and author_form.is_valid():
            form.save()
            author_form.save()

            messages.success(
                request,
                "Your profile was updated.",
            )
            return redirect("profile")

    else:
        form = ProfileUpdateForm(
            instance=request.user,
        )

        author_form = AuthorProfileForm(
            instance=author_profile,
        )

    return render(
        request,
        "blog/profile_edit.html",
        {
            "form": form,
            "author_form": author_form,
        },
    )
@login_required
@require_POST
def add_comment(request, slug):
    post = get_object_or_404(
        Post,
        slug=slug,
        status=Post.Status.PUBLISHED,
    )

    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.is_approved = False
        comment.save()

    return redirect(post.get_absolute_url())
@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(
        Comment.objects.select_related("post"),
        id=comment_id,
    )

    if comment.author_id != request.user.id and not request.user.is_staff:
        return redirect("blog:post_detail", slug=comment.post.slug)

    post_url = comment.post.get_absolute_url()
    comment.delete()

    return redirect(post_url)
User = get_user_model()


def author_detail(request, user_id):
    author = get_object_or_404(User, pk=user_id)
    author_profile = AuthorProfile.objects.filter(
    user=author
).first()

    
    posts = (
        Post.objects
        .filter(
            author=author,
            status=Post.Status.PUBLISHED,
        )
        .select_related("category")
        .prefetch_related("tags")
        .order_by("-created_at")
    )

    return render(
        request,
        "blog/author_detail.html",
        {
            "author": author,
            "author_profile": author_profile,
            "posts": posts,
        },
    )