from django.contrib import messages as messages_django
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from django.db import transaction

from gestion.forms import CultureForm, EntrepotForm,  InscriptionProducteurForm, LivraisonForm, MagasinierForm, RecolteForm, ZoneForm
from .models import Culture, Livraison, Recolte, Producteur, Entrepot, Zone

@login_required
def liste_recoltes(request):
    if request.user.is_superuser:
        recoltes = Recolte.objects.all().order_by('-date_recolte')
    elif request.user.is_staff:
        mes_entrepots = Entrepot.objects.filter(responsable=request.user)
        recoltes = Recolte.objects.filter(entrepot_destination__in=mes_entrepots).order_by('-date_recolte')
    else:
        producteur_profil = get_object_or_404(Producteur, user=request.user)
        recoltes = Recolte.objects.filter(producteur=producteur_profil).order_by('-date_recolte')

    # --- NOUVEAUX CALCULS POUR LES COMPTEURS ---
    stats_en_attente = recoltes.filter(statut='EN_ATTENTE').count()
    stats_validees = recoltes.filter(statut='RECU').count()
    # Calcul de la somme totale des quantités (retourne 0 si aucune récolte)
    somme_totale = recoltes.aggregate(total=Sum('quantite'))['total'] or 0

    context = {
        'recoltes': recoltes,
        'stats_en_attente': stats_en_attente,
        'stats_validees': stats_validees,
        'stats_quantite_totale': somme_totale,
    }

    return render(request, 'gestion/recolte/liste.html', context)


def dashboard_admin(request):
    entrepots = Entrepot.objects.all()
    # Calcul plus efficace de la somme
    total_recoltes = Recolte.objects.aggregate(Sum('quantite'))['quantite__sum'] or 0
    
    context = {
        'entrepots': entrepots,
        'total_recoltes': total_recoltes,
        'total_producteurs': Producteur.objects.count(),
        'total_zones': Zone.objects.count(),
        'alertes_count': sum(1 for e in entrepots if e.est_en_alerte()),
    }
    return render(request, 'gestion/dashboard.html', context)

@staff_member_required
def ajouter_membre(request):
    if request.method == 'POST':
        form = InscriptionProducteurForm(request.POST)
        if form.is_valid():
            # Création de l'User Django
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            # Création du profil Producteur lié
            producteur = form.save(commit=False)
            producteur.user = user
            producteur.save()
            return redirect('dashboard_admin')
    else:
        form = InscriptionProducteurForm()
    return render(request, 'gestion/ajouter_membre.html', {'form': form})


@staff_member_required
def liste_utilisateurs(request):
    # On récupère tous les utilisateurs sauf celui connecté
    utilisateurs = User.objects.exclude(id=request.user.id)
    
    # Calcul exact des compteurs
    # Producteurs : is_staff=False et is_superuser=False
    count_producteurs = utilisateurs.filter(is_staff=False, is_superuser=False).count()
    
    # Magasiniers : is_staff=True et is_superuser=False
    count_magasiniers = utilisateurs.filter(is_staff=True, is_superuser=False).count()
    
    # Administrateurs : is_superuser=True
    count_admins = utilisateurs.filter(is_superuser=True).count()

    context = {
        'utilisateurs': utilisateurs,
        'count_producteurs': count_producteurs,
        'count_magasiniers': count_magasiniers,
        'count_admins': count_admins,
    }
    
    return render(request, 'gestion/liste_utilisateurs.html', context)
@staff_member_required
def supprimer_utilisateur(request, user_id):
    utilisateur = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        utilisateur.delete()
        return redirect('liste_utilisateurs')
    return render(request, 'gestion/confirmer_suppression.html', {'utilisateur': utilisateur})



@staff_member_required
def modifier_utilisateur(request, user_id):
    utilisateur = get_object_or_404(User, id=user_id)
    # On récupère le profil producteur s'il existe
    producteur = getattr(utilisateur, 'producteur', None)
    
    if request.method == 'POST':
        # On remplit le formulaire avec les données envoyées
        form = InscriptionProducteurForm(request.POST, instance=producteur)
        if form.is_valid():
            # Mise à jour des infos de base de l'User
            utilisateur.first_name = form.cleaned_data['first_name']
            utilisateur.last_name = form.cleaned_data['last_name']
            utilisateur.username = form.cleaned_data['username']
            if form.cleaned_data['password']: # On ne change le pass que s'il est rempli
                utilisateur.set_password(form.cleaned_data['password'])
            utilisateur.save()
            
            # Mise à jour du profil Producteur
            if producteur:
                form.save()
            
            return redirect('liste_utilisateurs')
    else:
        # On pré-remplit le formulaire avec les données actuelles
        initial_data = {
            'username': utilisateur.username,
            'first_name': utilisateur.first_name,
            'last_name': utilisateur.last_name,
        }
        form = InscriptionProducteurForm(instance=producteur, initial=initial_data)
        # On rend le mot de passe non obligatoire pour la modification
        form.fields['password'].required = False
        form.fields['password'].help_text = "Laissez vide pour ne pas modifier"

    return render(request, 'gestion/modifier_utilisateur.html', {
        'form': form,
        'utilisateur': utilisateur
    })
    
def ajouter_magasinier(request):
    if request.method == 'POST':
        form = MagasinierForm(request.POST)
        if form.is_valid():
            # Création de l'utilisateur sans sauvegarder tout de suite
            user = form.save(commit=False)
            # On définit le mot de passe correctement (hachage)
            user.set_password(form.cleaned_data['password'])
            # On lui donne le rôle Magasinier (Staff)
            user.is_staff = True 
            user.save()
            return redirect('liste_utilisateurs')
    else:
        form = MagasinierForm()
    return render(request, 'gestion/ajouter_magasinier.html', {'form': form})




# Liste des entrepôts
def liste_entrepots(request):
    entrepots = Entrepot.objects.all()
    return render(request, 'gestion/entrepot/liste.html', {'entrepots': entrepots})

def ajouter_entrepot(request):
    if request.method == 'POST':
        form = EntrepotForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_entrepots')
    else:
        form = EntrepotForm()
    return render(request, 'gestion/entrepot/ajouter.html', {'form': form})
# Affecter un magasinier
def affecter_magasinier(request, entrepot_id):
    entrepot = get_object_or_404(Entrepot, id=entrepot_id)
    # On ne récupère que les magasiniers (is_staff=True)
    magasiniers = User.objects.filter(is_staff=True)
    
    if request.method == 'POST':
        user_id = request.POST.get('magasinier_id')
        if user_id:
            magasinier = get_object_or_404(User, id=user_id)
            entrepot.responsable = magasinier
            entrepot.save()
            return redirect('liste_entrepots')
            
    return render(request, 'gestion/entrepot/affecter.html', {
        'entrepot': entrepot,
        'magasiniers': magasiniers
    })
    
    
def liste_zones(request):
    zones = Zone.objects.all()
    return render(request, 'gestion/zone/liste.html', {'zones': zones})

def ajouter_zone(request):
    if request.method == 'POST':
        form = ZoneForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_zones')
    else:
        form = ZoneForm()
    return render(request, 'gestion/zone/ajouter.html', {'form': form})


def declarer_recolte(request):
    # On récupère le profil producteur de l'utilisateur connecté
    producteur_profil = get_object_or_404(Producteur, user=request.user)
    
    if request.method == 'POST':
        form = RecolteForm(request.POST)
        if form.is_valid():
            recolte = form.save(commit=False)
            recolte.producteur = producteur_profil
            recolte.save()
            return redirect('liste_recoltes')
    else:
        form = RecolteForm()
    
    return render(request, 'gestion/recolte/declarer.html', {'form': form})


@login_required
def valider_reception(request, recolte_id):
    if request.method == 'POST':
        recolte = get_object_or_404(Recolte, id=recolte_id)
        entrepot = recolte.entrepot_destination
        
        if not entrepot:
            messages_django.error(request, "Aucun entrepôt de destination défini.")
            return redirect('dashboard_magasinier')

        if recolte.statut == 'RECU':
            messages_django.warning(request, "Cette récolte a déjà été réceptionnée.")
            return redirect('dashboard_magasinier')

        stock_previsionnel = entrepot.stock_actuel + recolte.quantite
        if stock_previsionnel > entrepot.capacite_max:
            messages_django.error(request, f"L'entrepôt {entrepot.nom} est plein !")
            return redirect('dashboard_magasinier')

        # MISE À JOUR : On change le statut ET on ajoute au stock ici
        recolte.statut = 'RECU'
        recolte.save()
        
        entrepot.stock_actuel = stock_previsionnel
        entrepot.save()

        messages_django.success(request, f"Réception validée : {recolte.quantite}kg ajoutés.")
        
    return redirect('dashboard_magasinier')

        
@login_required(login_url='login') # Force la redirection vers login si non connecté
def home_redirect(request):
    if request.user.is_superuser:
        return redirect('dashboard_admin')
    elif request.user.is_staff:
        return redirect('dashboard_magasinier')
    else:
        return redirect('dashboard_producteur')

@login_required
def dashboard_magasinier(request):
    # On récupère les entrepôts dont l'utilisateur connecté est le responsable
    mes_entrepots = Entrepot.objects.filter(responsable=request.user)
    
    # On récupère les récoltes en attente pour ces entrepôts
    recoltes_en_attente = Recolte.objects.filter(
        entrepot_destination__in=mes_entrepots, 
        statut='EN_ATTENTE'
    ).order_by('-date_recolte')

    return render(request, 'gestion/dashboards/magasinier.html', {
        'entrepots': mes_entrepots,
        'recoltes_attente': recoltes_en_attente,
    })
    
@login_required
def dashboard_producteur(request):
    # On récupère le profil producteur lié à l'utilisateur connecté
    # Note : Assure-toi que ton modèle s'appelle bien Producteur
    profil = get_object_or_404(Producteur, user=request.user)
    
    # Récupérer ses 5 dernières récoltes
    dernieres_recoltes = Recolte.objects.filter(producteur=profil).order_by('-date_recolte')[:5]
    
    # Calculer le total des quantités livrées (statut 'RECU')
    total_livre = Recolte.objects.filter(
        producteur=profil, 
        statut='RECU'
    ).aggregate(Sum('quantite'))['quantite__sum'] or 0

    return render(request, 'gestion/dashboards/producteur.html', {
        'profil': profil,
        'recoltes': dernieres_recoltes,
        'total_livre': total_livre,
    })
    
    
def landing_page(request):
    # Si l'utilisateur est déjà connecté, on l'envoie direct vers son dashboard
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'gestion/index.html')


@staff_member_required
def liste_cultures(request):
    cultures = Culture.objects.all()
    return render(request, 'gestion/culture/liste.html', {'cultures': cultures})

@staff_member_required
def ajouter_culture(request):
    if request.method == 'POST':
        form = CultureForm(request.POST)
        if form.is_valid():
            form.save()
            messages_django.success(request, "Nouvelle culture ajoutée !")
            return redirect('liste_cultures')
    else:
        form = CultureForm()
    return render(request, 'gestion/culture/ajouter.html', {'form': form})

@staff_member_required
def supprimer_culture(request, culture_id):
    culture = get_object_or_404(Culture, id=culture_id)
    if request.method == 'POST':
        culture.delete()
        messages_django.success(request, "Culture supprimée avec succès.")
        return redirect('liste_cultures')
    return render(request, 'gestion/culture/confirmer_suppression.html', {'culture': culture})



@login_required
def creer_livraison(request):
    if not request.user.is_superuser:
        messages_django.error(request, "Accès réservé à l'administration.")
        return redirect('dashboard')

    if request.method == 'POST':
        entrepot_id = request.POST.get('entrepot')
        culture_id = request.POST.get('culture')
        quantite = int(request.POST.get('quantite'))
        client = request.POST.get('client')

        # 1. Vérification du stock disponible avant de créer l'ordre
        # (Calcul : Entrées RECU - Sorties EXPEDIE)
        entrees = Recolte.objects.filter(
            entrepot_destination_id=entrepot_id, 
            type_culture_id=culture_id, 
            statut='RECU'
        ).aggregate(total=Sum('quantite'))['total'] or 0
        
        sorties = Livraison.objects.filter(
            entrepot_source_id=entrepot_id, 
            type_culture_id=culture_id, 
            statut='EXPEDIE'
        ).aggregate(total=Sum('quantite'))['total'] or 0
        
        stock_reel = entrees - sorties

        if quantite > stock_reel:
            messages_django.error(request, f"Stock insuffisant ! Disponible : {stock_reel} kg")
        else:
            Livraison.objects.create(
                client=client,
                entrepot_source_id=entrepot_id,
                type_culture_id=culture_id,
                quantite=quantite,
                ordonne_par=request.user,
                statut='PROGRAMME'
            )
            messages_django.success(request, "L'ordre de livraison a été envoyé au magasinier.")
            return redirect('liste_livraisons')

    entrepots = Entrepot.objects.all()
    cultures = Culture.objects.all()
    return render(request, 'gestion/livraison/formulaire.html', {
        'entrepots': entrepots,
        'cultures': cultures
    })
    
    


@login_required
def liste_livraisons(request):
    if request.user.is_superuser:
        # L'Admin voit toutes les livraisons
        livraisons = Livraison.objects.all().order_by('-date_creation')
    elif request.user.is_staff:
        # Le Magasinier voit les livraisons de SES entrepôts
        mes_entrepots = Entrepot.objects.filter(responsable=request.user)
        livraisons = Livraison.objects.filter(entrepot_source__in=mes_entrepots).order_by('-date_creation')
    else:
        # Les producteurs n'ont pas accès aux bons de livraison
        return redirect('dashboard')

    return render(request, 'gestion/livraison/liste.html', {'livraisons': livraisons})

def confirmer_expedition(request, livraison_id):
    # Seul un magasinier (staff) ou admin peut confirmer
    if not request.user.is_staff:
        messages_django.error(request, "Accès refusé.")
        return redirect('dashboard')
        
    livraison = get_object_or_404(Livraison, id=livraison_id)
    
    if request.method == "POST":
        # On récupère l'entrepôt concerné
        entrepot = livraison.entrepot_source
        
        # Sécurité : On vérifie si le stock est suffisant avant de confirmer
        if entrepot.stock_actuel >= livraison.quantite:
            # Utilisation de transaction.atomic pour être sûr que tout se passe bien
            with transaction.atomic():
                # 1. ON DIMINUE LE STOCK DE L'ENTREPOT
                entrepot.stock_actuel -= livraison.quantite
                entrepot.save()
                
                # 2. ON MET A JOUR LA LIVRAISON
                livraison.statut = 'EXPEDIE'
                livraison.date_expedition = timezone.now()
                livraison.confirme_par = request.user
                livraison.save()
                
            messages_django.success(request, f"La livraison pour {livraison.client} a été confirmée. Le stock de l'entrepôt {entrepot.nom} a été diminué de {livraison.quantite} kg.")
        else:
            # Cas où le stock est insuffisant
            messages_django.error(request, f"Erreur : Stock insuffisant dans {entrepot.nom} ({entrepot.stock_actuel} kg disponibles pour {livraison.quantite} kg demandés).")
        
    return redirect('liste_livraisons')

@login_required
def creer_livraison(request):
    if not request.user.is_superuser:
        messages_django.error(request, "Accès réservé à l'administration.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = LivraisonForm(request.POST)
        if form.is_valid():
            livraison = form.save(commit=False)
            livraison.ordonne_par = request.user
            livraison.statut = 'PROGRAMME'
            livraison.save()
            
            messages_django.success(request, f"Ordre de livraison pour {livraison.client} envoyé au magasinier.")
            return redirect('liste_livraisons')
    else:
        form = LivraisonForm()

    return render(request, 'gestion/livraison/formulaire.html', {'form': form})


def detail_entrepot_admin(request, pk):
    # On récupère l'entrepôt par sa clé primaire (id)
    entrepot = get_object_or_404(Entrepot, pk=pk)
    
    # On utilise la méthode de calcul automatique qu'on a créée dans le modèle
    inventaire = entrepot.obtenir_inventaire_detaille()
    
    # On récupère aussi les 10 derniers mouvements pour cet entrepôt
    dernieres_recoltes = Recolte.objects.filter(entrepot_destination=entrepot, statut='RECU').order_by('-date_recolte')[:5]
    dernieres_livraisons = Livraison.objects.filter(entrepot_source=entrepot, statut='EXPEDIE').order_by('-date_expedition')[:5]

    return render(request, 'gestion/admin/detail_entrepot.html', {
        'entrepot': entrepot,
        'inventaire': inventaire,
        'recoltes': dernieres_recoltes,
        'livraisons': dernieres_livraisons
    })