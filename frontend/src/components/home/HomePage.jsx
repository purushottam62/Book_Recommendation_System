import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const HomePage = () => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const token = localStorage.getItem("access");
  const userId = localStorage.getItem("user_id"); // stored on login

  useEffect(() => {
    const init = async () => {
      if (!userId || !token) {
        navigate("/login");
        return;
      }

      try {
        // 1️⃣ Fetch recommended ISBNs
        const res = await axios.get(`/api/model/recommend/${userId}/?top_k=5`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        const recommendedIsbns = res.data.recommendations || [];
        console.log("Recommended ISBNs:", recommendedIsbns);

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
        console.log("Full recommended books:", bulkRes.data);
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

  if (loading) return <p style={{ padding: "20px" }}>Loading recommendations...</p>;

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
              }}
            >
              <img
                src={book.image_url_m || book.image_url_l || "https://via.placeholder.com/150"}
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
    </div>
  );
};

export default HomePage;
