import os
from django.core.management.base import BaseCommand

# قائمة الموديلات
MODELS = [
    "ExploitingTheSite",
    "ExploitingTheSiteAlready",
    "MangWk",
    "TypeMrde",
    "ActiveAstglal",
    "HandErea",
    "MethodHandErea",
    "HajzAsthmer",
    "TypeWkf",
    "NameWkf"
]

TEMPLATE_DIR = "new_st/templates/new_st"

FORM_TEMPLATE = """{% raw %}
{% extends 'new_st/base.html' %}
{% block content %}
<div class="container mt-4">
    <h2>{% if object %}تعديل {{ model_name }}{% else %}إضافة {{ model_name }}{% endif %}</h2>
    <hr>
    <form method="post">
        {% csrf_token %}
        {% for field in form %}
        <div class="form-group">
            {{ field.label_tag }}
            {{ field }}
            {% if field.errors %}
            <div class="text-danger">{{ field.errors|striptags }}</div>
            {% endif %}
        </div>
        {% endfor %}
        <button type="submit" class="btn btn-primary mt-2">{% if object %}تحديث{% else %}إضافة{% endif %}</button>
        <a href="{{ list_url }}" class="btn btn-secondary mt-2">إلغاء</a>
    </form>
</div>
{% endblock %}
{% endraw %}
"""

LIST_TEMPLATE = """{% raw %}
{% extends 'new_st/base.html' %}
{% block content %}
<div class="container mt-4">
    <h2>قائمة {{ model_name }}</h2>
    <a href="{{ create_url }}" class="btn btn-success mb-3">إضافة جديد</a>
    <table class="table table-bordered table-striped">
        <thead>
            <tr>
                <th>#</th>
                <th>الاسم</th>
                <th>الإجراءات</th>
            </tr>
        </thead>
        <tbody>
            {% for obj in object_list %}
            <tr>
                <td>{{ forloop.counter }}</td>
                <td>{{ obj.name }}</td>
                <td>
                    <a href="{{ update_url }}{{ obj.pk }}" class="btn btn-warning btn-sm">تعديل</a>
                    <a href="{{ delete_url }}{{ obj.pk }}" class="btn btn-danger btn-sm">حذف</a>
                </td>
            </tr>
            {% empty %}
            <tr><td colspan="3">لا توجد بيانات</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
{% endraw %}
"""

class Command(BaseCommand):
    help = "إنشاء كل قوالب CRUD تلقائيًا لكل الموديلات"

    def handle(self, *args, **kwargs):
        if not os.path.exists(TEMPLATE_DIR):
            os.makedirs(TEMPLATE_DIR)
        for model in MODELS:
            # Form template
            form_file = os.path.join(TEMPLATE_DIR, f"{model.lower()}_form.html")
            with open(form_file, "w", encoding="utf-8") as f:
                f.write(FORM_TEMPLATE.replace("{{ model_name }}", model)
                                     .replace("{{ list_url }}", f"{{% url 'new_st:{model.lower()}_list' %}}"))
            # List template
            list_file = os.path.join(TEMPLATE_DIR, f"{model.lower()}_list.html")
            with open(list_file, "w", encoding="utf-8") as f:
                f.write(LIST_TEMPLATE.replace("{{ model_name }}", model)
                                      .replace("{{ create_url }}", f"{{% url 'new_st:{model.lower()}_create' %}}")
                                      .replace("{{ update_url }}", f"{{% url 'new_st:{model.lower()}_update' %}}")
                                      .replace("{{ delete_url }}", f"{{% url 'new_st:{model.lower()}_delete' %}}"))
            self.stdout.write(self.style.SUCCESS(f"تم إنشاء قوالب {model}"))
