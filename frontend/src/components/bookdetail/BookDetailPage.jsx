import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";

const BookDetailPage = () => {
  const { isbn } = useParams();
  const [book, setBook] = useState(null);
  const [rating, setRating] = useState(0); // user rating
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const token = localStorage.getItem("access");
  const userId = localStorage.getItem("user_id");

  useEffect(() => {
    const fetchBookAndRating = async () => {
      if (!token) {
        navigate("/login");
        return;
      }

      try {
        // Fetch book details
        const resBook = await axios.get(`/api/books/${isbn}/`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setBook(resBook.data);

        // Fetch user's previous rating
        const resRating = await axios.get(
          `/api/model/rating/?user_id=${userId}&book_isbn=${isbn}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        const userRating = resRating.data.rating;

        // Only show rating if valid (ignore 3.14 or 7.14)
        setRating(userRating !== 3.14 && userRating !== 7.14 ? userRating : 0);
      } catch (err) {
        console.error("Error fetching book or rating:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchBookAndRating();
  }, [isbn, navigate, token, userId]);

  const handleSubmitRating = async () => {
    if (!book || !token) return;

    try {
      await axios.post(
        "/api/model/record/",
        {
          user_id: userId,
          book_isbn: book.book_isbn,
          rating: rating,
          implicit: false,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert("Rating submitted successfully!");
    } catch (err) {
      console.error("Error submitting rating:", err);
    }
  };

  if (loading) return <p style={{ padding: "20px" }}>Loading book...</p>;
  if (!book) return <p style={{ padding: "20px" }}>Book not found</p>;

  // ⭐ Render 10 stars (1–10)
  const renderStars = () => {
    const stars = [];
    for (let i = 1; i <= 10; i++) {
      stars.push(
        <span
          key={i}
          onClick={() => setRating(i)}
          style={{
            cursor: "pointer",
            fontSize: "28px",
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

  return (
    <div style={{ padding: "30px", maxWidth: "900px", margin: "0 auto" }}>
      <button
        onClick={() => navigate(-1)}
        style={{
          marginBottom: "25px",
          padding: "8px 15px",
          background: "#f3f4f6",
          border: "1px solid #ccc",
          borderRadius: "5px",
          cursor: "pointer",
          fontSize: "16px",
        }}
      >
        ← Back
      </button>

      <div
        style={{
          display: "flex",
          gap: "40px",
          alignItems: "flex-start",
          flexWrap: "wrap",
        }}
      >
        <img
          src={
            book.image_url_l ||
            book.image_url_m ||
            "https://via.placeholder.com/300x450"
          }
          alt={book.book_title}
          style={{
            width: "300px",
            maxHeight: "450px",
            objectFit: "cover",
            borderRadius: "12px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
          }}
        />

        <div style={{ flex: 1, minWidth: "300px" }}>
          <h1 style={{ fontSize: "2rem", marginBottom: "15px" }}>
            {book.book_title}
          </h1>
          <p style={{ fontSize: "1.1rem", marginBottom: "8px" }}>
            <strong>Author:</strong> {book.book_author}
          </p>
          <p style={{ fontSize: "1.1rem", marginBottom: "8px" }}>
            <strong>Publisher:</strong> {book.publisher}
          </p>
          <p style={{ fontSize: "1.1rem", marginBottom: "8px" }}>
            <strong>Year:</strong> {book.year}
          </p>
          <p
            style={{
              fontSize: "1rem",
              lineHeight: "1.6",
              marginTop: "15px",
              color: "#333",
            }}
          >
            <strong>Description:</strong>{" "}
            {book.description || "No description available."}
          </p>

          {/* Star Rating */}
          <div style={{ marginTop: "25px" }}>
            <p style={{ fontSize: "1rem", marginBottom: "5px" }}>
              Rate this book:
            </p>
            <div>{renderStars()}</div>
            <button
              onClick={handleSubmitRating}
              style={{
                marginTop: "15px",
                padding: "8px 20px",
                background: "#2563eb",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "1rem",
              }}
            >
              Submit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookDetailPage;
