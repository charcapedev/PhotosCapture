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
    
    def check_keyboard(self):
        """Verifica las teclas presionadas en ambos modos"""
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print("\nTecla 'Q' presionada - Deteniendo captura...")
            self.camera.running = False
            return 'quit'
        return key
    
    def start_capture(self):
        """Inicia el proceso de captura con vista previa"""
        if not self.camera.initialize_camera():
            print("No se pudo inicializar la cámara. Saliendo...")
            return False
            
        self.camera.running = True
        capture_count = 0
        target_count = self.config.config["total_captures"]
        capture_interval = self.config.config["capture_interval"]
        capture_mode = self.config.config.get("capture_mode", "auto")
        
        print("\n=== Sistema de Captura ===")
        print(f"Modo: {'AUTOMÁTICO' if capture_mode == 'auto' else 'MANUAL'}")
        
        if capture_mode == "auto":
            print(f"Intervalo: {capture_interval}s | Total: {target_count} capturas")
        print("Presione 'P' para capturar (manual) | 'Q' para salir")
        print("Iniciando captura...")
        
        last_capture_time = time.time()
        error_count = 0
        max_errors = 10
        
        try:
            while self.camera.running and capture_count < target_count and error_count < max_errors:
                current_time = time.time()
                
                try:
                    # Verificar teclas (esto se ejecuta en AMBOS modos)
                    key = self.check_keyboard()
                    if key == 'quit':
                        break
                    
                    # Capturar frame
                    frame = self.camera.capture_frame()
                    
                    if frame is None:
                        error_count += 1
                        print(f"Error en captura ({error_count}/{max_errors}). Reintentando...")
                        time.sleep(1)
                        continue
                    else:
                        error_count = 0
                    
                    # Lógica según el modo
                    if capture_mode == "auto":
                        # Modo automático - captura por intervalo
                        if current_time - last_capture_time >= capture_interval:
                            self.save_image(frame, capture_count)
                            capture_count += 1
                            last_capture_time = current_time
                            print(f"Auto: {capture_count}/{target_count}")
                    
                    else:
                        # Modo manual - captura con tecla P
                        if key == ord('p') or key == ord('P'):
                            self.save_image(frame, capture_count)
                            capture_count += 1
                            print(f"Manual: {capture_count}/{target_count}")
                            time.sleep(0.3)  # Anti-rebote
                
                except KeyboardInterrupt:
                    print("\n✗ Captura detenida por el usuario (Ctrl+C)")
                    self.camera.running = False
                    break
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error inesperado ({error_count}/{max_errors}): {e}")
                    time.sleep(1)
                
                # Pequeña pausa
                time.sleep(0.01)  # Reducido para mejor respuesta a teclas
            
            # Mensajes finales
            if error_count >= max_errors:
                print("\n✗ Demasiados errores consecutivos. Saliendo...")
            elif capture_count >= target_count:
                print("\n✓ Captura completada exitosamente")
            else:
                print("\n✗ Captura interrumpida")
                
            return True
            
        except KeyboardInterrupt:
            print("\n✗ Captura detenida por el usuario")
            return False
        except Exception as e:
            print(f"\n✗ Error durante la captura: {e}")
            return False
        finally:
            self.camera.release_camera()