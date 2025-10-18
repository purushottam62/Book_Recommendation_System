import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const HomePage = () => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBook, setSelectedBook] = useState(null);
  const [rating, setRating] = useState(3);
  const navigate = useNavigate();
  const token = localStorage.getItem("access");
  const userId = localStorage.getItem("user_id");

  useEffect(() => {
    const init = async () => {
      if (!userId || !token) {
        navigate("/login");
        return;
      }

      try {
        // 1️⃣ Fetch recommended ISBNs
        const res = await axios.get(`/api/model/recommend/${userId}/?top_k=20`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        const recommendedIsbns = res.data.recommendations || [];
        if (recommendedIsbns.length === 0) {
          setBooks([]);
          setLoading(false);
          return;
        }

        // 2️⃣ Fetch full book details in bulk
        const bulkRes = await axios.post(
          "/api/books/bulk/",
          { isbns: recommendedIsbns },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        setBooks(bulkRes.data);
      } catch (err) {
        console.error("Error fetching recommendations:", err);
        if (err.response?.status === 401) {
          localStorage.removeItem("access");
          localStorage.removeItem("refresh");
          navigate("/login");
        }
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [navigate, token, userId]);

  const handleBookClick = async (isbn) => {
    if (!token) return;

    navigate(`/books/${isbn}`);
  };

  const handleSubmitRating = async () => {
    if (!selectedBook || !token) return;

    try {
      await axios.post(
        "/api/model/record/",
        {
          user_id: userId,
          book_isbn: selectedBook.book_isbn,
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

  if (loading)
    return <p style={{ padding: "20px" }}>Loading recommendations...</p>;

  return (
    <div style={{ padding: "20px" }}>
      <h2>📚 Recommended Books</h2>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "15px" }}>
        {books.length > 0 ? (
          books.map((book) => (
            <div
              key={book.book_isbn}
              style={{
                width: "180px",
                border: "1px solid #ddd",
                borderRadius: "10px",
                padding: "10px",
                textAlign: "center",
                cursor: "pointer",
              }}
              onClick={() => handleBookClick(book.book_isbn)}
            >
              <img
                src={
                  book.image_url_m ||
                  book.image_url_l ||
                  "https://via.placeholder.com/150"
                }
                alt={book.book_title}
                style={{ width: "100%", borderRadius: "8px" }}
              />
              <h4>{book.book_title}</h4>
              <p>{book.book_author}</p>
            </div>
          ))
        ) : (
          <p>No recommendations available yet.</p>
        )}
      </div>

      {/* Book Details Modal */}
      {selectedBook && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 9999,
          }}
          onClick={() => setSelectedBook(null)}
        >
          <div
            style={{
              background: "white",
              padding: "20px",
              borderRadius: "10px",
              width: "400px",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedBook(null)}
              style={{
                position: "absolute",
                top: 10,
                right: 10,
                cursor: "pointer",
              }}
            >
              ✖
            </button>
            <img
              src={
                selectedBook.image_url_l ||
                selectedBook.image_url_m ||
                "https://via.placeholder.com/200"
              }
              alt={selectedBook.book_title}
              style={{ width: "100%", borderRadius: "8px" }}
            />
            <h2>{selectedBook.book_title}</h2>
            <p>
              <strong>Author:</strong> {selectedBook.book_author}
            </p>
            <p>
              <strong>Publisher:</strong> {selectedBook.publisher}
            </p>
            <p>
              <strong>Year:</strong> {selectedBook.year}
            </p>
            <p>
              <strong>Description:</strong>{" "}
              {selectedBook.description || "No description available."}
            </p>

            <div style={{ marginTop: "15px" }}>
              <label>
                Rate this book:{" "}
                <input
                  type="number"
                  min={1}
                  max={10}
                  step={0.1}
                  value={rating}
                  onChange={(e) => setRating(parseFloat(e.target.value))}
                  style={{ width: "60px" }}
                />
              </label>
              <button
                onClick={handleSubmitRating}
                style={{
                  marginLeft: "10px",
                  padding: "5px 10px",
                  background: "#2563eb",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                }}
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
