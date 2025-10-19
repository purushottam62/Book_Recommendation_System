import pandas as pd

# Load the ratings file
ratings = pd.read_csv("../clean_data/ratings.csv")

# Display original shape
print("Original shape:", ratings.shape)

# Keep only rated interactions (non-zero)
ratings = ratings[ratings["book_rating"] > 0]

# Display new shape after filtering
print("After removing unrated (0) entries:", ratings.shape)

# Optionally reset index
ratings = ratings.reset_index(drop=True)

# Save cleaned file (recommended)
ratings.to_csv("../clean_data/ratings.csv", index=False)

print("Cleaned ratings saved to ../clean_data/ratings.csv")
