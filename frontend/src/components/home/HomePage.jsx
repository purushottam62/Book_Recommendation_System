import styles from "./HomePage.module.css";

const HomePage = () => {
  return (
    <div className={styles.container}>
      <h1>Welcome to Book Recommender</h1>
      <p>Search or rate books to get personalized recommendations.</p>
    </div>
  );
};

export default HomePage;
