from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("login/firebase/", views.firebase_login, name="firebase_login"),
    path("logout/", views.logout_view, name="logout"),
    path("orders/", views.my_orders, name="orders"),
]
