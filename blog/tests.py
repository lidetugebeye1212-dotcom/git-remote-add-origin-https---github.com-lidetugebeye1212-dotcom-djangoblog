
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Category, Post

User = get_user_model()


class BlogTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username="author",
            password="Test-pass-12345!",
        )

        cls.other_user = User.objects.create_user(
            username="other",
            password="Test-pass-12345!",
        )

        # Create the category FIRST.
        cls.category = Category.objects.create(name="Testing")

        cls.published_post = Post.objects.create(
            title="Published article",
            slug="published-article",
            content="This article is public.",
            author=cls.author,
            category=cls.category,
            status=Post.Status.PUBLISHED,
        )

        cls.draft_post = Post.objects.create(
            title="Secret draft",
            slug="secret-draft",
            content="This content should stay private.",
            author=cls.author,
            category=cls.category,
            status=Post.Status.DRAFT,
        )


class AuthenticationTests(BlogTestBase):
    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials(self):
        logged_in = self.client.login(
            username="author",
            password="Test-pass-12345!",
        )
        self.assertTrue(logged_in)

    def test_anonymous_user_cannot_create_post(self):
        response = self.client.get(reverse("blog:post_create"))
        self.assertIn(response.status_code, (302, 403))


class DraftPrivacyTests(BlogTestBase):
    def test_draft_is_not_in_public_post_list(self):
        response = self.client.get(reverse("blog:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published article")
        self.assertNotContains(response, "Secret draft")

    def test_draft_cannot_be_opened_using_public_detail_url(self):
        response = self.client.get(
            reverse(
                "blog:post_detail",
                kwargs={"slug": self.draft_post.slug},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_owner_can_preview_draft(self):
        self.client.force_login(self.author)
        response = self.client.get(
            reverse(
                "blog:post_preview",
                kwargs={"slug": self.draft_post.slug},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Secret draft")

    def test_another_user_cannot_preview_draft(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse(
                "blog:post_preview",
                kwargs={"slug": self.draft_post.slug},
            )
        )
        self.assertEqual(response.status_code, 404)


class PostPermissionTests(BlogTestBase):
    def test_owner_can_open_edit_page(self):
        self.client.force_login(self.author)
        response = self.client.get(
            reverse(
                "blog:post_edit",
                kwargs={"slug": self.published_post.slug},
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_open_edit_page(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse(
                "blog:post_edit",
                kwargs={"slug": self.published_post.slug},
            )
        )
        self.assertIn(response.status_code, (403, 404))

    def test_other_user_cannot_delete_post(self):
        self.client.force_login(self.other_user)
        response = self.client.post(
            reverse(
                "blog:post_delete",
                kwargs={"slug": self.published_post.slug},
            )
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertTrue(
            Post.objects.filter(pk=self.published_post.pk).exists()
        )


class PostModelCRUDTests(BlogTestBase):
    def test_create_post(self):
        post = Post.objects.create(
            title="New article",
            slug="new-article",
            content="New content",
            author=self.author,
            category=self.category,
            status=Post.Status.DRAFT,
        )
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_read_post(self):
        post = Post.objects.get(slug="published-article")
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.status, Post.Status.PUBLISHED)

    def test_update_post(self):
        self.published_post.title = "Updated article"
        self.published_post.save()
        self.published_post.refresh_from_db()
        self.assertEqual(self.published_post.title, "Updated article")

    def test_delete_post(self):
        post = Post.objects.create(
            title="Temporary article",
            slug="temporary-article",
            content="Temporary content",
            author=self.author,
            category=self.category,
            status=Post.Status.DRAFT,
        )

        post_id = post.pk
        post.delete()

        self.assertFalse(Post.objects.filter(pk=post_id).exists())

