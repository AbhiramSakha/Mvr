async function searchMovie() {
    const query = document.getElementById("movieSearch").value.trim();
    const language = document.getElementById("languageSelect").value;

    if (!query) {
        alert("Please enter a movie name!");
        return;
    }

    try {
        const response = await fetch(`${TMDB_URL}/search/movie?query=${query}&language=${language}`, {
            headers: {
                Authorization: `Bearer ${API_KEY}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();
        const resultsContainer = document.getElementById("movie-results");
        resultsContainer.innerHTML = "";

        if (data.results.length === 0) {
            resultsContainer.innerHTML = "<p>No results found.</p>";
            return;
        }

        for (const movie of data.results) {
            const trailerUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(movie.title + " trailer")}`;
            const fullMovieUrl = await fetchWatchProvider(movie.id);

            const movieDiv = document.createElement("div");
            movieDiv.classList.add("movie");
            movieDiv.innerHTML = `
                <img src="https://image.tmdb.org/t/p/w200${movie.poster_path}" alt="${movie.title}">
                <p><b>${movie.title}</b></p>
                <p>⭐ ${movie.vote_average} | ${movie.release_date}</p>
                <div class="movie-buttons">
                    <a href="${trailerUrl}" target="_blank" class="watch-btn">Watch Trailer</a>
                    <a href="${fullMovieUrl}" target="_blank" class="watch-btn">Watch Full Movie</a>
                </div>
            `;
            resultsContainer.appendChild(movieDiv);
        }
    } catch (error) {
        console.error("Error fetching movie data:", error);
    }
}

async function fetchWatchProvider(movieId) {
    try {
        const response = await fetch(`${TMDB_URL}/movie/${movieId}/watch/providers`, {
            headers: {
                Authorization: `Bearer ${API_KEY}`,
                "Content-Type": "application/json"
            }
        });

        const data = await response.json();
        return data.results?.US?.link || "https://www.google.com/search?q=watch+movie";
    } catch (error) {
        console.error("Error fetching watch providers:", error);
        return "https://www.google.com/search?q=watch+movie";
    }
}
