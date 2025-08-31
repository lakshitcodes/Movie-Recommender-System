# app.py
import streamlit as st
import pickle
import requests
import math
from typing import Tuple

st.set_page_config(page_title="Movie Recommender", layout="wide", page_icon="🎬")

# ---------- CONFIG (change if necessary) ----------
TMDB_API_KEY = "abc7fe24bd8cfe37b1c9ebcbd90cb8e5"  # <-- replace with your key if needed
MOVIES_PKL = "movies.pkl"
SIMILARITY_PKL = "similarity.pkl"
FALLBACK_POSTER = "https://via.placeholder.com/400x600?text=No+Image"
# --------------------------------------------------


# ---------- HELPERS ----------
@st.cache_data
def load_data(movies_path: str, sim_path: str):
    new_df = pickle.load(open(movies_path, "rb"))
    similarity = pickle.load(open(sim_path, "rb"))
    return new_df, similarity


@st.cache_data
def fetch_poster_and_info(movie_id: int) -> Tuple[str, float, int, str, str]:
    """
    Returns: (poster_url, vote_average, vote_count, overview, tmdb_url)
    Cached to reduce API hits.
    """
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        r = requests.get(url, timeout=6)
        data = r.json()
        poster_path = data.get("poster_path")
        poster = (
            f"https://image.tmdb.org/t/p/w500{poster_path}"
            if poster_path
            else FALLBACK_POSTER
        )
        return (
            poster,
            float(data.get("vote_average", 0.0)),
            int(data.get("vote_count", 0)),
            data.get("overview", "") or "",
            f"https://www.themoviedb.org/movie/{movie_id}",
        )
    except Exception:
        return (
            FALLBACK_POSTER,
            0.0,
            0,
            "",
            f"https://www.themoviedb.org/movie/{movie_id}",
        )


def round_to_half(x: float) -> float:
    return round(x * 2) / 2.0


def stars_html(rating_raw: float, accent="#ff9f1a", size=16) -> str:
    """
    Generate HTML (SVG) for 5-star rating.
    Accepts rating in 0-10 scale or 0-5 scale. Normalizes to 5.
    Rounds to nearest half star.
    """
    r = float(rating_raw)
    if r > 5:
        r = r / 2.0  # map 0-10 to 0-5
    r = max(0.0, min(5.0, r))
    r = round_to_half(r)
    full = int(math.floor(r))
    half = 1 if (r - full) == 0.5 else 0
    empty = 5 - full - half

    # simple SVG templates
    full_svg = f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{accent}" xmlns="http://www.w3.org/2000/svg" style="margin-right:4px"><path d="M12 .587l3.668 7.431 8.2 1.192-5.934 5.787 1.402 8.169L12 18.896 4.664 23.166l1.402-8.169L.132 9.21l8.2-1.192z"/></svg>"""
    # half star built with linearGradient
    half_svg = f"""
    <svg width="{size}" height="{size}" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" style="margin-right:4px">
      <defs>
        <linearGradient id="g{int(size*10)}" x1="0" x2="1">
          <stop offset="50%" stop-color="{accent}" />
          <stop offset="50%" stop-color="#2b2b2b" />
        </linearGradient>
      </defs>
      <path fill="url(#g{int(size*10)})" d="M12 .587l3.668 7.431 8.2 1.192-5.934 5.787 1.402 8.169L12 18.896 4.664 23.166l1.402-8.169L.132 9.21l8.2-1.192z"/>
    </svg>
    """
    empty_svg = f"""<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.1" xmlns="http://www.w3.org/2000/svg" style="margin-right:4px"><path d="M12 .587l3.668 7.431 8.2 1.192-5.934 5.787 1.402 8.169L12 18.896 4.664 23.166l1.402-8.169L.132 9.21l8.2-1.192z"/></svg>"""

    html = '<div style="display:flex;align-items:center;">'
    html += full_svg * full
    html += half_svg * half
    html += empty_svg * empty
    html += "</div>"
    return html


def recommend(movie_title: str, df, similarity_matrix, top_n=5):
    try:
        idx = df[df["title"] == movie_title].index[0]
    except IndexError:
        return []
    distances = list(enumerate(similarity_matrix[idx]))
    distances = sorted(distances, key=lambda x: x[1], reverse=True)[1 : top_n + 1]
    recs = []
    for i, _ in distances:
        row = df.iloc[i]
        poster, vote_avg, vote_count, overview, tmdb_url = fetch_poster_and_info(
            row.movie_id
        )
        recs.append(
            {
                "title": row.title,
                "poster": poster,
                "vote_avg": vote_avg,
                "vote_count": vote_count,
                "overview": overview,
                "tmdb_url": tmdb_url,
            }
        )
    return recs


# ---------- Load data ----------
new_df, similarity = load_data(MOVIES_PKL, SIMILARITY_PKL)
movies_list = new_df["title"].tolist()


# ---------- Styles (clean & focused) ----------
st.markdown(
    """
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
    :root{
      --bg-1: #07142a;
      --bg-2: #071225;
      --card: rgba(255,255,255,0.04);
      --card-2: rgba(255,255,255,0.02);
      --accent: #ff7a18;
      --muted: #9aa6bf;
      --glass-border: rgba(255,255,255,0.06);
    }

    /* hide streamlit default items */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
      background: linear-gradient(180deg, var(--bg-1), var(--bg-2));
      color: #e8f0ff;
      font-family: "Poppins", system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      padding: 28px 28px;
    }

    /* HERO */
    .hero {
      display:flex;
      align-items:center;
      gap:18px;
      padding:18px;
      border-radius:12px;
      margin-bottom:20px;
      background: linear-gradient(135deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border: 1px solid var(--glass-border);
      box-shadow: 0 8px 30px rgba(2,6,23,0.6);
    }
    .hero .logo {
      width:72px; height:72px; border-radius:12px;
      display:flex;align-items:center;justify-content:center;font-size:30px;
      background: linear-gradient(135deg, rgba(255,122,24,0.12), rgba(109,40,217,0.12));
    }
    .hero h1 { font-size:22px; margin:0; font-weight:700; color:#fff; }
    .hero p { margin:4px 0 0 0; color:var(--muted); font-size:14px; }

    /* Controls row */
    .controls {
      display:flex;
      gap:12px;
      align-items:center;
      margin-bottom:14px;
    }
    .controls .btn {
      background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
      border:1px solid var(--glass-border);
      padding:8px 12px;
      border-radius:10px;
      cursor:pointer;
      color:var(--muted);
      font-weight:600;
    }

    /* Card container for scrolling on mobile */
    .cards-container {
      display: flex;
      flex-direction: row;
      gap: 16px;
      overflow-x: auto;
      padding-bottom: 20px;
      scroll-behavior: smooth;
      -webkit-overflow-scrolling: touch; /* smooth scrolling on iOS */
    }
    
    /* Movie card */
    .movie-card {
      width: 100%;
      margin : 10px;
      min-width: 240px; /* minimum width for cards */
      border-radius:14px;
      overflow:hidden;
      background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
      border: 1px solid var(--glass-border);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
      transition: transform 0.12s cubic-bezier(.2,.8,.2,1), box-shadow 0.12s;
      box-shadow: 0 10px 30px rgba(2,6,23,0.5);
      display:flex;
      flex-direction:column;
      align-items:stretch;
    }
    .movie-card:hover { transform: translateY(-6px) scale(1.03); box-shadow: 0 20px 50px rgba(2,6,23,0.65); }
    .movie-card .poster {
      width:100%;
      height:340px;
      object-fit:cover;
      display:block;
      background:#0b1220;
    }
    .movie-card .card-body {
      padding:12px;
      display:flex;
      flex-direction:column;
      gap:8px;
      align-items:center;
    }
    .movie-title { font-size:15px; font-weight:600; text-align:center; color:#fff; margin:0; }
    .meta { display:flex; gap:8px; align-items:center; justify-content:center; }
    .vote-pill { padding:6px 10px; border-radius:999px; font-weight:700; color:var(--accent); background: rgba(255,122,24,0.08); border:1px solid rgba(255,122,24,0.06); }
    .vote-count { color:var(--muted); font-size:13px; }
    .overview { color:#cbd6ea; font-size:13px; line-height:1.2; text-align:center; max-height:88px; overflow:hidden; }

    /* Footer */
    .app-footer {
      margin-top:22px;
      padding:12px 16px;
      border-radius:12px;
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;
      background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.005));
      border:1px solid var(--glass-border);
      backdrop-filter: blur(6px);
    }
    .social a { color:#cfe6ff; margin-left:12px; font-size:18px; text-decoration:none; }
    .social a:hover { transform: translateY(-3px); opacity:0.95; }

    /* Responsive: let streamlit columns wrap; adjust image height on small screens */
    @media (max-width: 1000px) {
      .movie-card .poster { height:260px; }
    }
    
    @media (max-width: 576px) {
      .movie-card { 
        min-width: 280px; 
        width: 90%;
      }
      .movie-card .poster { height: 220px; }
      .hero { flex-direction: column; align-items:flex-start; gap:10px; }
      .app-footer{
        display : flex;
        justify-content : center;
        align-items:center;
        flex-direction : column;
      }
      .e1haskxa19{
        display : flex;
        justify-content : center;
        align-items:center;
      }
      .footer-content{
        display : flex;
        flex-direction : column;
        justify-content : center;
        align-items:center;
      }
      .footer-subtitle{
        display:none;
      }
    }
    .stSelectbox{
      display: flex !important;
      align-items: center !important;
    }
    .stVerticalBlock{
      display: flex !important;
      align-items: center !important;
    }
    .stHorizontalBlock{
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
    }
    .e1haskxa1{
      height : 80%;
      width : 60%;
    }
    .e52wr8w2{
      margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
      <div class="logo">🎞️</div>
      <div>
        <h1>🎬 Movie Recommender System</h1>
        <p>Discover movies you'll actually want to watch ...</p>
      </div>
      <div style="margin-left:auto;color:var(--muted);font-weight:600">Pick a movie → Click Recommend</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Controls (top row) ----------
st.markdown(
    """
<style>
.controls-container {
  display: flex;
  align-items: center !important;
  gap: 20px;
  margin-bottom: 10px;
}
.movie-select-container {
  flex: 4;
}
.recommend-btn-container {
  flex: 1;
  display: flex;
  align-items: center;
}
button.recommend-btn {
  height: 48px !important;
  padding: 0px 20px !important;
  background: linear-gradient(90deg, #ff7a18 0%, #ffb36b 100%) !important;
  color: white !important;
  font-weight: 700 !important;
  font-size: 1.1rem !important;
  border-radius: 10px !important;
  border: none !important;
  box-shadow: 0 2px 12px rgba(255,122,24,0.13) !important;
  transition: all 0.2s !important;
  margin-top: 25px !important;
}
button.recommend-btn:hover {
  background: linear-gradient(90deg, #ffb36b 0%, #ff7a18 100%) !important;
  transform: translateY(-2px) scale(1.03) !important;
  box-shadow: 0 4px 18px rgba(255,122,24,0.18) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

col1, col2 = st.columns([4, 2])
with col1:
    selected_movie_name = st.selectbox("Choose a movie", movies_list, index=0)
with col2:
    recommend_btn = st.button(
        "Recommend",
        key="recommend_btn",
        help="Show top 5 similar movies",
        type="primary",
        use_container_width=True,
    )

# ---------- Recommendation logic & display ----------
if recommend_btn:
    recs = recommend(selected_movie_name, new_df, similarity, top_n=5)
    if not recs:
        st.warning("No recommendations found for the selected title.")
    else:
        # Generate columns: show up to 5 cards in a single row (columns will wrap responsively)
        n_cols = 5
        cols = st.columns(n_cols, gap="large")
        for idx, col in enumerate(cols):
            with col:
                if idx >= len(recs):
                    # empty placeholder card
                    st.markdown(
                        """
                        <div class="movie-card" style="height:520px; display:flex;align-items:center;justify-content:center;color:var(--muted)">
                          <div style="text-align:center;padding:20px">No more recommendations</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    continue

                m = recs[idx]
                poster = m["poster"] or FALLBACK_POSTER
                title = m["title"]
                vote_avg = m["vote_avg"]
                vote_count = m["vote_count"]
                overview = m["overview"] or "No description available."
                tmdb_url = m["tmdb_url"]

                card = f"""
                <div class="movie-card">
                  <img class="poster" src="{poster}" onerror="this.src='{FALLBACK_POSTER}'" alt="poster">
                  <div class="card-body">
                    <div class="movie-title">{title}</div>
                    <div class="meta" style="margin-top:4px">
                      <div class="vote-pill">{vote_avg:.1f}</div>
                      <div style="display:flex;flex-direction:column;align-items:flex-start">
                        <div style="display:flex;align-items:center">
                          {stars_html(vote_avg, accent='#ffb36b', size=14)}
                          <div style="margin-left:6px;color:#e8f0ff;font-weight:600;font-size:13px">{vote_avg:.1f}/10</div>
                        </div>
                        <div class="vote-count">🗳 {vote_count} votes</div>
                      </div>
                    </div>
                    <div class="overview">{overview}</div>
                    <div style="width:100%;display:flex;justify-content:center;margin-top:6px">
                      <a href="{tmdb_url}" target="_blank" style="text-decoration:none">
                        <div class="tmdb" style="padding:8px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.04);background:rgba(255,255,255,0.02);color:var(--muted);font-weight:600">View on TMDB</div>
                      </a>
                    </div>
                  </div>
                </div>
                """
                st.markdown(card, unsafe_allow_html=True)

else:
    st.info("Choose a movie and click **Recommend** to view top 5 movie cards.")

# Footer
st.markdown(
    """
            <div class="app-footer">
              <div class="footer-content" style="display:flex;align-items:center;gap:12px">
                <div style="font-weight:700">Movie Recommender</div>
                <div class="footer-subtitle" style="color:var(--muted)">Curated suggestions • Machine Learning</div>
              </div>
              <div style="display:flex;align-items:center;gap:12px">
                <div style="color:var(--muted);font-size:14px">Developed by <strong>Lakshit Jain</strong></div>
                <div class="social">
                  <a href="https://github.com/lakshitcodes/Movie-Recommender-System" target="_blank"><i class="fa-brands fa-github"></i></a>
                  <a href="https://linkedin.com/in/jainlakshit" target="_blank"><i class="fa-brands fa-linkedin"></i></a>
                </div>
              </div>
            </div>
            """,
    unsafe_allow_html=True,
)
