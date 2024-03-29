from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['index'] = True
        context['cache_seconds'] = settings.CACHE_PAGE_SECONDS
        return context

    def get_queryset(self):
        return Post.objects.select_related('author', 'group')


class GroupPostsView(ListView):
    paginate_by = settings.COUNT_OF_POSTS_PAGINATOR
    model = Post
    template_name = 'posts/group_list.html'

    def get_group_instance(self):
        return get_object_or_404(Group, slug=self.kwargs.get('slug'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        group = self.get_group_instance()
        context['group'] = group
        return context

    def get_queryset(self):
        return (Post.objects.select_related('author')
                .filter(group__slug=self.kwargs.get('slug')))


class ProfileView(ListView):
    paginate_by = settings.COUNT_OF_POSTS_PAGINATOR
    model = Post
    template_name = 'posts/profile.html'

    def get_queryset(self):
        return (Post.objects.select_related('group')
                .filter(author__username=self.kwargs.get('username')))

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        author = get_object_or_404(User, username=self.kwargs.get('username'))
        context['author'] = author
        context['following'] = (
            self.request.user.is_authenticated
            and author.following.filter(user=self.request.user).exists()
        )
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

    def get_queryset(self):
        return (Post.objects.select_related('author').all()
                .select_related('group').all())


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def form_valid(self, form):
        new_post = form.save(commit=False)
        new_post.author = self.request.user
        new_post.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'posts:profile',
            args=(self.request.user.username,)
        )


class PostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/create_post.html'
    object = None

    def get_context_data(self):
        context = super().get_context_data()
        context['is_edit'] = True
        return context

    def get_queryset(self):
        return (Post.objects.select_related('group').all()
                .select_related('author').all())

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != self.request.user:
            return redirect(
                reverse_lazy('posts:post_detail', args=(instance.pk,))
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('posts:post_detail', args=(self.object.pk,))


class AddCommentView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        post = get_object_or_404(Post, pk=self.kwargs.get('pk'))
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
        context['cache_seconds'] = settings.CACHE_PAGE_SECONDS
        return context

    def get_queryset(self):
        return Post.objects.filter(author__following__user=self.request.user)


class FollowAuthor(LoginRequiredMixin, View):
    model = User
    template_name = 'posts/profile.html'

    def get(self, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs.get('username'))
        if author != self.request.user:
            Follow.objects.get_or_create(author=author, user=self.request.user)
        return redirect(reverse(
            'posts:profile',
            args=(self.kwargs.get('username'),)
        ))


class UnFollowAuthor(LoginRequiredMixin, View):
    model = User
    template_name = 'posts/profile.html'

    def get(self, *args, **kwargs):
        author = get_object_or_404(User, username=self.kwargs.get('username'))
        is_follower = Follow.objects.filter(
            user=self.request.user,
            author=author,
        )
        is_follower.delete()
        return redirect(
            reverse('posts:profile', args=(self.kwargs.get('username'),))
        )
