from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,UserChangeForm
from .models import  Category, CustomUser, Product, ProductAttribute, ProductReview
from django.forms import inlineformset_factory


class SignupForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'username', 'password1', 'password2', 'role')
		
# Review Add Form
class ReviewAdd(forms.ModelForm):
	class Meta:
		model=ProductReview
		fields=('review_text','review_rating')



# ProfileEdit
class ProfileForm(UserChangeForm):
	class Meta:
		model=User
		fields=('first_name','last_name','email','username')

class ProductForm(forms.ModelForm):
    OTHER_OPTION = 'other'
    
    class Meta:
        model = Product
        fields = ['title', 'slug', 'detail', 'specs', 'category', 'status', 'is_featured']
    
    other_category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter other category', 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Extract 'user' from kwargs
        super().__init__(*args, **kwargs)  # Call the parent class's __init__ method

        # Populate categories with an "Other" option
        categories = list(Category.objects.all().values_list('id', 'title'))
        categories.append((self.OTHER_OPTION, 'Other'))
        self.fields['category'].choices = categories
        self.fields['category'].widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()

        # Ensure the user has the 'ARTISAN' role
        if self.user and self.user.role != 'ARTISAN':
            raise forms.ValidationError("Only users with the 'ARTISAN' role can post products.")

        # Handle the "Other" option for category 
        category = cleaned_data.get('category')
        other_category = cleaned_data.get('other_category')
        if category == self.OTHER_OPTION and not other_category:
            self.add_error('other_category', "Please specify the other category.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Assign the custom category if "Other" was selected
        if self.cleaned_data['category'] == self.OTHER_OPTION:
            category, created = Category.objects.get_or_create(title=self.cleaned_data['other_category'])
            instance.category = category

        # Ensure the user is assigned to the product
        if self.user:
            instance.user = self.user

        if commit:
            instance.save()

        return instance
    


class ProductAttributeForm(forms.ModelForm):
    color = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter color', 'class': 'form-control'})
    )
    size = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter size', 'class': 'form-control'})
    )
    price = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter price', 'class': 'form-control'})
    )
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ProductAttribute
        fields = ['color', 'size', 'price', 'image']