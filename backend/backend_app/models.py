from django.db import models

# ----------------------------
# Registered users for login
# ----------------------------
from django.db import models
from datetime import date

class RegisteredUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=150, blank=True)

    dob = models.DateField(null=True, blank=True)  # ✅ Date of Birth
    city = models.CharField(max_length=100, blank=True, null=True)      # ✅ City
    state = models.CharField(max_length=100, blank=True, null=True)     # ✅ State/Region
    country = models.CharField(max_length=100, blank=True, null=True)   # ✅ Country

    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    @property
    def age(self):
        """✅ Dynamically calculate age from date of birth."""
        if not self.dob:
            return None
        today = date.today()
        return today.year - self.dob.year - (
            (today.month, today.day) < (self.dob.month, self.dob.day)
        )

    @property
    def location(self):
        """✅ Return combined location string (for ML pipeline)."""
        parts = [p for p in [self.city, self.state, self.country] if p]
        return ", ".join(parts) if parts else None

    # --- Django Auth compatibility properties ---
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_staff(self):
        return True

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
