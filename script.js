// ======= TMDb API CONFIG (TEMP – move to backend later) =======
const API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3MTQ4NzRiMGY5YjAxM2ZiMmY2YTNmMjE2MmZiMzczMCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.ZQC4cE7jPNUr6BWvVC5Wn0G06EHGVhiut9eRfflCAio";
const TMDB_URL = "https://api.themoviedb.org/3";
const POSTER_PLACEHOLDER = "https://via.placeholder.com/200x300?text=No+Image";

// ======= FETCH TRENDING MOVIES =======
async function fetchTrendingMovies() {
  const track = document.getElementById("movie-track");
  if (!track) return;

  track.innerHTML = "<p>Loading trending movies...</p>";

  try {
    const res = await fetch(`${TMDB_URL}/trending/movie/week?language=en-US`, {
      headers: {
        Authorization: `Bearer ${API_KEY}`,
        "Content-Type": "application/json"
      }
    });

    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    track.innerHTML = "";

    if (!data.results?.length) {
      track.innerHTML = "<p>No trending movies found.</p>";
      return;
    }

    data.results.forEach(movie => {
      const img = movie.poster_path
        ? `https://image.tmdb.org/t/p/w200${movie.poster_path}`
        : POSTER_PLACEHOLDER;

      track.insertAdjacentHTML("beforeend", `
        <div class="movie">
          <img src="${img}" alt="${movie.title}">
          <p><b>${movie.title}</b></p>
        </div>
      `);
    });

  } catch (err) {
    console.error(err);
    track.innerHTML = `<p style="color:red">Failed to load trending movies.</p>`;
  }
}

// ======= SEARCH MOVIE =======
async function searchMovie() {
  const query = document.getElementById("movieSearch").value.trim();
  const language = document.getElementById("languageSelect").value;
  const results = document.getElementById("movie-results");

  if (!query) {
    alert("Enter a movie name");
    return;
  }

  results.innerHTML = "<p>Loading...</p>";

  try {
    const res = await fetch(
      `${TMDB_URL}/search/movie?query=${encodeURIComponent(query)}&language=${language}`,
      {
        headers: {
          Authorization: `Bearer ${API_KEY}`,
          "Content-Type": "application/json"
        }
      }
    );

    if (!res.ok) throw new Error(res.status);
    const data = await res.json();
    results.innerHTML = "";

    if (!data.results?.length) {
      results.innerHTML = "<p>No results found.</p>";
      return;
    }

    data.results.forEach(movie => {
      const img = movie.poster_path
        ? `https://image.tmdb.org/t/p/w200${movie.poster_path}`
        : POSTER_PLACEHOLDER;

      results.insertAdjacentHTML("beforeend", `
        <div class="movie">
          <img src="${img}">
          <p><b>${movie.title}</b></p>
          <p>⭐ ${movie.vote_average ?? "N/A"} | ${movie.release_date ?? "N/A"}</p>
          <div class="movie-buttons">
            <a target="_blank" href="https://www.youtube.com/results?search_query=${encodeURIComponent(movie.title + " trailer")}">Trailer</a>
          </div>
        </div>
      `);
    });

  } catch (err) {
    console.error(err);
    results.innerHTML = `<p style="color:red">Failed to fetch movies.</p>`;
  }
}

// ======= LOGIN + OTP =======
let otpCooldown = false;

async function sendOTP() {
  if (otpCooldown) return;

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const msg = document.getElementById("message");
  const otpSection = document.getElementById("otp-field");
  const btn = document.getElementById("otp-btn");

  if (!email || !password) {
    msg.textContent = "Enter email & password.";
    msg.className = "error";
    return;
  }

  btn.disabled = true;
  btn.innerText = "Sending OTP...";
  msg.textContent = "";

  try {
    const res = await fetch("/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      throw new Error(data.message || "Login failed");
    }

    msg.textContent = "OTP sent to email.";
    msg.className = "success";

    otpSection.style.display = "block";
    btn.style.display = "none";
    document.getElementById("email").readOnly = true;
    document.getElementById("password").readOnly = true;

    otpCooldown = true;
    setTimeout(() => otpCooldown = false, 30000); // 30s cooldown

  } catch (err) {
    msg.textContent = err.message;
    msg.className = "error";
    btn.disabled = false;
    btn.innerText = "Verify OTP";
  }
}

// ======= INIT =======
window.onload = () => {
  document.getElementById("message")?.textContent = "";
};
