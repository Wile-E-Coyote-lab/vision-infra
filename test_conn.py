import socket

def test_socket(host='127.0.0.1', port=5555, timeout=3):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        print(f"SUCCESS: Connected to upstream socket at {host}:{port}")
        return True
    except socket.timeout:
        print(f"TIMEOUT: Connection to {host}:{port} timed out.")
        return False
    except ConnectionRefusedError:
        print(f"REFUSED: Connection to {host}:{port} was refused (is the service or port forward running?).")
        return False
    except Exception as e:
        print(f"ERROR: Failed to connect to {host}:{port}: {e}")
        return False
    finally:
        s.close()

if __name__ == "__main__":
    test_socket()
