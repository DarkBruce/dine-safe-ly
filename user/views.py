import json

from django.contrib.auth import authenticate, login, logout
from restaurant.models import Categories

# from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model
from django.utils.encoding import force_text
from django.http import HttpResponse
from .utils import send_reset_password_email
from .forms import UserCreationForm, ResetPasswordForm, UpdatePasswordForm, GetEmailForm


import logging

logger = logging.getLogger(__name__)


def user_login(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("user:register")

    else:
        form = AuthenticationForm()
    return render(request, template_name="login.html", context={"form": form})


def register(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("user:login")
    else:
        form = UserCreationForm()
    return render(
        request=request, template_name="register.html", context={"form": form}
    )


# @login_required()
def post_logout(request):
    logout(request)
    return redirect("user:login")


# @login_required()
def account_details(request):
    if not request.user.is_authenticated:
        return redirect("user:login")

    user = request.user

    favorite_restaurant_list = user.favorite_restaurants.all()
    user_pref_list = user.preferences.all()

    if request.method == "POST" and "update_pass_form" in request.POST:
        form = UpdatePasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save(user)
            return redirect("user:login")
        logger.error(form.errors)
        return render(
            request=request,
            template_name="account_details.html",
            context={
                "form": form,
                "favorite_restaurant_list": favorite_restaurant_list,
                "user_pref": user_pref_list,
            },
        )
    else:
        form = ResetPasswordForm()
        return render(
            request=request,
            template_name="account_details.html",
            context={
                "form": form,
                "favorite_restaurant_list": favorite_restaurant_list,
                "user_pref": user_pref_list,
            },
        )


def reset_password_link(request, base64_id, token):
    if request.method == "POST":

        uid = force_text(urlsafe_base64_decode(base64_id))

        user = get_user_model().objects.get(pk=uid)
        if not user or not PasswordResetTokenGenerator().check_token(user, token):
            return HttpResponse("This is invalid!")
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            form.save(uid)
            return redirect("user:login")
        else:
            return HttpResponse("Invalid")
    else:
        form = ResetPasswordForm()
        return render(
            request=request, template_name="reset.html", context={"form": form}
        )


def forget_password(request):
    if request.method == "POST":
        form = GetEmailForm(request.POST)
        if form.is_valid():
            # TODO: Check the django reset password form
            send_reset_password_email(request, form.cleaned_data.get("email"))
            return render(request=request, template_name="sent_email.html")
        return render(
            request=request, template_name="reset_email.html", context={"form": form}
        )
    else:
        form = GetEmailForm()
        return render(
            request=request, template_name="reset_email.html", context={"form": form}
        )


def add_preference(request, category):
    if request.method == "POST":
        user = request.user
        user.preferences.add(Categories.objects.get(category=category))
        logger.info(category)
        return HttpResponse("Preference Saved")


def delete_preference(request, category):
    if request.method == "POST":
        user = request.user
        user.preferences.remove(Categories.objects.get(category=category))
        logger.info(category)
        return HttpResponse("Preference Removed")


def update_password(request):
    if not request.user.is_authenticated:
        return redirect("user:login")

    user = request.user
    if request.method == "POST":
        form = UpdatePasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save(user)
            return redirect("user:login")

        error_list = []
        for field in form:
            for error in field.errors:
                error_list.append(error)
        context = {"status": "400", "errors": error_list}
        response = HttpResponse(json.dumps(context), content_type="application/json")
        response.status_code = 400
        return response
