from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import AddressForm
from .models import Address


def _next(request):
    nxt = request.POST.get("next") or request.GET.get("next") or ""
    ok = url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure())
    return nxt if ok else reverse("store:addresses")


@login_required
def address_list(request):
    return render(request, "addresses.html", {"addresses": request.user.addresses.all()})


@login_required
def address_edit(request, pk=None):
    address = get_object_or_404(Address, pk=pk, user=request.user) if pk else None
    initial = {"full_name": request.user.name, "phone": request.user.national_number} if not address else None
    form = AddressForm(request.POST or None, instance=address, initial=initial)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        return redirect(_next(request))
    return render(request, "address_form.html", {"form": form, "address": address, "next": _next(request)})


@login_required
@require_POST
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    was_default = address.is_default
    address.delete()
    if was_default:
        nxt = request.user.addresses.first()
        if nxt:
            nxt.is_default = True
            nxt.save()
    return redirect("store:addresses")


@login_required
@require_POST
def address_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    return redirect("store:addresses")