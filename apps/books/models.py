from django.db import models
from django.utils.text import slugify
from apps.accounts.models import User


# Create your models here.
class Catregory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
 

class Book(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(Catregory, on_delete=models.CASCADE, blank=True, null=True, related_name='books_category')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='books_owner')
    author = models.CharField(max_length=255)
    book_image = models.ImageField(upload_to="book_images/", blank=True, null=True)
    language = models.CharField(max_length=30)
    short_description = models.TextField(null=True, blank=True)
    published_date = models.DateField(null=True, blank=True)
    slug = models.SlugField(max_length=300, unique=True, blank=True, null=True)
    rating = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.title and not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            while Book.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        return not self.borrow_requests.filter(status='ACCEPTED').exists()


    def __str__(self):
        return self.title
    
class BorrowRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
        ("RETURNED", "Returned"),
    )
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_requests")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_requests")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrow_requests")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    return_date = models.DateTimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    

    def __str__(self):
        return f"{self.requester.name} → {self.owner.name} ({self.status})"


class BookReview(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='book_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_reviews')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     unique_together = ('reviewer', 'book') 


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Comment_vote(models.Model):
    choice_field= (
        ('upvote', 'upvote'),
        ('downvote', 'downvote')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_votes')
    vote = models.CharField(max_length=10, choices=choice_field, default='upvote')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'comment')

    class Meta:
        ordering = ['-created_at']


class WishList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')



