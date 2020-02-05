from telnetM import Telnet

host = "crv025.cro.st.com"
username, password = "wsm", "hobbit0819"

tl = Telnet(terminal_emulation=True)
tl.open_connection(host, alias=None, port=23, timeout=None,
                        newline=None, prompt='>', prompt_is_regexp=False,
                        encoding=None, encoding_errors=None,
                        default_log_level=None, window_size=None,
                        environ_user=None, terminal_emulation=None,
                        terminal_type=None, telnetlib_log_level=None,
                        connection_timeout=None)
tl._conn.login(username, password, login_prompt='Username:',
              password_prompt='Password:')
tl.read_until_prompt()