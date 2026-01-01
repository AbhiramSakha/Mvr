// ======= TMDb API CONFIG (TEMP – move to backend later) =======
const API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3MTQ4NzRiMGY5YjAxM2ZiMmY2YTNmMjE2MmZiMzczMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.ZQC4cE7jPNUr6BWvVC5Wn0G06EHGVhiut9eRfflCAio";
const TMDB_URL = "https://api.themoviedb.org/3";
const POSTER_PLACEHOLDER = "https://via.placeholder.com/200x300?text=No+Image";

// ================= TRENDING MOVIES =================
async function fetchTrendingMovies() {
  const track = document.getElementById("movie-track");
  if (!track) return;

  track.innerHTML = "<p>Loading trending movies...</p>";

  try {
    const response = await fetch(
      `${TMDB_URL}/trending/movie/week?language=en-US`,
      {
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (!response.ok) throw new Error(response.status);

    const data = await response.json();
    track.innerHTML = "";

    if (!data.results || data.results.length === 0) {
      track.innerHTML = "<p>No trending movies found.</p>";
      return;
    }

    data.results.forEach(movie => {
      const img = movie.poster_path
        ? `https://image.tmdb.org/t/p/w200${movie.poster_path}`
        : POSTER_PLACEHOLDER;

      track.insertAdjacentHTML(
        "beforeend",
        `
        <div class="movie">
          <img src="${img}" alt="${movie.title}">
          <p><b>${movie.title}</b></p>
        </div>
        `
      );
    });

  } catch (err) {
    console.error(err);
    track.innerHTML =
      "<p style='color:red'>Failed to load trending movies.</p>";
  }
}

// ================= SEARCH MOVIE =================
async function searchMovie() {
  const query = document.getElementById("movieSearch").value.trim();
  const language = document.getElementById("languageSelect").value;
  const results = document.getElementById("movie-results");

  if (!query) {
    alert("Please enter a movie name!");
    return;
  }

  results.innerHTML = "<p>Loading...</p>";

  try {
    const response = await fetch(
      `${TMDB_URL}/search/movie?query=${encodeURIComponent(query)}&language=${language}`,
      {
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (!response.ok) throw new Error(response.status);

    const data = await response.json();
    results.innerHTML = "";

    if (!data.results || data.results.length === 0) {
      results.innerHTML = "<p>No results found.</p>";
      return;
    }

    data.results.forEach(movie => {
      const img = movie.poster_path
        ? `https://image.tmdb.org/t/p/w200${movie.poster_path}`
        : POSTER_PLACEHOLDER;

      const trailer =
        `https://www.youtube.com/results?search_query=${encodeURIComponent(movie.title + " trailer")}`;

      results.insertAdjacentHTML(
        "beforeend",
        `
        <div class="movie">
          <img src="${img}">
          <p><b>${movie.title}</b></p>
          <p>⭐ ${movie.vote_average ?? "N/A"} | ${movie.release_date ?? "N/A"}</p>
          <div class="movie-buttons">
            <a target="_blank" href="${trailer}">Watch Trailer</a>
          </div>
        </div>
        `
      );
    });

  } catch (err) {
    console.error(err);
    results.innerHTML =
      "<p style='color:red'>Failed to fetch movies.</p>";
  }
}

