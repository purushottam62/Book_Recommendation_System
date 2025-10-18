import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const HomePage = () => {
  const [books, setBooks] = useState([]);
  const navigate = useNavigate();
  const token = localStorage.getItem("access");
  const userId = localStorage.getItem("user_id"); // store this when user logs in
  console.log("access token in homepage:", token);
  useEffect(() => {
    const init = async () => {
      if (!userId || !token) {
        navigate("/login");
        return;
      }

      // 1. Load model
      try {
        await axios.post(
          "/api/model/load/",
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
      } catch (err) {
        console.error("Error loading model:", err);
      }

      // 2. Fetch recommendations
      try {
        const res = await axios.get(`/api/model/recommend/${userId}/?top_k=5`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setBooks(res.data);
      } catch (err) {
        console.error("Error fetching recommendations:", err);
        if (err.response?.status === 401) {
          localStorage.removeItem("access");
          localStorage.removeItem("refresh");
          navigate("/login");
        }
      }
    };

    init();
  }, [navigate, token, userId]);

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
                src={book.image_url_m || book.image_url_l}
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
