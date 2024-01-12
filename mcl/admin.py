from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from import_export.admin import ImportExportModelAdmin
from .resources import UserResource, ProfileResource, AreaResource, DistrictResource, SiteResource
from .models import SiteSettings, UserSettings, Category, Topic, EntryList, CheckList, Site, Comment, Area, District
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin, ImportExportModelAdmin):
    inlines = (ProfileInline,)
    resource_class = UserResource

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class ProfileAdmin(ImportExportModelAdmin):
    list_display = ('user', 'employee_id', 'get_name', 'department', 'designation', 'phone')
    search_fields = ['user__username']
    resource_class = ProfileResource

    def get_name(self, obj):
        return "{0} {1}".format(obj.user.first_name, obj.user.last_name)
    get_name.short_description = 'Full Name'
    get_name.admin_order_field = 'user__first_name'

admin.site.register(Profile, ProfileAdmin)

class SiteSettingsAdmin(admin.ModelAdmin):
   list_display = ('site_id', 'name', 'title')
   search_fields = ('name',)
admin.site.register(SiteSettings, SiteSettingsAdmin)

class UserSettingsAdmin(admin.ModelAdmin):
   list_display = ('user', 'item_limit')
   search_fields = ('user',)
admin.site.register(UserSettings, UserSettingsAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_bn', 'name_en', 'order', 'is_active')
admin.site.register(Category, CategoryAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('name_bn', 'name_en', 'category', 'order')
admin.site.register(Topic, TopicAdmin)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment', 'is_active')
admin.site.register(Comment, CommentAdmin)

class EntryListAdmin(admin.ModelAdmin):
    list_display = ('id', 'site', 'otp', 'created_at')
admin.site.register(EntryList, EntryListAdmin)

class CheckListAdmin(admin.ModelAdmin):
    list_display = ('entry_list', 'topic', 'point', 'topic_image')
admin.site.register(CheckList, CheckListAdmin)

class AreaAdmin(ImportExportModelAdmin):
    list_display = ('name', 'address', 'manager', 'is_active')
    resource_class = AreaResource
admin.site.register(Area, AreaAdmin)

class DistrictAdmin(ImportExportModelAdmin):
    list_display = ('code', 'area', 'manager', 'address', 'is_active')
    resource_class = DistrictResource
admin.site.register(District, DistrictAdmin)

class SiteAdmin(ImportExportModelAdmin):
    list_display = ('code', 'district', 'manager', 'address', 'is_active')
    resource_class = SiteResource
admin.site.register(Site, SiteAdmin)