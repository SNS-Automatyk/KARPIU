import usocket
import ssl as ssl_module  # Zmieniamy nazwę importu, aby uniknąć kolizji
import ubinascii

DEFAULT_TIMEOUT = 10  # sec
LOCAL_DOMAIN = '127.0.0.1'
CMD_EHLO = 'EHLO'
CMD_STARTTLS = 'STARTTLS'
CMD_AUTH = 'AUTH'
CMD_MAIL = 'MAIL'
AUTH_PLAIN = 'PLAIN'
AUTH_LOGIN = 'LOGIN'

class SMTP:
    def cmd(self, cmd_str):
        """Wysyła komendę do serwera i oczekuje odpowiedzi"""
        sock = self._sock
        sock.write('%s\r\n' % cmd_str)
        resp = []
        next = True
        while next:
            code = sock.read(3)
            next = sock.read(1) == b'-'
            resp.append(sock.readline().strip().decode())
        return int(code), resp

    def __init__(self, host, port, ssl=False, username=None, password=None):
        try:
            addr = usocket.getaddrinfo(host, port)[0][-1]
            sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            sock.settimeout(DEFAULT_TIMEOUT)  # Ustaw timeout
            sock.connect(addr)
            if ssl:
                sock = ssl_module.wrap_socket(sock)  # Używamy ssl_module, aby uniknąć kolizji
            code = int(sock.read(3))
            sock.readline()
            if code != 220:
                raise ConnectionError(f'Błąd połączenia z serwerem: {code}')
            
            self._sock = sock
            code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
            if code != 250:
                raise ConnectionError(f'Błąd EHLO: {code}')

            if not ssl and CMD_STARTTLS in resp:
                code, resp = self.cmd(CMD_STARTTLS)
                if code != 220:
                    raise ConnectionError(f'Błąd STARTTLS: {code}')
                self._sock = ssl_module.wrap_socket(sock)  # Używamy ssl_module, aby uniknąć kolizji

            if username and password:
                self.login(username, password)
        except Exception as e:
            print(f"Nie udało się połączyć z serwerem: {e}")
            if hasattr(self, '_sock') and self._sock:
                self._sock.close()  # Zamykanie połączenia w przypadku błędu
            raise

    def login(self, username, password):
        try:
            self.username = username
            code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
            if code != 250:
                raise ConnectionError(f'Błąd EHLO: {code}')
            
            auths = None
            for feature in resp:
                if feature[:4].upper() == CMD_AUTH:
                    auths = feature[4:].strip('=').upper().split()
            if not auths:
                raise Exception("Brak obsługi autentykacji.")

            if AUTH_PLAIN in auths:
                from ubinascii import b2a_base64 as b64
                cren = b64(f"\0{username}\0{password}")[:-1].decode()
                code, resp = self.cmd(f'{CMD_AUTH} {AUTH_PLAIN} {cren}')
            elif AUTH_LOGIN in auths:
                from ubinascii import b2a_base64 as b64
                code, resp = self.cmd(f"{CMD_AUTH} {AUTH_LOGIN} {b64(username)[:-1].decode()}")
                if code != 334:
                    raise Exception(f'Błąd logowania: {code}')
                code, resp = self.cmd(b64(password)[:-1].decode())
            else:
                raise Exception(f"Metoda autentykacji ({', '.join(auths)}) nie jest obsługiwana.")
            
            if code not in [235, 503]:
                raise Exception(f'Błąd autentykacji: {code}')
        except Exception as e:
            print(f"Problem podczas logowania: {e}")
            if hasattr(self, '_sock') and self._sock:
                self._sock.close()  # Zamykanie połączenia w przypadku błędu
            raise

    def to(self, addrs, mail_from=None):
        try:
            mail_from = self.username if mail_from is None else mail_from
            code, resp = self.cmd(CMD_EHLO + ' ' + LOCAL_DOMAIN)
            if code != 250:
                raise Exception(f'Błąd EHLO: {code}')
            code, resp = self.cmd(f'MAIL FROM: <{mail_from}>')
            if code != 250:
                raise Exception(f'Błąd nadawcy: {code}')

            if isinstance(addrs, str):
                addrs = [addrs]
            count = 0
            for addr in addrs:
                code, resp = self.cmd(f'RCPT TO: <{addr}>')
                if code not in [250, 251]:
                    print(f'{addr} odmówiono, {resp}')
                    count += 1
            if count == len(addrs):
                raise Exception(f'Wszyscy odbiorcy odmówili, kod: {code}')

            code, resp = self.cmd('DATA')
            if code != 354:
                raise Exception(f'Błąd przesyłania danych: {code}')
        except Exception as e:
            print(f"Błąd w trakcie wysyłania wiadomości: {e}")
            if hasattr(self, '_sock') and self._sock:
                self._sock.close()  # Zamykanie połączenia w przypadku błędu
            raise

    def write(self, content):
        """Wysyła treść wiadomości"""
        self._sock.write(content)

    def send(self, content=''):
        """Kończy wysyłanie wiadomości"""
        try:
            if content:
                self.write(content)
            self._sock.write('\r\n.\r\n')  # zakończenie wiadomości
            line = self._sock.readline()
            return int(line[:3]), line[4:].strip().decode()
        except Exception as e:
            print(f"Błąd podczas wysyłania wiadomości: {e}")
            if hasattr(self, '_sock') and self._sock:
                self._sock.close()  # Zamykanie połączenia w przypadku błędu
            raise

    def quit(self):
        """Kończy połączenie SMTP"""
        try:
            self.cmd("QUIT")
            self._sock.close()
        except Exception as e:
            print(f"Błąd podczas zamykania połączenia: {e}")
            if hasattr(self, '_sock') and self._sock:
                self._sock.close()  # Zamykanie połączenia w przypadku błędu

