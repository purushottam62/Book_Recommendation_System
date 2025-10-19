import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const RegisterPage = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    full_name: "",
    email: "",
    password: "",
    dob: "",      // ✅ backend expects 'dob', not 'date_of_birth'
    city: "",
    state: "",
    country: "",
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

const handleSubmit = async (e) => {
  e.preventDefault();
  try {
    await axios.post("/api/auth/register/", form, {
      headers: { "Content-Type": "application/json" },
    });
    alert("✅ Registration successful! Please login.");
    navigate("/login");
  } catch (err) {
    // Capture and format server-side validation errors
    const data = err.response?.data;
    console.error("❌ Error registering:", data);

    if (data) {
      // If backend returned field-wise validation errors
      let msg = "";
      for (const key in data) {
        const value = Array.isArray(data[key]) ? data[key][0] : data[key];
        msg += `${key}: ${value}\n`;
      }
      alert("⚠️ Registration failed:\n" + msg);
    } else {
      // Fallback for network or unexpected errors
      alert("⚠️ Registration failed. Please check your inputs or try again.");
    }
  }
};


  return (
    <div style={{ maxWidth: "400px", margin: "40px auto" }}>
      <h2>Register</h2>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", flexDirection: "column", gap: "10px" }}
      >
        <input
          type="text"
          name="username"
          placeholder="Username"
          value={form.username}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="full_name"
          placeholder="Full Name"
          value={form.full_name}
          onChange={handleChange}
          required
        />
        <input
          type="email"
          name="email"
          placeholder="Email"
          value={form.email}
          onChange={handleChange}
          required
        />
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={form.password}
          onChange={handleChange}
          required
        />
        <input
          type="date"
          name="dob"     // ✅ Must match Django field name
          placeholder="Date of Birth"
          value={form.dob}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="city"
          placeholder="City"
          value={form.city}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="state"
          placeholder="State"
          value={form.state}
          onChange={handleChange}
          required
        />
        <input
          type="text"
          name="country"
          placeholder="Country"
          value={form.country}
          onChange={handleChange}
          required
        />
        <button
          type="submit"
          style={{
            marginTop: "10px",
            padding: "10px",
            background: "#2563eb",
            color: "white",
            border: "none",
            borderRadius: "5px",
          }}
        >
          Register
        </button>
      </form>
    </div>
  );
};

export default RegisterPage;
