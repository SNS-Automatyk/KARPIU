import umail
import network

#UZUPELNIC DANE
ssid = ''
password = ''

sender_email = 'karpiunator@gmail.com'
sender_name = 'ESP32' #sender name
sender_app_password = 'iwpemdqmrccpaknw'
recipient_email ='stone.ruina@gmail.com'
email_subject ='Test Email'

def connect_wifi(ssid, password):
  station = network.WLAN(network.STA_IF)
  station.active(True)
  station.connect(ssid, password)
  while station.isconnected() == False:
    pass
  print('Connection successful')
  print(station.ifconfig())
    
connect_wifi(ssid, password)

smtp = umail.SMTP('smtp.gmail.com', 465, ssl=False) # Gmail's SSL port
smtp.login(sender_email, sender_app_password)
smtp.to(recipient_email)
smtp.write("From:" + sender_name + "<"+ sender_email+">\n")
smtp.write("Subject:" + email_subject + "\n")
smtp.write("Hello from ESP32")
smtp.send()
smtp.quit()
