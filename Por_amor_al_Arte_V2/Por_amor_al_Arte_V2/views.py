from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def nosotros(request):
    return render(request, 'nosotros.html')

def nuestro_proposito(request):
    return render(request, 'nuestro_proposito.html')

def experiencia(request):
    return render(request, 'experiencia.html')

def nuestros_artistas(request):
    return render(request, 'nuestros_artistas.html')
