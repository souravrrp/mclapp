import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from .models import Category, Topic, Comment, Area, District, Site, EntryList


class UserTable(tables.Table):
    action_link = tables.Column(accessor='action_link', verbose_name='Action', orderable=False)
    last_login = tables.DateTimeColumn(format ='F d, Y P')
    get_full_name = tables.Column(verbose_name="Full Name")

    class Meta:
        model = User
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-bordered table-striped table-hover text-sm"}
        fields = ("username", "profile.employee_id", "get_full_name", "profile.department", "profile.designation",
         "email", "last_login", "is_staff", "is_active")


class CategoryTable(tables.Table):
    action_link = tables.Column(accessor='action_link', verbose_name='Action', orderable=False)

    class Meta:
        model = Category
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-bordered table-striped table-hover"}
        fields = ("name_bn", "name_en", "order", "is_active")


class TopicTable(tables.Table):
    action_link = tables.Column(accessor='action_link', verbose_name='Action', orderable=False)
    # sample_image = tables.Column(verbose_name='Sample Image')

    class Meta:
        model = Topic
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-bordered table-striped table-hover"}
        fields = ("name_bn", "name_en", "category", "order")

class CommentTable(tables.Table):
    action_link = tables.Column(accessor='action_link', verbose_name='Action', orderable=False)

    class Meta:
        model = Comment
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-bordered table-striped table-hover"}
        fields = ("comment", "is_active")

class EntryListTable(tables.Table):
    total_score = tables.Column(accessor='total_score', verbose_name='Total Score', orderable=False)
    action_link = tables.Column(accessor='action_link', verbose_name='Action', orderable=False)
    view_link = tables.Column(accessor='view_link', verbose_name='View', orderable=False)
    resubmit_link = tables.Column(accessor='resubmit_link', verbose_name='Resubmit', orderable=False)
    created_at = tables.DateTimeColumn(format ='d N Y, h:i A')
    #site_extension = tables.Column(verbose_name='Extension')
    #entry_date = tables.DateTimeColumn(format ='F d, Y')

    class Meta:
        model = EntryList
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-bordered table-striped table-hover"}
        fields = ("id", "site", "site.district.area.name", "site.district", "otp", "created_by", "created_at")

class AreaTable(tables.Table):
    action_link = tables.Column(accessor='action_link', verbose_name='Action', orderable=False)

    class Meta:
        model = Area
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-bordered table-striped table-hover"}
        fields = ("name", "manager", "address", "is_active")

class DistrictTable(tables.Table):
    action_link = tables.Column(accessor='action_link', verbose_name='Action', orderable=False)

    class Meta:
        model = District
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-bordered table-striped table-hover"}
        fields = ("code", "area", "manager", "address", "is_active")

    #def render_manager(self, record, value):
    #    return mark_safe(f"{record.manager.first_name} {record.manager.last_name} - {value}")

class SiteTable(tables.Table):
    action_link = tables.Column(accessor='action_link', verbose_name='Action', orderable=False)

    class Meta:
        model = Site
        template_name = "django_tables2/bootstrap4.html"
        attrs = {"class": "table table-bordered table-striped table-hover"}
        fields = ("code", "district", "district__area__name", "manager", "address", "is_active")
