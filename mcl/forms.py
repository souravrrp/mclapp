from django import forms
from crispy_forms.helper import FormHelper
from django.contrib.auth.models import User
from crispy_forms.layout import Layout, Div, Submit, Row, Column, Field, HTML, Fieldset
from .models import Profile, Category, Topic, Comment, Area, District, Site, UserSettings, SiteSettings
from django.utils.translation import gettext as _
from django_select2 import forms as s2forms


class ManagerWidget(s2forms.ModelSelect2Widget):
    search_fields = [
        "username__icontains",
        "first_name__icontains",
        "last_name__icontains",
    ]

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class UserCreateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['is_active'].help_text = None
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Fieldset(
                'User Information',
                HTML('<hr>'),
                Row(
                    Column('username', css_class='col-md-4'),
                    Column('first_name', css_class='col-md-4'),
                    Column('last_name', css_class='col-md-4'),
                ),
                Row(
                    Column('password', css_class='col-md-4'),
                    Column('email', css_class='col-md-6'),
                    Column('is_active', css_class='col-md-2'),
                ),
            ),
        )

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Fieldset(
                'User Information',
                HTML('<hr>'),
                Row(
                    Column('username', css_class='col-md-4'),
                    Column('first_name', css_class='col-md-4'),
                    Column('last_name', css_class='col-md-4'),
                ),
                Row(
                    Column('email', css_class='col-md-8'),
                    Column('is_active', css_class='col-md-4'),
                ),
            ),
        )

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['employee_id', 'department', 'designation', 'phone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee_id'].widget.attrs['required'] = True
        self.fields['department'].widget.attrs['required'] = True
        self.fields['designation'].widget.attrs['required'] = True
        self.fields['phone'].widget.attrs['required'] = True
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Fieldset(
                'User Profile',
                HTML('<hr>'),
                Row(
                    Column('employee_id', css_class='col-md-6'),
                    Column('department', css_class='col-md-6'),
                    css_class='form-row'
                ),
                Row(
                    Column('designation', css_class='col-md-6'),
                    Column('phone', css_class='col-md-6'),
                ),
            ),
        )

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['name', 'title', 'description', 'entry_last_date']
        widgets = {
            'description' : forms.Textarea(attrs={
                'rows': '3',
            }),
        }
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Row(
                    Column('name', css_class='col-md-4'),
                    Column('title', css_class='col-md-8'),
                ),
                Row(
                    Column('entry_last_date', css_class='col-md-4'),
                    Column('description', css_class='col-md-8'),
                ),
            )
        )

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name_bn', 'name_en', 'order', 'is_active']
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Row(
                    Column('name_bn', css_class='col-md-6'),
                    Column('name_en', css_class='col-md-6'),
                ),
                Row(
                    Column('order', css_class='col-md-6'),
                    Column('is_active', css_class='col-md-6'),
                ),
            )
        )

class TopicForm(forms.ModelForm):
    sample_image = forms.ImageField(required=False)

    class Meta:
        model = Topic
        fields = ['name_bn', 'name_en', 'category', 'order', 'sample_image']
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Row(
                    Column('name_bn', css_class='col-md-6'),
                    Column('name_en', css_class='col-md-6'),
                ),
                Row(
                    Column('category', css_class='col-md-8'),
                    Column('order', css_class='col-md-4'),
                ),
                Row(
                    Column('sample_image', css_class='col-md-12'),
                ),
            )
        )


# class TopicForm(forms.ModelForm):
#     class Meta:
#         model = Topic
#         fields = ['name_bn', 'name_en', 'category', 'order']
       
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.helper = FormHelper()
#         self.helper.form_tag = False
#         self.helper.layout = Layout(
#             Fieldset(
#                 '',
#                 Row(
#                     Column('name_bn', css_class='col-md-6'),
#                     Column('name_en', css_class='col-md-6'),
#                 ),
#                 Row(
#                     Column('category', css_class='col-md-8'),
#                     Column('order', css_class='col-md-4'),
#                 ),
#             )
#         )

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment', 'is_active']
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Row(
                    Column('comment', css_class='col-md-8'),
                    Column('is_active', css_class='col-md-4'),
                ),
            )
        )

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['item_limit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Row(
                    Column('item_limit', css_class='col'),
                ),
            )
        )

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['name', 'manager', 'address', 'is_active']
        widgets = {
            "manager": ManagerWidget,
        }
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Row(
                    Column('name', css_class='col-md-4'),
                    Column('manager', css_class='col-md-8'),
                ),
                Row(
                    Column('address', css_class='col-md-8'),
                    Column('is_active', css_class='col-md-4'),
                ),
            )
        )

class DistrictForm(forms.ModelForm):
    class Meta:
        model = District
        fields = ['code', 'area', 'address', 'manager', 'is_active']
        widgets = {
            "manager": ManagerWidget,
        }
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['area'] = forms.ModelChoiceField(Area.objects.filter(is_active=True))
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Row(
                    Column('code', css_class='col-md-3'),
                    Column('manager', css_class='col-md-6'),
                    Column('area', css_class='col-md-3'),
                ),
                Row(
                    Column('address', css_class='col-md-8'),
                    Column('is_active', css_class='col-md-4'),
                ),
            )
        )


class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['code', 'district', 'address', 'manager', 'is_active']
        widgets = {
            "manager": ManagerWidget,
        }
       
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['district'] = forms.ModelChoiceField(District.objects.filter(is_active=True))
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                Row(
                    Column('code', css_class='col-md-3'),
                    Column('manager', css_class='col-md-6'),
                    Column('district', css_class='col-md-3'),
                ),
                Row(
                    Column('address', css_class='col-md-8'),
                    Column('is_active', css_class='col-md-4'),
                ),
            )
        )