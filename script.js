// ======= TMDb API CONFIG =======
const API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3MTQ4NzRiMGY5YjAxM2ZiMmY2YTNmMjE2MmZiMzczMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.ZQC4cE7jPNUr6BWvVC5Wn0G06EHGVhiut9eRfflCAio";
const TMDB_URL = "https://api.themoviedb.org/3";
const POSTER_PLACEHOLDER = "https://via.placeholder.com/200x300?text=No+Image";

// ======= FETCH TRENDING MOVIES =======
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

// ======= SEARCH MOVIE =======
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

// ======= LOGIN + OTP =======
async function sendOTP() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const messageBox = document.getElementById("message");
  const otpSection = document.getElementById("otp-field");
  const otpBtn = document.getElementById("otp-btn");

  if (!email || !password) {
    messageBox.textContent = "Please enter both email and password.";
    messageBox.className = "error";
    return;
  }

  otpBtn.disabled = true;
  otpBtn.innerText = "Sending OTP...";
  messageBox.textContent = "";

  try {
    const response = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (response.ok && data.success) {
      messageBox.textContent = data.message;
      messageBox.className = "success";
      otpSection.style.display = "block";
      otpBtn.style.display = "none";
      document.getElementById("email").readOnly = true;
      document.getElementById("password").readOnly = true;
      document.getElementById("otp").focus();
    } else {
      messageBox.textContent = data.message || "Failed to send OTP.";
      messageBox.className = "error";
      otpBtn.disabled = false;
      otpBtn.innerText = "Verify OTP";
    }

  } catch (error) {
    console.error("Login fetch error:", error);
    messageBox.textContent = "Server error. Please try again.";
    messageBox.className = "error";
    otpBtn.disabled = false;
    otpBtn.innerText = "Verify OTP";
  }
}

// ======= INITIALIZE =======
window.onload = () => {
  const messageBox = document.getElementById("message");
  if (messageBox) messageBox.textContent = "";
};
