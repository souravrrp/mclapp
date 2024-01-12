from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import Profile, Area, District, Site

class UserResource(resources.ModelResource):
   
    def before_import_row(self,row, **kwargs):
           value = row['password']
           row['password'] = make_password(value)

    class Meta:
        model = User
        import_id_fields = ('username',)
        fields = ('username', 'password', 'first_name', 'last_name', 'email')

class ProfileResource(resources.ModelResource):
    user = fields.Field(column_name='user', attribute='user', widget=ForeignKeyWidget(User, 'username'))

    class Meta:
        model = Profile
        import_id_fields = ('user',)
        fields = ('user',  'employee_id', 'department', 'designation', 'phone')   

class AreaResource(resources.ModelResource):
    class Meta:
        model = Area

class DistrictResource(resources.ModelResource):
    area = fields.Field(column_name='area', attribute='area', widget=ForeignKeyWidget(Area, 'name'))

    class Meta:
        model = District
        #fields = ('id', 'code', 'area', 'manager', 'address', 'is_active')
        export_order = ['id', 'code', 'area', 'manager', 'address', 'is_active']


class SiteResource(resources.ModelResource):
    district = fields.Field(column_name='district', attribute='district', widget=ForeignKeyWidget(District, 'code'))

    class Meta:
        model = Site
        export_order = ['id', 'code', 'district', 'manager', 'address', 'is_active']