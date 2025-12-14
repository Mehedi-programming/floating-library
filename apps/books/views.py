from .models import *
from .serializers import *
from apps.accounts.permissions import IsActiveUser, IsSuperAdmin
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db.models import Count, Avg, Sum, Max, Min
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone


# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsActiveUser])
@authentication_classes([JWTAuthentication])
def book_create(request):
        serializer = BookCreateUpdateSerializer(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)
        book = serializer.save()
        bookSerializer = BookDetailSerializer(book)
        return Response({"message": "Book created successfully", "data": bookSerializer.data}, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsActiveUser])
@authentication_classes([JWTAuthentication])
def book_update(request, book_id):
        book = get_object_or_404(Book, id=book_id, owner=request.user)
        serializer = BookCreateUpdateSerializer(book, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        book_data = serializer.save(owner=request.user)
        bookSerializer = BookDetailSerializer(book_data)
        return Response({"message": "Book updated successfully", "data": bookSerializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def book_details(request, book_id):
        book = get_object_or_404(Book, id=book_id)
        serializer = BookDetailSerializer(book, context={'request': request})
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def book_list(request):
        books = Book.objects.all()
        serializer = BookListSerializer(books, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def book_search(request):
    query = request.GET.get('q', '')
    if not query:
        return Response({"message": "Please provide a search query."}, status=status.HTTP_400_BAD_REQUEST) 
    books = Book.objects.filter(Q(title__icontains=query) |
                                    Q(author__icontains=query) |
                                    Q(category__name__icontains=query)).distinct()
    if not books.exists():
        return Response({"message": "No books found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = BookListSerializer(books, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def top_rated_books(request):
    books = Book.objects.filter(rating__gt=4).order_by('-rating')
    serializer = BookListSerializer(books, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def updated_books(request):
        books = Book.objects.all().order_by('-updated_at')
        serializer = BookListSerializer(books, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def user_books(request):
        books = Book.objects.filter(owner=request.user)
        serializer = BookListSerializer(books, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def book_delete(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.owner != request.user:
        return Response({"message": "This is not your book"}, status=status.HTTP_403_FORBIDDEN)
    
    book.delete()
    return Response({"message": "Book deleted successfully"}, status=status.HTTP_200_OK)
        

@api_view(['GET'])
def category_list(request):
        categories = Catregory.objects.all()
        serializers = CategorySerializer(categories, many=True)
        return Response({"data": serializers.data}, status=status.HTTP_200_OK)


@api_view(["GET"])
def books_by_category(request, category_id):
    category = get_object_or_404(Catregory, id=category_id)
    books = Book.objects.filter(category=category)
    serializer = BookListSerializer(books, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def add_comment(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    serializer = CommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(user=request.user, book=book)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def edit_comment(requset, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.user != requset.user:
            return Response({"error":"You can't edit the comment."}, status=status.HTTP_403_FORBIDDEN)
        serializer = CommentSerializer(comment, data=requset.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data) 

      
@api_view(['DELETE']) 
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def delete_comment(request,comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.user != request.user:
        return Response({"error":"You can't delete the comment."}, status=status.HTTP_403_FORBIDDEN)
    comment.delete()
    return Response({"message":"Comment deleted successfully."}, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def votes_comment(request, comment_id):
    vote_type = request.data.get("vote")
    comment = get_object_or_404(Comment, id=comment_id)
    existing_vote = Comment_vote.objects.filter(user=request.user, comment=comment).first()
    if existing_vote and existing_vote.vote == vote_type:
        existing_vote.delete()
        if vote_type == "upvote":
            comment.upvotes -= 1
        else:
            comment.downvotes -= 1
        comment.save()
        return Response({"message": "Vote removed"})

    if existing_vote:
        if existing_vote.vote == "upvote":
            comment.upvotes -= 1
        else:
            comment.downvotes -= 1
        existing_vote.vote = vote_type
        existing_vote.save()
    else:
        Comment_vote.objects.create(
            user=request.user, comment=comment, vote=vote_type
        )
    if vote_type == "upvote":
        comment.upvotes += 1
    else:
        comment.downvotes += 1
    comment.save()
    return Response({"upvotes": comment.upvotes, "downvotes": comment.downvotes}, status=status.HTTP_200_OK)



# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# @authentication_classes([JWTAuthentication])
# def upvote_comment(request, comment_id):
#     comment = get_object_or_404(Comment, id=comment_id)
#     existing_vote = Comment_vote.objects.filter(user=request.user, comment=comment, vote='upvote').first()
#     comment.upvotes += 1
#     comment.save()
#     return Response({"upvotes": comment.upvotes}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([JWTAuthentication])
def book_review(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    existing_review = BookReview.objects.filter(book=book, reviewer=request.user).first()
    if existing_review:
        book.rating -= 1
        book.save()
        existing_review.delete()
        return Response({"rating": book.rating}, status=status.HTTP_200_OK)
    
    BookReview.objects.create(book=book, reviewer=request.user)
    book.rating += 1
    book.save()
    return Response({"rating": book.rating}, status=status.HTTP_201_CREATED)




# borrower request view, accept/reject request, lender history, borrower history can be added here
@api_view(["POST"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def borrow_request(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if book.owner == request.user:
        return Response({"message":"You cannot request your own book."}, status=status.HTTP_400_BAD_REQUEST)
    
    request_count = BorrowRequest.objects.filter(requester=request.user, status='ACCEPTED').count()
    if request_count >= 2:
        return Response({"message":"You have reached the maximum number of borrowed books (2)"}, status=status.HTTP_400_BAD_REQUEST)
    
    requested_book = BorrowRequest.objects.filter(book=book, status='ACCEPTED').first()
    if requested_book:
        return Response({"message":"This book is currently unavailable."}, status=status.HTTP_400_BAD_REQUEST)

    existing_request = BorrowRequest.objects.filter(requester=request.user, book=book, status='PENDING').first()
    if existing_request:
        return Response({"message":"You have already requested this book."}, status=status.HTTP_400_BAD_REQUEST)
    
    borrower_request = BorrowRequest.objects.create(
        requester=request.user,
        owner=book.owner,
        book=book,
        status='PENDING'
    )
    serializer = BorrowRequestSerializer(borrower_request, context={'request': request})

    borrower_mail = request.user.email
    book_owner = book.owner.email
    send_mail_to_lender(book_owner, borrower_mail, book.title)
    return Response({"message":"Borrower request created successfully.", "data": serializer.data}, status=status.HTTP_201_CREATED)


# send email to lender when borrower request is created
def send_mail_to_lender(recipient_email, borrower_email, book_title):
    subject = "New Borrow Request"
    message = f"You have a new borrow request for your book '{book_title}' from {borrower_email}."
    from_email = borrower_email
    recipient_list = recipient_email
    body = message
    mail = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[recipient_list],
    )
    mail.send(fail_silently=False)    


@api_view(["PATCH"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def cancel_borrow_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=request_id, requester=request.user)
    if borrow_request.status != 'PENDING':
        return Response({"message":"This request has already been processed."}, status=status.HTTP_400_BAD_REQUEST)
    
    borrow_request.status = 'CANCELLED'
    borrow_request.save()
    return Response({"message":"Borrow request cancelled."}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def accept_borrow_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)


    if borrow_request.status != 'PENDING':
        return Response({"message":"This request has already been processed."}, status=status.HTTP_400_BAD_REQUEST)
    
    if BorrowRequest.objects.filter(book=borrow_request.book, status='ACCEPTED').exists():
        return Response({"message":"This book has already been accepted for borrowing."}, status=status.HTTP_400_BAD_REQUEST)
    

    if borrow_request.owner != request.user:
        return Response({"message":"You are not authorized to accept this request."}, status=status.HTTP_403_FORBIDDEN)
    
    borrow_request.status = 'ACCEPTED'
    borrow_request.accepted_at = timezone.now()
    borrow_request.return_date = timezone.now() + timezone.timedelta(days=14)  

    borrow_request.requester.is_borrower = True
    borrow_request.owner.is_lender = True

    borrow_request.requester.save()
    borrow_request.owner.save()
    borrow_request.save()
    serializer = BorrowRequestSerializer(borrow_request)
    return Response({"message":"Borrow request accepted.", "data": serializer.data}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def reject_borrow_request(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)
    if borrow_request.status != 'PENDING':
        return Response({"message":"This request has already been processed."}, status=status.HTTP_400_BAD_REQUEST)
    
    if borrow_request.owner != request.user:
        return Response({"message":"You are not authorized to reject this request."}, status=status.HTTP_403_FORBIDDEN)
    
    borrow_request.status = 'REJECTED'
    borrow_request.save()
    serializer = BorrowRequestSerializer(borrow_request)
    return Response({"message":"Borrow request rejected.", "data": serializer.data}, status=status.HTTP_200_OK)       


# borrower history
@api_view(["GET"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def borrow_request_page(request):
    borrow_requests = BorrowRequest.objects.filter(requester=request.user).order_by('-created_at')
    serializer = BorrowRequestSerializer(borrow_requests, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


# lender history
@api_view(["GET"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def lend_request_page(request):
    lend_requests = BorrowRequest.objects.filter(owner=request.user).order_by('-created_at')
    serializer = BorrowRequestSerializer(lend_requests, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


# return borrowed book to lender
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsActiveUser])
@authentication_classes([JWTAuthentication])
def return_book(request, request_id):
    borrow_request = get_object_or_404(BorrowRequest, id=request_id)
    if borrow_request.requester != request.user:
        return Response({"message":"You are not authorized to return this book."}, status=status.HTTP_403_FORBIDDEN)
    if borrow_request.status != 'ACCEPTED':
        return Response({"message": "This book you have not borrowed yet."}, status=status.HTTP_400_BAD_REQUEST)
    
    borrow_request.status = 'RETURNED'
    if timezone.now() > borrow_request.return_date:
        borrow_request.is_late = True

    borrow_request.save()
    still_active_borrower = BorrowRequest.objects.filter(
        requester=request.user,
        status='ACCEPTED'
    ).exists()

    if not still_active_borrower:
        request.user.is_borrower = False
        request.user.save()

    serializer = BorrowRequestSerializer(borrow_request)
    return Response(
        {"message": "Book returned successfully.", "data": serializer.data},
        status=status.HTTP_200_OK
    )


@api_view(["GET"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def my_requests(request):
    requests = BorrowRequest.objects.filter(requester=request.user)
    serializer = BorrowRequestSerializer(requests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)



# books count
@api_view(["GET"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def books_count(request):
    total_books = Book.objects.filter(owner=request.user).count()
    return Response({"total_books": total_books}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def borrowed_books_count(request):
    borrowed_books = BorrowRequest.objects.filter(requester=request.user, status='ACCEPTED').count()
    return Response({"borrowed_books": borrowed_books}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def lent_books_count(request):
    lent_books = BorrowRequest.objects.filter(owner=request.user, status='ACCEPTED').count()
    return Response({"lent_books": lent_books}, status=status.HTTP_200_OK)



# add book to wishlist
@api_view(['POST'])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def add_to_wishlist(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    wishlist_entry, _ = WishList.objects.get_or_create(user=request.user, book=book)
    serializer = WishListSerializer(wishlist_entry)
    return Response({"message": "Book added to wishlist.", "data": serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def wishlist(request):
    wishlist = WishList.objects.filter(user=request.user)
    serializer = WishListSerializer(wishlist, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def remove_from_wishlist(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    wishlist_entry = WishList.objects.filter(user=request.user, book=book).first()
    if not wishlist_entry:
        return Response({"message": "Book not found in wishlist."}, status=status.HTTP_404_NOT_FOUND)
    wishlist_entry.delete()
    return Response({"message": "Book removed from wishlist."}, status=status.HTTP_200_OK)


#list of borrow and lend requests
@api_view(['GET'])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def borrow_request_list(request):
    borrow_requests = BorrowRequest.objects.filter(requester=request.user).order_by('-created_at')
    serializer = BorrowRequestSerializer(borrow_requests, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsActiveUser])
@authentication_classes([JWTAuthentication])
def lend_request_list(request):
    lend_requests = BorrowRequest.objects.filter(owner=request.user).order_by('-created_at')
    serializer = BorrowRequestSerializer(lend_requests, many=True)
    return Response({"data": serializer.data}, status=status.HTTP_200_OK)