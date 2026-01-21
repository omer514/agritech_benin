from .models import Livraison, Entrepot

def notifications_livraison(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # L'admin voit toutes les livraisons programmées
            count = Livraison.objects.filter(statut='PROGRAMME').count()
            return {'count_livraisons_attente': count}
        
        elif request.user.is_staff:
            # Le magasinier voit seulement celles de ses entrepôts
            mes_entrepots = Entrepot.objects.filter(responsable=request.user)
            count = Livraison.objects.filter(entrepot_source__in=mes_entrepots, statut='PROGRAMME').count()
            return {'count_livraisons_attente': count}
            
    return {'count_livraisons_attente': 0}