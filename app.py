
from datetime import datetime
import threading
from camera import CameraConfig
from capture import CaptureSystem



def main():
    try:
        config = CameraConfig()
        system = CaptureSystem(config)
        
        # Ejecutar en hilo separado
        capture_thread = threading.Thread(target=system.start_capture)
        capture_thread.start()
        
        try:
            while capture_thread.is_alive():
                capture_thread.join(0.5)
        except KeyboardInterrupt:
            system.camera.running = False
            capture_thread.join()
        
    except Exception as e:
        print(f"\nError: {str(e)}")
    finally:
        print("Programa terminado")

if __name__ == "__main__":
    main()