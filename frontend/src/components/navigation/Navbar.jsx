import { useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./Navbar.module.css";

const Navbar = () => {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      // send query to backend (later we'll connect API)
      console.log("Searching for:", query);
    }
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
        <button onClick={() => navigate("/login")} className={styles.linkBtn}>
          Login
        </button>
        <button
          onClick={() => navigate("/register")}
          className={styles.linkBtn}
        >
          Register
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
