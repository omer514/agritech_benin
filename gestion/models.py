from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save

from django.contrib.auth.models import User
from django.dispatch import receiver

# Table pour la localisation géographique
class Zone(models.Model):
    commune = models.CharField(max_length=100, verbose_name="Commune")
    arrondissement = models.CharField(max_length=100, verbose_name="Arrondissement")
    village = models.CharField(max_length=100, verbose_name="Village/Quartier", help_text="Ex: Kpébié, Fidjrossè, etc.")

    class Meta:
        verbose_name = "Zone géographique"
        unique_together = ('commune', 'arrondissement', 'village') # Évite les doublons exacts

    def __str__(self):
        # Format : "Village (Arrondissement, Commune)"
        return f"{self.village} - {self.arrondissement} ({self.commune})"

    
    
class Producteur(models.Model):
    # Lien vers l'utilisateur Django (nom d'utilisateur, mot de passe)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=15)
    # Lien vers la zone (Une zone peut avoir plusieurs producteurs)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True)
    parcelles_info = models.TextField(verbose_name="Localisation des parcelles")

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
 # On crée une table dédiée pour les types de produits
class Culture(models.Model):
    nom = models.CharField(max_length=50, unique=True) # Ex: Maïs, Soja, Tomate

    def __str__(self):
        return self.nom
class Recolte(models.Model):
    STATUTS = [
        ('EN_ATTENTE', 'En attente'),
        ('RECU', 'Reçu au magasin'),
    ]

    producteur = models.ForeignKey(Producteur, on_delete=models.CASCADE)
    type_culture = models.ForeignKey(Culture, on_delete=models.PROTECT) 
    quantite = models.FloatField(verbose_name="Quantité (kg)")
    date_recolte = models.DateField()
    
    # --- ON AJOUTE CES DEUX CHAMPS ---
    entrepot_destination = models.ForeignKey('Entrepot', on_delete=models.SET_NULL, null=True, verbose_name="Dépôt vers")
    statut = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    # ---------------------------------

    def __str__(self):
        return f"{self.type_culture} - {self.quantite}kg ({self.producteur})"
# 4. La Table Stockage (Entrepôts)
class Entrepot(models.Model):
    nom = models.CharField(max_length=100)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE)
    
    # Ajout du responsable (Magasinier). 
    # On filtre pour ne proposer que les utilisateurs qui font partie du Staff.
    responsable = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'is_staff': True},
        verbose_name="Magasinier responsable"
    )
    
    capacite_max = models.FloatField(verbose_name="Capacité totale (kg)")
    stock_actuel = models.FloatField(default=0, verbose_name="Stock actuel (kg)")
    seuil_alerte = models.FloatField(verbose_name="Seuil d'alerte minimum (kg)")

    def __str__(self):
        return f"{self.nom} ({self.zone.arrondissement})"
    
    
    # --- NOUVELLE MÉTHODE POUR LE DÉTAIL PAR CULTURE ---
    def obtenir_inventaire_detaille(self):
        """Calcule dynamiquement le stock pour chaque type de culture"""
        from .models import Recolte, Livraison, Culture
        inventaire = []
        cultures = Culture.objects.all()
        
        total_general = 0 # Pour vérifier la cohérence
        
        for culture in cultures:
            # Somme des récoltes reçues ici
            entrees = Recolte.objects.filter(
                entrepot_destination=self, 
                type_culture=culture, 
                statut='RECU'
            ).aggregate(total=Sum('quantite'))['total'] or 0
            
            # Somme des livraisons expédiées d'ici
            sorties = Livraison.objects.filter(
                entrepot_source=self, 
                type_culture=culture, 
                statut='EXPEDIE'
            ).aggregate(total=Sum('quantite'))['total'] or 0
            
            stock_culture = entrees - sorties
            total_general += stock_culture
            
            if entrees > 0:
                inventaire.append({
                    'culture': culture.nom,
                    'entrees': entrees,
                    'sorties': sorties,
                    'stock': stock_culture,
                })
        
        # Optionnel : mettre à jour le champ stock_actuel automatiquement
        # self.stock_actuel = total_general
        
        return inventaire

    # Logique pour savoir si le stock est bas
    def est_en_alerte(self):
        return self.stock_actuel < self.seuil_alerte

    # Calcul du pourcentage pour les barres de progression HTML
    def taux_remplissage(self):
        if self.capacite_max > 0:
            return (self.stock_actuel / self.capacite_max) * 100
        return 0


class Livraison(models.Model):
    STATUT_LIVRAISON = [
        ('PROGRAMME', 'Programmé (En attente)'),
        ('EXPEDIE', 'Expédié (Sorti du stock)'),
        ('ANNULE', 'Annulé'),
    ]
    
    client = models.CharField(max_length=200, verbose_name="Entreprise Cliente")
    entrepot_source = models.ForeignKey(Entrepot, on_delete=models.CASCADE, verbose_name="Entrepôt d'origine")
    
    # Utilisation de votre classe Culture ici
    type_culture = models.ForeignKey(Culture, on_delete=models.PROTECT, verbose_name="Produit / Culture")
    
    quantite = models.PositiveIntegerField(verbose_name="Quantité (kg)")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expedition = models.DateTimeField(null=True, blank=True, verbose_name="Date effective de sortie")
    statut = models.CharField(max_length=20, choices=STATUT_LIVRAISON, default='PROGRAMME')
    
    ordonne_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sorties_ordonnees')
    confirme_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sorties_confirmees')

    def __str__(self):
        return f"Livraison {self.client} - {self.quantite}kg de {self.type_culture.nom}"

    class Meta:
        verbose_name = "Livraison / Sortie"
