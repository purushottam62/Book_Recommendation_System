from django.db import models

# ----------------------------
# Registered users for login
# ----------------------------
class RegisteredUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # store hashed passwords ideally
    full_name = models.CharField(max_length=150, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username


# ----------------------------
# AI Model tables
# ----------------------------
class User(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    age = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

class Book(models.Model):
    book_isbn = models.CharField(max_length=50, unique=True)
    book_title = models.CharField(max_length=255)
    book_author = models.CharField(max_length=255, null=True, blank=True)
    year_of_publication = models.IntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=255, null=True, blank=True)
    image_url_s = models.URLField(max_length=500, null=True, blank=True)
    image_url_m = models.URLField(max_length=500, null=True, blank=True)
    image_url_l = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"{self.book_title} ({self.book_isbn})"

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.FloatField()