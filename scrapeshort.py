import requests
from bs4 import BeautifulSoup
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

def scrape_episode_links(url):
    response = requests.get(url)
    if response.status_code != 200:
        return []
    soup = BeautifulSoup(response.content, 'html.parser')
    episode_list_div = soup.find('div', class_='relatedEpisode_relatedEpisode__l_NFQ')
    if not episode_list_div:
        return []
    episode_links = []
    for link in episode_list_div.find_all('a'):
        href = link.get('href')
        if href:
            episode_links.append(href)
    return episode_links

def scrape_hd_link(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.content, 'html.parser')
    video_tag = soup.find('video', id='my-video')
    if not video_tag:
        return None
    sources = video_tag.find_all('source')
    hd_link = None
    for source in sources:
        if source.get('label') == 'HD':
            hd_link = source.get('src')
            break
    return hd_link

def download_video(hd_link, episode_number):
    response = requests.get(hd_link, stream=True)
    if response.status_code == 200:
        os.makedirs("downloads", exist_ok=True)
        filename = f"downloads/Episode_{episode_number}.mp4"
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    return None

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send me a URL and I'll download the video for you!")

def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    episode_links = scrape_episode_links(url)

    if episode_links:
        for index, link in enumerate(episode_links, start=1):
            full_link = f"https://shortflixme.site{link}"
            hd_link = scrape_hd_link(full_link)
            if hd_link:
                video_file = download_video(hd_link, index)
                if video_file:
                    with open(video_file, 'rb') as f:
                        update.message.reply_video(f)
                    os.remove(video_file)  # Hapus video setelah diupload
                else:
                    update.message.reply_text("Failed to download video.")
            else:
                update.message.reply_text("HD link not found.")
    else:
        update.message.reply_text("No episode links found or failed to access the URL.")

def main():
    # Ganti 'YOUR_TOKEN' dengan token bot Anda
    updater = Updater("7932643319:AAFaQy4-KjAAv0MZWzH9Qh0hHXsptuTMRiU")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
