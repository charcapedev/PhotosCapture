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
        print(f"Archivos guardados en: {os.path.abspath(self.config.config['output_folder'])}")
    
    def save_image(self, frame, count):
        """Guarda la imagen con numeración secuencial"""
        photo_format = self.config.config.get("photo_format", "jpg")
        filename = os.path.join(
            self.config.config["output_folder"],
            f"capture_{count:06d}.{photo_format}"
        )
        cv2.imwrite(filename, frame)
        print(f"Imagen guardada: {filename}")
    
    def check_keyboard(self):
        """Verifica las teclas presionadas"""
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            print("\nTecla 'Q' presionada - Deteniendo...")
            self.camera.running = False
            return 'quit'
        return key
    
    def start_capture(self):
        """Inicia el proceso de captura según el modo de operación"""
        if not self.camera.initialize_camera():
            print("No se pudo inicializar la cámara. Saliendo...")
            return False
            
        operation_mode = self.config.config.get("operation_mode", "photo")
        
        if operation_mode == "photo":
            return self.start_photo_mode()
        elif operation_mode == "video":
            return self.start_video_mode()
        else:
            print(f"Modo de operación no reconocido: {operation_mode}")
            return False
    
    def start_photo_mode(self):
        """Modo Foto: captura imágenes"""
        print("\n=== MODO FOTO ===")
        
        photo_mode = self.config.config.get("photo_mode", "auto")
        self.camera.running = True
        capture_count = 0
        target_count = self.config.config["total_captures"]
        capture_interval = self.config.config["capture_interval"]
        
        print(f"Submodo: {'AUTOMÁTICO' if photo_mode == 'auto' else 'MANUAL'}")
        
        if photo_mode == "auto":
            print(f"Intervalo: {capture_interval}s | Total: {target_count} fotos")
        else:
            print(f"Total máximo: {target_count} fotos")
        print("Presione 'P' para capturar (manual) | 'Q' para salir")
        print("Iniciando...")
        
        last_capture_time = time.time()
        error_count = 0
        max_errors = 10
        
        try:
            while self.camera.running and capture_count < target_count and error_count < max_errors:
                current_time = time.time()
                
                try:
                    # Verificar teclas
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
                    
                    # Lógica según submodo de foto
                    if photo_mode == "auto":
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
                
                time.sleep(0.01)
            
            # Mensajes finales
            if error_count >= max_errors:
                print("\n✗ Demasiados errores consecutivos. Saliendo...")
            elif capture_count >= target_count:
                print("\n✓ Captura de fotos completada exitosamente")
            else:
                print("\n✗ Captura interrumpida")
                
            return True
            
        except Exception as e:
            print(f"\n✗ Error durante la captura: {e}")
            return False
        finally:
            self.camera.release_camera()
    
    def start_video_mode(self):
        """Modo Video: graba video continuo"""
        print("\n=== MODO VIDEO ===")
        
        # Inicializar video writer
        if not self.camera.initialize_video_writer():
            print("No se pudo inicializar el grabador de video. Saliendo...")
            return False
        
        video_duration = self.config.config.get("video_duration", 30)
        self.camera.running = True
        
        print(f"Duración: {video_duration} segundos")
        print("Presione 'Q' para salir en cualquier momento")
        print("Grabando video...")
        
        start_time = time.time()
        error_count = 0
        max_errors = 10
        
        try:
            while self.camera.running and error_count < max_errors:
                current_time = time.time()
                elapsed_time = current_time - start_time
                
                # Verificar si ha terminado el tiempo
                if elapsed_time >= video_duration:
                    print(f"\n✓ Video completado ({elapsed_time:.1f}s)")
                    break
                
                # Verificar tecla Q para salir
                key = self.check_keyboard()
                if key == 'quit':
                    print(f"\nVideo interrumpido por usuario ({elapsed_time:.1f}s)")
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
                
                # Escribir frame en video
                self.camera.write_video_frame(frame)
                
                # Mostrar progreso
                print(f"Grabando: {int(elapsed_time)}/{video_duration}s", end='\r')
                
                time.sleep(0.01)
            
            if error_count >= max_errors:
                print("\n✗ Demasiados errores consecutivos. Saliendo...")
            else:
                print("\n✓ Grabación de video completada")
                
            return True
            
        except KeyboardInterrupt:
            print("\n✗ Grabación detenida por el usuario")
            return False
        except Exception as e:
            print(f"\n✗ Error durante la grabación: {e}")
            return False
        finally:
            self.camera.release_camera()