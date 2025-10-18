import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";

const SearchResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const token = localStorage.getItem("access");
  const userId = localStorage.getItem("user_id");
  const { isbns = [], query } = location.state || {};
  const [books, setBooks] = useState([]);
  const [ratings, setRatings] = useState({}); // { isbn: rating }
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    if (!isbns.length) {
      setBooks([]);
      setLoading(false);
      return;
    }

    const fetchBooksAndRatings = async () => {
      try {
        // Fetch all books
        const resBooks = await axios.post(
          "/api/books/bulk/",
          { isbns },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setBooks(resBooks.data);

        // Fetch ratings for each book
        const ratingsData = {};
        await Promise.all(
          resBooks.data.map(async (book) => {
            try {
              const resRating = await axios.get(
                `/api/model/rating/?user_id=${userId}&book_isbn=${book.book_isbn}`,
                { headers: { Authorization: `Bearer ${token}` } }
              );
              const userRating = resRating.data.rating;
              ratingsData[book.book_isbn] =
                userRating !== 3.14 ? userRating : 0;
            } catch (err) {
              ratingsData[book.book_isbn] = 0;
            }
          })
        );
        setRatings(ratingsData);
      } catch (err) {
        console.error("Error fetching search results or ratings:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchBooksAndRatings();
  }, [isbns, token, navigate, userId]);

  const handleSubmitRating = async (isbn) => {
    if (!isbn || !token) return;

    try {
      await axios.post(
        "/api/model/record/",
        {
          user_id: userId,
          book_isbn: isbn,
          rating: ratings[isbn],
          implicit: false,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert("Rating submitted successfully!");
    } catch (err) {
      console.error("Error submitting rating:", err);
    }
  };

  const renderStars = (isbn) => {
    const stars = [];
    const rating = ratings[isbn] || 0;
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span
          key={i}
          onClick={(e) => {
            e.stopPropagation();
            setRatings((prev) => ({ ...prev, [isbn]: i }));
          }}
          style={{
            cursor: "pointer",
            fontSize: "22px",
            color: i <= rating ? "#FFD700" : "#ccc",
            transition: "color 0.2s",
          }}
        >
          ★
        </span>
      );
    }
    return stars;
  };

  if (loading)
    return <p style={{ padding: "20px" }}>Loading search results...</p>;

  return (
    <div style={{ padding: "30px", maxWidth: "1000px", margin: "0 auto" }}>
      <h2 style={{ marginBottom: "25px" }}>🔍 Search results for "{query}"</h2>
      {books.length > 0 ? (
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "25px",
            justifyContent: "flex-start",
          }}
        >
          {books.map((book) => (
            <div
              key={book.book_isbn}
              onClick={() => navigate(`/books/${book.book_isbn}`)}
              style={{
                width: "200px",
                cursor: "pointer",
                border: "1px solid #ddd",
                borderRadius: "12px",
                padding: "10px",
                textAlign: "center",
                boxShadow: "0 4px 10px rgba(0,0,0,0.1)",
                transition: "transform 0.2s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.transform = "scale(1.05)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.transform = "scale(1)")
              }
            >
              <img
                src={
                  book.image_url_l ||
                  book.image_url_m ||
                  "https://via.placeholder.com/200x300"
                }
                alt={book.book_title}
                style={{
                  width: "100%",
                  height: "280px",
                  objectFit: "cover",
                  borderRadius: "10px",
                  marginBottom: "10px",
                }}
              />
              <h3 style={{ fontSize: "1.1rem", marginBottom: "5px" }}>
                {book.book_title}
              </h3>
              <p style={{ fontSize: "0.95rem", color: "#555" }}>
                {book.book_author}
              </p>

              {/* Star rating */}
              <div style={{ marginTop: "5px" }}>
                {renderStars(book.book_isbn)}
              </div>

              {/* Submit rating button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSubmitRating(book.book_isbn);
                }}
                style={{
                  marginTop: "8px",
                  padding: "5px 12px",
                  background: "#2563eb",
                  color: "white",
                  border: "none",
                  borderRadius: "5px",
                  cursor: "pointer",
                  fontSize: "0.9rem",
                }}
              >
                Submit
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p>No books found for "{query}".</p>
      )}
    </div>
  );
};

export default SearchResultsPage;
