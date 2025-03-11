import umail
import network
import ubinascii
import urandom as random


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


def boundary():
    return ''.join(random.choice('0123456789ABCDEFGHIJKLMNOUPQRSTUWVXYZ') for i in range(15))

def send_mail(sender, recipient, password, subject, content, attachment = None):
    smtp = umail.SMTP('smtp.gmail.com', 465, ssl=False)
    smtp.login(sender, password)
    smtp.to(recipient)
    smtp.write("From: {0} <{0}>\n".format(sender))
    smtp.write("To: {0} <{0}>\n".format(recipient))
    smtp.write("Subject: {0}\n".format(subject))
    if attachment:
        text_id = boundary()
        attachment_id = boundary()
        smtp.write("MIME-Version: 1.0\n")
        smtp.write('Content-Type: multipart/mixed;\n boundary="------------{0}"\n'.format(attachment_id))
        smtp.write('--------------{0}\nContent-Type: multipart/alternative;\n boundary="------------{1}"\n\n'.format(attachment_id, text_id))
        smtp.write('--------------{0}\nContent-Type: text/plain; charset=utf-8; format=flowed\nContent-Transfer-Encoding: 7bit\n\n{1}\n\n--------------{0}--\n\n'.format(text_id, email['text']))
        smtp.write('--------------{0}\nContent-Type: image/jpeg;\n name="{1}"\nContent-Transfer-Encoding: base64\nContent-Disposition: attachment;\n  filename="{1}"\n\n'.format(attachment_id, attachment['name']))
        b64 = ubinascii.b2a_base64(attachment['bytes'])
        smtp.write(b64)
        smtp.write('--------------{0}--'.format(attachment_id))
        smtp.send()
    else:
        smtp.send(content)
    smtp.quit()


    
connect_wifi(ssid, password)
send_mail(sender_email, recipient_email, sender_app_password, "temat","tresc!!!!!!!!!!!!!...\n\n\n")

