import umail
import network

#UZUPELNIC DANE
ssid = 'Automatyk'
password = 'automatyk5n5'

sender_email = 'karpiunator@gmail.com'
sender_name = 'ESP32'
sender_app_password = 'iwpemdqmrccpaknw'
recipient_email ='275414@student.pwr.edu.pl'
email_subject ='Karpiu test'

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
smtp.write("test 123456789 2137 halo halo")
smtp.send()
smtp.quit()
