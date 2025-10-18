import { useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Navbar.module.css";

const Navbar = () => {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const token = localStorage.getItem("access"); // check your stored access token

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      console.log("Searching for:", query);
      // TODO: connect search API later
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("user_id");
    navigate("/login");
  };

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
        {token ? (
          <>
            <button
              onClick={() => navigate("/profile")}
              className={styles.linkBtn}
            >
              Profile
            </button>
            <button onClick={handleLogout} className={styles.linkBtn}>
              Logout
            </button>
          </>
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
