from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View
from RITCSE_codeWars.models import Submission, Contest, Question
from .form import UserForm


def index(request):
    now = timezone.now()
    contest_list = Contest.objects.all()
    contests = []
    for contest in contest_list:
        if contest.contest_start_date < now < contest.contest_end_date:
            contests.append(contest)

    return render(request, 'RITCSE_codeWars/ContestList.html', {
        "contest_list": contests
    })


def all_submission(request):
    try:
        contest_pk = request.GET['contest']
    except KeyError:
        return HttpResponseRedirect(reverse('Index'))
    contest = Contest.objects.all().filter(pk=contest_pk)[0]
    request.session['contest'] = contest
    submission_list = Submission.objects.all().filter(contest=contest)
    users = set()
    for submission in submission_list:
        if submission.user not in users:
            users.add(submission.user)
    user_submission_details = {}
    max_count = 0
    for user in users:
        user_submission_list = Submission.objects.all().filter(user=user)
        user_count = len(user_submission_list)
        user_submission_details[user] = user_count
        if user_count > max_count:
            max_count = user_count
    rank_list = []
    for i in range(max_count)[::-1]:
        same_rank = []
        for user in users:
            if user_submission_details[user] == i:
                same_rank.append(user)
        if len(same_rank) > 0: rank_list.append(same_rank)

    def date_last(var):
        return Submission.objects.all().filter(user=var).order_by('-submission_time')[0]

    final_list = []
    for l in rank_list:
        if len(l) > 1:
            for i, user_in_list in enumerate(l):
                larg = user_in_list
                j = 0
                while len(l) - i > j > 0:
                    if date_last(larg) < date_last(l[j]):
                        larg = l[j]
                t = larg
                larg = l[j]
                l[j] = t
            final_list += l

    class rankHolder:
        def __init__(self, username, question_solved, last_submitted):
            self.username = username
            self.question_solved = question_solved
            self.last_submitted = last_submitted

    final_rank_list = []
    for item in final_list:
        final_rank_list.append(rankHolder(item.username, user_submission_details[item], date_last(item)))

    return render(request, 'RITCSE_codeWars/AllSubmissions.html', {
        "submission_list": submission_list,
        "rank_list": final_rank_list
    })


def your_submissions(request):
    if request.user.is_authenticated:
        user = request.user
        submision_list = Submission.objects.all().filter(user=user)
        return render(request, 'RITCSE_codeWars/YourSubmissions.html', {
            "submission_list": submision_list
        })


def your_code(request):
    try:
        id = request.GET['submission_id']
    except KeyError:
        return HttpResponseRedirect(reverse('YourSubmissions'))
    user = request.user
    submission = Submission.objects.all().filter(submission_id=id)

    if submission[0].user.username != user.username:
        return render(request, 'RITCSE_codeWars/YourCode.html', {
            "submission": "You are not authorised"
        })

    return render(request, 'RITCSE_codeWars/YourCode.html', {
        "submission": submission
    })


class UserFormView(View):
    form_class = UserForm
    template_name = 'RITCSE_codeWars/registration.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save(commit=True)
        return HttpResponseRedirect(reverse('Index'))


def login_user(request):
    return render(request, 'RITCSE_codeWars/Login.html')


def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse('Index'))


def authenticate_user(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
    except KeyError:
        return HttpResponseRedirect(reverse('Login'))
    user = authenticate(username=username, password=password)

    if user is None:
        return HttpResponseRedirect(reverse('Login') + '?error=true')
    login(request, user)
    request.session.set_expiry(0)
    return HttpResponseRedirect(reverse('Index'))


def questions_list(request, contest_list_id):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('Login') + "?error=true")
    try:
        contest_obj = Contest.objects.all().filter(pk=contest_list_id)
    except Contest.DoesNotExist:
        return HttpResponseRedirect(reverse('Index'))
    questions = Question.objects.all().filter(contest=contest_obj)
    return render(request, 'RITCSE_codeWars/QuestionList.html', {
        'username': request.user.username,
        'contest': contest_list_id,
        'question_list': questions,
    })


def problem(request, question_code):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('Login') + "?error=true")
    try:
        question = Question.objects.all().filter(question_code=question_code)
    except Question.DoesNotExist:
        return HttpResponseRedirect('Index')
    return render('RITCSE_codeWars/Home.html', {
        'username': request.user.username,
        'question': question
    })
