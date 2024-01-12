from django.urls import path, include, re_path
from . import views
from django.contrib.auth import views as auth_views

app_name = "mcl"

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name= "logout"),

    path('password-reset/', views.ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='mcl/password_reset_confirm.html'),
         name='password_reset_confirm'),
    #Password reset complete url in core urls.py

    path('not-authorized/', views.not_authorized, name='not_authorized'),

    path('user/settings/', views.user_settings, name='user_settings'),
    path('user/password/', views.change_password, name='change_password'),

    path('settings/', views.site_settings, name='site_settings'),

    path('users/add/', views.users_add, name='users_add'),
    path('users/list/', views.users_list, name='users_list'),
    path('users/<id>/update/', views.users_update, name='users_update'),

    path('entry/otp/', views.entry_otp, name='entry_otp'),
    path('entry/add/', views.entry_add, name='entry_add'),
    path('entry/bn/otp/', views.entry_otp_bn, name='entry_otp_bn'),
    path('entry/bn/add/', views.entry_add_bn, name='entry_add_bn'),
    path('entry/promotion/bn/otp/', views.entry_otp_promotion_bn, name='entry_otp_promotion_bn'),
    path('entry/promotion/bn/', views.entry_promotion_bn, name='entry_promotion_bn'),
    path('entry/list/', views.entry_list, name='entry_list'),
    path('entry/<id>/', views.entry_detail, name='entry_detail'),
    path('entry/bn/<id>/', views.entry_detail_bn, name='entry_detail_bn'),
    
    path('edit/<id>/', views.entry_detail_update, name='entry_detail_update'),
    path('entry_details/<id>/', views.entry_details, name='entry_details'),
    path('resubmit/<id>/', views.resubmit_entry, name='resubmit_entry'),

    path('category/add/', views.category_add, name='category_add'),
    path('category/list/', views.category_list, name='category_list'),
    path('category/<id>/update/', views.category_update, name='category_update'),

    path('topic/add/', views.topic_add, name='topic_add'),
    path('topic/list/', views.topic_list, name='topic_list'),
    path('topic/<id>/update/', views.topic_update, name='topic_update'),

    path('comment/add/', views.comment_add, name='comment_add'),
    path('comment/list/', views.comment_list, name='comment_list'),
    path('comment/<id>/update/', views.comment_update, name='comment_update'),

    path('area/add/', views.area_add, name='area_add'),
    path('area/list/', views.area_list, name='area_list'),
    path('area/<id>/update/', views.area_update, name='area_update'),

    path('district/add/', views.district_add, name='district_add'),
    path('district/list/', views.district_list, name='district_list'),
    path('district/<id>/update/', views.district_update, name='district_update'),
    
    path('site/add/', views.site_add, name='site_add'),
    path('site/list/', views.site_list, name='site_list'),
    path('site/<id>/update/', views.site_update, name='site_update'),

    path('report/', views.report, name='report'),
    path('report_result/', views.report_result, name='report_result'),
    path('download_images/', views.download_images, name='download_images'),
]