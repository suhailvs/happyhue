from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("login/google/", views.google_login, name="google_login"),
    path("logout/", views.logout_view, name="logout"),
    path("orders/", views.my_orders, name="orders"),
]