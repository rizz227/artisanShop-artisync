from .models import Product,ProductAttribute
from django.db.models import Min,Max
def get_filters(request):
	cats=Product.objects.distinct().values('category__title','category__id')
	minMaxPrice=ProductAttribute.objects.aggregate(Min('price'),Max('price'))
	data={
		'cats':cats,
		'minMaxPrice':minMaxPrice,
	}
	return data