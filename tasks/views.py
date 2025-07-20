from .models import Task
from .forms import TaskForm
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.utils.timezone import now, timedelta
from django.core.exceptions import PermissionDenied


# декоратор для доступа только авторизованным пользователям
def login_required_403(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied("Вы не авторизованы.")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required_403
def task_list(request):
    tasks = Task.objects.filter(user=request.user)

    # фильтрация по поиску
    q = request.GET.get('q')
    if q:
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))

    # фильтрация по статусу
    status = request.GET.get('status')
    if status == 'completed':
        tasks = tasks.filter(is_completed=True)
    elif status == 'not_completed':
        tasks = tasks.filter(is_completed=False)

    # фильтрация по приоритету
    priority = request.GET.get('priority')
    if priority in ['1', '2', '3']:
        tasks = tasks.filter(priority=priority)

    # фильтрация по дате
    date_filter = request.GET.get('date_filter')
    if date_filter == 'today':
        tasks = tasks.filter(due_date__date=now().date())
    elif date_filter == 'week':
        tasks = tasks.filter(due_date__date__gte=now().date(),
                             due_date__date__lte=(now() + timedelta(days=7)).date())
    elif date_filter == 'overdue':
        tasks = tasks.filter(due_date__lt=now(), is_completed=False)

    # сортировка задач
    sort = request.GET.get('sort')
    if sort == 'due_date':
        tasks = tasks.order_by('due_date')
    elif sort == 'priority':
        tasks = tasks.order_by('priority')
    elif sort == 'title':
        tasks = tasks.order_by('title')
    else:
        tasks = tasks.order_by('is_completed', 'due_date')

    # пагинация
    page_number = request.GET.get('page', 1)
    paginator = Paginator(tasks, 10)
    page_obj = paginator.get_page(page_number)

    # if request.headers.get('x-requested-with') == 'XMLHttpRequest':
    #     html = render_to_string('tasks/_task_cards.html', {'tasks': page_obj}, request=request)
    #     return JsonResponse({'html': html})

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('tasks/_task_cards.html', {'tasks': page_obj}, request=request)
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next()
        })

    return render(request, 'tasks/task_list.html', {'tasks': page_obj})


def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ваш аккаунт зарегистрирован, войдите в него")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


@login_required_403
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Создание задачи'})


@login_required_403
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Редактирование задачи'})


@login_required_403
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required_403
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.is_completed = not task.is_completed
    task.save()
    return redirect('task_list')


def error_view(request, exception=None, code=500, message=None):
    if code == 400:
        message = message or "Некорректный запрос."
    elif code == 403:
        message = message or "Доступ запрещён."
    elif code == 404:
        message = message or "Страница не найдена."
    elif code == 500:
        message = message or "Внутренняя ошибка сервера."
    else:
        message = message or "Неизвестная ошибка."

    return render(request, 'error.html', {
        'code': code,
        'message': message
    }, status=code)


def bad_request(request, exception):
    return error_view(request, exception=exception, code=400)


def permission_denied(request, exception):
    return error_view(request, exception=exception, code=403)


def page_not_found(request, exception):
    return error_view(request, exception=exception, code=404)


def server_error(request):
    return error_view(request, code=500)
