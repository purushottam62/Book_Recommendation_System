import { useEffect, useState } from "react";
import API from "../api/api";
import { Link } from "react-router-dom";

const Dashboard = () => {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchMe = async () => {
      try {
        const res = await API.get("auth/me/");
        setUser(res.data);
      } catch (err) {
        console.log(err.response.data);
      }
    };
    fetchMe();
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      {user && (
        <div>
          <p>Welcome, {user.username}!</p>
          <p>Email: {user.email}</p>
        </div>
      )}
      <Link to="/books">View Books</Link>
    </div>
  );
};

export default Dashboard;
