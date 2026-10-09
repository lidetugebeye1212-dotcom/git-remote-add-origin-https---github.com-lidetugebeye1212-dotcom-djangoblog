
from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("post/create/", views.post_create, name="post_create"),

    path(
        "post/<slug:slug>/preview/",
        views.post_preview,
        name="post_preview",
    ),

path("post/<slug:slug>/edit/", views.post_update, name="post_edit"),   
 path("post/<slug:slug>/delete/", views.post_delete, name="post_delete"),
    path("post/<slug:slug>/", views.post_detail, name="post_detail"),
    path(
    "posts/<slug:slug>/comments/add/",
    views.add_comment,
    name="add_comment",
),
path(
    "comments/<int:comment_id>/delete/",
    views.delete_comment,
    name="delete_comment",
),
path(
    "authors/<int:user_id>/",
    views.author_detail,
    name="author_detail",
),
]