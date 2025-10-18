import { useState } from "react";
import axios from "axios";
// import { BASE_URL } from "../api";

const SearchPage = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const token = localStorage.getItem("access");

  const handleSearch = async (e) => {
    e.preventDefault();
    const res = await axios.get(`/api/books/?search=${query}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    setResults(res.data);
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Search Books</h2>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Enter book title..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      <div style={{ marginTop: "20px" }}>
        {results.map((book) => (
          <div key={book.book_isbn}>
            <h4>{book.book_title}</h4>
            <p>{book.book_author}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchPage;
