from django.urls import path,include
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('artisan/home/', views.artisan_home, name='artisan_home'),
    path('client/home/', views.client_home, name='client_home'),
    path('',views.home,name='home'),
    path('search',views.search,name='search'),
    path('category-list',views.category_list,name='category-list'),
       
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('review/<int:pk>/', views.review_detail, name='review_detail'),
    path('my-services/', views.my_services, name='my_services'),
    path('product/create/', views.create_product, name='create_product'),
    path('product/<int:product_id>/update/', views.update_product, name='update_product'),
    path('product/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    path('product-list',views.product_list,name='product-list'),
    path('product/<int:pk>/', views.service_detail, name='service_detail'),
    path('category-product-list/<int:cat_id>',views.category_product_list,name='category-product-list'),
    path('product/<str:slug>/<int:id>',views.product_detail,name='product_detail'),
    path('filter-data',views.filter_data,name='filter_data'),
    path('load-more-data',views.load_more_data,name='load_more_data'),
    path('add-to-cart',views.add_to_cart,name='add_to_cart'),
    path('cart',views.cart_list,name='cart'),
    path('delete-from-cart',views.delete_cart_item,name='delete-from-cart'),
    path('update-cart',views.update_cart_item,name='update-cart'),
    path('accounts/signup',views.signup,name='signup'),
    path('checkout',views.checkout,name='checkout'),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('payment-done/', views.payment_done, name='payment_done'),
    path('payment-cancelled/', views.payment_canceled, name='payment_cancelled'),
    path('save-review/<int:pid>',views.save_review, name='save-review'),
    # User Section Start
    path('my-dashboard',views.my_dashboard, name='my_dashboard'),
    path('my-orders',views.my_orders, name='my_orders'),
    path('my-orders-items/<int:id>',views.my_order_items, name='my_order_items'),
    # End

    # Wishlist
    path('add-wishlist',views.add_wishlist, name='add_wishlist'),
    path('remove-wishlist/',views.remove_wishlist, name='remove_wishlist'),
    path('my-wishlist',views.my_wishlist, name='my_wishlist'),
    # My Reviews
    path('my-reviews',views.my_reviews, name='my-reviews'),
    # My AddressBook

    path('edit-profile',views.edit_profile, name='edit-profile'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)