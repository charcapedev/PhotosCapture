import cv2
import time
import os
from datetime import datetime
from camera import CameraController


class CaptureSystem:
    def __init__(self, config):
        self.config = config
        self.camera = CameraController(config)
        self.create_output_folder()
        
    def create_output_folder(self):
        """Crea la carpeta de salida"""
        os.makedirs(self.config.config["output_folder"], exist_ok=True)
        print(f"Capturas guardadas en: {os.path.abspath(self.config.config['output_folder'])}")
    
    def save_image(self, frame):
        """Guarda la imagen con timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = os.path.join(
            self.config.config["output_folder"],
            f"capture_{timestamp}.jpg"
        )
        cv2.imwrite(filename, frame)
        print(f"Imagen guardada: {filename}")
    
    def start_capture(self):
        """Inicia el proceso de captura con vista previa"""
        if not self.camera.initialize_camera():
            return False
            
        self.camera.running = True
        start_time = time.time()
        end_time = start_time + self.config.config["total_capture_time"]
        last_capture = 0
        
        print("\n=== Sistema de Captura ===")
        print(f"Mostrando vista previa... Presione 'q' para salir")
        print(f"Intervalo: {self.config.config['capture_interval']}s | Duración: {self.config.config['total_capture_time']}s")
        
        try:
            while self.camera.running and time.time() < end_time:
                current_time = time.time()
                
                # Capturar y mostrar vista previa continuamente
                try:
                    frame = self.camera.capture_frame()
                    
                    # Guardar solo cuando haya pasado el intervalo
                    if current_time - last_capture >= self.config.config["capture_interval"]:
                        self.save_image(frame)
                        last_capture = current_time
                except Exception as e:
                    print(f"Error en captura: {str(e)}")
                    time.sleep(1)
                
                # Pequeña pausa para no saturar la CPU
                time.sleep(0.01)
            
            print("\nCaptura completada")
            return True
        except KeyboardInterrupt:
            print("\nCaptura detenida por el usuario")
            return False
        finally:
            self.camera.release_camera()