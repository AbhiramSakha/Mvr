const API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMzA4MWUxMDkyYzEyNTYxZGY3YjUyNjE3YmI0NmZkOSIsIm5iZiI6MTc0MTY3NzAzMC43MDcsInN1YiI6IjY3Y2ZlMWU2NDJjMGNjYzNjYTFkZDZhNyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.4j3QoS43gBtG_-bmYmu0Z-KdNZr7AwVhmUvwQdIXs2AeyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMzA4MWUxMDkyYzEyNTYxZGY3YjUyNjE3YmI0NmZkOSIsIm5iZiI6MTc0MTY3NzAzMC43MDcsInN1YiI6IjY3Y2ZlMWU2NDJjMGNjYzNjYTFkZDZhNyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.4j3QoS43gBtG_-bmYmu0Z-KdNZr7AwVhmUvwQdIXs2A";  // Replace with your real TMDb key
const TMDB_URL = "https://api.themoviedb.org/3";
const POSTER_PLACEHOLDER = "https://via.placeholder.com/200x300?text=No+Image";

async function fetchTrendingMovies() {
  const track = document.getElementById("movie-track");
  if (!track) return;
  track.innerHTML = "<p>Loading trending movies...</p>";

  try {
    const response = await fetch(`${TMDB_URL}/trending/movie/week?language=en-US`, {
      headers: {
        Authorization: `Bearer ${API_KEY}`,
        "Content-Type": "application/json"
      }
    });

    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

    const data = await response.json();
    track.innerHTML = "";

    if (data.status_code) {
      track.innerHTML = `<p style="color:#e50914">TMDb API Error: ${data.status_message}</p>`;
      return;
    }
    if (!data.results || data.results.length === 0) {
      track.innerHTML = "<p>No trending movies found.</p>";
      return;
    }

    for (const movie of data.results) {
      const imgUrl = movie.poster_path
        ? `https://image.tmdb.org/t/p/w200${movie.poster_path}`
        : POSTER_PLACEHOLDER;

      const movieElement = `
        <div class="movie" tabindex="0">
          <img src="${imgUrl}" alt="${movie.title}">
          <p><b>${movie.title}</b></p>
        </div>
      `;
      track.insertAdjacentHTML("beforeend", movieElement);
    }
  } catch (error) {
    console.error("Error fetching trending movies:", error);
    track.innerHTML = `<p style="color:#e50914">Failed to fetch trending movies. Check your network.</p>`;
  }
}

async function searchMovie() {
  const query = document.getElementById("movieSearch").value.trim();
  const language = document.getElementById("languageSelect").value;
  const resultsContainer = document.getElementById("movie-results");

  if (!query) {
    alert("Please enter a movie name!");
    resultsContainer.innerHTML = "";
    return;
  }

  resultsContainer.innerHTML = "<p>Loading...</p>";

  try {
    const response = await fetch(`${TMDB_URL}/search/movie?query=${encodeURIComponent(query)}&language=${language}`, {
      headers: {
        Authorization: `Bearer ${API_KEY}`,
        "Content-Type": "application/json"
      }
    });

    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

    const data = await response.json();
    resultsContainer.innerHTML = "";

    if (data.status_code) {
      resultsContainer.innerHTML = `<p style="color:#e50914">TMDb API Error: ${data.status_message}</p>`;
      return;
    }
    if (!data.results || data.results.length === 0) {
      resultsContainer.innerHTML = "<p>No results found.</p>";
      return;
    }

    for (const movie of data.results) {
      const imgUrl = movie.poster_path
        ? `https://image.tmdb.org/t/p/w200${movie.poster_path}`
        : POSTER_PLACEHOLDER;
      const trailerUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(movie.title + " trailer")}`;
      const fullMovieUrl = `https://www.google.com/search?q=watch+${encodeURIComponent(movie.title)}+full+movie+online`;

      const movieDiv = document.createElement("div");
      movieDiv.classList.add("movie");
      movieDiv.innerHTML = `
        <img src="${imgUrl}" alt="${movie.title}">
        <p><b>${movie.title}</b></p>
        <p>⭐ ${movie.vote_average ?? 'N/A'} | ${movie.release_date ?? 'N/A'}</p>
        <div class="movie-buttons">
          <a href="${trailerUrl}" target="_blank" class="watch-btn">Watch Trailer</a>
          <a href="${fullMovieUrl}" target="_blank" class="watch-btn">Watch Full Movie</a>
        </div>
      `;
      resultsContainer.appendChild(movieDiv);
    }
  } catch (error) {
    console.error("Error fetching movie data:", error);
    resultsContainer.innerHTML = `<p style="color:#e50914">Failed to fetch movies. Check your network.</p>`;
  }
}
