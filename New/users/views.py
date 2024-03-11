from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .forms import UserRegisterForm

# Create your views here.

# def register(request):
#     if request.method == "POST":
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             form.save()
#             username = form.cleaned_data.get('username')
#             messages.success(request, f'Создан аккаунт {username}!')
#             return HttpResponseRedirect("/auth/")
#         else:
#             form = UserRegisterForm()
#         return render(request, 'users/auth.html', {'form': form})

def register(request):

    if request.method == 'GET':
        form = UserRegisterForm()
        return render(request, 'users/auth.html', {'form': form})
    elif request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                l = user.groups.values_list('name',flat = True)
                l_as_list = list(l)
                print(l_as_list)
                if user.has_perm('gaz.add_result'):
                    messages.success(request, f'Hi, {username.title()}, welcome back! Again')
                    return redirect('/home/')
                else:
                    messages.error(request, f'No permission to work here')
                    return redirect('/noperm/')
                    # return render(request, 'users/noperm.html')

        messages.error(request, f'Invalid username or password')
        return render(request, 'users/auth.html', {'form': form})


def noperm(request):
    return render(request, 'users/noperm.html')