import requests
from bs4 import BeautifulSoup
import os
import subprocess
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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

async def download_video(hd_link, episode_number):
    response = requests.get(hd_link, stream=True)
    if response.status_code == 200:
        os.makedirs("downloads", exist_ok=True)
        filename = f"downloads/Episode_{episode_number}.mp4"
        
        await update.message.reply_text(f"Starting download for Episode {episode_number}...")

        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        await update.message.reply_text(f"Download complete for Episode {episode_number}.")
        return filename
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send me a URL and I'll download the video for you!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    episode_links = scrape_episode_links(url)
    downloaded_files = []

    if episode_links:
        for index, link in enumerate(episode_links, start=1):
            full_link = f"https://shortflixme.site{link}"
            hd_link = scrape_hd_link(full_link)
            if hd_link:
                video_file = await download_video(hd_link, index)
                if video_file:
                    downloaded_files.append(video_file)
                else:
                    await update.message.reply_text("Failed to download video.")
            else:
                await update.message.reply_text("HD link not found.")

        # Merge videos after downloading all
        if downloaded_files:
            await update.message.reply_text("Starting merge process...")
            merged_file = "downloads/merged_video.mp4"
            # Create the ffmpeg command
            input_files = ' '.join(f"-i {file}" for file in downloaded_files)
            ffmpeg_command = f"ffmpeg {input_files} -filter_complex 'concat=n={len(downloaded_files)}:v=1:a=1' -y {merged_file}"
            
            # Execute the command
            subprocess.run(ffmpeg_command, shell=True, check=True)
            await update.message.reply_text("Merge complete.")

            # Upload the merged video
            await update.message.reply_text("Starting upload...")
            with open(merged_file, 'rb') as f:
                await update.message.reply_video(f, caption="Here is your merged video!")
            await update.message.reply_text("Upload complete.")

            # Clean up downloaded files
            for file in downloaded_files:
                os.remove(file)
            os.remove(merged_file)  # Remove the merged video after sending
        else:
            await update.message.reply_text("No videos were downloaded.")
    else:
        await update.message.reply_text("No episode links found or failed to access the URL.")

def main():
    # Ganti 'YOUR_TOKEN' dengan token bot Anda
    updater = ApplicationBuilder().token("8073329754:AAGq63AkumCruRyiYpI0rC-Cu6d8MwrrknQ").build()
    
    # Tambahkan handler
    updater.add_handler(CommandHandler("start", start))
    updater.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Mulai bot
    updater.run_polling()

if __name__ == '__main__':
    main()
