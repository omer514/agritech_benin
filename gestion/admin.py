from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Zone, Culture, Producteur, Recolte, Entrepot

# Configuration de l'affichage pour la table Entrepot
class EntrepotAdmin(admin.ModelAdmin):
    # On choisit les colonnes à afficher dans la liste
    list_display = ('nom', 'zone', 'stock_actuel', 'capacite_max', 'seuil_alerte')
    # On ajoute une barre de recherche
    search_fields = ('nom',)

# On enregistre tous nos modèles
admin.site.register(Zone)
admin.site.register(Culture)
admin.site.register(Producteur)
admin.site.register(Recolte)
admin.site.register(Entrepot, EntrepotAdmin)