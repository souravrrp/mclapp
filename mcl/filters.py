import django_filters
from django.db.models import Q
from django_filters import CharFilter
from django.contrib.auth.models import User
from .models import Category, Topic, Comment, Area, District, Site, EntryList

class UserFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='custom_filter', label="Search")
    class Meta:
        model = User
        fields = ['q']
    
    def custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(username__icontains=value) | Q(first_name__icontains=value) | Q(last_name__icontains=value)
        )

class CategoryFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='custom_filter', label="Search")
    class Meta:
        model = Category
        fields = ['q']
    
    def custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(name_bn__icontains=value) | Q(name_en__icontains=value)
        )

class TopicFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='custom_filter', label="Search")
    class Meta:
        model = Topic
        fields = ['q']
    
    def custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(name_bn__icontains=value) | Q(name_en__icontains=value) | Q(category__name_bn__icontains=value)
            | Q(category__name_en__icontains=value)
        )

class CommentFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='custom_filter', label="Search")
    class Meta:
        model = Comment
        fields = ['q']
    
    def custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(comment__icontains=value)
        )

class EntryListFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='custom_filter', label="Search")
    class Meta:
        model = EntryList
        fields = ['q']
    
    def custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(id__iexact=value) | Q(site__code__icontains=value) | Q(otp__icontains=value)
            | Q(site__district__area__name__icontains=value) | Q(site__district__code__icontains=value)
            | Q(created_by__username__icontains=value)
        )

class AreaFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='custom_filter', label="Search")
    class Meta:
        model = Area
        fields = ['q']
    
    def custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(address__icontains=value) | Q(manager__icontains=value) 
        )

class DistrictFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='custom_filter', label="Search")
    class Meta:
        model = District
        fields = ['q']
    
    def custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(code__icontains=value) | Q(address__icontains=value) | Q(manager__icontains=value)
            | Q(area__name__icontains=value)
        )

class SiteFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='custom_filter', label="Search")
    class Meta:
        model = Site
        fields = ['q']
    
    def custom_filter(self, queryset, name, value):
        return queryset.filter(
            Q(code__icontains=value) | Q(address__icontains=value) | Q(manager__icontains=value) 
            | Q(district__area__name__icontains=value) | Q(district__code__icontains=value)
        )