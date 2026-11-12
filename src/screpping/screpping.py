"""
Menjalankan aplikasi:
    streamlit run screpping.py

Instalasi:
    pip install -U streamlit twscrape pandas scikit-learn
"""
import asyncio
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import pandas as pd
try:
    import streamlit as st
except ImportError:
    st = None
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# KONFIGURASI
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
configured_db = os.getenv("COORDINX_SCRAPER_DB")
configured_db_path = Path(configured_db) if configured_db else REPOSITORY_ROOT / "accounts.db"
if not configured_db_path.is_absolute():
    configured_db_path = REPOSITORY_ROOT / configured_db_path
DB_PATH = str(configured_db_path.resolve())
ACCOUNT_NAME = "acc1"
RAW_DATA_DIR = Path("../../data/raw")

def parse_post_id(value: str):
    """Ambil ID postingan dari URL X/Twitter yang mengandung /status/{id}."""
    match = re.search(r"/status/(\d+)", str(value))
    return int(match.group(1)) if match else None

def normalize_query(value: str) -> str:
    """Ubah URL hashtag atau URL pencarian X menjadi query pencarian."""
    value = str(value).strip()

    hashtag_match = re.search(
        r"(?:x|twitter)\.com/hashtag/([^/?#]+)",
        value,
        flags=re.IGNORECASE,
    )
    if hashtag_match:
        return f"#{unquote(hashtag_match.group(1))}"

    if re.match(
        r"https?://(?:www\.)?(?:x|twitter)\.com/search",
        value,
        flags=re.IGNORECASE,
    ):
        query = parse_qs(urlparse(value).query).get("q", [""])[0]
        return unquote(query)
    return value

def build_query(query: str, days=None) -> str:
    """Tambahkan operator since: jika batas waktu digunakan."""
    normalized = normalize_query(query)

    if days and "since:" not in normalized.lower():
        start_date = (
            pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=int(days))
        ).strftime("%Y-%m-%d")
        normalized = f"{normalized} since:{start_date}"
    return normalized

def clean_cookies(cookies: str) -> str:
    """Rapikan format cookie tanpa mencetak nilainya ke log."""
    cookies = (cookies or "").strip().strip('"').strip("'")
    return re.sub(r"\s*;\s*", "; ", cookies)

def safe_filename(value: str) -> str:
    """Batasi nama file agar tidak mengandung path atau karakter berbahaya."""
    filename = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).strip())
    return filename.strip("_") or "dataset"

def extract_post_row(tweet) -> dict | None:
    """
    Ubah objek Tweet twscrape menjadi satu baris data.

    source_account_id = akun yang membuat postingan yang sedang diproses.
    target_account_id = akun pemilik postingan yang menjadi target relasi.
    """
    if tweet is None:
        return None

    user = getattr(tweet, "user", None)
    if user is None:
        return None

    relation_type = "original"
    target_post_id = None
    target_account_id = None
    target_username = None

    retweeted_tweet = getattr(tweet, "retweetedTweet", None)
    quoted_tweet = getattr(tweet, "quotedTweet", None)
    reply_post_id = getattr(tweet, "inReplyToTweetId", None)
    reply_user = getattr(tweet, "inReplyToUser", None)

    if retweeted_tweet is not None:
        relation_type = "retweet"
        target_post_id = getattr(retweeted_tweet, "id", None)

        target_user = getattr(retweeted_tweet, "user", None)
        if target_user is not None:
            target_account_id = getattr(target_user, "id", None)
            target_username = getattr(target_user, "username", None)

    elif quoted_tweet is not None:
        relation_type = "quote"
        target_post_id = getattr(quoted_tweet, "id", None)

        target_user = getattr(quoted_tweet, "user", None)
        if target_user is not None:
            target_account_id = getattr(target_user, "id", None)
            target_username = getattr(target_user, "username", None)

    elif reply_post_id is not None:
        relation_type = "reply"
        target_post_id = reply_post_id

        if reply_user is not None:
            target_account_id = getattr(reply_user, "id", None)
            target_username = getattr(reply_user, "username", None)

    mentioned_users = getattr(tweet, "mentionedUsers", None) or []
    mentioned_user_ids = [
        str(getattr(mentioned_user, "id"))
        for mentioned_user in mentioned_users
        if getattr(mentioned_user, "id", None) is not None
    ]

    post_id = getattr(tweet, "id", None)
    account_id = getattr(user, "id", None)

    return {
        "post_id": str(post_id) if post_id is not None else None,
        "account_id": str(account_id) if account_id is not None else None,

        "id": str(post_id) if post_id is not None else None,
        "user_id": str(account_id) if account_id is not None else None,

        "source_post_id": str(post_id) if post_id is not None else None,
        "source_account_id": str(account_id) if account_id is not None else None,
        "target_post_id": (
            str(target_post_id) if target_post_id is not None else None
        ),
        "target_account_id": (
            str(target_account_id) if target_account_id is not None else None
        ),
        "target_username": target_username,
        "relation_type": relation_type,
        "mentioned_user_ids": mentioned_user_ids,

        "date": getattr(tweet, "date", None),
        "text": getattr(tweet, "rawContent", "") or "",
        "url": getattr(tweet, "url", None),
        "conversation_id": (
            str(getattr(tweet, "conversationId", None))
            if getattr(tweet, "conversationId", None) is not None
            else None
        ),

        "username": getattr(user, "username", None),
        "created": getattr(user, "created", None),
        "followers": getattr(user, "followersCount", None),
        "following": getattr(user, "friendsCount", None),
        "statuses": getattr(user, "statusesCount", None),
        "bio": getattr(user, "rawDescription", "") or "",
        "avatar": getattr(user, "profileImageUrl", "") or "",

        "is_rt": relation_type == "retweet",
        "is_reply": relation_type == "reply",
        "is_quote": relation_type == "quote",
    }

# SCRAPING DENGAN TWSCRAPE
async def _scrape(query, limit, cookies, fetch_replies=False, days=None):
    from twscrape import API, gather

    api = API(DB_PATH, raise_when_no_account=True)
    cookies = clean_cookies(cookies)

    if cookies:
        if "auth_token=" not in cookies or "ct0=" not in cookies:
            raise RuntimeError(
                "Format cookie tidak sesuai. Dibutuhkan auth_token dan ct0."
            )

        await api.pool.delete_accounts(ACCOUNT_NAME)
        await api.pool.add_account(
            ACCOUNT_NAME,
            "x",
            "x@example.com",
            "x",
            cookies=cookies,
        )

    accounts = await api.pool.get_all()

    if not accounts:
        raise RuntimeError(
            "Belum ada akun di accounts.db. Tambahkan akun twscrape terlebih dahulu."
        )

    active_accounts = [account for account in accounts if account.active]
    if not active_accounts:
        errors = "; ".join(
            f"{account.username}: {account.error_msg}"
            for account in accounts
        )
        raise RuntimeError(f"Tidak ada akun aktif. Detail: {errors}")

    post_id = parse_post_id(query)

    if post_id:
        first_post = await api.tweet_details(post_id)
        items = [first_post] if first_post else []
        items.extend(await gather(api.tweet_replies(post_id, limit=int(limit))))

    else:
        search_query = build_query(query, days)
        items = await gather(api.search(search_query, limit=int(limit)))

        if fetch_replies:
            seen_ids = {
                getattr(tweet, "id", None)
                for tweet in items
                if tweet is not None
            }

            for tweet in items[:20]:
                if not tweet:
                    continue

                reply_count = getattr(tweet, "replyCount", 0) or 0
                if reply_count <= 0:
                    continue

                replies = await gather(
                    api.tweet_replies(tweet.id, limit=50)
                )

                for reply in replies:
                    reply_id = getattr(reply, "id", None)
                    if reply is not None and reply_id not in seen_ids:
                        seen_ids.add(reply_id)
                        items.append(reply)

    rows = []
    for tweet in items:
        row = extract_post_row(tweet)
        if row is not None:
            rows.append(row)

    dataframe = pd.DataFrame(rows)

    if not dataframe.empty and days:
        cutoff = (
            pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=int(days))
        )
        dataframe["date"] = pd.to_datetime(
            dataframe["date"], utc=True, errors="coerce"
        )
        dataframe = dataframe[dataframe["date"] >= cutoff]

    if dataframe.empty:
        raise RuntimeError(
            "Tidak ada postingan yang berhasil dikumpulkan. "
            "Periksa query, akses akun, batas waktu, dan kemungkinan rate limit."
        )
    return dataframe

async def scrape_async(query, limit, cookies, fetch_replies=False, days=None):
    """Koleksi data untuk caller async seperti FastAPI."""
    return await _scrape(
        query=query,
        limit=limit,
        cookies=cookies,
        fetch_replies=fetch_replies,
        days=days,
    )


def scrape(query, limit, cookies, fetch_replies=False, days=None):
    """Jalankan koleksi async dari antarmuka sinkron seperti Streamlit."""
    return asyncio.run(scrape_async(query, limit, cookies, fetch_replies, days))

async def _accounts_status():
    from twscrape import API

    api = API(DB_PATH)
    accounts = await api.pool.get_all()

    return [
        {
            "username": account.username,
            "active": bool(account.active),
            "error": account.error_msg,
        }
        for account in accounts
    ]

def normalize_text_for_similarity(text) -> str:
    """
    Normalisasi ringan untuk perbandingan teks.
    Teks asli tetap disimpan di kolom 'text'.
    """
    text = str(text or "").lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def ensure_compatible_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Samakan beberapa nama kolom CSV lama dan baru."""
    dataframe = dataframe.copy()

    aliases = {
        "post_id": ["post_id", "source_post_id", "id"],
        "account_id": ["account_id", "source_account_id", "user_id"],
        "text": ["text", "raw_text"],
        "username": ["username"],
    }

    for destination, candidates in aliases.items():
        if destination not in dataframe.columns:
            for candidate in candidates:
                if candidate in dataframe.columns:
                    dataframe[destination] = dataframe[candidate]
                    break

    required_defaults = {
        "post_id": None,
        "account_id": None,
        "text": "",
        "username": "unknown",
        "date": None,
        "created": None,
        "followers": 0,
        "following": 0,
        "statuses": 0,
        "bio": "",
        "avatar": "",
        "is_rt": False,
        "is_reply": False,
        "is_quote": False,
    }

    for column, default in required_defaults.items():
        if column not in dataframe.columns:
            dataframe[column] = default

    dataframe["account_key"] = dataframe["account_id"].fillna(
        dataframe["username"]
    ).astype(str)

    dataframe["date"] = pd.to_datetime(
        dataframe["date"], utc=True, errors="coerce"
    )
    dataframe["created"] = pd.to_datetime(
        dataframe["created"], utc=True, errors="coerce"
    )

    for column in ["followers", "following", "statuses"]:
        dataframe[column] = pd.to_numeric(
            dataframe[column], errors="coerce"
        ).fillna(0)

    for column in ["is_rt", "is_reply", "is_quote"]:
        dataframe[column] = (
            dataframe[column]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
        )

    dataframe["text"] = dataframe["text"].fillna("").astype(str)
    dataframe["username"] = dataframe["username"].fillna("unknown")
    dataframe["bio"] = dataframe["bio"].fillna("")
    dataframe["avatar"] = dataframe["avatar"].fillna("")

    return dataframe

def score(data, similarity_threshold=0.8, burst_users=5):
    """
    Menghasilkan skor heuristik awal.

    Skor ini bukan prediksi model machine learning dan bukan bukti
    bahwa suatu akun merupakan buzzer.
    """
    dataframe = ensure_compatible_columns(data)

    dataframe["duplicate_similarity"] = 0.0
    dataframe["burst"] = 0.0

    original_posts = dataframe[
        ~dataframe["is_rt"] & dataframe["text"].str.strip().ne("")
    ].copy()

    if len(original_posts) > 1:
        try:
            vectorizer = TfidfVectorizer(
                max_features=10000,
                ngram_range=(1, 2),
            )
            text_matrix = vectorizer.fit_transform(
                original_posts["text"].map(normalize_text_for_similarity)
            )
            similarity_matrix = cosine_similarity(text_matrix)

            account_keys = original_posts["account_key"].to_numpy()

            for index in range(len(original_posts)):
                same_account = account_keys == account_keys[index]
                similarity_matrix[index, same_account] = 0.0

            max_similarity = similarity_matrix.max(axis=1)
            dataframe.loc[
                original_posts.index, "duplicate_similarity"
            ] = max_similarity

        except ValueError:
            pass

    valid_dates = dataframe["date"].notna()
    dataframe.loc[valid_dates, "minute"] = (
        dataframe.loc[valid_dates, "date"].dt.floor("min")
    )

    minute_account_count = (
        dataframe.loc[valid_dates]
        .groupby("minute")["account_key"]
        .transform("nunique")
    )

    dataframe.loc[valid_dates, "burst"] = (
        minute_account_count >= int(burst_users)
    ).astype(float)

    account_summary = (
        dataframe.groupby("account_key", dropna=False)
        .agg(
            username=("username", "last"),
            posts_in_dataset=("post_id", "count"),
            followers=("followers", "max"),
            following=("following", "max"),
            statuses=("statuses", "max"),
            created=("created", "min"),
            bio=("bio", "first"),
            avatar=("avatar", "first"),
            duplicate_ratio=("duplicate_similarity", "mean"),
            burst_ratio=("burst", "mean"),
            retweet_ratio=("is_rt", "mean"),
            reply_ratio=("is_reply", "mean"),
            quote_ratio=("is_quote", "mean"),
        )
        .reset_index()
        .rename(columns={"account_key": "account_id"})
    )

    now = pd.Timestamp.now(tz="UTC")
    account_age = (now - account_summary["created"]).dt.days
    account_age = account_age.clip(lower=1)
    
    tweets_per_day = account_summary["statuses"] / account_age
    following_follower_ratio = (
        account_summary["following"]
        / account_summary["followers"].clip(lower=1)
    )

    heuristic_score = (
        (account_age < 90).astype(int) * 10
        + (account_age < 30).astype(int) * 5
        + (tweets_per_day > 50).astype(int) * 15
        + (following_follower_ratio > 5).astype(int) * 10
        + account_summary["avatar"]
        .str.contains("default_profile", na=False)
        .astype(int) * 5
        + (account_summary["bio"].str.len() == 0).astype(int) * 5
        + account_summary["username"]
        .str.count(r"\d")
        .ge(5)
        .astype(int) * 5
        + account_summary["duplicate_ratio"] * 25
        + account_summary["burst_ratio"] * 20
    )

    account_summary["account_age_days"] = account_age
    account_summary["statuses_per_day_estimate"] = tweets_per_day.round(1)
    account_summary["heuristic_score"] = (
        heuristic_score.clip(upper=100).round().astype(int)
    )

    account_summary = account_summary.sort_values(
        "heuristic_score", ascending=False
    )

    return dataframe, account_summary

# STREAMLIT
def render_scrape_mode():
    query = st.text_input(
        "Link postingan / keyword / #hashtag / link hashtag"
    )
    issue_name = st.sidebar.text_input(
        "Nama isu",
        "isu",
    )
    limit = st.sidebar.number_input(
        "Jumlah maksimum postingan",
        min_value=1,
        max_value=5000,
        value=200,
        step=50,
    )
    cookies = st.sidebar.text_input(
        "Cookie X (auth_token=...; ct0=...)",
        type="password",
        help="Cookie bersifat rahasia. Jangan dibagikan atau dimasukkan ke Git.",
    )
    use_days = st.sidebar.checkbox("Batasi rentang waktu", True)
    days = (
        st.sidebar.number_input(
            "Maksimal berapa hari terakhir",
            min_value=1,
            max_value=365,
            value=30,
        )
        if use_days
        else None
    )
    fetch_replies = st.sidebar.checkbox(
        "Ambil balasan dari hasil pencarian (lebih lambat)",
        False,
    )

    if st.sidebar.button("Cek status akun"):
        try:
            status = asyncio.run(_accounts_status())
            st.sidebar.dataframe(
                pd.DataFrame(status),
                use_container_width=True,
            )
        except Exception as error:
            st.sidebar.error(f"Gagal memeriksa akun: {error}")

    if st.button("Scrape & Analisis", type="primary") and query.strip():
        with st.spinner("Mengambil data dari X..."):
            try:
                data = scrape(
                    query=query,
                    limit=int(limit),
                    cookies=cookies,
                    fetch_replies=fetch_replies,
                    days=days,
                )

                data["isu"] = issue_name
                data["query"] = query

                RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
                output_path = RAW_DATA_DIR / f"{safe_filename(issue_name)}.csv"
                data.to_csv(output_path, index=False)

                st.session_state["raw_data"] = data
                st.session_state["raw_path"] = str(output_path)

            except Exception as error:
                st.error(f"Scraping gagal: {error}")

    raw_data = st.session_state.get("raw_data")

    if raw_data is not None:
        st.success(
            f"Data mentah tersimpan: {st.session_state.get('raw_path')}"
        )

    return raw_data

def render_upload_mode():
    uploaded_file = st.file_uploader(
        "Upload CSV hasil scraping",
        type=["csv"],
    )

    if uploaded_file is None:
        return None

    try:
        return pd.read_csv(uploaded_file)
    except Exception as error:
        st.error(f"Gagal membaca CSV: {error}")
        return None

def render_analysis(data):
    if data is None or data.empty:
        return

    similarity_threshold = st.sidebar.slider(
        "Ambang kemiripan teks",
        min_value=0.5,
        max_value=1.0,
        value=0.8,
        step=0.05,
    )
    burst_users = st.sidebar.slider(
        "Minimal akun per menit (burst)",
        min_value=3,
        max_value=20,
        value=5,
    )

    try:
        analyzed_posts, account_summary = score(
            data,
            similarity_threshold=similarity_threshold,
            burst_users=burst_users,
        )
    except Exception as error:
        st.error(f"Analisis gagal: {error}")
        return

    st.caption(
        f"{len(analyzed_posts)} postingan dari "
        f"{account_summary.shape[0]} akun unik."
    )
    st.info(
        "Skor yang ditampilkan adalah skor heuristik untuk eksplorasi awal, "
        "bukan hasil klasifikasi AI dan bukan bukti bahwa akun melakukan "
        "koordinasi tidak autentik."
    )

    left_column, right_column = st.columns([3, 2])
    
    with left_column:
        st.subheader("Akun dengan skor heuristik tertinggi")
        st.dataframe(
            account_summary.head(50),
            use_container_width=True,
        )

        st.download_button(
            "Unduh ringkasan akun (CSV)",
            data=account_summary.to_csv(index=False).encode("utf-8"),
            file_name="hasil_analisis_akun.csv",
            mime="text/csv",
        )

    with right_column:
        st.subheader("Pola posting per jam")
        hourly_posts = (
            analyzed_posts.dropna(subset=["date"])
            .groupby(analyzed_posts.dropna(subset=["date"])["date"].dt.floor("h"))
            .size()
        )
        st.bar_chart(hourly_posts)

    st.subheader("Postingan dengan kemiripan tinggi antar-akun")
    similar_posts = analyzed_posts[
        analyzed_posts["duplicate_similarity"] >= similarity_threshold
    ]

    display_columns = [
        column
        for column in ["date", "username", "text", "duplicate_similarity"]
        if column in similar_posts.columns
    ]

    st.dataframe(
        similar_posts[display_columns].sort_values(
            "duplicate_similarity",
            ascending=False,
        ),
        use_container_width=True,
    )

    st.download_button(
        "Unduh postingan hasil analisis (CSV)",
        data=analyzed_posts.to_csv(index=False).encode("utf-8"),
        file_name="hasil_analisis_postingan.csv",
        mime="text/csv",
    )

def main():
    st.set_page_config(
        page_title="Scaping Data X ",
        page_icon="🔎",
        layout="wide",
    )

    st.title("Scaping X")
    st.caption(
        "AI-powered coordinated behavior analysis for public X posts"
    )

    # mode = st.sidebar.radio(
    #     "Sumber data",
    #     ["Scrape X", "Upload CSV"],
    # )
    
    # if mode == "Scrape X":
        #     raw_data = render_scrape_mode()
        # else:
        #     raw_data = render_upload_mode()
    
    raw_data = render_scrape_mode()

    if raw_data is not None and not raw_data.empty:
        render_analysis(raw_data)
    elif raw_data is not None:
        st.warning("Dataset kosong atau tidak memiliki postingan.")

if __name__ == "__main__":
    main()
