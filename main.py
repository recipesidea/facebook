import os
import random
import requests
import google.generativeai as genai
import urllib.parse
import feedparser
import facebook  # Library baru untuk Facebook

# --- FUNGSI SCRAPING DAN GENERASI KONTEN (TETAP SAMA) ---
def scrape_google_news_sports():
    """Mengambil satu berita olahraga teratas dari Google News RSS Feed untuk Amerika Serikat."""
    rss_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnpHZ0pKVGlnQVAB?hl=en-US&gl=US&ceid=US:en"
    try:
        news_feed = feedparser.parse(rss_url)
        if not news_feed.entries:
            print("Peringatan: Tidak ada berita yang ditemukan di RSS Feed.")
            return None
        news_titles = [entry.title for entry in news_feed.entries]
        selected_news = random.choice(news_titles)
        return selected_news
    except Exception as e:
        print(f"Error saat mengakses atau parsing RSS Feed: {e}")
        return None

def generate_post_with_gemini(trend):
    """Membuat konten post dengan Gemini API berdasarkan satu tren."""
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan di environment variables!")
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = (
        f"You are a social media expert. Write a short, engaging post in English about this topic: '{trend}'. "
        f"The post MUST have a strong Call to Action to encourage clicks. "
        f"Do NOT add any links or hashtags in your response. Just provide the main text."
    )
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error saat menghubungi Gemini API: {e}")
        return None

def get_random_link(filename="links.txt"):
    """Membaca file dan memilih satu link secara acak."""
    try:
        with open(filename, 'r') as f:
            links = [line.strip() for line in f if line.strip()]
        return random.choice(links) if links else None
    except FileNotFoundError:
        print(f"Error: File '{filename}' tidak ditemukan.")
        return None

# --- FUNGSI BARU UNTUK POSTING KE FACEBOOK ---
def post_to_facebook(text_to_post, image_url=None):
    """Memposting teks dan gambar (opsional) ke Halaman Facebook."""
    page_id = os.getenv('FACEBOOK_PAGE_ID')
    facebook_access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')

    if not page_id or not facebook_access_token:
        print("❌ GAGAL: Pastikan FACEBOOK_PAGE_ID dan FACEBOOK_ACCESS_TOKEN ada di environment variables.")
        return

    try:
        graph = facebook.GraphAPI(access_token=facebook_access_token)

        if image_url:
            # Memposting dengan gambar
            graph.put_photo(image=requests.get(image_url).content,
                            message=text_to_post,
                            album_path=f'{page_id}/photos')
            print("✅ Berhasil memposting ke Facebook dengan gambar!")
        else:
            # Memposting hanya teks
            graph.put_object(parent_object=page_id,
                             connection_name='feed',
                             message=text_to_post)
            print("✅ Berhasil memposting teks ke Facebook!")

    except Exception as e:
        print(f"❌ GAGAL: Error saat memposting ke Facebook: {e}")


# --- FUNGSI UTAMA (DIPERBARUI) ---
if __name__ == "__main__":
    print("Memulai proses auto-posting ke Facebook...")

    # Langkah 1: Mengambil berita olahraga
    selected_news = scrape_google_news_sports()

    if selected_news:
        print(f"✅ Berita berhasil didapatkan: '{selected_news}'")

        # Langkah 2: Mendapatkan link acak
        random_link = get_random_link()
        if random_link:
            print(f"✅ Link berhasil didapatkan: '{random_link}'")

            # Langkah 3: Membuat konten dengan Gemini
            gemini_text = generate_post_with_gemini(selected_news)
            if gemini_text:
                print(f"✅ Teks dari Gemini berhasil dibuat.")

                # Langkah 4: Membuat URL gambar
                image_url = f"https://tse1.mm.bing.net/th?q={urllib.parse.quote(selected_news)}"
                print(f"✅ URL Gambar dibuat: {image_url}")

                # Gabungkan teks dan link
                final_post_text = f"{gemini_text}\n\n{random_link}" # Gunakan baris baru untuk keterbacaan

                print("\n--- POSTINGAN FINAL SIAP ---")
                print(f"Teks: {final_post_text}")
                print("----------------------------\n")

                # Langkah 5: Posting ke Facebook
                post_to_facebook(final_post_text, image_url)

            else:
                print("❌ GAGAL: Gemini tidak dapat membuat konten. Proses dihentikan.")
        else:
            print("❌ GAGAL: Tidak ada link yang ditemukan di links.txt. Proses dihentikan.")
    else:
        print("❌ GAGAL: Tidak ada berita yang bisa diambil dari RSS Feed. Proses dihentikan.")

    print("\nProses selesai.")