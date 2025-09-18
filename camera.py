import cv2
import json
import os
import time
from datetime import datetime

class CameraConfig:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.load_config()
        
    def load_config(self):
        """Carga la configuración desde el archivo JSON"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Archivo de configuración {self.config_file} no encontrado")

class CameraController:
    def __init__(self, config):
        self.config = config
        self.cap = None
        self.video_writer = None  # Para modo video
        self.running = False
        self.window_name = "Vista Previa - Presione 'q' para salir"
        
    def initialize_camera(self):
        """Inicializa la cámara con vista previa"""
        try:
            print("Inicializando cámara...")
            
            if self.config.config["camera_type"] == "ip":
                self.cap = cv2.VideoCapture(self.config.config["ip_camera_url"], cv2.CAP_FFMPEG)
                time.sleep(2)
            else:
                self.cap = cv2.VideoCapture(self.config.config["camera_index"], cv2.CAP_DSHOW)
            
            if not self.cap.isOpened():
                print("Primer intento fallido, probando método alternativo...")
                self.cap = cv2.VideoCapture(self.config.config["camera_index"], cv2.CAP_ANY)
                time.sleep(1)
                
            if not self.cap.isOpened():
                raise ConnectionError("No se pudo abrir la cámara después de 2 intentos")
            
            # Configurar propiedades de la cámara
            if self.config.config["camera_type"] == "usb":
                amcap_properties = [
                    (cv2.CAP_PROP_BRIGHTNESS, "brightness", 0),
                    (cv2.CAP_PROP_CONTRAST, "contrast", 2),
                    (cv2.CAP_PROP_SATURATION, "saturation", 48),
                    (cv2.CAP_PROP_GAIN, "gain", 32),
                    (cv2.CAP_PROP_EXPOSURE, "exposure", 0),
                    (cv2.CAP_PROP_HUE, "hue", 0),
                    (cv2.CAP_PROP_SHARPNESS, "sharpness", 0),
                    (cv2.CAP_PROP_GAMMA, "gamma", 100),
                ]
                
                print("Configurando parámetros de cámara...")
                for prop_code, prop_name, default_value in amcap_properties:
                    try:
                        value = self.config.config.get(prop_name, default_value)
                        success = self.cap.set(prop_code, value)
                        if success:
                            actual_value = self.cap.get(prop_code)
                            print(f"✓ {prop_name}: {value} (ajustado a: {actual_value:.1f})")
                        else:
                            print(f"⚠ {prop_name}: No soportado por esta cámara")
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"⚠ Error configurando {prop_name}: {e}")
            
            # Configurar resolución
            try:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.config["resolution"]["width"])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.config["resolution"]["height"])
                time.sleep(0.2)
            except:
                print("⚠ No se pudo configurar resolución, usando valor por defecto")
            
            # Crear ventana de vista previa
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, 800, 600)
            
            # Probar captura final
            ret, frame = self.cap.read()
            if not ret:
                raise ConnectionError("Cámara abierta pero no puede capturar frames")
                
            print("✓ Cámara inicializada correctamente")
            return True
            
        except Exception as e:
            print(f"Error al inicializar cámara: {str(e)}")
            if self.cap:
                self.cap.release()
            return False
        
    def initialize_video_writer(self):
        """Inicializa el escritor de video para modo video"""
        try:
            # Obtener codec y formato
            video_format = self.config.config.get("video_format", "avi")
            fourcc_dict = {
                "avi": cv2.VideoWriter_fourcc(*'XVID'),
                "mp4": cv2.VideoWriter_fourcc(*'mp4v'),
                "mov": cv2.VideoWriter_fourcc(*'XVID')
            }
            fourcc = fourcc_dict.get(video_format, cv2.VideoWriter_fourcc(*'XVID'))
            
            # Obtener FPS (cuadros por segundo)
            fps = 30.0
            
            # Obtener resolución
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Crear nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(
                self.config.config["output_folder"],
                f"video_{timestamp}.{video_format}"
            )
            
            # Crear el escritor de video
            self.video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height))
            
            if not self.video_writer.isOpened():
                print("⚠ No se pudo inicializar el escritor de video")
                return False
            
            print(f"✓ Video writer inicializado: {filename}")
            return True
            
        except Exception as e:
            print(f"Error inicializando video writer: {e}")
            return False
        
    def write_video_frame(self, frame):
        """Escribe un frame en el video (modo video)"""
        if self.video_writer and self.video_writer.isOpened():
            self.video_writer.write(frame)
        
    def show_preview(self, frame):
        """Muestra el frame en una ventana"""
        cv2.imshow(self.window_name, frame)
        # Salir si se presiona 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.running = False
    
    def capture_frame(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                print("Error capturando frame, reintentando...")
                ret, frame = self.cap.read()
                if not ret:
                    raise ConnectionError("No se pudo capturar frame después de reintento")
            
            # Aplicar volteos si están configurados
            flip_horizontal = self.config.config.get("flip_horizontal", False)
            flip_vertical = self.config.config.get("flip_vertical", False)
            
            if flip_horizontal or flip_vertical:
                flip_code = 1 if flip_horizontal else 0
                if flip_vertical:
                    flip_code = -1 if flip_horizontal else 1
                frame = cv2.flip(frame, flip_code)
            
            # Mostrar vista previa
            self.show_preview(frame)
            return frame
            
        except Exception as e:
            print(f"Error en captura: {e}")
            return None

    
    def release_camera(self):
        """Libera los recursos"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        # Liberar video writer si existe
        if self.video_writer and self.video_writer.isOpened():
            self.video_writer.release()
            print("✓ Video writer liberado")
        
        cv2.destroyAllWindows()
        self.running = False