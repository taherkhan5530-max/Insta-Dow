# app.py

from flask import Flask, render_template, request, send_file
import instaloader
import os
import shutil
from urllib.parse import urlparse

# 'Cx Instagram video Downloader' নামে Flask অ্যাপ্লিকেশন তৈরি
app = Flask(__name__)

# Instaloader অবজেক্ট ইনিশিয়ালাইজ করুন
# এটি একটি সাধারণ ডাউনলোডের জন্য, কিন্তু ইনস্টাগ্রাম প্রায়ই এটিকে ব্লক করে দিতে পারে।
L = instaloader.Instaloader()

# ডাউনলোড করার জন্য একটি ডিরেক্টরি সেট করুন
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/', methods=['GET', 'POST'])
def index():
    download_link = None
    error_message = None
    
    # POST রিকোয়েস্ট হ্যান্ডেল করা
    if request.method == 'POST':
        post_url = request.form.get('instagram_url')
        
        if post_url:
            # URL থেকে Post Shortcode বের করা
            try:
                # URL পার্স করে শর্টকোড বের করা
                parsed_url = urlparse(post_url)
                path_parts = parsed_url.path.strip('/').split('/')
                
                # যদি URL-এ 'p' (post) বা 'reel' থাকে
                if 'p' in path_parts or 'reel' in path_parts:
                    post_shortcode = path_parts[-1] if 'reel' in path_parts else path_parts[1]
                else:
                    error_message = "Invalid Instagram Post or Reel URL."
                    return render_template('index.html', error=error_message, app_name="Cx Instagram video Downloader")

                # Instaloader ব্যবহার করে পোস্ট ডাউনলোড করা
                try:
                    # Instaloader একটি পোস্ট ডাউনলোড করলে, এটি পোস্টের মেটাডেটা সহ বেশ কিছু ফাইল তৈরি করে।
                    # আমরা শুধুমাত্র ভিডিও ফাইলটি খুঁজব।
                    
                    # একটি টেম্পোরারি ডিরেক্টরি তৈরি করুন ডাউনলোড করার জন্য
                    temp_dir = os.path.join(DOWNLOAD_DIR, post_shortcode)
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)

                    # Instaloader দিয়ে ডাউনলোড
                    # L.dirname_pattern সেট করলে সব ফাইল নির্দিষ্ট ডিরেক্টরিতে ডাউনলোড হবে
                    L.dirname_pattern = temp_dir
                    
                    # Instaloader ব্যবহার করে সরাসরি পোস্ট ডাউনলোড করার চেষ্টা
                    # পোস্টের URL থেকে শর্টকোড বা আইডি পেতে হবে
                    # Instaloader এর Post.from_shortcode() ফাংশন ব্যবহার করা যেতে পারে।
                    
                    post = instaloader.Post.from_shortcode(L.context, post_shortcode)
                    
                    # যদি এটি ভিডিও হয়, তবে ডাউনলোড করুন
                    if post.is_video:
                        L.download_post(post, temp_dir)
                        
                        # ডাউনলোড হওয়ার পর ভিডিও ফাইলটি খুঁজে বের করা
                        video_file_name = None
                        for filename in os.listdir(temp_dir):
                            if filename.endswith(".mp4"):
                                video_file_name = filename
                                break
                        
                        if video_file_name:
                            video_path = os.path.join(temp_dir, video_file_name)
                            # ডাউনলোডের জন্য লিঙ্ক তৈরি করা
                            download_link = f"/download/{post_shortcode}/{video_file_name}"
                        else:
                            error_message = "Video file not found after download."

                    else:
                        error_message = "The provided URL is not a video post (Reel/Video). It might be an image."
                        
                    
                except Exception as e:
                    error_message = f"Download failed: {str(e)}. Instagram's protection might be active."
                
            except Exception as e:
                error_message = f"Error processing URL: {str(e)}"
        else:
            error_message = "Please enter an Instagram URL."

    # ডাউনলোড লিঙ্ক সহ প্রধান টেমপ্লেট রেন্ডার করা
    return render_template('index.html', download_link=download_link, error=error_message, app_name="Cx Instagram video Downloader")

@app.route('/download/<shortcode>/<filename>', methods=['GET'])
def serve_video(shortcode, filename):
    file_path = os.path.join(DOWNLOAD_DIR, shortcode, filename)
    
    if os.path.exists(file_path):
        # ফাইলটি পরিবেশন (serve) করা এবং তারপর ডিরেক্টরি মুছে ফেলা
        try:
            return send_file(file_path, as_attachment=True, download_name=filename)
        finally:
            # একবার ফাইল সার্ভ করার পর, টেম্পোরারি ডিরেক্টরিটি মুছে ফেলুন
            try:
                shutil.rmtree(os.path.join(DOWNLOAD_DIR, shortcode))
            except Exception as e:
                print(f"Error removing directory: {e}")
    
    return "File not found", 404


if __name__ == '__main__':
    # '0.0.0.0' হোস্ট করলে এটি যেকোনো আইপি অ্যাড্রেস থেকে অ্যাক্সেস করা যাবে (হোস্টিং এর জন্য প্রয়োজনীয়)
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
