import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import styles from "./Navbar.module.css";

const Navbar = () => {
  const [query, setQuery] = useState("");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showProfile, setShowProfile] = useState(false);
  const navigate = useNavigate();
  const token = localStorage.getItem("access");

  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await axios.get("/api/auth/me/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(res.data);
      } catch (err) {
        console.error("Error fetching user profile:", err);
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        localStorage.removeItem("user_id");
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [token]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    if (!token) {
      navigate("/login");
      return;
    }

    try {
      // 1️⃣ Search ISBNs from backend
      const searchRes = await axios.get(
        `/api/books/search/${encodeURIComponent(query)}/`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const isbns = searchRes.data.matches || [];
      if (isbns.length === 0) {
        alert("No books found for your search.");
        return;
      }

      // 2️⃣ Navigate to SearchResults page with ISBNs
      navigate("/search", { state: { isbns } });
    } catch (err) {
      console.error("Error searching books:", err);
      if (err.response?.status === 401) {
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        localStorage.removeItem("user_id");
        navigate("/login");
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("user_id");
    setUser(null);
    setShowProfile(false);
    navigate("/login");
  };

  if (loading) return <p style={{ padding: "20px" }}>Loading...</p>;

  return (
    <nav className={styles.navbar}>
      <div className={styles.logo} onClick={() => navigate("/")}>
        📚 Book Recommender
      </div>

      <form onSubmit={handleSearch} className={styles.searchForm}>
        <input
          type="text"
          placeholder="Search a book..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className={styles.searchInput}
        />
        <button type="submit" className={styles.searchBtn}>
          Search
        </button>
      </form>

      <div className={styles.links}>
        {user ? (
          <div className={styles.profileWrapper}>
            <button
              onClick={() => setShowProfile(!showProfile)}
              className={styles.linkBtn}
            >
              {user.full_name || user.username} ▼
            </button>
            {showProfile && (
              <div className={styles.profileCard}>
                <p>
                  <strong>Name:</strong> {user.full_name || user.username}
                </p>
                <p>
                  <strong>Username:</strong> {user.username}
                </p>
                <p>
                  <strong>Email:</strong> {user.email}
                </p>
                <p>
                  <strong>Joined:</strong>{" "}
                  {new Date(user.date_joined).toLocaleDateString()}
                </p>
                <button onClick={handleLogout} className={styles.logoutBtn}>
                  Logout
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            <button
              onClick={() => navigate("/login")}
              className={styles.linkBtn}
            >
              Login
            </button>
            <button
              onClick={() => navigate("/register")}
              className={styles.linkBtn}
            >
              Register
            </button>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
