from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q
from django.db.models.functions import Trim
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from .models import AcademicGroup, Course, Department, StudentProfile


PAGES = {
    "overview": ("Обзор", "Факультеты, группы, студенты и курсы"),
    "students": ("Студенты", "Распределение студентов и участие в курсах"),
    "courses": ("Курсы", "Популярность курсов и заполнение описаний"),
}


def make_chart(title, pairs):
    rows = [{"label": label, "value": value} for label, value in pairs]
    maximum = max((row["value"] for row in rows), default=0)
    for row in rows:
        row["width"] = round(row["value"] / maximum * 100) if maximum else 0
    return {"title": title, "rows": rows, "maximum": maximum}


@login_required
@never_cache
def dashboard(request, section="overview"):
    if section not in PAGES:
        raise Http404("Такого дашборда нет")

    selected = None
    raw_department = request.GET.get("department", "")
    if raw_department:
        if not raw_department.isascii() or not raw_department.isdecimal():
            raise Http404("Некорректный факультет")
        if len(raw_department) > 10 or int(raw_department) > 2147483647:
            raise Http404("Некорректный факультет")
        selected = get_object_or_404(Department, pk=int(raw_department))

    departments = Department.objects.order_by("name", "pk")
    students = StudentProfile.objects.all()
    groups = AcademicGroup.objects.all()
    courses = Course.objects.all()
    scoped_departments = departments
    if selected:
        scoped_departments = departments.filter(pk=selected.pk)
        students = students.filter(department=selected)
        groups = groups.filter(department=selected)
        courses = courses.filter(department=selected)

    if section == "overview":
        cards = [
            ("Факультеты", scoped_departments.count()),
            ("Учебные группы", groups.count()),
            ("Студенты", students.count()),
            ("Курсы", courses.count()),
        ]
        summary = list(scoped_departments.annotate(
            student_total=Count("students", distinct=True),
            course_total=Count("courses", distinct=True),
        ))
        student_pairs = [(f"{d.name} (#{d.pk})", d.student_total) for d in summary]
        if not selected:
            student_pairs.append(("Без факультета", students.filter(department__isnull=True).count()))
        charts = [
            make_chart("Студенты по факультетам", student_pairs),
            make_chart("Курсы по факультетам",
                       [(f"{d.name} (#{d.pk})", d.course_total) for d in summary]),
        ]
        explanation = "Фильтр выбирает объекты по их собственному полю department."

    elif section == "students":
        total = students.count()
        enrolled = students.filter(courses__isnull=False).distinct().count()
        missing_group = students.filter(academic_group__isnull=True).count()
        mismatched = students.filter(academic_group__isnull=False).filter(
            Q(department__isnull=True)
            | ~Q(department_id=F("academic_group__department_id"))
        ).count()
        cards = [
            ("Студенты", total),
            ("Есть хотя бы один курс", enrolled),
            ("Без учебной группы", missing_group),
            ("Факультет и группа не согласованы", mismatched),
        ]
        summary = students.values("academic_group_id", "academic_group__name").annotate(
            total=Count("pk")
        ).order_by("-total", "academic_group__name", "academic_group_id")
        pairs = [
            (f"{row['academic_group__name']} (#{row['academic_group_id']})"
             if row["academic_group_id"] else "Без группы", row["total"])
            for row in summary
        ]
        charts = [
            make_chart("Студенты по учебным группам", pairs),
            make_chart("Участие в курсах",
                       [("Есть курсы", enrolled), ("Нет курсов", total - enrolled)]),
        ]
        explanation = (
            "Фильтр выбирает студентов по факультету профиля. Их группы и курсы могут "
            "относиться к другому факультету. Несогласованность факультета и группы "
            "показывается отдельно; она не исключает студента из статистики."
        )

    else:
        summary = list(courses.annotate(student_total=Count("students", distinct=True))
                       .order_by("-student_total", "title", "pk"))
        total = len(summary)
        enrollments = sum(course.student_total for course in summary)
        empty = sum(course.student_total == 0 for course in summary)
        described = courses.annotate(clean_description=Trim("description")).exclude(
            clean_description=""
        ).count()
        cards = [
            ("Курсы", total),
            ("Связи студент–курс", enrollments),
            ("Курсы без студентов", empty),
            ("Курсы с описанием", described),
        ]
        charts = [
            make_chart("Количество студентов на курсах",
                       [(f"{course.title} (#{course.pk})", course.student_total) for course in summary]),
            make_chart("Заполнение описаний",
                       [("Есть описание", described), ("Нет описания", total - described)]),
        ]
        explanation = (
            "Фильтр выбирает курсы по их факультету. На выбранных курсах учитываются "
            "все записанные студенты, включая студентов других факультетов. "
            "Связи студент–курс — это количество записей на курсы, а не уникальных людей."
        )

    query = f"?department={selected.pk}" if selected else ""
    tabs = [
        {"title": page[0], "url": reverse("dashboard", args=[key]) + query,
         "active": key == section}
        for key, page in PAGES.items()
    ]
    return render(request, "dashboards/page.html", {
        "title": PAGES[section][0],
        "subtitle": PAGES[section][1],
        "cards": cards,
        "charts": charts,
        "tabs": tabs,
        "departments": departments,
        "selected_department": selected,
        "explanation": explanation,
        "updated_at": timezone.now(),
    })