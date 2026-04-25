from cryptography.fernet import Fernet

# Generate key once (in real system, persist it)
key = Fernet.generate_key()
cipher = Fernet(key)

def encrypt(data):
    return cipher.encrypt(data)

def decrypt(data):
    return cipher.decrypt(data)

def split_file(file_path, chunk_size=1024 * 1024):
    chunks = []
    with open(file_path, 'rb') as f:
        i = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            chunks.append((i, data))
            i += 1
    return chunks