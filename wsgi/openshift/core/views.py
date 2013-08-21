# -*- coding: utf-8 -*-

from core.models import Place, Student, UsersPlace
from core.utils import QuestionService, JsonResponse
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.utils import simplejson
from lazysignup.decorators import allow_lazy_user
from django.conf import settings



# Create your views here.
def home(request):
    request.META["CSRF_COOKIE_USED"] = True
    title = 'Loc - ' if not settings.ON_OPENSHIFT else ''
    c = {
         'title' : title,
         'isProduction' : settings.ON_OPENSHIFT,
    }
    c.update(csrf(request))
    return render_to_response('home/home.html', c)

def places(request):
    ps = Place.objects.all().order_by('name')
    response = [{
        'name': u'Státy',
        'places': [p.to_serializable() for p in ps]
    }]
    return JsonResponse(response)

def users_places(request, part, user=''):
    if (user == ''):
        user = request.user
    else:
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            raise HttpResponseBadRequest("Invalid username: {0}" % user)
        
    if request.user.is_authenticated():
        student = Student.objects.fromUser(user)
        ps = UsersPlace.objects.filter(user=student)
    else:
        ps =[]
    response = [{
        'name': u'Státy',
        'places': []
    }]
    for p in ps:
        response[0]['places'].append(p.to_serializable())
    return JsonResponse(response)

@allow_lazy_user
def question(request):
    qs = QuestionService(user=request.user)
    questionIndex = 0
    if (request.raw_post_data != ""):
        answer = simplejson.loads(request.raw_post_data)
        questionIndex = answer['index'] + 1
        qs.answer(answer);
    noOfQuestions = 5 if Student.objects.fromUser(request.user).points < 10 else 10
    noOfQuestions -= questionIndex
    response = qs.get_questions(noOfQuestions)
    return JsonResponse(response)

def updateStates_view(request):
    if (Place.objects.count() == 0):
        updateStates();
    else:
        states = Place.objects.all()
        [ s.updateDifficulty() for s in states ]
    return HttpResponse("states Updated")

def updateStates():
    Place.objects.all().delete()
    statesFile = open('app-root/runtime/repo/usa.txt')
    states = statesFile.read()
    ss = states.split("\n")
    for s in ss:
        state = s.split("\t")
        if(len(state) > 3):
            name = state[2]
            code = 'us-' + state[0].lower()
            Place(code=code, name=name).save()
