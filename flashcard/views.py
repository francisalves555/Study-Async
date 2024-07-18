from django.shortcuts import render, redirect
from .models import Categoria, Flashcard, Desafio, FlashcardDesafio, User
from django.contrib.messages import constants
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError
from django.http import HttpResponse, Http404

# Create your views here.
def novo_flashcard(request):
    if not request.user.is_authenticated:
        return redirect ('/usuarios/cadastro/')
    
    if request.method == "GET":
        categorias = Categoria.objects.all()
        dificuldades = Flashcard.DIFICULDADE_CHOICES
        flashcards = Flashcard.objects.filter(user=request.user)
        
        categoria_filtrar = request.GET.get('categoria')
        dificuldade_filtrar = request.GET.get('dificuldade')

        if categoria_filtrar:
            flashcards = flashcards.filter(categoria__id=categoria_filtrar)

        if dificuldade_filtrar:
            flashcards = flashcards.filter(dificuldade=dificuldade_filtrar)

        return render(request, 'novo_flashcard.html', {'categorias':categorias, 'dificuldades':dificuldades, 'flashcards':flashcards})
    
    elif request.method == "POST":
        pergunta = request.POST.get('pergunta')
        resposta = request.POST.get('resposta')
        categoria = request.POST.get('categoria')
        dificuldade = request.POST.get('dificuldade')

        if len(pergunta.strip()) == 0 or len(resposta.strip()) == 0:
            messages.add_message(request, constants.ERROR, "O campo de pergunta e resposta não foram preenchidas")
            return redirect ('/flashcard/novo_flashcard/')
        
        flashcard = Flashcard(
            user = request.user,
            pergunta = pergunta,
            resposta = resposta,
            categoria_id = categoria,
            dificuldade = dificuldade,
        )

        flashcard.save()
        messages.add_message(request, constants.SUCCESS, "Cadastrados com sucesso")
        return redirect ('/flashcard/novo_flashcard/')
    
def deletar_flashcard(request, id):
    flashcard = Flashcard.objects.get(id=id)

    if flashcard.user != request.user:
        messages.add_message(request, constants.SUCCESS, 'Você não tem permissão para deletar esse flashcard')
        return redirect ('/flashcard/novo_flashcard/')
    
    flashcard.delete()
    messages.add_message(request, constants.SUCCESS, 'Deletado com sucesso')
    return redirect ('/flashcard/novo_flashcard/')

def iniciar_desafio(request):
    if request.method == "GET":
        categorias = Categoria.objects.all()
        dificuldades = Flashcard.DIFICULDADE_CHOICES
        return render(request, 'iniciar_desafio.html',{'categorias':categorias, 'dificuldades':dificuldades,})
    
    elif request.method == "POST":
        titulo = request.POST.get('titulo')
        categorias = request.POST.getlist('categoria')
        dificuldade = request.POST.get('dificuldade')
        qtd_perguntas = request.POST.get('qtd_perguntas')

        desafio = Desafio(
            user=request.user,
            titulo=titulo,
            quantidade_perguntas=qtd_perguntas,
            dificuldade=dificuldade,
        )
        desafio.save()

        for categoria in categorias:
            desafio.categoria.add(categoria) #metodo dois desafio.categoria.add(*categoria)

        flashcards = (
            Flashcard.objects.filter(user=request.user)
            .filter(dificuldade=dificuldade)
            .filter(categoria_id__in=categorias)
            .order_by('?')
            )
        
        if flashcards.count() < int(qtd_perguntas):
            messages.add_message(request, constants.ERROR, 'Você não tem Flashcard suficientes para iniciar o desafio')
            desafio.delete()
            return redirect('/flashcard/iniciar_desafio/')

        flashcards = flashcards[:int(qtd_perguntas)]

        for f in flashcards:
            flashcard_desafio = FlashcardDesafio(
                flashcard=f
            )

            flashcard_desafio.save()
            desafio.flashcards.add(flashcard_desafio)

        desafio.save()

        return redirect ('/flashcard/listar_desafio/')
    
def listar_desafio(request):
    desafios = Desafio.objects.filter(user=request.user)
    categorias = Categoria.objects.all()
    dificuldades = Flashcard.DIFICULDADE_CHOICES

    categoria_filtro = request.GET.get('categoria')
    dificuldade_filtro = request.GET.get('dificuldade')

    if categoria_filtro:
        desafios = desafios.filter(categoria__id=categoria_filtro)

    if dificuldade_filtro:
        desafios = desafios.filter(dificuldade=dificuldade_filtro)
    
    return render(request, 'listar_desafio.html', {'desafios': desafios,'categorias':categorias, 'dificuldades':dificuldades})

def desafio(request, id):
    desafio = Desafio.objects.get(id=id)

    if not desafio.user == request.user:
        raise Http404()

    if request.method == "GET":
        acertou = desafio.flashcards.filter(respondido=True).filter(acertou=True).count()
        errou = desafio.flashcards.filter(respondido=True).filter(acertou=False).count()
        falta_responder = desafio.flashcards.filter(respondido=False).count()

        return render(request, 'desafio.html', {'desafio':desafio, 'acertou':acertou, 'errou':errou, 'falta_responder':falta_responder})  

def responder_flashcard (request, id):
    flashcard_desafio =FlashcardDesafio.objects.get(id=id)
    desafio_id = request.GET.get('desafio_id')
    acertou = request.GET.get('acertou')

    if not flashcard_desafio.flashcard.user == request.user:
        raise Http404
    
    flashcard_desafio.respondido = True
    
    if acertou == "1":
        flashcard_desafio.acertou = True
    elif acertou == "0":
        flashcard_desafio.acertou = False

    #flashcard_desafio.acertou = True if acertou == "1" else False
    
    flashcard_desafio.save()

    return redirect (f'/flashcard/desafio/{desafio_id}')

def relatorio (request, id):
    desafio = Desafio.objects.get(id=id)
    
    acertos = desafio.flashcards.filter(acertou=True).count()
    errou = desafio.flashcards.filter(acertou=False).count()

    dados = [acertos, errou]

    categorias = desafio.categoria.all()
    
    
    
    categoria_dados = [ ]
    for categoria in categorias:
        categoria_acerto = desafio.flashcards.filter(flashcard__categoria=categoria, acertou=True).count()
        categoria_errou = desafio.flashcards.filter(flashcard__categoria=categoria, acertou=False).count()
        categoria_total = desafio.flashcards.filter(flashcard__categoria=categoria).count()
        categoria_dados.append({
            'acertou': categoria_acerto,
            'errou': categoria_errou,
            'nome': categoria.nome,
            'total': categoria_total
            
        })

    name_categoria = [i.nome for i in categorias]
    #for i in categorias:
    #    name_categoria.append(i.nome)

    dados2 = []

    for categoria in categorias:
        dados2.append(desafio.flashcards.filter(flashcard__categoria=categoria).filter(acertou=True).count())

    return render (request, 'relatorio.html', {'desafio':desafio, 'dados':dados, 'categoria_dados':categoria_dados, 'categorias':name_categoria, 'dados2':dados2})

@login_required
def usuario (request):
    if request.method == "GET":
        info_usu = request.user
        categorias = Categoria.objects.filter(id=request.user.id)
        print(categorias)
    if request.method == "POST":
        usu_novo = request.POST.get('login')
        senha_novo = request.POST.get('new_password')

        if request.user.is_authenticated:
            try:
                if usu_novo and usu_novo != request.user.username:
                    if User.objects.filter(username=usu_novo).exists():
                        raise IntegrityError ('Usuário já existe')              
                    request.user.username = usu_novo
                    request.user.save()
                    update_session_auth_hash(request, request.user)
                if senha_novo:
                    request.user.set_password(senha_novo)
                    request.user.save()
                    update_session_auth_hash(request, request.user)

            except IntegrityError:  
                messages.add_message(request, constants.ERROR, 'Nome de usuário já existe.')
                return redirect(reverse('usuario'))

        messages.add_message(request, constants.SUCCESS, 'Alteração realizada com sucesso')
        return redirect ('/flashcard/usuario/')
        
    return render(request, 'usuario.html', {'info_usu':info_usu, 'categorias':categorias })


