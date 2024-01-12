import json
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import make_password
from django.forms import inlineformset_factory
from django.shortcuts import redirect, render
from django.db.models import Count
import requests
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from .models import Profile, UserSettings, Category, Topic, EntryList, CheckList, Area, District, Site, Comment
from .models import SiteSettings, EntryImage
from django.shortcuts import get_object_or_404
import geopy.distance
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.forms import PasswordChangeForm
from .forms import LoginForm, UserSettingsForm, CategoryForm, TopicForm, CommentForm, AreaForm, DistrictForm, SiteForm
from .forms import UserForm, UserCreateForm, ProfileForm, SiteSettingsForm
from .tables import EntryListTable, CategoryTable, TopicTable, AreaTable, CommentTable, DistrictTable, SiteTable
from .tables import UserTable
from .filters import EntryListFilter, CategoryFilter, TopicFilter, AreaFilter, CommentFilter, DistrictFilter, SiteFilter
from .filters import UserFilter
from django_tables2 import MultiTableMixin, RequestConfig, SingleTableMixin, SingleTableView
from django.db import connection
from django.db.models import IntegerField, Sum, Case, When, Count, Avg, F, ExpressionWrapper, FloatField, Subquery, Value, OuterRef, Max
from django.db.models.functions import Coalesce
from django.db.models import CharField
import uuid
from django.core.exceptions import ValidationError
import os
from django.core.mail import send_mail, EmailMultiAlternatives, EmailMessage
import pandas as pd
from datetime import datetime, timedelta
import shutil
from django.http import FileResponse


def handle_404(request, exception):
    context = {}
    return render(request, 'mcl/404.html', context)


def handle_500(request, exception=None):
    context = {}
    return render(request, 'mcl/500.html', context)


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

# Check whether user is superuser or member of Admin group


def user_superuser_or_admin(user):
    if user.is_superuser or user.groups.filter(name="Admin"):
        return True
    else:
        return False


@login_required
def not_authorized(request):
    msg = "You are not authorized to view this page."
    page = request.GET.get('next')
    return render(request, "mcl/error.html", {'context': msg, 'page': page})


def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return HttpResponseRedirect(next_url)
                else:
                    return redirect('mcl:dashboard')
            else:
                messages.warning(
                    request, "Username or Password is Incorrect !")

    return render(request, 'mcl/login.html', context={'form': form})

# Password reset


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'mcl/password_reset.html'
    email_template_name = 'mcl/password_reset_email.html'
    subject_template_name = 'mcl/password_reset_subject.txt'
    success_message = "We have sent you a email with password reset instruction." \
        " If you don't see the email please check your spam folder."
    success_url = reverse_lazy('mcl:password_reset')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password successfully changed!')
            return redirect('mcl:change_password')
        else:
            messages.warning(request, 'Please correct the errors below !')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'mcl/change_password.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out !")
    return redirect("mcl:login")


@login_required
def dashboard(request):
    context = {}
    category_id = 2
    category = get_object_or_404(Category, id=category_id)
    category_name = category.name_en
    area_count = Area.objects.filter(is_active=True).count()
    site_count = Site.objects.filter(is_active=True).count()
    user_count = User.objects.filter(is_active=True).count()
    category_count = Category.objects.filter(is_active=True).count()
    entry_count = EntryList.objects.all().count()
    topic_count = Topic.objects.filter(category_id=category_id).count()
    checkList_count = CheckList.objects.values('entry_list_id').annotate(
        total_score=Sum(
            Case(
                # If point is less than 5, set total_score to 0
                When(point__lt=5, then=0),
                # If point is None, set total_score to 0
                When(point__isnull=True, then=0),
                # Otherwise, use the actual point value
                default=F('point'),
                output_field=IntegerField()
            ))).exclude(total_score__gte=5).count()  # Exclude the entries with total_score=0
    
    context['category_name'] = category_name
    context['area_count'] = area_count
    context['site_count'] = site_count
    context['user_count'] = user_count
    context['category_count'] = category_count
    context['entry_count'] = entry_count
    context['topic_count'] = topic_count
    context['checkList_count'] = checkList_count
    
    return render(request, 'mcl/dashboard.html', context)

@login_required
def dashboard_old(request):
    context = {}
    area_count = Area.objects.filter(is_active=True).count()
    site_count = Site.objects.filter(is_active=True).count()
    entry_count = EntryList.objects.all().count()
    user_count = User.objects.filter(is_active=True).count()
    category_count = Category.objects.filter(is_active=True).count()
    category_id = 2
    category = get_object_or_404(Category, id=category_id)
    category_name = category.name_en
    print(category_name)
    topic_count = Topic.objects.filter(category_id=category_id).count()
    checkList_count = CheckList.objects.values('entry_list_id').annotate(
        total_score=Sum(
            Case(
                # If point is less than 5, set total_score to 0
                When(point__lt=5, then=0),
                # If point is None, set total_score to 0
                When(point__isnull=True, then=0),
                # Otherwise, use the actual point value
                default=F('point'),
                output_field=IntegerField()
            ))).exclude(total_score__gte=5).count()  # Exclude the entries with total_score=0

    context['area_count'] = area_count
    context['site_count'] = site_count
    context['user_count'] = user_count
    context['entry_count'] = entry_count
    context['category_count'] = category_count
    context['category_name'] = category_name
    context['topic_count'] = topic_count
    context['checkList_count'] = checkList_count

    # Check if user is admin
    if request.user.is_superuser or request.user.groups.filter(name="Admin"):
        # Entry Line Graph Datewise
        admin_line_chart = EntryList.objects.values('created_at__date').order_by(
            'created_at__date').annotate(count=Count('id'))
        context['entryLineChartadmin'] = admin_line_chart

        # Entry Donut Graph Areawise


    # Check if user is area manger
    try:
        # Entry Line Chart
        area_manager = Area.objects.get(manager_id=request.user.id)
        am_line_chart = EntryList.objects.filter(site__district__area=area_manager.id).values(
            'created_at__date').order_by('created_at__date').annotate(count=Count('id'))
        context['entryLineChartam'] = am_line_chart

        # Entry Donut Graph Districtwise
        am_doughnut_chart = EntryList.objects.filter(site__district__area=area_manager.id).values(
            'site__district__code').order_by('site__district__code').annotate(count=Count('id'))
        context['entryChartDoughnutam'] = am_doughnut_chart
    except:
        pass

    # Check if user is district manger
    try:
        # Entry Line Chart
        dist_manager = District.objects.get(manager_id=request.user.id)
        dm_line_chart = EntryList.objects.filter(site__district=dist_manager.id).values(
            'created_at__date').order_by('created_at__date').annotate(count=Count('id'))
        context['entryLineChartdm'] = dm_line_chart

        # Entry Donut Graph Districtwise
        dm_doughnut_chart = EntryList.objects.filter(site__district=dist_manager.id).values(
            'site__code').order_by('site__code').annotate(count=Count('id'))
        context['entryChartDoughnutdm'] = dm_doughnut_chart
    except:
        pass

    # Check if user is site manger

    return render(request, 'mcl/dashboard.html', context)


@login_required
def report(request):
    context = {}

    # Checklist Entry for the current month
    today = datetime.now()
    entrylist_entries = EntryList.objects.filter(
        created_at__month=today.month,
    )

    result = entrylist_entries.values(
        'site__code',
        'site__district__code',
        'site__district__area__name',
        'id',
        'checklist__topic__name_en',
        'checklist__topic',
        'checklist__topic__category__name_en',
        'checklist__point'
    )
    if result:
        df = pd.DataFrame(result)
        df['Serial'] = range(1, len(df) + 1)

        df = df.rename(columns={'site__code': 'Shop Code'})
        df = df.rename(columns={'site__district__code': 'District Name'})
        df = df.rename(columns={'site__district__area__name': 'Area Name'})
        df = df.rename(columns={'id': 'Entry List'})
        df = df.rename(columns={'checklist__topic__name_en': 'Topic Name'})
        df = df.rename(columns={'checklist__topic': 'Question'})
        df = df.rename(
            columns={'checklist__topic__category__name_en': 'Category Name'})
        df = df.rename(columns={'checklist__point': 'Point'})
        grouped_df = df.groupby(['Area Name', 'District Name', 'Entry List',
                                'Shop Code', 'Category Name', 'Topic Name'])['Point'].sum().reset_index()
        pivot_table = grouped_df.pivot_table('Point', [
                                             'Area Name', 'District Name', 'Entry List', 'Shop Code'], ['Category Name', 'Topic Name'])
        # pivot_table = df.pivot_table('Point', ['Entry List', 'Shop Code','District Name','Area Name'], ['Category Name','Topic Name'])
        pivot_table['Total Score'] = pivot_table.sum(axis=1)
        pivot_table = pivot_table.sort_values('Total Score', ascending=False)

        final_table = pivot_table.to_html()
        row_count = len(pivot_table)

        # Generate CSV
        # csv_filename = str(uuid.uuid4())[:8]
        csv_filename = 'cur_entry_report'
        pivot_table.to_csv(settings.MEDIA_ROOT +
                           '/reports/' + csv_filename + '.csv')
        cur_csv_file = settings.MEDIA_URL + '/reports/' + csv_filename + '.csv'

    else:
        final_table = "<h1>No data found !</h1>"
        cur_csv_file = ""
        row_count = 0

    # Checklist Entry for the Last month
    lastmonth_date = today - timedelta(days=today.day)
    lastmonth = lastmonth_date.strftime("%m")
    lastmonth_entrylist_entries = EntryList.objects.filter(
        created_at__month=lastmonth,
    )

    lastmonth_result = lastmonth_entrylist_entries.values(
        'site__code',
        'site__district__code',
        'site__district__area__name',
        'id',
        'checklist__topic__name_en',
        'checklist__topic',
        'checklist__topic__category__name_en',
        'checklist__point'
    )
    if lastmonth_result:
        df = pd.DataFrame(lastmonth_result)
        df['Serial'] = range(1, len(df) + 1)

        df = df.rename(columns={'site__code': 'Shop Code'})
        df = df.rename(columns={'site__district__code': 'District Name'})
        df = df.rename(columns={'site__district__area__name': 'Area Name'})
        df = df.rename(columns={'id': 'Entry List'})
        df = df.rename(columns={'checklist__topic__name_en': 'Topic Name'})
        df = df.rename(columns={'checklist__topic': 'Question'})
        df = df.rename(
            columns={'checklist__topic__category__name_en': 'Category Name'})
        df = df.rename(columns={'checklist__point': 'Point'})
        pivot_table = df.pivot_table('Point', ['Entry List', 'Shop Code', 'District Name', 'Area Name'], [
                                     'Category Name', 'Topic Name'])
        pivot_table['Total Score'] = pivot_table.sum(axis=1)
        pivot_table = pivot_table.sort_values('Total Score', ascending=False)

        final_table = pivot_table.to_html()
        row_count = len(pivot_table)

        # Generate CSV
        # csv_filename = str(uuid.uuid4())[:8]
        csv_filename = 'last_entry_report'
        pivot_table.to_csv(settings.MEDIA_ROOT +
                           '/reports/' + csv_filename + '.csv')
        last_csv_file = settings.MEDIA_URL + '/reports/' + csv_filename + '.csv'

    else:
        final_table = "<h1>No data found !</h1>"
        last_csv_file = ""
        row_count = 0

    shops = Site.objects.values_list('code', flat=True)
    districts = District.objects.values_list('code', flat=True)
    areas = Area.objects.values_list('name', flat=True)

    context = {
        'areas': areas,
        'districts': districts,
        'shops': shops,
        'cur_csv_file': cur_csv_file,
        'last_csv_file': last_csv_file,
    }

    return render(request, 'mcl/report.html', context)


@login_required
def download_images(request):
    context = {}
    # parameter_value={}
    # parameter_value = request.POST.get('sample_topic_images')
    # print(parameter_value)

    # sample_topic_images
    if request.method == 'POST' and 'sample_topic_images' in request.POST:
        instances = Topic.objects.all()
        # download_dir = os.path.join(settings.MEDIA_ROOT + '/download/', 'checklist_entry_images')
        download_dir = os.path.join(
            settings.MEDIA_ROOT + '/download/', 'sample_topic_images')
        os.makedirs(download_dir, exist_ok=True)
        for instance in instances:
            if instance.sample_image:
                image_path = instance.sample_image.path
                image_filename = os.path.basename(image_path)
                new_image_path = os.path.join(download_dir, image_filename)
                shutil.copy(image_path, new_image_path)
        shutil.make_archive(download_dir, 'zip', download_dir)
        zip_filepath = os.path.join(download_dir + '.zip')
        topic_image_filename = os.path.basename(zip_filepath)
        response = FileResponse(open(zip_filepath, 'rb'),
                                content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(zip_filepath)}"'
        # context = {
        #     'zip_filepath': zip_filepath,
        #     'download_response': response,
        #     'topic_image_filename': topic_image_filename}
        return response

    # checklist_entry_images
    elif request.method == 'POST' and 'checklist_entry_images' in request.POST:
        instances = CheckList.objects.all()
        download_dir = os.path.join(
            settings.MEDIA_ROOT + '/download/', 'checklist_entry_images')
        os.makedirs(download_dir, exist_ok=True)
        for instance in instances:
            if instance.topic_image:
                image_path = instance.topic_image.path
                image_filename = os.path.basename(image_path)
                new_image_path = os.path.join(download_dir, image_filename)
                shutil.copy(image_path, new_image_path)
        shutil.make_archive(download_dir, 'zip', download_dir)
        zip_filepath = os.path.join(download_dir + '.zip')
        checklist_image_filename = os.path.basename(zip_filepath)
        response = FileResponse(open(zip_filepath, 'rb'),
                                content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(zip_filepath)}"'
        # context = {
        #     'zip_filepath': zip_filepath,
        #     'download_response': response,
        #     'topic_image_filename': topic_image_filename}
        return response

    return render(request, 'mcl/url/download_images.html', context)


@login_required
def report_result(request):
    context = {}
    final_table = ""
    # final_site_codes = ""
    row_count = ""
    csv_file = ""

    if request.method == 'POST':

        from_date = request.POST.get('from_date')
        # to_date = request.POST.get('to_date')
        # Add one day to to_date
        get_date = request.POST.get('to_date')
        my_date = datetime.strptime(get_date, '%Y-%m-%d')
        to_date = my_date + timedelta(days=1)
        # from_date_str = request.POST.get('from_date')
        # to_date_str = request.POST.get('to_date')
        # from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
        # to_date = datetime.strptime(to_date_str, '%Y-%m-%d')

        option = request.POST.get('option')
        shop_code = request.POST.getlist('shops')
        district_code = request.POST.getlist('districts')
        area_code = request.POST.getlist('areas')
        # areas = Area.objects.filter(name__in=area_code)
        # area_ids = areas.values_list('id', flat=True)
        # print(area_code)

        if 'tot_sum_rep' in option:
            # Filter EntryList entries based on the provided parameters
            entrylist_entries = EntryList.objects.filter(
                created_at__range=[from_date, to_date],
            )

            if shop_code:
                entrylist_entries = entrylist_entries.filter(
                    site__code__in=shop_code)
            if district_code:
                entrylist_entries = entrylist_entries.filter(
                    site__district__code__in=district_code)
            if area_code:
                entrylist_entries = entrylist_entries.filter(
                    site__district__area__name__in=area_code)

            result = entrylist_entries.values(
                'site__code',
                'id',
                'created_by__profile__designation',
                'checklist__topic__name_en',
                'checklist__topic',
                'checklist__topic__category__name_en',
                'checklist__point'
            )

            # Filter CheckList entries based on the provided parameters
            # checklist_entries = CheckList.objects.filter(
            #     entry_list__created_at__range=[from_date, to_date]
            # )

            # if shop_code:
            #     checklist_entries = checklist_entries.filter(entry_list__site__code__in=shop_code)
            # if district_code:
            #     checklist_entries = checklist_entries.filter(entry_list__site__district__code__in=district_code)
            # if area_code:
            #     checklist_entries = checklist_entries.filter(entry_list__site__district__area__name__in=area_code)

            # result = checklist_entries.values(
            #     'entry_list__site__code',
            #     'entry_list',
            #     'topic__name_en',
            #     'topic',
            #     'topic__category__name_en',
            #     'point'
            # )

            if result:
                df = pd.DataFrame(result)
                df['Serial'] = range(1, len(df) + 1)

                df = df.rename(columns={'site__code': 'Shop Code'})
                df = df.rename(columns={'id': 'Entry List'})
                df = df.rename(
                    columns={'created_by__profile__designation': 'Designation'})
                df = df.rename(
                    columns={'checklist__topic__name_en': 'Topic Name'})
                df = df.rename(columns={'checklist__topic': 'Question'})
                df = df.rename(
                    columns={'checklist__topic__category__name_en': 'Category Name'})
                df = df.rename(columns={'checklist__point': 'Point'})
                # pivot_table = df.pivot_table(
                #     values='Point',  # Values to be filled in the cells
                #     index=['Entry List', 'Shop Code'],  # Rows
                #     columns=['Category Name', 'Topic Name'],  # Columns
                #     aggfunc='sum',  # Use the 'sum' function to aggregate the 'Point' values
                #     fill_value=0  # Fill missing values with 0
                # )
                pivot_table = df.pivot_table('Point', ['Designation', 'Entry List', 'Shop Code'], [
                                             'Category Name', 'Topic Name'])
                # Calculate the total sum for each column
                pivot_table['Total Score'] = pivot_table.sum(axis=1)
                pivot_table = pivot_table.sort_values(
                    'Total Score', ascending=False)

                # Add a Serial column with sequential numbers
                # pivot_table.insert(0, 'Serial', range(1, len(pivot_table) + 1))
                # pivot_table.insert(1, 'Total Score', ['Total Score'])

                final_table = pivot_table.to_html()
                row_count = len(pivot_table)

                # Generate CSV
                csv_filename = str(uuid.uuid4())[:8]
                pivot_table.to_csv(settings.MEDIA_ROOT +
                                   '/reports/' + csv_filename + '.csv')
                csv_file = settings.MEDIA_URL + '/reports/' + csv_filename + '.csv'

            else:
                final_table = "<h1>No data found !</h1>"
                csv_file = ""
                row_count = 0

        # area_sub_rep
        elif 'area_sub_rep' in option:
            # Get the latest entry for each site within the date range
            # latest_entries = EntryList.objects.filter(
            #     created_at__range=[from_date, to_date]
            # ).order_by('-created_at')

            # # Query to get the latest entry for each site
            # latest_entry_subquery = latest_entries.values('site').annotate(latest_entry_id=Subquery(latest_entries.values('id')[:1]))

            # # Fetch the latest entries
            # site_submissions = EntryList.objects.filter(id__in=Subquery(latest_entry_subquery.values('latest_entry_id')))
            # Get the last entries for each site
            last_entries = EntryList.objects.values('site').annotate(
                max_created_at=Max('created_at')
            ).order_by().values('site', 'max_created_at')

            last_entry_ids = EntryList.objects.filter(
                created_at__in=Subquery(last_entries.values('max_created_at'))
            ).values('site').annotate(
                last_entry_id=Max('id')
            )

            site_submissions = EntryList.objects.filter(
                id__in=Subquery(last_entry_ids.values('last_entry_id'))
            )
            if shop_code:
                site_submissions = site_submissions.filter(
                    site__code__in=shop_code)
            if district_code:
                site_submissions = site_submissions.filter(
                    site__district__code__in=district_code)
            if area_code:
                site_submissions = site_submissions.filter(
                    site__district__area__name__in=area_code)

            site_submissions = site_submissions.values('site__district__area').annotate(
                total_submissions=Count('id')
            )
            # Get the latest entry IDs for each site within the date range
            latest_entry_ids = last_entry_ids.values('last_entry_id')

            # Get the site scores for the latest entries
            site_scores = CheckList.objects.filter(
                entry_list__id__in=latest_entry_ids,
                entry_list__created_at__range=[from_date, to_date]
            )

            if shop_code:
                site_scores = site_scores.filter(
                    entry_list__site__code__in=shop_code)
            if district_code:
                site_scores = site_scores.filter(
                    entry_list__site__district__code__in=district_code)
            if area_code:
                site_scores = site_scores.filter(
                    entry_list__site__district__area__name__in=area_code)

            site_scores = site_scores.values('entry_list__site__code').annotate(
                total_score=Coalesce(
                    Sum('point', output_field=FloatField()), Value(0.0))
            )

            site_scores_subquery = site_scores.filter(
                entry_list__site__code=OuterRef('site__code')).values('total_score')[:1]

            # Total Shop Count
            filtered_sites = Site.objects.all()
            if shop_code:
                filtered_sites = filtered_sites.filter(code__in=shop_code)
            if district_code:
                filtered_sites = filtered_sites.filter(
                    district__code__in=district_code)
            if area_code:
                filtered_sites = filtered_sites.filter(
                    district__area__name__in=area_code)

            number_of_sites = filtered_sites.count()

            # Combine the two queries to get the desired results
            result = site_submissions.annotate(
                # site_count=Coalesce(Subquery(number_of_sites), Value(0.0)),
                site_count=Value(number_of_sites, output_field=FloatField()),
                total_score=Coalesce(
                    Subquery(site_scores_subquery), Value(0.0)),
                average_score=ExpressionWrapper(
                    F('total_score') * 1.0 / F('total_submissions'),
                    output_field=FloatField(),
                ),
                submission_percentage=ExpressionWrapper(
                    (F('total_submissions') / \
                     Value(number_of_sites, output_field=FloatField())) * 100,
                    output_field=FloatField(),
                )
            )

            if result:
                df = pd.DataFrame(result)
                # df['Serial'] = range(1, len(df) + 1)
                # df = df.rename(columns = {'site__code':'Shop Code'})
                df = df.rename(columns={'site_count': 'Total Shop'})
                df = df.rename(columns={'site__district__area': 'Area Name'})
                df = df.rename(
                    columns={'total_submissions': 'Total Submissions'})
                df = df.rename(
                    columns={'submission_percentage': 'Submissions Percentage %'})
                df = df.rename(columns={'total_score': 'Total Score'})
                df = df.rename(columns={'average_score': 'Average Score'})
                pivot_table = df.pivot_table(
                    index=['Area Name', 'Total Shop'],
                    values=['Total Submissions', 'Submissions Percentage %',
                            'Total Score', 'Average Score'],
                    aggfunc={'Total Submissions': 'sum', 'Submissions Percentage %': 'sum',
                             'Total Score': 'sum', 'Average Score': 'mean'},
                ).reset_index()

                pivot_table = pivot_table[['Area Name', 'Total Shop', 'Total Submissions',
                                           'Submissions Percentage %', 'Total Score', 'Average Score']]

                # pivot_table = pd.pivot_table(df, index=['Serial','Area Name','Total Shop'], fill_value=0)
                # pivot_table = pivot_table[['Total Submissions', 'Submissions Percentage %', 'Total Score', 'Average Score']]

                final_table = pivot_table.to_html()
                row_count = len(pivot_table)

                # Generate CSV
                csv_filename = str(uuid.uuid4())[:8]
                pivot_table.to_csv(settings.MEDIA_ROOT +
                                   '/reports/' + csv_filename + '.csv')
                csv_file = settings.MEDIA_URL + '/reports/' + csv_filename + '.csv'

            else:
                final_table = "<h1>No data found !</h1>"
                csv_file = ""
                row_count = 0

        # dist_sub_rep
        elif 'dist_sub_rep' in option:
            # Get the latest entry for each site within the date range
            # latest_entries = EntryList.objects.filter(
            #     created_at__range=[from_date, to_date]
            # ).order_by('-created_at')

            # # Query to get the latest entry for each site
            # latest_entry_subquery = latest_entries.values('site').annotate(latest_entry_id=Subquery(latest_entries.values('id')[:1]))

            # # Fetch the latest entries
            # site_submissions = EntryList.objects.filter(id__in=Subquery(latest_entry_subquery.values('latest_entry_id')))

            last_entries = EntryList.objects.values('site').annotate(
                max_created_at=Max('created_at')
            ).order_by().values('site', 'max_created_at')

            last_entry_ids = EntryList.objects.filter(
                created_at__in=Subquery(last_entries.values('max_created_at'))
            ).values('site').annotate(
                last_entry_id=Max('id')
            )

            site_submissions = EntryList.objects.filter(
                id__in=Subquery(last_entry_ids.values('last_entry_id'))
            )
            if shop_code:
                site_submissions = site_submissions.filter(
                    site__code__in=shop_code)
            if district_code:
                site_submissions = site_submissions.filter(
                    site__district__code__in=district_code)
            if area_code:
                site_submissions = site_submissions.filter(
                    site__district__area__name__in=area_code)

            # site_submissions = site_submissions.values('site__district__code').annotate(
            #     total_submissions=Count('id')
            # )

            # # Get the latest entry IDs for each site within the date range
            # latest_entry_ids = latest_entry_subquery.values('latest_entry_id')

            # # Get the site scores for the latest entries
            # site_scores = CheckList.objects.filter(
            #     entry_list__id__in=latest_entry_ids,
            #     entry_list__created_at__range=[from_date, to_date]
            # )

            site_submissions = site_submissions.values('site__district__code').annotate(
                total_submissions=Count('id')
            )
            # Get the latest entry IDs for each site within the date range
            latest_entry_ids = last_entry_ids.values('last_entry_id')

            # Get the site scores for the latest entries
            site_scores = CheckList.objects.filter(
                entry_list__id__in=latest_entry_ids,
                entry_list__created_at__range=[from_date, to_date]
            )

            if shop_code:
                site_scores = site_scores.filter(
                    entry_list__site__code__in=shop_code)
            if district_code:
                site_scores = site_scores.filter(
                    entry_list__site__district__code__in=district_code)
            if area_code:
                site_scores = site_scores.filter(
                    entry_list__site__district__area__name__in=area_code)

            # Combine the two queries to get the desired results
            # result = site_submissions.annotate(
            #     total_score=Coalesce(Subquery(site_scores.filter(entry_list__site__code=OuterRef('site__code')).values('total_score')), Value(0.0)),
            #     average_score=ExpressionWrapper(F('total_score') / F('total_submissions'), output_field=FloatField())
            # )

            site_scores = site_scores.values('entry_list__site__code').annotate(
                total_score=Coalesce(
                    Sum('point', output_field=FloatField()), Value(0.0))
            )

            site_scores_subquery = site_scores.filter(
                entry_list__site__code=OuterRef('site__code')).values('total_score')[:1]

            # Total Shop Count
            filtered_sites = Site.objects.all()
            if shop_code:
                filtered_sites = filtered_sites.filter(code__in=shop_code)
            if district_code:
                filtered_sites = filtered_sites.filter(
                    district__code__in=district_code)
            if area_code:
                filtered_sites = filtered_sites.filter(
                    district__area__name__in=area_code)

            number_of_sites = filtered_sites.count()

            # Combine the two queries to get the desired results
            result = site_submissions.annotate(
                # site_count=Coalesce(Subquery(number_of_sites), Value(0.0)),
                site_count=Value(number_of_sites, output_field=FloatField()),
                total_score=Coalesce(
                    Subquery(site_scores_subquery), Value(0.0)),
                average_score=ExpressionWrapper(
                    F('total_score') * 1.0 / F('total_submissions'),
                    output_field=FloatField(),
                ),
                submission_percentage=ExpressionWrapper(
                    (F('total_submissions') / \
                     Value(number_of_sites, output_field=FloatField())) * 100,
                    output_field=FloatField(),
                )
            )

            if result:
                df = pd.DataFrame(result)
                df['Serial'] = range(1, len(df) + 1)
                # df = df.rename(columns = {'site__code':'Shop Code'})
                df = df.rename(columns={'site_count': 'Total Shop'})
                df = df.rename(
                    columns={'site__district__code': 'District Name'})
                df = df.rename(
                    columns={'total_submissions': 'Total Submissions'})
                df = df.rename(
                    columns={'submission_percentage': 'Submissions Percentage %'})
                df = df.rename(columns={'total_score': 'Total Score'})
                df = df.rename(columns={'average_score': 'Average Score'})
                # pivot_table = pd.pivot_table(df, values=['Total Shop','Total Submissions', 'Submissions Percentage %', 'Total Score', 'Average Score'],  index=['Serial','District Name'], fill_value=0)
                # pivot_table = pivot_table[['Total Shop','Total Submissions', 'Submissions Percentage %', 'Total Score', 'Average Score']]

                pivot_table = df.pivot_table(
                    index=['District Name', 'Total Shop'],
                    values=['Total Submissions', 'Submissions Percentage %',
                            'Total Score', 'Average Score'],
                    aggfunc={'Total Submissions': 'sum', 'Submissions Percentage %': 'sum',
                             'Total Score': 'sum', 'Average Score': 'mean'},
                ).reset_index()

                pivot_table = pivot_table[['District Name', 'Total Shop', 'Total Submissions',
                                           'Submissions Percentage %', 'Total Score', 'Average Score']]

                # Add additional columns to the pivot table
                # pivot_table['Site Code'] = entry['site__code']
                # pivot_table['District Name'] = entry['site__district__code']
                # pivot_table.insert(0, 'District Name', entry['site__district__code'])
                # pivot_table.insert(0, 'Total Submissions', entry['total_submissions'])
                # pivot_table.insert(1, 'Total Score', entry['total_score'])
                # pivot_table.insert(2, 'Average Score', entry['average_score'])
                # pivot_table['Total Submissions'] = entry['total_submissions']
                # pivot_table['Total Score'] = entry['total_score']
                # pivot_table['Average Score (%)'] = entry['average_score']

                final_table = pivot_table.to_html()
                row_count = len(pivot_table)

                # Generate CSV
                csv_filename = str(uuid.uuid4())[:8]
                pivot_table.to_csv(settings.MEDIA_ROOT +
                                   '/reports/' + csv_filename + '.csv')
                csv_file = settings.MEDIA_URL + '/reports/' + csv_filename + '.csv'

            else:
                final_table = "<h1>No data found !</h1>"
                csv_file = ""
                row_count = 0

        # checklist_entry_images
        elif 'checklist_entry_images' in option:
            entry_list_ids = EntryList.objects.filter(
                created_at__range=[from_date, to_date]
            ).values_list('id', flat=True)
            checklist_data = CheckList.objects.filter(
                entry_list_id__in=entry_list_ids
            ).annotate(total_score=Sum('point'))

            zip_filename = str(uuid.uuid4())[:8]
            download_dir = os.path.join(
                settings.MEDIA_ROOT + '/download/', 'checklist_entry_images_'+zip_filename)
            os.makedirs(download_dir, exist_ok=True)
            for instance in checklist_data:
                if instance.topic_image:
                    image_path = instance.topic_image.path
                    image_filename = os.path.basename(image_path)
                    new_image_path = os.path.join(download_dir, image_filename)
                    shutil.copy(image_path, new_image_path)
            shutil.make_archive(download_dir, 'zip', download_dir)
            zip_filepath = os.path.join(download_dir + '.zip')
            checklist_image_filename = os.path.basename(zip_filepath)
            response = FileResponse(
                open(zip_filepath, 'rb'), content_type='application/zip')
            response[
                'Content-Disposition'] = f'attachment; filename="{os.path.basename(zip_filepath)}"'
            # Delete the created zip file after download
            # response.streaming_callback = lambda streaming_response: os.remove(zip_filepath)
            # context = {
            #     'zip_filepath': zip_filepath,
            #     'download_response': response,
            #     'topic_image_filename': topic_image_filename}

            return response
        else:
            # Create a case expression to handle different options
            case_expression = Case(
                When(option='sum_rep', then=Value('Summary Report')),
                When(option='det_rep', then=Value('Details Report')),
                When(option='checklist_entry_images',
                     then=Value('Checklist Entry Images')),
                default=Value('')
            )

            # Calculate the total number of submissions per site
            site_submissions = EntryList.objects.filter(
                created_at__range=[from_date, to_date]
            )
            if shop_code:
                site_submissions = site_submissions.filter(
                    site__code__in=shop_code)
            if district_code:
                site_submissions = site_submissions.filter(
                    site__district__code__in=district_code)
            if area_code:
                site_submissions = site_submissions.filter(
                    site__district__area__in=area_code)

            site_submissions = site_submissions.values('site__code', 'site__district__area').annotate(
                total_submissions=Count('id')
            )

            # Calculate the total score per site
            site_scores = CheckList.objects.filter(
                entry_list__site__is_active=True,
                entry_list__created_at__range=[from_date, to_date]
            )
            if shop_code:
                site_scores = site_scores.filter(
                    entry_list__site__code__in=shop_code)
            if district_code:
                site_scores = site_scores.filter(
                    entry_list__site__district__code__in=district_code)
            if area_code:
                site_scores = site_scores.filter(
                    entry_list__site__district__area__in=area_code)

            site_scores = site_scores.values('entry_list__site__code').annotate(
                total_score=Coalesce(
                    Sum('point', output_field=FloatField()), Value(0.0))
            )

            # Combine the two queries to get the desired results
            result = site_submissions.annotate(
                total_score=Coalesce(Subquery(site_scores.filter(
                    entry_list__site__code=OuterRef('site__code')).values('total_score')), Value(0.0)),
                average_score=ExpressionWrapper(
                    F('total_score') / F('total_submissions'), output_field=FloatField()) * 100,
                report_type=case_expression
            )

            for entry in result:
                print(
                    "Report Type:", entry['report_type'],
                    "Site Code:", entry['site__code'],
                    "Area:", entry['site__district__area'],
                    "Total Submissions:", entry['total_submissions'],
                    "Total Score:", entry['total_score'],
                    "Average Score (%):", entry['average_score']
                )

            if result:
                df = pd.DataFrame(result)

                pivot_table = pd.pivot_table(df, values='total_score', index=[
                                             'site__code'], fill_value=0)

                # Add additional columns to the pivot table
                # pivot_table['Site Code'] = entry['entry_list__site__code']
                # pivot_table['Area'] = entry['entry_list__site__district__area']
                # pivot_table['Total Submissions'] = entry['total_submissions']
                # pivot_table['Total Score'] = entry['total_score']
                # pivot_table['Average Score (%)'] = entry['average_score']

                final_table = pivot_table.to_html()
                row_count = len(pivot_table)

                # Generate CSV
                csv_filename = str(uuid.uuid4())[:8]
                pivot_table.to_csv(settings.MEDIA_ROOT +
                                   '/reports/' + csv_filename + '.csv')
                csv_file = settings.MEDIA_URL + '/reports/' + csv_filename + '.csv'

            else:
                final_table = "<h1>No data found !</h1>"
                csv_file = ""
                row_count = 0

        context = {'df': final_table, 'row_count': row_count, 'csv_file': csv_file, 'form_date': from_date,
                   'to_date': get_date, 'area_code': area_code, 'district_code': district_code, 'shop_code': shop_code, 'option': option}

        return render(request, 'mcl/report_result.html', context)
    else:
        return redirect('mcl:dashboard')


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def site_settings(request):

    obj = get_object_or_404(SiteSettings, site_id='main')
    form = SiteSettingsForm(request.POST or None, instance=obj)
    context = {}
    if form.is_valid():
        form.save()
        messages.success(request, "Site Settings has been updated !")
        return redirect('mcl:site_settings')
    context['form'] = form
    context['obj'] = obj

    return render(request, "mcl/site_settings.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def users_add(request):
    user = User()
    user_form = UserCreateForm(instance=user)
    ProfileInlineFormSet = inlineformset_factory(
        User, Profile, form=ProfileForm, can_delete=False)

    if request.method == "POST":
        user_form = UserCreateForm(request.POST)
        formset = ProfileInlineFormSet(request.POST, request.FILES)

        if user_form.is_valid():
            created_user = user_form.save(commit=False)
            created_user.password = make_password(
                user_form.cleaned_data['password'])
            formset = ProfileInlineFormSet(
                request.POST, request.FILES, instance=created_user)

            if formset.is_valid():
                created_user.save()
                formset.save()
                message = _('User "%(created_user)s" has been added !') % {
                    'created_user': created_user.username}
                messages.success(request, message)
                return redirect('mcl:users_list')
    else:
        user_form = UserCreateForm(instance=user)
        formset = ProfileInlineFormSet()

    return render(request, "mcl/users_add.html", {"form": user_form, "formset": formset})


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def users_list(request):
    queryset = User.objects.filter(is_superuser=False).order_by('-id')
    f = UserFilter(request.GET, queryset=queryset)
    table = UserTable(f.qs)
    user_settings = UserSettings.objects.get(user=request.user)
    RequestConfig(request, paginate={
                  "per_page": user_settings.item_limit, "page": 1}).configure(table)
    context = {"table": table, "filter": f}
    return render(request, 'mcl/users_list.html', context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def users_update(request, id):
    obj = get_object_or_404(User, pk=id)
    ProfileInlineFormSet = inlineformset_factory(
        User, Profile, form=ProfileForm, can_delete=False)

    if request.method == "POST":
        form = UserForm(request.POST, request.FILES,
                        instance=obj, prefix="main")
        formset = ProfileInlineFormSet(
            request.POST, request.FILES, instance=obj, prefix="nested")

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "User has been updated !")
            return redirect('mcl:users_list')
    else:
        form = UserForm(instance=obj, prefix="main")
        formset = ProfileInlineFormSet(instance=obj, prefix="nested")

    return render(request, "mcl/users_update.html", {"form": form, "formset": formset, 'obj': obj})


@login_required
def user_settings(request):
    obj = get_object_or_404(UserSettings, user=request.user)
    form = UserSettingsForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Settings updated !")
        return redirect('mcl:user_settings')
    return render(request, 'mcl/user_settings.html', {'form': form})


@login_required
def entry_otp(request):
    if request.method == 'POST':
        form = request.POST
        otp_code = form.get('otp').upper()

        try:
            dup_otp = EntryList.objects.get(otp=otp_code)
            messages.warning(request, "OTP already used !")
        except EntryList.DoesNotExist:

            apiKey = "rbE4nUt9.SmQpMqKVQD2I6UdI3lG6p5ClTeuKh2Yz"
            headers = {'Content-Type': 'application/json; charset=utf-8',
                       'Authorization': 'Api-Key ' + apiKey}

            otp_check = requests.get(
                'https://otp.singerbd.com:8585/api/otp/' + otp_code + '/', headers=headers)

            if otp_check.status_code == 200:
                otp_decoded = json.loads(otp_check.text)
                site = otp_decoded[0]['site_code'].upper()
                otp = otp_decoded[0]['otp'].upper()
                otp_lat = otp_decoded[0]['lattitude']
                otp_lon = otp_decoded[0]['longitude']
                otp_user = otp_decoded[0]['user']

                # check user
                if otp_user != request.user.username:
                    messages.warning(
                        request, "OTP and MCL user did not match !")
                    return redirect('mcl:entry_otp')

                # check distance
                site_check = requests.get(
                    'https://otp.singerbd.com:8585/api/site/' + site + '/', headers=headers)
                site_decoded = json.loads(site_check.text)
                site_lat = site_decoded[0]['lattitude']
                site_lon = site_decoded[0]['longitude']
                coords_one = (otp_lat, otp_lon)
                coords_two = (site_lat, site_lon)

                dist_result = geopy.distance.geodesic(
                    coords_one, coords_two).km
                final_distance = '{:.3}'.format(dist_result)

                if float(final_distance) < 0.1524:
                    request.session['site'] = site
                    request.session['otp'] = otp
                    return redirect('mcl:entry_add')
                else:
                    messages.warning(
                        request, "OTP exceeded allowed range, please try again !")

            else:
                messages.warning(request, "Invalid OTP !")

    else:
        # Entry For Site Manager
        try:
            site_manager = Site.objects.get(manager=request.user)

            # Saving site and otp to cookies request

            shop_otp = uuid.uuid4().hex[:5].upper()
            request.session['site'] = site_manager.code
            request.session['otp'] = site_manager.code + "-" + shop_otp
            last_entry_date = SiteSettings.objects.get(site_id="main")
            today = timezone.now().day

            if today > last_entry_date.entry_last_date:
                msg = ("""Last date of Check List entry has been passed. 
                You can not entry Check List for this month. Last date of entry is "%s" of every month."""
                       % (last_entry_date.entry_last_date))
                return render(request, "mcl/error.html", {'context': msg})
            else:
                return redirect('mcl:entry_add')

        except Site.DoesNotExist:
            pass

    context = {}
    return render(request, "mcl/entry_otp.html", context)


@login_required
def entry_add(request):

    # Get session data
    sess_site = request.session.get('site')
    sess_otp = request.session.get('otp')

    if sess_site and sess_otp:
        try:
            site = Site.objects.get(code=sess_site, is_active=True)
        except Site.DoesNotExist:
            messages.warning(request, "Your requested site is not active !")
            return redirect('mcl:entry_otp')
    else:
        messages.warning(request, "Your session expired. Please try again..")
        return redirect('mcl:entry_otp')

    # Survey Form
    topics = Topic.objects.filter(
        category__is_active=True).order_by('category', 'order')
    comments = Comment.objects.filter(is_active=True)

    if request.method == "POST":
        form = request.POST
        com_one = form.get('com_one')
        com_two = form.get('com_two')
        com_three = form.get('com_three')
        cust_comm = form.get('cust_comm')

        # saving entry list
        entry_list = EntryList(site_id=site.id, otp=sess_otp, comment_one=com_one,
                               comment_two=com_two, comment_three=com_three, cust_comm=cust_comm)
        entry_list.save()

        topic_images = request.FILES.getlist('topicimages')

        # save points
        for i in topics:
            pst = 'qs' + str(i.id)
            point_cat = form.get(pst)
            pointss = form.get(pst)

            """
            if pointss == 'A':
                pointss = 0
            if pointss == 'B':
                pointss = 1
            if pointss == 'C':
                pointss = 2
            if pointss == 'D':
                pointss = 1
            if pointss == 'E':
                pointss = 0
            """

            if pointss == 'A':
                pointss = 5
            if pointss == 'B':
                pointss = 4
            if pointss == 'C':
                pointss = 3
            if pointss == 'D':
                pointss = 2
            if pointss == 'E':
                pointss = 1

            # saving check list
            chk_list = CheckList(entry_list_id=entry_list.pk,
                                 topic_id=i.id, point=pointss, point_cat=point_cat)
            chk_list.save()
            chk_list_instance = get_object_or_404(
                CheckList, id=chk_list.pk, topic_id=i.id)
            for index, topic_image_file in enumerate(topic_images, start=1):
                if index == i.id:
                    chk_list_instance.topic_image.save(
                        topic_image_file.name, topic_image_file)
                    chk_list_instance.save()

        # Save image
        photos = request.FILES.getlist('images')
        for i in photos:
            ext = os.path.splitext(i.name)[1]
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not ext.lower() in valid_extensions:
                # Remove entry list check list
                entry_list_instance = EntryList.objects.get(id=entry_list.pk)
                entry_list_instance.delete()

                chk_list_instance = CheckList.objects.filter(id=chk_list.pk)
                chk_list_instance.delete()

                messages.warning(
                    request, "Image file type not allowed ! Only [JPG, JPEG, GIF, PNG] allowed")
                return redirect('mcl:entry_add')

            else:
                img = EntryImage.objects.create(
                    image=i, entry_id=entry_list.pk)
                img.save()

        # delete user session site and otp
        try:
            del request.session['site']
            del request.session['otp']
        except KeyError:
            pass

        messages.success(
            request, "You have successfully completed Check List Entry. " + str(entry_list.pk))
        return redirect('mcl:entry_detail', id=entry_list.pk)
    else:
        pass
    context = {'topics': topics, 'site': site, 'comments': comments}
    return render(request, 'mcl/entry_add.html', context)


@login_required
def entry_otp_bn(request):
    if request.method == 'POST':
        form = request.POST
        otp_code = form.get('otp').upper()

        try:
            dup_otp = EntryList.objects.get(otp=otp_code)
            messages.warning(request, "OTP already used !")
        except EntryList.DoesNotExist:

            apiKey = "rbE4nUt9.SmQpMqKVQD2I6UdI3lG6p5ClTeuKh2Yz"
            headers = {'Content-Type': 'application/json; charset=utf-8',
                       'Authorization': 'Api-Key ' + apiKey}

            otp_check = requests.get(
                'https://otp.singerbd.com:8585/api/otp/' + otp_code + '/', headers=headers)

            if otp_check.status_code == 200:
                otp_decoded = json.loads(otp_check.text)
                site = otp_decoded[0]['site_code'].upper()
                otp = otp_decoded[0]['otp'].upper()
                otp_lat = otp_decoded[0]['lattitude']
                otp_lon = otp_decoded[0]['longitude']
                otp_user = otp_decoded[0]['user']

                # check user
                if otp_user != request.user.username:
                    messages.warning(
                        request, "OTP and MCL user did not match !")
                    return redirect('mcl:entry_otp')

                # check distance
                site_check = requests.get(
                    'https://otp.singerbd.com:8585/api/site/' + site + '/', headers=headers)
                site_decoded = json.loads(site_check.text)
                site_lat = site_decoded[0]['lattitude']
                site_lon = site_decoded[0]['longitude']
                coords_one = (otp_lat, otp_lon)
                coords_two = (site_lat, site_lon)

                dist_result = geopy.distance.geodesic(
                    coords_one, coords_two).km
                final_distance = '{:.3}'.format(dist_result)

                if float(final_distance) < 0.1524:
                    request.session['site'] = site
                    request.session['otp'] = otp
                    return redirect('mcl:entry_add')
                else:
                    messages.warning(
                        request, "OTP exceeded allowed range, please try again !")
            else:
                messages.warning(request, "Invalid OTP !")
    else:
        # Entry For Site Manager
        try:
            site_manager = Site.objects.get(manager=request.user)

            # Saving site and otp to cookies request

            shop_otp = uuid.uuid4().hex[:5].upper()
            request.session['site'] = site_manager.code
            request.session['otp'] = site_manager.code + "-" + shop_otp
            last_entry_date = SiteSettings.objects.get(site_id="main")
            today = timezone.now().day

            if today > last_entry_date.entry_last_date:
                msg = ("""Last date of Check List entry has been passed. 
                You can not entry Check List for this month. Last date of entry is "%s" of every month."""
                       % (last_entry_date.entry_last_date))
                return render(request, "mcl/error.html", {'context': msg})
            else:
                return redirect('mcl:entry_add_bn')

        except Site.DoesNotExist:
            pass

    context = {}
    return render(request, "mcl/entry_otp_bn.html", context)


@login_required
def entry_add_bn(request):

    # Get session data
    sess_site = request.session.get('site')
    sess_otp = request.session.get('otp')

    if sess_site and sess_otp:
        try:
            site = Site.objects.get(code=sess_site, is_active=True)
        except Site.DoesNotExist:
            messages.warning(request, "Your requested site is not active !")
            return redirect('mcl:entry_otp')
    else:
        messages.warning(request, "Your session expired. Please try again..")
        return redirect('mcl:entry_otp')

    # Survey Form
    topics = Topic.objects.filter(
        category__is_active=True).order_by('category', 'order')
    comments = Comment.objects.filter(is_active=True)

    if request.method == "POST":
        form = request.POST
        com_one = form.get('com_one')
        com_two = form.get('com_two')
        com_three = form.get('com_three')
        cust_comm = form.get('cust_comm')

        # saving entry list
        entry_list = EntryList(site_id=site.id, otp=sess_otp, comment_one=com_one,
                               comment_two=com_two, comment_three=com_three, cust_comm=cust_comm)
        entry_list.save()

        topic_images = request.FILES.getlist('topicimages')

        # save points
        for i in topics:
            pst = 'qs' + str(i.id)
            point_cat = form.get(pst)
            pointss = form.get(pst)

            # if pointss == 'A':
            #     pointss = 0
            # if pointss == 'B':
            #     pointss = 1
            # if pointss == 'C':
            #     pointss = 2
            # if pointss == 'D':
            #     pointss = 1
            # if pointss == 'E':
            #     pointss = 0

            if pointss == 'A':
                pointss = 5
            if pointss == 'B':
                pointss = 4
            if pointss == 'C':
                pointss = 3
            if pointss == 'D':
                pointss = 2
            if pointss == 'E':
                pointss = 1

            # saving check list
            chk_list = CheckList(entry_list_id=entry_list.pk,
                                 topic_id=i.id, point=pointss, point_cat=point_cat)
            chk_list.save()
            chk_list_instance = get_object_or_404(
                CheckList, id=chk_list.pk, topic_id=i.id)
            for index, topic_image_file in enumerate(topic_images, start=1):
                if index == i.id:
                    chk_list_instance.topic_image.save(
                        topic_image_file.name, topic_image_file)
                    chk_list_instance.save()

        # Save image
        photos = request.FILES.getlist('images')
        for i in photos:
            ext = os.path.splitext(i.name)[1]
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not ext.lower() in valid_extensions:
                # Remove entry list check list
                entry_list_instance = EntryList.objects.get(id=entry_list.pk)
                entry_list_instance.delete()

                chk_list_instance = CheckList.objects.filter(id=chk_list.pk)
                chk_list_instance.delete()

                messages.warning(
                    request, "Image file type not allowed ! Only [JPG, JPEG, GIF, PNG] allowed")
                return redirect('mcl:entry_add')

            else:
                img = EntryImage.objects.create(
                    image=i, entry_id=entry_list.pk)
                img.save()

        # delete user session site and otp
        try:
            del request.session['site']
            del request.session['otp']
        except KeyError:
            pass

        messages.success(
            request, "আপনি সফলভাবে চেকলিস্ট এন্ট্রি সম্পন্ন করেছেন । " + str(entry_list.pk))
        # return redirect('mcl:entry_detail', id=entry_list.pk)
        return redirect('mcl:entry_detail_bn', id=entry_list.pk)
    else:
        pass
    context = {'topics': topics, 'site': site, 'comments': comments}
    return render(request, 'mcl/entry_add_bn.html', context)


@login_required
def entry_otp_promotion_bn(request):
    if request.method == 'POST':
        form = request.POST
        otp_code = form.get('otp').upper()

        try:
            dup_otp = EntryList.objects.get(otp=otp_code)
            messages.warning(request, "OTP already used !")
        except EntryList.DoesNotExist:

            apiKey = "rbE4nUt9.SmQpMqKVQD2I6UdI3lG6p5ClTeuKh2Yz"
            headers = {'Content-Type': 'application/json; charset=utf-8',
                       'Authorization': 'Api-Key ' + apiKey}

            otp_check = requests.get(
                'https://otp.singerbd.com:8585/api/otp/' + otp_code + '/', headers=headers)

            if otp_check.status_code == 200:
                otp_decoded = json.loads(otp_check.text)
                site = otp_decoded[0]['site_code'].upper()
                otp = otp_decoded[0]['otp'].upper()
                otp_lat = otp_decoded[0]['lattitude']
                otp_lon = otp_decoded[0]['longitude']
                otp_user = otp_decoded[0]['user']

                # check user
                if otp_user != request.user.username:
                    messages.warning(
                        request, "OTP and MCL user did not match !")
                    return redirect('mcl:entry_otp')

                # check distance
                site_check = requests.get(
                    'https://otp.singerbd.com:8585/api/site/' + site + '/', headers=headers)
                site_decoded = json.loads(site_check.text)
                site_lat = site_decoded[0]['lattitude']
                site_lon = site_decoded[0]['longitude']
                coords_one = (otp_lat, otp_lon)
                coords_two = (site_lat, site_lon)

                dist_result = geopy.distance.geodesic(
                    coords_one, coords_two).km
                final_distance = '{:.3}'.format(dist_result)

                if float(final_distance) < 0.1524:
                    request.session['site'] = site
                    request.session['otp'] = otp
                    return redirect('mcl:entry_add')
                else:
                    messages.warning(
                        request, "OTP exceeded allowed range, please try again !")
            else:
                messages.warning(request, "Invalid OTP !")
    else:
        # Entry For Site Manager
        try:
            site_manager = Site.objects.get(manager=request.user)

            # Saving site and otp to cookies request

            shop_otp = uuid.uuid4().hex[:5].upper()
            request.session['site'] = site_manager.code
            request.session['otp'] = site_manager.code + "-" + shop_otp
            last_entry_date = SiteSettings.objects.get(site_id="main")
            today = timezone.now().day

            if today > last_entry_date.entry_last_date:
                msg = ("""Last date of Check List entry has been passed. 
                You can not entry Check List for this month. Last date of entry is "%s" of every month."""
                       % (last_entry_date.entry_last_date))
                return render(request, "mcl/error.html", {'context': msg})
            else:
                return redirect('mcl:entry_promotion_bn')

        except Site.DoesNotExist:
            pass

    context = {}
    return render(request, "mcl/entry_otp.html", context)


@login_required
def entry_promotion_bn(request):

    # Get session data
    sess_site = request.session.get('site')
    sess_otp = request.session.get('otp')

    if sess_site and sess_otp:
        try:
            site = Site.objects.get(code=sess_site, is_active=True)
        except Site.DoesNotExist:
            messages.warning(request, "Your requested site is not active !")
            return redirect('mcl:entry_otp')
    else:
        messages.warning(request, "Your session expired. Please try again..")
        return redirect('mcl:entry_otp')

    # Survey Form
    topics = Topic.objects.filter(
        category__is_active=True, category__order=2).order_by('category', 'order')
    comments = Comment.objects.filter(is_active=True)

    if request.method == "POST":
        form = request.POST
        com_one = form.get('com_one')
        com_two = form.get('com_two')
        com_three = form.get('com_three')
        cust_comm = form.get('cust_comm')

        # saving entry list
        entry_list = EntryList(site_id=site.id, otp=sess_otp, comment_one=com_one,
                               comment_two=com_two, comment_three=com_three, cust_comm=cust_comm)
        entry_list.save()

        topic_images = request.FILES.getlist('topicimages')

        # save points
        for i in topics:
            j = 1
            pst = 'qs' + str(i.id)
            point_cat = form.get(pst)
            pointss = form.get(pst)

            # if pointss == 'A':
            #     pointss = 0
            # if pointss == 'B':
            #     pointss = 1
            # if pointss == 'C':
            #     pointss = 2
            # if pointss == 'D':
            #     pointss = 1
            # if pointss == 'E':
            #     pointss = 0

            if pointss == 'A':
                pointss = 5
            if pointss == 'B':
                pointss = 4
            if pointss == 'C':
                pointss = 3
            if pointss == 'D':
                pointss = 2
            if pointss == 'E':
                pointss = 1

            # saving check list
            chk_list = CheckList(entry_list_id=entry_list.pk,
                                 topic_id=i.id, point=pointss, point_cat=point_cat)
            chk_list.save()

        # Save points and images for each topic
        for index, topic in enumerate(topics):
            if index < len(topic_images):
                topic_image_file = topic_images[index]
                topic_image_file_name = topic_image_file.name
                chk_list_instance = get_object_or_404(
                    CheckList, entry_list=entry_list, topic=topic)

                # Save the image for the current topic
                chk_list_instance.topic_image.save(
                    topic_image_file_name, topic_image_file)
                chk_list_instance.save()
            else:
                break  # Stop if there are more topics than images

        # Save image
        photos = request.FILES.getlist('images')
        for i in photos:
            ext = os.path.splitext(i.name)[1]
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not ext.lower() in valid_extensions:
                # Remove entry list check list
                entry_list_instance = EntryList.objects.get(id=entry_list.pk)
                entry_list_instance.delete()

                chk_list_instance = CheckList.objects.filter(id=chk_list.pk)
                chk_list_instance.delete()

                messages.warning(
                    request, "Image file type not allowed ! Only [JPG, JPEG, GIF, PNG] allowed")
                return redirect('mcl:entry_add')

            else:
                img = EntryImage.objects.create(
                    image=i, entry_id=entry_list.pk)
                img.save()

        # delete user session site and otp
        try:
            del request.session['site']
            del request.session['otp']
        except KeyError:
            pass

        messages.success(
            request, "আপনি সফলভাবে চেকলিস্ট এন্ট্রি সম্পন্ন করেছেন । " + str(entry_list.pk))
        # return redirect('mcl:entry_detail', id=entry_list.pk)
        return redirect('mcl:entry_detail_bn', id=entry_list.pk)
    else:
        pass
    context = {'topics': topics, 'site': site, 'comments': comments}
    return render(request, 'mcl/entry_promotion_bn.html', context)


@login_required
def entry_list(request):
    if request.user.is_superuser or request.user.groups.filter(name="Admin"):
        queryset = EntryList.objects.all().order_by('-id')
    else:
        queryset = EntryList.objects.filter(
            created_by=request.user).order_by('-id')

    # Get Entry list for Area Manager
    try:
        area_manager = Area.objects.get(manager_id=request.user.id)
        queryset = EntryList.objects.filter(
            site__district__area=area_manager).order_by('-id')
    except:
        pass

    # Get Entry list for District Manager
    try:
        district_manager = District.objects.get(manager_id=request.user.id)
        queryset = EntryList.objects.filter(
            site__district=district_manager).order_by('-id')
    except:
        pass

    # Get Entry list for Site Manager
    try:
        site_manager = Site.objects.get(manager_id=request.user.id)
        queryset = EntryList.objects.filter(site=site_manager).order_by('-id')
    except:
        pass

    f = EntryListFilter(request.GET, queryset=queryset)
    if request.user.is_superuser or request.user.groups.filter(name="Admin"):
        table = EntryListTable(f.qs, exclude=('view_link',))
    else:
        table = EntryListTable(f.qs, exclude=('action_link', 'resubmit_link',))
    user_settings = UserSettings.objects.get(user=request.user)
    RequestConfig(request, paginate={
                  "per_page": user_settings.item_limit, "page": 1}).configure(table)
    context = {"table": table, "filter": f}
    return render(request, 'mcl/entry_list.html', context)


@login_required
def entry_detail(request, id):
    context = {}
    entry = get_object_or_404(EntryList, id=id)
    context['entry'] = entry

    # Get Entry list for Area Manager
    try:
        area_manager = Area.objects.get(manager_id=request.user.id)
        if entry.site.district.area == area_manager:
            with connection.cursor() as cursor:
                sql_am = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_am, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for District Manager
    try:
        district_manager = District.objects.get(manager_id=request.user.id)
        if entry.site.district == district_manager:
            with connection.cursor() as cursor:
                sql_dm = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_dm, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for Site Manager
    try:
        site_manager = Site.objects.get(manager_id=request.user.id)
        if entry.site == site_manager:
            with connection.cursor() as cursor:
                sql_site = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_site, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Admin and normal user
    if request.user.is_superuser or request.user.groups.filter(name="Admin") or entry.created_by == request.user:
        sql_admin = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
        with connection.cursor() as cursor:
            cursor.execute(sql_admin, [id])
            raw_res = dictfetchall(cursor)
            context['raw_res'] = raw_res
            total_score = CheckList.objects.filter(
                entry_list_id=id).aggregate(Sum('point'))
            context['raw_res'] = raw_res
            context['total_score'] = total_score
        

    # Images
    try:
        images = EntryImage.objects.filter(entry=entry)
        context['images'] = images
    except EntryImage.DoesNotExist:
        context['images'] = None
    return render(request, 'mcl/entry_detail.html', context)


@login_required
def entry_detail_bn(request, id):
    context = {}
    entry = get_object_or_404(EntryList, id=id)
    context['entry'] = entry

    # Get Entry list for Area Manager
    try:
        area_manager = Area.objects.get(manager_id=request.user.id)
        if entry.site.district.area == area_manager:
            with connection.cursor() as cursor:
                sql_am = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_am, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for District Manager
    try:
        district_manager = District.objects.get(manager_id=request.user.id)
        if entry.site.district == district_manager:
            with connection.cursor() as cursor:
                sql_dm = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_dm, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for Site Manager
    try:
        site_manager = Site.objects.get(manager_id=request.user.id)
        if entry.site == site_manager:
            with connection.cursor() as cursor:
                sql_site = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_site, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Admin and normal user
    if request.user.is_superuser or request.user.groups.filter(name="Admin") or entry.created_by == request.user:
        with connection.cursor() as cursor:
          sql_admin = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
          cursor.execute(sql_admin, [id])
          raw_res = dictfetchall(cursor)
          total_score = CheckList.objects.filter(
              entry_list_id=id).aggregate(Sum('point'))
          context['raw_res'] = raw_res
          context['total_score'] = total_score

    # Images
    try:
        images = EntryImage.objects.filter(entry=entry)
        context['images'] = images
    except EntryImage.DoesNotExist:
        context['images'] = None
    return render(request, 'mcl/entry_detail_bn.html', context)


@login_required
def entry_detail_update(request, id):
    context = {}
    entry = get_object_or_404(EntryList, id=id)
    context['entry'] = entry

    # topics = Topic.objects.filter(category__is_active=True).order_by('category', 'order')
    topics = Topic.objects.filter(
        category__is_active=True, checklist__entry_list=id).order_by('category', 'order')
    if request.method == "POST":
        form = request.POST
        rem_comm = form.get('rem_comm')

        # saving entry list
        entry.rem_comm = rem_comm
        entry.save()

        # save points
        for i in topics:
            pst = 'qs' + str(i.id)
            point_cat = form.get(pst)
            pointss = form.get(pst)

            if pointss == 'A':
                pointss = 5
            if pointss == 'B':
                pointss = 4
            if pointss == 'C':
                pointss = 3
            if pointss == 'D':
                pointss = 2
            if pointss == 'E':
                pointss = 1

            # saving check list
            chk_list_instance = CheckList.objects.get(
                entry_list_id=id, topic_id=i.id)
            # chk_list_instance = get_object_or_404(CheckList, entry_list_id=id, topic_id=i.id)
            chk_list_instance.point = pointss
            chk_list_instance.point_cat = point_cat
            chk_list_instance.save()

        messages.success(
            request, "You have sucessfully update the Entry. " + str(entry.pk))
        return redirect('mcl:entry_details', id=entry.pk)
    else:
        pass

    # Add Marks
    # topics = Topic.objects.filter(category__is_active=True).order_by('category', 'order')
    # if request.method == "POST":
    #     form = request.POST
        # rem_comm = form.get('rem_comm')

        # saving entry list
        # entry_list_instance = get_object_or_404(EntryList, entry_list_id=id)
        # entry_list_instance.rem_comm = rem_comm
        # entry_list_instance.save()

        # marks = request.POST.get('marks')
        # for i in topics:
        #     chk_list_instance = get_object_or_404(CheckList, id=chk_list.pk, topic_id=i.id)
        #     for index, mark in enumerate(marks, start=1):
        #         if index == i.id:
        #             chk_list_instance.marks = mark
        #             chk_list_instance.save()

    # Get Entry list for Area Manager
    try:
        area_manager = Area.objects.get(manager_id=request.user.id)
        if entry.site.district.area == area_manager:
            with connection.cursor() as cursor:
                sql_am = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_am, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for District Manager
    try:
        district_manager = District.objects.get(manager_id=request.user.id)
        if entry.site.district == district_manager:
            with connection.cursor() as cursor:
                sql_dm = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_dm, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for Site Manager
    try:
        site_manager = Site.objects.get(manager_id=request.user.id)
        if entry.site == site_manager:
            with connection.cursor() as cursor:
                sql_site = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_site, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Admin and normal user
    if request.user.is_superuser or request.user.groups.filter(name="Admin") or entry.created_by == request.user:
        with connection.cursor() as cursor:
            sql_admin = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
            cursor.execute(sql_admin, [id])
            raw_res = dictfetchall(cursor)
            total_score = CheckList.objects.filter(
                entry_list_id=id).aggregate(Sum('point'))
            context['raw_res'] = raw_res
            context['total_score'] = total_score

    # Images
    try:
        images = EntryImage.objects.filter(entry=entry)
        # topic_images = CheckList.objects.filter(topic_image=topic_image)
        # print(topic_images)
        context['images'] = images
        # context['topic_images'] = topic_images
    except EntryImage.DoesNotExist:
        context['images'] = None
        # context['topic_images'] = None
    return render(request, 'mcl/entry_detail_update.html', context)


@login_required
def entry_details(request, id):
    context = {}
    entry = get_object_or_404(EntryList, id=id)
    context['entry'] = entry

    # Get Entry list for Area Manager
    try:
        area_manager = Area.objects.get(manager_id=request.user.id)
        if entry.site.district.area == area_manager:
            with connection.cursor() as cursor:
                sql_am = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_am, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for District Manager
    try:
        district_manager = District.objects.get(manager_id=request.user.id)
        if entry.site.district == district_manager:
            with connection.cursor() as cursor:
                sql_dm = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_dm, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for Site Manager
    try:
        site_manager = Site.objects.get(manager_id=request.user.id)
        if entry.site == site_manager:
            with connection.cursor() as cursor:
                sql_site = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_site, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Admin and normal user
    if request.user.is_superuser or request.user.groups.filter(name="Admin") or entry.created_by == request.user:
        with connection.cursor() as cursor:
            sql_admin = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
            cursor.execute(sql_admin, [id])
            raw_res = dictfetchall(cursor)
            total_score = CheckList.objects.filter(
                entry_list_id=id).aggregate(Sum('point'))
            context['raw_res'] = raw_res
            context['total_score'] = total_score

    # Images
    try:
        images = EntryImage.objects.filter(entry=entry)
        context['images'] = images
    except EntryImage.DoesNotExist:
        context['images'] = None
    return render(request, 'mcl/entry_details.html', context)


@login_required
def resubmit_entry(request, id):
    context = {}
    entry = get_object_or_404(EntryList, id=id)
    context['entry'] = entry
    entry_list = EntryList.objects.filter(
        id=id).values('created_by__email').first()
    if entry_list:
        to_email = entry_list['created_by__email']
    if request.method == 'POST':
        subject = 'Resubmit MCL Entry'
        message = 'Please Resubmit the MCL Entry for the current month'
        from_email = 'mcl@singerbd.com'
        recipient_list = [to_email]
        send_mail(subject, message, from_email, recipient_list)

        return redirect('mcl:entry_details', id=entry.pk)
    else:
        # Your regular GET request handling code goes here
        pass


    # Get Entry list for Area Manager
    try:
        area_manager = Area.objects.get(manager_id=request.user.id)
        if entry.site.district.area == area_manager:
            with connection.cursor() as cursor:
                sql_am = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_am, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for District Manager
    try:
        district_manager = District.objects.get(manager_id=request.user.id)
        if entry.site.district == district_manager:
            with connection.cursor() as cursor:
                sql_dm = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_dm, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Get Entry list for Site Manager
    try:
        site_manager = Site.objects.get(manager_id=request.user.id)
        if entry.site == site_manager:
            with connection.cursor() as cursor:
                sql_site = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
                cursor.execute(sql_site, [id])
                raw_res = dictfetchall(cursor)
                total_score = CheckList.objects.filter(
                    entry_list_id=id).aggregate(Sum('point'))
                context['raw_res'] = raw_res
                context['total_score'] = total_score
    except:
        pass

    # Admin and normal user
    if request.user.is_superuser or request.user.groups.filter(name="Admin") or entry.created_by == request.user:
        with connection.cursor() as cursor:
            sql_admin = """SELECT cat.id as cat_id, cat.name_bn as cat_name_bn, cat.name_en as cat_name_en, topic.id as topic_id, topic.name_bn as topic_name_bn, topic.name_en as topic_name_en, chk.point as chk_point, chk.point_cat as chk_point_cat, chk.topic_id as chk_topic_id, chk.topic_image as chk_topic_image, entry.id as entry_id from mcl_category as cat, mcl_topic as topic, mcl_checklist as chk, mcl_entrylist as entry where topic.category_id=cat.id and chk.entry_list_id=entry.id and chk.topic_id=topic.id and entry.id=%s GROUP BY topic.id, cat.id ORDER BY cat.`order` ASC, topic.`order` ASC;"""
            cursor.execute(sql_admin, [id])
            raw_res = dictfetchall(cursor)
            total_score = CheckList.objects.filter(
                entry_list_id=id).aggregate(Sum('point'))
            context['raw_res'] = raw_res
            context['total_score'] = total_score

    # Images
    try:
        images = EntryImage.objects.filter(entry=entry)
        context['images'] = images
    except EntryImage.DoesNotExist:
        context['images'] = None
    return render(request, 'mcl/resubmit_entry.html', context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def category_add(request):
    context = {}
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category has been added !")
            return redirect('mcl:category_list')
    else:
        form = CategoryForm()

    context['form'] = form
    return render(request, "mcl/category_add.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def category_list(request):
    queryset = Category.objects.all().order_by('-id')
    f = CategoryFilter(request.GET, queryset=queryset)
    table = CategoryTable(f.qs)
    user_settings = UserSettings.objects.get(user=request.user)
    RequestConfig(request, paginate={
                  "per_page": user_settings.item_limit, "page": 1}).configure(table)
    context = {"table": table, "filter": f}
    return render(request, 'mcl/category_list.html', context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def category_update(request, id):
    obj = get_object_or_404(Category, id=id)
    form = CategoryForm(request.POST or None, instance=obj)
    context = {}
    if form.is_valid():
        form.save()
        messages.success(request, "Category has been updated !")
        return redirect('mcl:category_list')
    context['form'] = form
    context['obj'] = obj
    return render(request, "mcl/category_update.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def topic_add(request):
    context = {}
    if request.method == "POST":
        form = TopicForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Topic has been added !")
            return redirect('mcl:topic_list')
    else:
        form = TopicForm()

    context['form'] = form
    return render(request, "mcl/topic_add.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def topic_list(request):
    queryset = Topic.objects.all().order_by('-id')
    f = TopicFilter(request.GET, queryset=queryset)
    table = TopicTable(f.qs)
    user_settings = UserSettings.objects.get(user=request.user)
    RequestConfig(request, paginate={
                  "per_page": user_settings.item_limit, "page": 1}).configure(table)
    context = {"table": table, "filter": f}
    return render(request, 'mcl/topic_list.html', context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def topic_update(request, id):
    obj = get_object_or_404(Topic, id=id)
    form = TopicForm(request.POST or None, request.FILES or None, instance=obj)
    context = {}
    if form.is_valid():
        form.save()
        messages.success(request, "Topic has been updated !")
        return redirect('mcl:topic_list')
    context['form'] = form
    context['obj'] = obj
    return render(request, "mcl/topic_update.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def comment_add(request):
    context = {}
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Comment has been added !")
            return redirect('mcl:comment_list')
    else:
        form = CommentForm()

    context['form'] = form
    return render(request, "mcl/comment_add.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def comment_list(request):
    queryset = Comment.objects.all().order_by('-id')
    f = CommentFilter(request.GET, queryset=queryset)
    table = CommentTable(f.qs)
    user_settings = UserSettings.objects.get(user=request.user)
    RequestConfig(request, paginate={
                  "per_page": user_settings.item_limit, "page": 1}).configure(table)
    context = {"table": table, "filter": f}
    return render(request, 'mcl/comment_list.html', context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def comment_update(request, id):
    obj = get_object_or_404(Comment, id=id)
    form = CommentForm(request.POST or None, instance=obj)
    context = {}
    if form.is_valid():
        form.save()
        messages.success(request, "Comment has been updated !")
        return redirect('mcl:comment_list')
    context['form'] = form
    context['obj'] = obj
    return render(request, "mcl/comment_update.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def area_add(request):
    context = {}
    if request.method == "POST":
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Area has been added !")
            return redirect('mcl:area_list')
    else:
        form = AreaForm()

    context['form'] = form
    return render(request, "mcl/area_add.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def area_list(request):
    queryset = Area.objects.all().order_by('-id')
    f = AreaFilter(request.GET, queryset=queryset)
    table = AreaTable(f.qs)
    user_settings = UserSettings.objects.get(user=request.user)
    RequestConfig(request, paginate={
                  "per_page": user_settings.item_limit, "page": 1}).configure(table)
    context = {"table": table, "filter": f}
    return render(request, 'mcl/area_list.html', context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def area_update(request, id):
    obj = get_object_or_404(Area, id=id)
    form = AreaForm(request.POST or None, instance=obj)
    context = {}
    if form.is_valid():
        form.save()
        messages.success(request, "Area has been updated !")
        return redirect('mcl:area_list')
    context['form'] = form
    context['obj'] = obj
    return render(request, "mcl/area_update.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def district_add(request):
    context = {}
    if request.method == "POST":
        form = DistrictForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "District has been added !")
            return redirect('mcl:district_list')
    else:
        form = DistrictForm()

    context['form'] = form
    return render(request, "mcl/district_add.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def district_list(request):
    queryset = District.objects.all().order_by('-id')
    f = DistrictFilter(request.GET, queryset=queryset)
    table = DistrictTable(f.qs)
    user_settings = UserSettings.objects.get(user=request.user)
    RequestConfig(request, paginate={
                  "per_page": user_settings.item_limit, "page": 1}).configure(table)
    context = {"table": table, "filter": f}
    return render(request, 'mcl/district_list.html', context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def district_update(request, id):
    obj = get_object_or_404(District, id=id)
    form = DistrictForm(request.POST or None, instance=obj)
    context = {}
    if form.is_valid():
        form.save()
        messages.success(request, "District has been updated !")
        return redirect('mcl:district_list')
    context['form'] = form
    context['obj'] = obj
    return render(request, "mcl/district_update.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def site_add(request):
    context = {}
    if request.method == "POST":
        form = SiteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Site has been added !")
            return redirect('mcl:site_list')
    else:
        form = SiteForm()

    context['form'] = form
    return render(request, "mcl/site_add.html", context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def site_list(request):
    queryset = Site.objects.all().order_by('-id')
    f = SiteFilter(request.GET, queryset=queryset)
    table = SiteTable(f.qs)
    user_settings = UserSettings.objects.get(user=request.user)
    RequestConfig(request, paginate={
                  "per_page": user_settings.item_limit, "page": 1}).configure(table)
    context = {"table": table, "filter": f}
    return render(request, 'mcl/site_list.html', context)


@login_required
@user_passes_test(user_superuser_or_admin, login_url='mcl:not_authorized')
def site_update(request, id):
    obj = get_object_or_404(Site, id=id)
    form = SiteForm(request.POST or None, instance=obj)
    context = {}
    if form.is_valid():
        form.save()
        messages.success(request, "Site has been updated !")
        return redirect('mcl:site_list')
    context['form'] = form
    context['obj'] = obj
    return render(request, "mcl/site_update.html", context)
