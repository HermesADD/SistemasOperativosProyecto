import os

print("Saturando disco I/O...")
print("Presiona Ctrl+C para detener")

try:
    while True:
        with open('test_write.tmp', 'wb') as f:
            f.write(os.urandom(100 * 1024 * 1024))
        
        # Leer 100MB
        with open('test_write.tmp', 'rb') as f:
            data = f.read()
        
        print(".", end="", flush=True)
        
except KeyboardInterrupt:
    if os.path.exists('test_write.tmp'):
        os.remove('test_write.tmp')