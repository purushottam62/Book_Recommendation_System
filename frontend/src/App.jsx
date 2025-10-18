import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/navigation/Navbar";
import HomePage from "./components/home/HomePage";
import RegisterPage from "./components/register/RegisterPage";
import LoginPage from "./components/login/LoginPage";
import SearchResultsPage from "./search/SearchResultsPage";
import BookDetailPage from "./components/bookdetail/BookDetailPage";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/search"
          element={<SearchResultsPage></SearchResultsPage>}
        />
        <Route
          path="/books/:isbn"
          element={<BookDetailPage></BookDetailPage>}
        />
      </Routes>
    </Router>
  );
}

export default App;
