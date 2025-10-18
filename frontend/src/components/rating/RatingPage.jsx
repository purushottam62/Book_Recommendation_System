import { useState } from "react";
import axios from "axios";
// import { BASE_URL } from "../api";

const RatingPage = () => {
  const [form, setForm] = useState({ user_id: "", book_isbn: "", rating: "" });
  const token = localStorage.getItem("access");

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    await axios.post(`/api/model/record/`, form, {
      headers: { Authorization: `Bearer ${token}` },
    });
    alert("✅ Rating submitted!");
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Rate a Book</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="user_id"
          placeholder="User ID"
          value={form.user_id}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="book_isbn"
          placeholder="Book ISBN"
          value={form.book_isbn}
          onChange={handleChange}
          required
        />
        <input
          type="number"
          name="rating"
          placeholder="Rating (1-10)"
          value={form.rating}
          onChange={handleChange}
          required
        />
        <button type="submit">Submit Rating</button>
      </form>
    </div>
  );
};

export default RatingPage;
