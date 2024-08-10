from django.shortcuts import get_object_or_404, render,redirect
from django.http import JsonResponse,HttpResponse
from .models import Banner,Category, CustomUser,Product,ProductAttribute,CartOrder,CartOrderItems,ProductReview,Wishlist
from django.db.models import Max,Min,Count,Avg
from django.db.models.functions import ExtractMonth
from django.template.loader import render_to_string
from .forms import ProductAttributeForm, ProductForm, SignupForm,ReviewAdd,ProfileForm
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
#paypal
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.db.models import Avg





class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    
    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        if form.get_user().role == 'ARTISAN':
            return redirect('my_dashboard')
        elif form.get_user().role == 'CLIENT':
            return redirect('client_home')
        else:
            return redirect('home') 

# Define home views for each role
@login_required
def artisan_home(request):
    return render(request, 'user/dashboard.html')


@login_required
def client_home(request):
    data = Product.objects.all()
    min_price = ProductAttribute.objects.aggregate(Min('price'))
    max_price = ProductAttribute.objects.aggregate(Max('price'))

    return render(request, 'user/client_home.html', {
        'data': data,
        'min_price': min_price,
        'max_price': max_price,
    })



# Home Page
def home(request):
	banners=Banner.objects.all().order_by('-id')
	data=Product.objects.filter(is_featured=True).order_by('-id')
	return render(request,'index.html',{'data':data,'banners':banners})

# Category
def category_list(request):
    data=Category.objects.all().order_by('-id')
    return render(request,'category_list.html',{'data':data})

def product_list(request):
    print("here")
    total_data = Product.objects.count()
    data = Product.objects.prefetch_related('productattribute_set').all()

    min_price = ProductAttribute.objects.aggregate(Min('price'))['price__min']
    max_price = ProductAttribute.objects.aggregate(Max('price'))['price__max']

    # Debugging print statements
    print("Total Products:", total_data)
    print("Products Data:", data)
    print("Min Price:", min_price)
    print("Max Price:", max_price)

    return render(request, 'product_list.html', {
        'data': data,
        'total_data': total_data,
        'min_price': min_price,
        'max_price': max_price,
    })




def category_product_list(request, cat_id):
    category = Category.objects.get(id=cat_id)
    data = Product.objects.filter(category=category).annotate(
        average_rating=Avg('productreview__review_rating')
    ).order_by('-id')

    return render(request, 'category_product_list.html', {
        'data': data,
    })


# Product Detail
def product_detail(request, slug, id):
    # Fetch the product or return 404 if not found
    product = get_object_or_404(Product, id=id)

    # Fetch related products by category, excluding the current product
    related_products = Product.objects.filter(category=product.category).exclude(id=id)[:4]

    # Fetch distinct colors and sizes for the product
    # Since color and size are now CharField, you don't need to use double underscores
    attributes = ProductAttribute.objects.filter(product=product).values('color', 'size', 'price').distinct()

    # Extract distinct colors and sizes
    colors = attributes.values_list('color', flat=True).distinct()
    sizes = attributes.values_list('size', flat=True).distinct()

    # Initialize the review form
    reviewForm = ReviewAdd()

    # Check if the user can add a review
    canAdd = True
    if request.user.is_authenticated:
        reviewCheck = ProductReview.objects.filter(user=request.user, product=product).count()
        if reviewCheck > 0:
            canAdd = False

    # Fetch all reviews for the product
    reviews = ProductReview.objects.filter(product=product)

    # Calculate the average rating for the product
    avg_reviews = ProductReview.objects.filter(product=product).aggregate(avg_rating=Avg('review_rating'))

    # Render the template with context
    return render(request, 'product_detail.html', {
        'data': product,
        'related': related_products,
        'colors': colors,
        'sizes': sizes,
        'reviewForm': reviewForm,
        'canAdd': canAdd,
        'reviews': reviews,
        'avg_reviews': avg_reviews
    })

# Search
def search(request):
	q=request.GET['q']
	data=Product.objects.filter(title__icontains=q).order_by('-id')
	return render(request,'search.html',{'data':data})

def filter_data(request):
    # Safely get query parameters
    colors = request.GET.getlist('color')  # Get list of selected colors
    categories = request.GET.getlist('category[]')  # Get list of selected categories
    sizes = request.GET.getlist('size')  # Get list of selected sizes
    min_price = request.GET.get('minPrice', 0)  # Default to 0 if not provided
    max_price = request.GET.get('maxPrice', float('inf'))  # Default to infinity if not provided

    # Query all products and apply filters
    all_products = Product.objects.all().order_by('-id').distinct()
    
    # Apply price range filter
    all_products = all_products.filter(productattribute__price__gte=min_price)
    all_products = all_products.filter(productattribute__price__lte=max_price)
    
    # Apply color filter if colors are selected
    if colors:
        all_products = all_products.filter(productattribute__color__in=colors).distinct()
    
    # Apply category filter if categories are selected
    if categories:
        all_products = all_products.filter(category__id__in=categories).distinct()
    
    # Apply size filter if sizes are selected
    if sizes:
        all_products = all_products.filter(productattribute__size__in=sizes).distinct()

    # Render filtered products to HTML
    html = render_to_string('ajax/product-list.html', {'data': all_products})
    
    # Return response as JSON
    return JsonResponse({'data': html})

# Load More
def load_more_data(request):
	offset=int(request.GET['offset'])
	limit=int(request.GET['limit'])
	data=Product.objects.all().order_by('-id')[offset:offset+limit]
	t=render_to_string('ajax/product-list.html',{'data':data})
	return JsonResponse({'data':t}
)








def add_to_cart(request):
    product_id = str(request.GET.get('id', '')).strip()
    image = request.GET.get('image', 'path/to/default/image.jpg').strip()
    title = request.GET.get('title', 'No Title').strip()
    qty_str = request.GET.get('qty', '1').strip()
    price_str = request.GET.get('price', '0').strip()

    print(f"Product ID: {product_id}")
    print(f"Image: {image}")
    print(f"Title: {title}")
    print(f"Quantity: {qty_str}")
    print(f"Price: {price_str}")

    try:
        qty = int(qty_str)
        price = float(price_str) if price_str else 0
    except ValueError:
        qty = 1
        price = 0

    if not product_id:
        print("Error: Product ID is missing.")
        return redirect(reverse('cart'))  # Redirect back to wishlist if product ID is missing

    # Prepare the product data to add to cart
    cart_p = {
        product_id: {
            'image': image,
            'title': title,
            'qty': qty,
            'price': price,
        }
    }

    if 'cartdata' in request.session:
        cart_data = request.session['cartdata']
        if product_id in cart_data:
            cart_data[product_id]['qty'] += qty  # Increment quantity if the item is already in the cart
        else:
            cart_data.update(cart_p)  # Add new item to the cart
        request.session['cartdata'] = cart_data
    else:
        request.session['cartdata'] = cart_p

    return redirect(reverse('cart'))









def cart_list(request):
    total_amt = 0
    cart_data = request.session.get('cartdata', {})

    for p_id, item in cart_data.items():
        try:
            qty = int(item.get('qty', 0))  # Default to 0 if qty is missing or invalid
            price = float(item.get('price', 0))  # Default to 0 if price is missing or invalid
            total_amt += qty * price
        except (ValueError, TypeError):
            # Handle cases where qty or price are invalid
            continue

    return render(request, 'cart.html', {
        'cart_data': cart_data,
        'totalitems': len(cart_data),
        'total_amt': total_amt
    })


# Delete Cart Item
def delete_cart_item(request):
	p_id=str(request.GET['id'])
	if 'cartdata' in request.session:
		if p_id in request.session['cartdata']:
			cart_data=request.session['cartdata']
			del request.session['cartdata'][p_id]
			request.session['cartdata']=cart_data
	total_amt=0
	for p_id,item in request.session['cartdata'].items():
		total_amt+=int(item['qty'])*float(item['price'])
	t=render_to_string('ajax/cart-list.html',{'cart_data':request.session['cartdata'],'totalitems':len(request.session['cartdata']),'total_amt':total_amt})
	return JsonResponse({'data':t,'totalitems':len(request.session['cartdata'])})

# Delete Cart Item
def update_cart_item(request):
	p_id=str(request.GET['id'])
	p_qty=request.GET['qty']
	if 'cartdata' in request.session:
		if p_id in request.session['cartdata']:
			cart_data=request.session['cartdata']
			cart_data[str(request.GET['id'])]['qty']=p_qty
			request.session['cartdata']=cart_data
	total_amt=0
	for p_id,item in request.session['cartdata'].items():
		total_amt+=int(item['qty'])*float(item['price'])
	t=render_to_string('ajax/cart-list.html',{'cart_data':request.session['cartdata'],'totalitems':len(request.session['cartdata']),'total_amt':total_amt})
	return JsonResponse({'data':t,'totalitems':len(request.session['cartdata'])})








def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            pwd = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=pwd)
            if user is not None:
                auth_login(request, user)
                if user.role == CustomUser.ARTISAN:
                    return redirect('artisan_home')
                elif user.role == CustomUser.CLIENT:
                    return redirect('client_home')
                else:
                    return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})

# Checkout
@login_required
def checkout(request):
	total_amt=0
	totalAmt=0
	if 'cartdata' in request.session:
		for p_id,item in request.session['cartdata'].items():
			totalAmt+=int(item['qty'])*float(item['price'])
		# Order
		order=CartOrder.objects.create(
				user=request.user,
				total_amt=totalAmt
			)
		# End
		for p_id,item in request.session['cartdata'].items():
			total_amt+=int(item['qty'])*float(item['price'])
			# OrderItems
			items=CartOrderItems.objects.create(
				order=order,
				invoice_no='INV-'+str(order.id),
				item=item['title'],
				image=item['image'],
				qty=item['qty'],
				price=item['price'],
				total=float(item['qty'])*float(item['price'])
				)
			# End
		# Process Payment
		host = request.get_host()
		paypal_dict = {
		    'business': settings.PAYPAL_RECEIVER_EMAIL,
		    'amount': total_amt,
		    'item_name': 'OrderNo-'+str(order.id),
		    'invoice': 'INV-'+str(order.id),
		    'currency_code': 'USD',
		    'notify_url': 'http://{}{}'.format(host,reverse('paypal-ipn')),
		    'return_url': 'http://{}{}'.format(host,reverse('payment_done')),
		    'cancel_return': 'http://{}{}'.format(host,reverse('payment_cancelled')),
		}
		form = PayPalPaymentsForm(initial=paypal_dict)
		address="random address test"
		return render(request, 'checkout.html',{'cart_data':request.session['cartdata'],'totalitems':len(request.session['cartdata']),'total_amt':total_amt,'form':form,'address':address})

@csrf_exempt
def payment_done(request):
	returnData=request.POST
	return render(request, 'payment-success.html',{'data':returnData})


@csrf_exempt
def payment_canceled(request):
	return render(request, 'payment-fail.html')


# Save Review
def save_review(request,pid):
	product=Product.objects.get(pk=pid)
	user=request.user
	review=ProductReview.objects.create(
		user=user,
		product=product,
		review_text=request.POST['review_text'],
		review_rating=request.POST['review_rating'],
		)
	data={
		'user':user.username,
		'review_text':request.POST['review_text'],
		'review_rating':request.POST['review_rating']
	}

	# Fetch avg rating for reviews
	avg_reviews=ProductReview.objects.filter(product=product).aggregate(avg_rating=Avg('review_rating'))
	# End

	return JsonResponse({'bool':True,'data':data,'avg_reviews':avg_reviews})

# User Dashboard


from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import ExtractMonth
import calendar
from .models import CartOrder  # Ensure the model is imported

def my_dashboard(request):
    # Get the logged-in artisan
    artisan = request.user

    # Filter orders by the logged-in artisan and only include paid orders
    orders_by_month = CartOrder.objects.filter(
        user=artisan, paid_status=True  # Use paid_status if that's the correct field for payment status
    ).annotate(
        month=ExtractMonth('order_dt')
    ).values('month').annotate(
        count=Count('id')
    ).values('month', 'count')

    # Prepare month names and counts for the chart
    monthNumber = []
    totalOrders = []
    
    for d in orders_by_month:
        # Get month name from the month number
        month_name = calendar.month_name[d['month']]
        monthNumber.append(month_name)
        totalOrders.append(d['count'])
    
    return render(request, 'user/dashboard.html', {
        'monthNumber': monthNumber,
        'totalOrders': totalOrders,
    })


# My Orders
def my_orders(request):
	orders=CartOrder.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/orders.html',{'orders':orders})

# Order Detail
def my_order_items(request,id):
	order=CartOrder.objects.get(pk=id)
	orderitems=CartOrderItems.objects.filter(order=order).order_by('-id')
	return render(request, 'user/order-items.html',{'orderitems':orderitems})

# Wishlist
def add_wishlist(request):
    pid = request.GET.get('product')
    product = get_object_or_404(Product, pk=pid)
    
    if not Wishlist.objects.filter(product=product, user=request.user).exists():
        Wishlist.objects.create(product=product, user=request.user)
    
    return redirect('my_wishlist')

def remove_wishlist(request):
    pid = request.GET.get('product')
    product = get_object_or_404(Product, pk=pid)
    
    Wishlist.objects.filter(product=product, user=request.user).delete()
    
    return redirect('my_wishlist')

# My Wishlist
def my_wishlist(request):
	wlist=Wishlist.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/wishlist.html',{'wlist':wlist})



# My Reviews
def my_reviews(request):

    artisan = request.user
    products = Product.objects.filter(user=artisan)
    reviews = ProductReview.objects.filter(product__in=products).order_by('-id')
    print(f'Number of reviews found: {reviews.count()}')
    for review in reviews[:5]:
        print(f'Review ID: {review.id}, Product: {review.product.title}, Rating: {review.review_rating}')
    return render(request, 'user/reviews.html', {'reviews': reviews})




# Edit Profile
def edit_profile(request):
	msg=None
	if request.method=='POST':
		form=ProfileForm(request.POST,instance=request.user)
		if form.is_valid():
			form.save()
			msg='Data has been saved'
	form=ProfileForm(instance=request.user)
	return render(request, 'user/edit-profile.html',{'form':form,'msg':msg})

# Update addressbook


def create_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            product = form.save()  # Save the Product instance

            # Handle ProductAttributes
            for i in range(int(request.POST.get('attribute_count', 0))):
                color = request.POST.get(f'color_{i}')
                size = request.POST.get(f'size_{i}')
                price = request.POST.get(f'price_{i}')
                image = request.FILES.get(f'image_{i}')
                
                if color and size and price:  # Ensure all required fields are provided
                    ProductAttribute.objects.create(
                        product=product,
                        color=color,
                        size=size,
                        price=price,
                        image=image
                    )
            
            return redirect('my_services')  # Replace with your success URL
    else:
        form = ProductForm(user=request.user)
    
    return render(request, 'create_product.html', {'form': form})

def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not request.user.role == 'ARTISAN':
        raise PermissionDenied("You do not have permission to update this product.")

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, user=request.user)
        if form.is_valid():
            # Save the Product instance
            form.save()

            # Handle ProductAttributes
            existing_attributes = ProductAttribute.objects.filter(product=product)
            existing_attributes_dict = {attr.id: attr for attr in existing_attributes}

            # Process the POST data for attributes
            for i in range(int(request.POST.get('attribute_count', 0))):
                color = request.POST.get(f'color_{i}')
                size = request.POST.get(f'size_{i}')
                price = request.POST.get(f'price_{i}')
                image = request.FILES.get(f'image_{i}')
                attribute_id = request.POST.get(f'attribute_id_{i}')

                if color and size and price:  # Ensure all required fields are provided
                    if attribute_id:  # Update existing attribute
                        attribute = existing_attributes_dict.get(int(attribute_id))
                        if attribute:
                            attribute.color = color
                            attribute.size = size
                            attribute.price = price
                            if image:
                                attribute.image = image
                            attribute.save()
                            del existing_attributes_dict[int(attribute_id)]  # Remove updated attribute from dict
                    else:  # Create new attribute
                        ProductAttribute.objects.create(
                            product=product,
                            color=color,
                            size=size,
                            price=price,
                            image=image
                        )
            
            # Delete any remaining attributes that were not included in the update
            for attribute in existing_attributes_dict.values():
                attribute.delete()

            return redirect('my_services')
    else:
        form = ProductForm(instance=product)
        # Optionally, you can include existing attributes in context if needed
        existing_attributes = ProductAttribute.objects.filter(product=product)
    
    return render(request, 'update_product.html', {'form': form, 'existing_attributes': existing_attributes})

def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not request.user.role == 'ARTISAN':
        raise PermissionDenied("You do not have permission to delete this product.")

    if request.method == 'POST':
        product.delete()
        return redirect('my_services')

    return render(request, 'confirm_delete_product.html', {'product': product})

def my_services(request):
    if not request.user.role == 'ARTISAN':
        raise PermissionDenied("You do not have permission to view services.")

    products = Product.objects.filter(user=request.user)
    return render(request, 'my_services.html', {'products': products})

def review_detail(request, pk):
    review = get_object_or_404(ProductReview, pk=pk)
    return render(request, 'user/review_detail.html', {'review': review})

def service_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'service_detail.html', {'product': product})