from django import forms
from django.contrib.auth.models import User
from .models import Culture, Entrepot, Livraison, Producteur, Recolte, Zone

class InscriptionProducteurForm(forms.ModelForm):
    username = forms.CharField(label="Nom d'utilisateur", widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label="Prénom", widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label="Nom", widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Producteur
        fields = ['telephone', 'zone', 'parcelles_info']
        widgets = {
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'zone': forms.Select(attrs={'class': 'form-control'}),
            'parcelles_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        

class MagasinierForm(forms.ModelForm):
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }



class EntrepotForm(forms.ModelForm):
    class Meta:
        model = Entrepot
        fields = ['nom', 'zone', 'responsable', 'capacite_max', 'seuil_alerte']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Magasin Central'}),
            'zone': forms.Select(attrs={'class': 'form-control'}),
            'responsable': forms.Select(attrs={'class': 'form-control'}),
            'capacite_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
        
class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ['commune', 'arrondissement', 'village']
        widgets = {
            'commune': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Parakou'}),
            'arrondissement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1er Arrondissement'}),
            'village': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Kpébié'}),
        }
        
        
class RecolteForm(forms.ModelForm):
    class Meta:
        model = Recolte
        fields = ['type_culture', 'quantite', 'date_recolte', 'entrepot_destination']
        widgets = {
            'type_culture': forms.Select(attrs={'class': 'form-select'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Poids en kg'}),
            'date_recolte': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'entrepot_destination': forms.Select(attrs={'class': 'form-select'}),
        }


class CultureForm(forms.ModelForm):
    class Meta:
        model = Culture
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Maïs, Soja...'}),
        }
        



class LivraisonForm(forms.ModelForm):
    class Meta:
        model = Livraison
        fields = ['client', 'entrepot_source', 'type_culture', 'quantite']
        widgets = {
            'client': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'entreprise'}),
            'entrepot_source': forms.Select(attrs={'class': 'form-select'}),
            'type_culture': forms.Select(attrs={'class': 'form-select'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 500'}),
        }

    def clean_quantite(self):
        quantite = self.cleaned_data.get('quantite')
        if quantite <= 0:
            raise forms.ValidationError("La quantité doit être supérieure à 0.")
        return quantite