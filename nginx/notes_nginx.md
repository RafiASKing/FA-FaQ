# Tujuan untuk mengarahkanan proxy ini

http://43.218.92.10:8080/ (app baru) -> faq-assist.cloud
http://43.218.92.10:8502/ (admin) -> faq-assist.cloud/admin
http://43.218.92.10:8501/ (app jadul) -> faq-assist.cloud/old-version


sudo ln -s "/home/ubuntu/eighthExperiment/nginx/faq-assist.cloud.conf" /etc/nginx/sites-available/faq-assist.cloud.conf

# Perintah yang perlu Anda jalankan setelah pull, jadi tidak hanya pull saja tapi perlu refresh
sudo nginx -t && sudo systemctl reload nginx

