import { useState } from "react";
import { useNavigate } from "react-router-dom";
import styles from "./LoginPage.module.css";

const LoginPage = () => {
  const [userId, setUserId] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    localStorage.setItem("user_id", userId);
    console.log("User logged in with ID:", userId);
    navigate("/");
  };

  return (
    <div className={styles.container}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="text"
          placeholder="Enter your User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          required
        />
        <button type="submit">Login</button>
      </form>
    </div>
  );
};

export default LoginPage;
