from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm, UserCreateForm
from .models import Category, Comment, Post

PAGINATION_OF_POSTS = 10

User = get_user_model()


def get_filtered_posts(posts):
    return posts.select_related(
        'category',
        'location',
        'author'
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    )


def get_comment_count(posts):
    return posts.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


class UserUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    form_class = UserCreateForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        username = self.request.user
        return reverse('blog:profile', kwargs={'username': username})


class HomeListView(ListView):

    model = Post
    template_name = 'blog/index.html'
    ordering = '-created_at'
    paginate_by = PAGINATION_OF_POSTS

    def get_queryset(self):
        return get_comment_count(
            get_filtered_posts(self.model.objects)

        )


class UserDetailView(ListView):

    model = Post
    paginate_by = PAGINATION_OF_POSTS
    slug_url_kwargs = 'username'
    template_name = 'blog/profile.html'

    def get_object(self):
        return get_object_or_404(
            User,
            username=self.kwargs[self.slug_url_kwargs]
        )

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            profile=self.get_object()
        )

    def get_queryset(self):
        author = self.get_object()
        posts = get_comment_count(author.posts)
        if author == self.request.user:
            return posts
        return get_filtered_posts(posts)






class PostCreateView(LoginRequiredMixin, CreateView):

    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        username = self.request.user.username
        return reverse('blog:profile', kwargs={'username': username})


class PostDetailView(DetailView):

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'id'

    def get_object(self):
        queryset = self.model.objects.select_related(
            'category', 'location', 'author')
        post = super().get_object(queryset)
        if post.author != self.request.user:
            queryset = get_filtered_posts(queryset)
        return get_object_or_404(
            queryset,
            id=self.kwargs[self.pk_url_kwarg]
        )

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            comments=self.object.comments.select_related('author'),
            form=CommentForm()
        )

class PostUpdateDeleteMixin(MixinPostComment):

    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        return redirect(self.get_success_url())


class MixinPostComment(UserPassesTestMixin):

    def test_func(self):
        self.object = self.get_object()
        return self.request.user == self.object.author


class PostUpdateView(PostUpdateDeleteMixin, UpdateView):

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.kwargs[self.pk_url_kwarg]}
        )


class PostDeleteView(LoginRequiredMixin, PostUpdateDeleteMixin, DeleteView):

    def get_success_url(self):
        return reverse('blog:index')

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=self.form_class(instance=self.object)
        )


class CategoryListView(ListView):

    template_name = 'blog/category.html'
    model = Post
    slug_url_kwarg = 'category_slug'
    paginate_by = PAGINATION_OF_POSTS

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs[self.slug_url_kwarg],
            is_published=True
        )
        query_set = get_filtered_posts(category.posts)
        return get_comment_count(query_set)

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            category=get_object_or_404(
                Category,
                slug=self.kwargs[self.slug_url_kwarg],
                is_published=True),
        )


class CommentCreateView(LoginRequiredMixin, CreateView):

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'post_id'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            id=self.kwargs[self.pk_url_kwarg]
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'id': self.kwargs[self.pk_url_kwarg]})


class CommentMixin(LoginRequiredMixin, MixinPostComment):

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'comment_id'


class CommentDeleteView(CommentMixin, DeleteView):
    """Удаление комментария."""


class CommentUpdateView(CommentMixin, UpdateView):
    """Изменение комментария."""