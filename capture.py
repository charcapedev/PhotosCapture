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
    
    def save_image(self, frame, count):
        """Guarda la imagen con numeración secuencial"""
        filename = os.path.join(
            self.config.config["output_folder"],
            f"capture_{count:06d}.jpg"
        )
        cv2.imwrite(filename, frame)
        print(f"Imagen guardada: {filename}")
    
    def start_capture(self):
        """Inicia el proceso de captura con vista previa - SIN HILOS"""
        if not self.camera.initialize_camera():
            print("No se pudo inicializar la cámara. Saliendo...")
            return False
            
        self.camera.running = True
        capture_count = 0
        target_count = self.config.config["total_captures"]
        capture_interval = self.config.config["capture_interval"]
        capture_mode = self.config.config.get("capture_mode", "auto")  # Modo por defecto: auto
        
        print("\n=== Sistema de Captura ===")
        print(f"Presione 'q' para salir en cualquier momento")
        print(f"Intervalo: {capture_interval}s | Total: {target_count} capturas")
        print("Iniciando captura...")
        
        print("\n=== Sistema de Captura ===")
        if capture_mode == "auto":
            print(f"Modo AUTOMÁTICO - Intervalo: {capture_interval}s")
            print(f"Total: {target_count} capturas | Presione 'q' para salir")
        else:
            print("Modo MANUAL - Presione 'ESPACIO' para capturar")
            print(f"Máximo: {target_count} capturas | 'q' para salir")
        
        last_capture_time = time.time()
    
        try:
            while self.camera.running and capture_count < target_count:
                # Capturar frame
                frame = self.camera.capture_frame()
                if frame is None:
                    continue
                
                # Lógica diferente según el modo
                if capture_mode == "auto":
                    # Modo automático
                    current_time = time.time()
                    if current_time - last_capture_time >= capture_interval:
                        self.save_image(frame, capture_count)
                        capture_count += 1
                        last_capture_time = current_time
                        print(f"Auto: {capture_count}/{target_count}")
                else:
                    # Modo manual - verificar tecla ESPACIO
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord(' '):
                        self.save_image(frame, capture_count)
                        capture_count += 1
                        print(f"Manual: {capture_count}/{target_count}")
                        time.sleep(0.5)  # Evitar múltiples capturas
                
                # Pequeña pausa
                time.sleep(0.1)
            
            print("\n✓ Captura completada")
            return True
            
        except KeyboardInterrupt:
            print("\n✗ Captura detenida por el usuario")
            return False
        except Exception as e:
            print(f"\n✗ Error: {e}")
            return False
        finally:
            self.camera.release_camera()