from django import template
from django.contrib.auth.models import User
from mcl.models import SiteSettings, Category, Topic, Comment, Area, District, Site

register = template.Library()

@register.simple_tag
def site_name():
    try:
        site = SiteSettings.objects.values_list('name', flat=True).get(site_id='main')
    except SiteSettings.DoesNotExist:
        site = "App Name"
    return site

@register.simple_tag
def site_title():
    try:
        site = SiteSettings.objects.values_list('title', flat=True).get(site_id='main')
    except SiteSettings.DoesNotExist:
        site = "App Title"
    return site

@register.simple_tag
def site_description():
    try:
        site = SiteSettings.objects.values_list('description', flat=True).get(site_id='main')
    except SiteSettings.DoesNotExist:
        site = "Description"
    return site

@register.filter(name='zip')
def zip_lists(a, b):
  return zip(a, b)

@register.simple_tag
def user_count():
    try:
        site = User.objects.filter(is_superuser=False).count()
    except User.DoesNotExist:
        site = "0"
    return site

@register.simple_tag
def category_count():
    try:
        site = Category.objects.all().count()
    except Category.DoesNotExist:
        site = "0"
    return site

@register.simple_tag
def topic_count():
    try:
        site = Topic.objects.all().count()
    except Topic.DoesNotExist:
        site = "0"
    return site

@register.simple_tag
def comment_count():
    try:
        site = Comment.objects.all().count()
    except Comment.DoesNotExist:
        site = "0"
    return site

@register.simple_tag
def area_count():
    try:
        site = Area.objects.all().count()
    except Area.DoesNotExist:
        site = "0"
    return site

@register.simple_tag
def district_count():
    try:
        site = District.objects.all().count()
    except District.DoesNotExist:
        site = "0"
    return site

@register.simple_tag
def site_count():
    try:
        site = Site.objects.all().count()
    except Site.DoesNotExist:
        site = "0"
    return site

