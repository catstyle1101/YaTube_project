from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin

from .models import Group, Follow, Post, User, Comment

from .forms import CommentForm, PostForm


class Index(ListView):
    paginate_by = settings.COUNT_OF_POSTS_PAGINATOR
    model = Post
    template_name = 'posts/index.html'


class GroupPostsView(ListView):
    paginate_by = settings.COUNT_OF_POSTS_PAGINATOR
    model = Group
    template_name = 'posts/group_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        group = get_object_or_404(Group, slug=self.kwargs['slug'])
        context['group'] = group
        return context

    def get_queryset(self):
        group = get_object_or_404(Group, slug=self.kwargs['slug'])
        return group.posts.all()


class ProfileView(ListView):
    paginate_by = settings.COUNT_OF_POSTS_PAGINATOR
    model = Post
    template_name = 'posts/profile.html'

    def get_queryset(self):
        author = get_object_or_404(User, username=self.kwargs['username'])
        return author.posts.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        author = get_object_or_404(User, username=self.kwargs['username'])
        context['author'] = author
        if self.request.user.is_authenticated:
            context['following'] = author.following.filter(
                user=self.request.user).exists()
            context['author_is_not_user'] = author != self.request.user
        return context


class PostDetailView(DetailView, FormMixin):
    model = Post
    template_name = 'posts/post_detail.html'
    form_class = CommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        post = get_object_or_404(Post, pk=self.object.pk)
        comments = post.comments.all()
        context['comments'] = comments
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def form_valid(self, form):
        new_post = form.save(commit=False)
        new_post.author = self.request.user
        new_post.save()
        return redirect(
            reverse('posts:profile',
                    args=(new_post.author.username,)
                    )
        )


class PostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'
    slug_field = 'post_id'
    template_name_suffix = '_update_form'

    def get_context_data(self):
        context = super().get_context_data()
        context['is_edit'] = True
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(author=self.request.user)
        return queryset

    def form_valid(self, form):
        form.save()
        return redirect(reverse('posts:post_detail', args=(self.object.pk,)))


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        new_comment = form.save(commit=False)
        new_comment.post = post
        new_comment.author = self.request.user
        new_comment.save()
        return redirect(reverse('posts:post_detail', args=(post.pk,)))


class FollowingListView(LoginRequiredMixin, ListView):
    paginate_by = settings.COUNT_OF_POSTS_PAGINATOR
    model = Post
    template_name = 'posts/index.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['following_view'] = True
        return context

    def get_queryset(self):
        return Post.objects.filter(author__following__user=self.request.user)


class FollowAuthor(LoginRequiredMixin, View):
    model = User
    template_name = 'posts/profile.html'

    def get(self, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs['username'])
        is_follower = Follow.objects.filter(
            user=self.request.user,
            author=author
        )
        if self.request.user != author and not is_follower.exists():
            Follow.objects.create(author=author, user=self.request.user)
        return redirect(reverse(
            'posts:profile',
            args=(self.kwargs['username'],)
        ))


class UnFollowAuthor(LoginRequiredMixin, View):
    model = User
    template_name = 'posts/profile.html'

    def get(self, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs['username'])
        is_follower = Follow.objects.filter(
            user=self.request.user,
            author=author,
        )
        if is_follower.exists():
            is_follower.delete()
        return redirect(
            reverse('posts:profile', args=(self.kwargs['username'],))
        )
