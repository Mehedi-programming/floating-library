from django.urls import path
from .views import *


urlpatterns = [
    path('book-create/', book_create, name='book_create'),
    path('book-update/<int:book_id>/', book_update, name='book_update'),
    path('book-details/<int:book_id>/', book_details, name='book_details'),
    path('book-list/', book_list, name='book_list'),
    path('updated-books/', updated_books, name='updated_books'),
    path('top-rated-books/', top_rated_books, name='top_rated_books'),
    path('book-search/', book_search, name='book_search'),
    path('user-books/', user_books, name='user_books'),
    path('book-delete/<int:book_id>/', book_delete, name='book_delete'),
    path('category-list/', category_list, name='category_list'),
    path('books-by-category/<int:category_id>/', books_by_category, name='books_by_category'),
    path('add-comment/<int:book_id>/', add_comment, name='add_comment'),
    path('edit-comment/<int:comment_id>/', edit_comment, name='edit_comment'),
    path('delete-comment/<int:comment_id>/', delete_comment, name='delete_comment'),
    path('votes-comment/<int:comment_id>/', votes_comment, name='votes_comment'),
    path('book-review/<int:book_id>/', book_review, name='book_review'),
    path('borrow-request/<int:book_id>/', borrow_request, name='borrow_request'),
    path('cancel-borrow-request/<int:request_id>/', cancel_borrow_request, name='cancel_borrow_request'),
    path('accept_borrow_request/<int:request_id>/', accept_borrow_request, name='accept_borrow_request'),
    path('reject-borrow-request/<int:request_id>/', reject_borrow_request, name='reject_borrow_request'),
    path('delete-borrow-request/<int:request_id>/', delete_borrow_request, name='delete_borrow_request'),
    path('borrow-request-page/', borrow_request_page, name='borrow_request_page'),
    path('lend-request-page/', lend_request_page, name='lend_request_page'),
    path('return-book/<int:request_id>/', return_book, name='return_book'),
    path('my-requests/', my_requests, name='my_requests'),
    path('add-to-wishlist/<int:book_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/', wishlist, name='wishlist'),
    path('remove-from-wishlist/<int:book_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('borrow-request-list/', borrow_request_list, name='borrow_request_list'),
    path('lend-request-list/', lend_request_list, name='lend_request_list'),
    
]
