from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def index(request):
    template = 'posts/index.html'
    title = 'Последние обновления на сайте'
    paginator = Paginator(Post.objects.all(), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': title,
        'index': True,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    title = f'Записи сообщества {group.title}'
    paginator = Paginator(group.posts.all(), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
        'title': title,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    title = f'Профайл пользователя {author.username}'
    paginator = Paginator(author.posts.all(), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    if (request.user.is_authenticated):
        following = True
    else:
        following = False
    context = {
        'user_s': author,
        'page_obj': page_obj,
        'title': title,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    title = f'Пост {post.text[:29]}'
    form_title = 'Добавить комментарий:'
    context = {
        'post': post,
        'title': title,
        'form': form,
        'form_title': form_title,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    title = 'Новый пост'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author.username)
    context = {
        'form': form,
        'title': title,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    template = 'posts/create_post.html'
    title = 'Редактировать пост'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post_id': post_id,
        'title': title,
        'is_edit': True
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    title = 'Последние обновления в подписках'
    following = Follow.objects.filter(user=request.user)
    authors = User.objects.filter(following__in=following)
    f_posts = Post.objects.filter(author__in=authors)
    paginator = Paginator(f_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'title': title,
        'follow': True,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    following = get_object_or_404(User, username=username)
    if not Follow.objects.filter(
        user=request.user,
        author=following
    ).exists() and not request.user == following:
        Follow.objects.create(
            user=request.user,
            author=following
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    follow = get_object_or_404(
        Follow,
        user=request.user,
        author=following
    )
    follow.delete()
    return redirect('posts:profile', username=username)
