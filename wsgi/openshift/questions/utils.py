# -*- coding: utf-8 -*-
from core.models import Place
from datetime import datetime, timedelta
from questions.models import Answer, UsersPlace, ConfusedPlaces
from random import choice
from logging import getLogger
from django.db.models import F


logger = getLogger(__name__)


class QuestionType(object):
    id = 0
    text = ""
    no_of_options = 0

    def to_serializable(self):
        return {
            'type': self.id,
            'text': self.text,
        }


class QuestionTypeFactory():

    @staticmethod
    def get_instance_by_id(id):
        possible_question_types = [
            qType for qType in QuestionTypeFactory.get_possible_question_types() if qType.id == id]
        if len(possible_question_types) == 1:
            return possible_question_types[0]
        else:
            logger.error("Requested question type with id '{0}'".format(id))

    @staticmethod
    def get_instance_by_no_of_options(no_of_options):
        possible_question_types = [
            qType for qType in QuestionTypeFactory.get_possible_question_types(
            ) if qType.no_of_options == no_of_options]
        qtype = choice(possible_question_types)
        return qtype

    @staticmethod
    def get_possible_question_types():
        possible_question_types = [
            QuestionTypeFactory.get_question_type_object(
                qType) for qType in Answer.QUESTION_TYPES]
        return possible_question_types

    @staticmethod
    def get_question_type_object(qType):
        qt = QuestionType()
        qt.id = qType[0]
        qt.text = qType[1]
        qt.no_of_options = qType[0] % 10
        return qt


def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]


class QuestionTextService():
    texts = {
        Place.STATE: {
            Answer.FIND_ON_MAP: u"Vyber na mapě stát",
            Answer.PICK_NAME_OF_6: u"Jak se jmenuje stát zvýrazněný na mapě?",
            Answer.FIND_ON_MAP_OF_6: u"Ze šesti zvýrazněných států na mapě vyber",
            Answer.PICK_NAME_OF_4: u"Jak se jmenuje stát zvýrazněný na mapě?",
            Answer.FIND_ON_MAP_OF_4: u"Ze čtyř zvýrazněných států na mapě vyber",
            Answer.PICK_NAME_OF_2: u"Jak se jmenuje stát zvýrazněný na mapě?",
            Answer.FIND_ON_MAP_OF_2: u"Ze dvou zvýrazněných států na mapě vyber",
        },
        Place.CITY: {
            Answer.FIND_ON_MAP: u"Vyber na mapě město",
            Answer.PICK_NAME_OF_6: u"Jak se jmenuje město zvýrazněné na mapě?",
            Answer.FIND_ON_MAP_OF_6: u"Ze šesti zvýrazněných měst na mapě vyber",
            Answer.PICK_NAME_OF_4: u"Jak se jmenuje město zvýrazněné na mapě?",
            Answer.FIND_ON_MAP_OF_4: u"Ze čtyř zvýrazněných měst na mapě vyber",
            Answer.PICK_NAME_OF_2: u"Jak se jmenuje město zvýrazněné na mapě?",
            Answer.FIND_ON_MAP_OF_2: u"Ze dvou zvýrazněných měst na mapě vyber",
        },
        Place.RIVER: {
            Answer.FIND_ON_MAP: u"Vyber na mapě řeku",
            Answer.PICK_NAME_OF_6: u"Jak se jmenuje řeka zvýrazněná na mapě?",
            Answer.FIND_ON_MAP_OF_6: u"Ze šesti zvýrazněných řek na mapě vyber",
            Answer.PICK_NAME_OF_4: u"Jak se jmenuje řeka zvýrazněná na mapě?",
            Answer.FIND_ON_MAP_OF_4: u"Ze čtyř zvýrazněných řek na mapě vyber",
            Answer.PICK_NAME_OF_2: u"Jak se jmenuje řeka zvýrazněná na mapě?",
            Answer.FIND_ON_MAP_OF_2: u"Ze dvou zvýrazněných řek na mapě vyber",
        },
        Place.LAKE: {
            Answer.FIND_ON_MAP: u"Vyber na mapě jezero",
            Answer.PICK_NAME_OF_6: u"Jak se jmenuje jezero zvýrazněné na mapě?",
            Answer.FIND_ON_MAP_OF_6: u"Ze šesti zvýrazněných jezer na mapě vyber",
            Answer.PICK_NAME_OF_4: u"Jak se jmenuje jezero zvýrazněné na mapě?",
            Answer.FIND_ON_MAP_OF_4: u"Ze čtyř zvýrazněných jezer na mapě vyber",
            Answer.PICK_NAME_OF_2: u"Jak se jmenuje jezero zvýrazněné na mapě?",
            Answer.FIND_ON_MAP_OF_2: u"Ze dvou zvýrazněných jezer na mapě vyber",
        },
    }

    @staticmethod
    def get_text(qtype, place):
        texts = QuestionTextService.texts
        if place.type in texts:
            if qtype.id in texts[place.type]:
                return texts[place.type][qtype.id]
        return qtype.text


class Question():
    options = []

    def __init__(self, place, qtype, map):
        self.place = place
        self.qtype = qtype
        self.map = map
        if (qtype.no_of_options != 0):
            self.options = self.get_options(self.qtype.no_of_options)

    def to_serializable(self):
        ret = self.qtype.to_serializable()
        ret["text"] = QuestionTextService.get_text(self.qtype, self.place)
        ret.update(self.place.to_serializable())
        ret["place"] = ret["name"]
        ret.pop("name")
        if (self.options != []):
            ret["options"] = self.options
        logger.debug(u"Question: type: {0} place: {1}".format(
            self.qtype.id, ret["place"]))
        return ret

    def get_options(self, n):
        ps = [self.place]
        ps += self.get_confused_options(n - 1)
        remains = n - len(ps)
        if (remains > 0):
            ps += self.get_random_options(remains, ps)
        options = [p.to_serializable() for p in ps]
        options.sort(key=lambda tup: tup["name"])
        return options

    def get_options_base(self):
        return Place.objects.filter(
            id__in=self.map.related_places.all(),
            type=self.place.type,
        )

    def get_easy_options(self, n):
        return (
            self.get_options_base().filter(
                difficulty__lt=self.place.difficulty).order_by('?')[:n]
        )

    def get_random_options(self, n, excluded):
        return (
            self.get_options_base().exclude(
                id__in=[p.id for p in excluded]).order_by('?')[:n]
        )

    def get_confused_options(self, n):
        return ConfusedPlaces.objects.get_similar_to(self.place, self.map)[:n]


class QuestionChooser(object):

    def __init__(self, user, map, pre_questions):
        # TODO: figure out how to make these 3 params work without setting them
        # again in get_questions method
        self.user = user
        self.map = map
        self.pre_questions = pre_questions

    @classmethod
    def get_ready_users_places(self, correctAnswerDelayMinutes=2):
        delay_miuntes = 1 if correctAnswerDelayMinutes > 1 else correctAnswerDelayMinutes
        minute_ago = datetime.now() - timedelta(seconds=60 * delay_miuntes)
        correct_minutes_ago = datetime.now() - timedelta(
            seconds=correctAnswerDelayMinutes * 60)
        return UsersPlace.objects.filter(
            user=self.user,
            lastAsked__lt=minute_ago,
            place_id__in=self.map.related_places.all(),
        ).exclude(
            place_id__in=[a.place_id for a in Answer.objects.filter(
                user=self.user,
                askedDate__gt=correct_minutes_ago,
                place=F("answer")
            )]
        ).exclude(
            place__code__in=[q['code'] for q in self.pre_questions]
        ).select_related('place').order_by('?')

    @classmethod
    def get_question_type(self, usersplace):
        if usersplace.askedCount < 2:
            successRate = self.success_rate
        else:
            successRate = usersplace.skill
        if (successRate > 0.85):
            no_of_options = 0
        elif (successRate > 0.7):
            no_of_options = 6
        elif (successRate > 0.5):
            no_of_options = 4
        else:
            no_of_options = 2
        qtype = QuestionTypeFactory.get_instance_by_no_of_options(
            no_of_options)
        return qtype

    @classmethod
    def get_questions(self, n, user, map, pre_questions):
        self.user = user
        self.map = map
        self.pre_questions = pre_questions
        self.success_rate = self.get_success_rate()
        usersplaces = self.get_usersplaces(n)
        questions = []
        for up in usersplaces:
            qtype = self.get_question_type(up)
            question = Question(up.place, qtype, self.map)
            questions.append(question.to_serializable())
        logger.info(u"{0}: generated '{1}' questions".format(
            self.__name__, len(questions)))
        return questions

    @classmethod
    def get_success_rate(self):
        lastAnswers = Answer.objects.get_last_10_answers(self.user)
        correct_answers = [a for a in lastAnswers if a.place_id == a.answer_id]
        last_answers_len = len(lastAnswers) if len(lastAnswers) > 0 else 1
        successRate = 1.0 * len(correct_answers) / last_answers_len
        return successRate


class UncertainPlacesQuestionChooser(QuestionChooser):

    @classmethod
    def get_usersplaces(self, n):
        return (
            [up for up in self.get_ready_users_places() if up.get_certainty() < 1][
                :n]
        )


class WeakPlacesQuestionChooser(QuestionChooser):

    @classmethod
    def get_usersplaces(self, n):
        return (
            [up for up in self.get_ready_users_places(
                5).filter(skill__lt=0.8)[:n]]
        )


class NewPlacesQuestionChooser(QuestionChooser):

    @classmethod
    def get_usersplaces(self, n):
        places = Place.objects.filter(
            id__in=self.map.related_places.all()
        ).exclude(
            id__in=[
                up.place_id for up in UsersPlace.objects.filter(user=self.user)]
        ).order_by('difficulty')[:n]
        return [UsersPlace(place=p, user=self.user) for p in places]


class LongestUnpracticedPlacesQuestionChooser(QuestionChooser):
    @classmethod
    def get_usersplaces(self, n):
        return UsersPlace.objects.filter(
            user=self.user,
            place_id__in=self.map.related_places.all(),
        ).exclude(
            place__code__in=[q['code'] for q in self.pre_questions]
        ).select_related('place').order_by('lastAsked')[:n]


class ShortRepeatIntervalPlacesQuestionChooser(QuestionChooser):

    @classmethod
    def get_usersplaces(self, n):
        return (
            [up for up in self.get_ready_users_places(
                0.5) if up.skill < 1 or up.get_certainty() < 1][:n]
        )


class QuestionService():

    def __init__(self, user, map):
        self.user = user
        self.map = map

    def get_questions(self, n):
        question_choosers = all_subclasses(QuestionChooser)
        questions = []
        logger.info(
            u"QuestionService: '{0}' questions for user '{1}' on map '{2}'".
            format(n, self.user, self.map.place.name))
        for QC in question_choosers:
            remains = n - len(questions)
            if remains <= 0:
                break
            qc = QC(self.user, self.map, questions)
            questions += qc.get_questions(
                remains,
                self.user,
                self.map,
                questions)
        return questions

    def answer(self, a):
        place = Place.objects.get(code=a["code"])
        try:
            answerPlace = Place.objects.get(
                code=a[
                    "answer"]) if "answer" in a and a[
                "answer"] != "" else None
        except Place.DoesNotExist:
            answerPlace = None
            code = a["answer"] if "answer" in a else None
            logger.error("Place with code '{0}' does not exist.".format(code))

        answer = Answer(
            user=self.user,
            place=place,
            answer=answerPlace,
            type=a["type"],
            msResposeTime=a["msResponseTime"],
        )
        answer.save()
        if "options" in a:
            answer.options = Place.objects.filter(
                code__in=[o["code"] for o in a["options"]],
            )

        if place == answerPlace:
            self.user.points += 1
            self.user.save()

        UsersPlace.objects.add_answer(answer)
