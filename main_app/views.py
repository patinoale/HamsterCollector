from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic  import DetailView, ListView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import FeedingForm
from .models import Hamster, Toy, Photo
import uuid
import boto3

S3_BASE_URL = 'https://s3-us-west-1.amazonaws.com/'
BUCKET = 'hamstercollector'

def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')

@login_required
def hamsters_index(request):
  hamsters = Hamster.objects.filter(user=request.user)
  return render(request, 'hamsters/index.html', { 'hamsters': hamsters })

@login_required
def hamsters_detail(request, hamster_id):
  hamster = Hamster.objects.get(id=hamster_id)
  toys_hamster_doesnt_have = Toy.objects.exclude(id__in = hamster.toys.all().values_list('id'))
  feeding_form = FeedingForm()
  return render(request, 'hamsters/detail.html', { 
    'hamster': hamster, 'feeding_form': feeding_form,
    'toys': toys_hamster_doesnt_have
  })
class HamsterCreate(LoginRequiredMixin, CreateView):
  model = Hamster
  fields = ['name', 'breed', 'description', 'age']

  def form_valid(self, form):
    form.instance.user = self.request.user  # form.instance is the cat
    return super().form_valid(form)
class HamsterUpdate(LoginRequiredMixin, UpdateView):
  model = Hamster
  fields = ['breed', 'description', 'age']
class HamsterDelete(LoginRequiredMixin, DeleteView):
  model = Hamster
  success_url = '/hamsters/'

@login_required
def add_feeding(request, hamster_id):
  form = FeedingForm(request.POST)
  if form.is_valid():
    new_feeding = form.save(commit=False)
    new_feeding.hamster_id = hamster_id
    new_feeding.save()
  return redirect('detail', hamster_id=hamster_id)

@login_required
def assoc_toy(request, hamster_id, toy_id):
  Hamster.objects.get(id=hamster_id).toys.add(toy_id)
  return redirect('detail', hamster_id=hamster_id)

@login_required
def unassoc_toy(request, hamster_id, toy_id):
  Hamster.objects.get(id=hamster_id).toys.remove(toy_id)
  return redirect('detail', hamster_id=hamster_id)
class ToyCreate(LoginRequiredMixin, CreateView):
    model = Toy
    fields = '__all__'

class ToyDetail(LoginRequiredMixin, DetailView):
    model = Toy

class ToyList(LoginRequiredMixin, ListView):
    model = Toy

class ToyUpdate(LoginRequiredMixin, UpdateView):
    model = Toy
    fields = ['name', 'color']
class ToyDelete(LoginRequiredMixin, DeleteView):
    model = Toy
    success_url = '/toys/'

@login_required
def add_photo(request, hamster_id):
    photo_file = request.FILES.get('photo-file', None)
    if photo_file:
        s3 = boto3.client('s3')
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        try:
            s3.upload_fileobj(photo_file, BUCKET, key)
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            photo = Photo(url=url, hamster_id=hamster_id)
            photo.save()
        except:
            print('An error occurred uploading file to S3')
    return redirect('detail', hamster_id=hamster_id)

def signup(request):
  error_message = ''
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('index')
    else:
      error_message = 'Invalid sign up - try again'
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)