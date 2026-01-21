from django.urls import path
from . import views

urlpatterns = [
   path('', views.landing_page, name='landing'), # Nouvelle page d'accueil
    path('home/', views.home_redirect, name='home'),
    
    # 2. Les différents tableaux de bord
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/magasinier/', views.dashboard_magasinier, name='dashboard_magasinier'),
    path('dashboard/producteur/', views.dashboard_producteur, name='dashboard_producteur'),

    # 3. Récoltes
    path('recoltes/', views.liste_recoltes, name='liste_recoltes'),
    path('recoltes/declarer/', views.declarer_recolte, name='declarer_recolte'),
    path('recoltes/valider/<int:recolte_id>/', views.valider_reception, name='valider_reception'),

    # 4. Utilisateurs / Membres
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('ajouter-membre/', views.ajouter_membre, name='ajouter_membre'),
    path('utilisateurs/ajouter-magasinier/', views.ajouter_magasinier, name='ajouter_magasinier'),
    path('utilisateurs/modifier/<int:user_id>/', views.modifier_utilisateur, name='modifier_utilisateur'),
    path('utilisateurs/supprimer/<int:user_id>/', views.supprimer_utilisateur, name='supprimer_utilisateur'),

    # 5. Entrepôts
    path('entrepots/', views.liste_entrepots, name='liste_entrepots'),
    path('entrepots/ajouter/', views.ajouter_entrepot, name='ajouter_entrepot'),
    path('entrepots/affecter/<int:entrepot_id>/', views.affecter_magasinier, name='affecter_magasinier'),
    
    # 6. Zones
    path('zones/', views.liste_zones, name='liste_zones'),
    path('zones/ajouter/', views.ajouter_zone, name='ajouter_zone'),
    
    
    # 7. cultures
    
    path('cultures/', views.liste_cultures, name='liste_cultures'),
    path('cultures/ajouter/', views.ajouter_culture, name='ajouter_culture'),
    path('cultures/supprimer/<int:culture_id>/', views.supprimer_culture, name='supprimer_culture'),
    
    
    path('livraisons/', views.liste_livraisons, name='liste_livraisons'),
    path('livraisons/creer/', views.creer_livraison, name='creer_livraison'),
    path('livraisons/confirmer/<int:livraison_id>/', views.confirmer_expedition, name='confirmer_expedition'),
    
    path('entrepot/<int:pk>/details/', views.detail_entrepot_admin, name='detail_entrepot_admin')
]