from django.db import models
from django_currentuser.db.models import CurrentUserField
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
import os
from django.contrib.auth import get_user_model
from django_resized import ResizedImageField

User.__str__ = lambda user: user.get_full_name() +' ('+ user.get_username()+')'

def user_action_link(self):
        update = reverse('mcl:users_update', args=[str(self.id)])

        return format_html(
                "<a class='btn btn-warning btn-sm' href='{eurl}'><i class='fas fa-edit'></i> Edit</a>",
                eurl=update
            )

User.add_to_class("action_link", user_action_link)

class Profile(models.Model):
    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True, null=True, verbose_name="Employee ID")
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    phone = models.CharField(max_length=50, null=True, verbose_name="Phone No")

    def __str__(self):
        return "{0} {1} ({2})".format(self.user.first_name, self.user.last_name, self.employee_id)


class UserSettings(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    item_limit = models.IntegerField(default=50, verbose_name="Item Per Page", choices=[
        (20, 20),
        (50, 50),
        (100, 100),
        (200, 200),
        (500, 500),
        (1000, 1000)
        ])

    def __str__(self):
        return self.user.username

SITE_ID_CHOICES = [
    ("main", "main"),
]
class SiteSettings(models.Model):
    site_id = models.CharField(max_length=50, choices=SITE_ID_CHOICES, default="main", editable=False)
    name = models.CharField(blank=True, null=True, max_length=100, default="App Name")
    title = models.CharField(blank=True, null=True, max_length=100, default="App Title")
    description = models.TextField(blank=True, null=True, default="Description")
    entry_last_date = models.PositiveIntegerField(verbose_name="Last Entry Date for BM", 
        null=True, help_text="eg. 10")

    def __str__(self):
        return self.name

    def save(self):
        count = SiteSettings.objects.all().count()
        save_permission = SiteSettings.has_add_permission(self)

        if count < 1:
            super(SiteSettings, self).save()
        elif save_permission:
            super(SiteSettings, self).save()

    def has_add_permission(self):
        return SiteSettings.objects.filter(id=self.id).exists()


class Category(models.Model):
    name_bn = models.CharField(max_length=500, null=True, verbose_name="Bangla Name")
    name_en = models.CharField(max_length=500, null=True, verbose_name="English Name")
    order = models.IntegerField(null=True)
    is_active = models.BooleanField(default=True, null=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name_en

    def action_link(self):
        update = reverse('mcl:category_update', args=[str(self.id)])

        return format_html(
                "<a class='btn btn-warning btn-sm' href='{eurl}'><i class='fas fa-edit'></i> Edit</a>",
                eurl=update
            )

class Topic(models.Model):
    name_bn = models.CharField(max_length=500, null=True, verbose_name="Bangla Name")
    name_en = models.CharField(max_length=500, null=True, verbose_name="English Name")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    order = models.IntegerField(null=True)

    def sample_image(self, filename):
        extension = "." + filename.split('.')[-1]
        filename = str(self.category) + "_" + str(self.name_en) + extension
        return os.path.join(str("sample_image"), filename)
        
    sample_image = models.ImageField(upload_to=sample_image, null=True, blank=True)

    def save(self, *args, **kwargs):
        try:
            this = Topic.objects.get(id=self.id)
            if this.sample_image != self.sample_image:
                this.sample_image.delete(save=False)
        except:
            pass  # when new photo then we do nothing, normal case
        super().save(*args, **kwargs)

    class Meta:
            verbose_name = 'Topic'
            verbose_name_plural = 'Topics'

    def __str__(self):
        return self.name_en

    def action_link(self):
        update = reverse('mcl:topic_update', args=[str(self.id)])

        return format_html(
                "<a class='btn btn-warning btn-sm' href='{eurl}'><i class='fas fa-edit'></i> Edit</a>",
                eurl=update
            )

class Area(models.Model):
    name = models.CharField(max_length=100, null=True, unique=True, verbose_name="Area Name", help_text="eg. CENTRAL-A")
    address = models.CharField(max_length=500, null=True)
    manager = models.OneToOneField(User, related_name='area_manager', null=True, on_delete=models.SET_NULL, verbose_name="Area Manager")
    is_active = models.BooleanField(default=True, null=True)

    class Meta:
            verbose_name = 'Area'
            verbose_name_plural = 'Areas'

    def __str__(self):
        return self.name
    
    def action_link(self):
        update = reverse('mcl:area_update', args=[str(self.id)])

        return format_html(
                "<a class='btn btn-warning btn-sm' href='{eurl}'><i class='fas fa-edit'></i> Edit</a>",
                eurl=update
            )

class District(models.Model):
    code = models.CharField(max_length=50, null=True, unique=True, help_text="eg. 1, 25")
    area = models.ForeignKey(Area, null=True, on_delete=models.PROTECT)
    address = models.CharField(max_length=500, null=True)
    manager = models.OneToOneField(User, related_name='district_manager', null=True, on_delete=models.SET_NULL, verbose_name="District Manager")
    is_active = models.BooleanField(default=True, null=True)

    class Meta:
            verbose_name = 'District'
            verbose_name_plural = 'Districts'

    def __str__(self):
        return self.code

    def action_link(self):
        update = reverse('mcl:district_update', args=[str(self.id)])

        return format_html(
                "<a class='btn btn-warning btn-sm' href='{eurl}'><i class='fas fa-edit'></i> Edit</a>",
                eurl=update
            )

class Site(models.Model):
    code = models.CharField(max_length=10, null=True, unique=True)
    district = models.ForeignKey(District, null=True, on_delete=models.PROTECT)
    address = models.CharField(max_length=300, null=True)
    manager = models.OneToOneField(User, related_name='site_manager', null=True, on_delete=models.SET_NULL, verbose_name="Site Manager")
    is_active = models.BooleanField(default=True, null=True)

    class Meta:
            verbose_name = 'Site'
            verbose_name_plural = 'Sites'

    def __str__(self):
        return self.code

    def action_link(self):
        update = reverse('mcl:site_update', args=[str(self.id)])

        return format_html(
                "<a class='btn btn-warning btn-sm' href='{eurl}'><i class='fas fa-edit'></i> Edit</a>",
                eurl=update
            )

class Comment(models.Model):
    comment = models.CharField(max_length=250, null=True)
    is_active = models.BooleanField(default=True, null=True)

    class Meta:
            verbose_name = 'Comment'
            verbose_name_plural = 'Comments'

    def __str__(self):
        return str(self.comment)

    def action_link(self):
        update = reverse('mcl:comment_update', args=[str(self.id)])

        return format_html(
                "<a class='btn btn-warning btn-sm' href='{eurl}'><i class='fas fa-edit'></i> Edit</a>",
                eurl=update
            )

class EntryList(models.Model):
    site = models.ForeignKey(Site, null=True, on_delete=models.PROTECT)
    otp = models.CharField(max_length=30, unique=True, null=True)
    comment_one = models.CharField(max_length=400, null=True, blank=True, verbose_name='Comment One')
    comment_two = models.CharField(max_length=400, null=True, blank=True, verbose_name='Comment Two')
    comment_three = models.CharField(max_length=400, null=True, blank=True, verbose_name='Comment Three')
    cust_comm = models.CharField(max_length=400, null=True, blank=True, verbose_name='Custom Comment')
    rem_comm = models.CharField(max_length=400, null=True, blank=True, verbose_name='Remarks Comment')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = CurrentUserField()
    updated_by = CurrentUserField(on_update=True, related_name='updated_by')

    class Meta:
            verbose_name = 'Entry List'
            verbose_name_plural = 'Entry Lists'

    def __str__(self):
        return f'{self.site} - {self.id}'
    
    def total_score(self):
        total_scr = CheckList.objects.filter(entry_list_id=self.id).aggregate(Sum('point'))
        return total_scr['point__sum']
    
    def action_link(self):
        update = reverse('mcl:entry_detail_update', args=[str(self.id)])
        # update = reverse('mcl:entry_detail', args=[str(self.id)])
        view = reverse('mcl:entry_detail', args=[str(self.id)])
        return format_html(
                "<a class='btn btn-primary btn-sm' href='{vurl}'><i class='fas fa-info-circle'></i> View</a> <a class='btn btn-warning btn-sm' href='{eurl}'><i class='fas fa-edit'></i> Edit</a>",
                eurl=update, vurl=view
            )
    
    def view_link(self):
        view = reverse('mcl:entry_detail_bn', args=[str(self.id)])
        return format_html(
                "<a class='btn btn-primary btn-sm' href='{vurl}'><i class='fas fa-info-circle'></i> View</a>",
                vurl=view
            )

    def resubmit_link(self):
        resubmit = reverse('mcl:resubmit_entry', args=[str(self.id)])
        return format_html(
                "<a class='btn btn-danger btn-sm' href='{surl}'><i class='fas fa-undo'></i> Resubmit</a>",
                surl=resubmit
            )


class EntryImage(models.Model):
    
    def file_dir(self, filename):
        extension = "." + filename.split('.')[-1]
        filename = str(self.entry.id) + extension
        return os.path.join(str("entry_image"), filename)

    entry=models.ForeignKey(EntryList,on_delete=models.CASCADE, related_name='entryimage', null=True, blank=True)
    image = models.ImageField(upload_to=file_dir, null=True, blank=True)
    

class CheckList(models.Model):
    entry_list = models.ForeignKey(EntryList, null=True, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, null=True, on_delete=models.PROTECT)
    point = models.CharField(max_length=10, null=True)
    point_cat = models.CharField(max_length=10, null=True)
    
    def image_dir(self, filename):
        extension = "." + filename.split('.')[-1]
        filename = str(self.entry_list) + "_" + str(self.id) + "_" + str(self.topic) + extension
        return os.path.join(str("topic_image"), filename)
        
    # topic_image = models.ImageField(upload_to=image_dir, null=True, blank=True)
    topic_image = ResizedImageField(upload_to=image_dir, null=True, blank=True)

    class Meta:
            verbose_name = 'Check List'
            verbose_name_plural = 'Check Lists'

    def __str__(self):
        return str(self.entry_list)