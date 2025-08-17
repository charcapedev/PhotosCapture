import cv2
import json
import os

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
        self.running = False
        self.window_name = "Vista Previa - Presione 'q' para salir"
        
    def initialize_camera(self):
        """Inicializa la cámara con vista previa"""
        try:
            if self.config.config["camera_type"] == "ip":
                self.cap = cv2.VideoCapture(self.config.config["ip_camera_url"], cv2.CAP_FFMPEG)
            else:
                self.cap = cv2.VideoCapture(self.config.config["camera_index"])
                
                # Configuración de propiedades para cámaras USB/built-in
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.config["resolution"]["width"])
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.config["resolution"]["height"])
                    self.cap.set(cv2.CAP_PROP_AUTOFOCUS, int(self.config.config["autofocus"]))
                    self.cap.set(cv2.CAP_PROP_AUTO_WB, int(self.config.config["auto_white_balance"]))
            
            if not self.cap.isOpened():
                raise ConnectionError("No se pudo abrir la cámara")
                
            # Crear ventana de vista previa
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            if self.config.config["resolution"]:
                cv2.resizeWindow(self.window_name, 
                                self.config.config["resolution"]["width"], 
                                self.config.config["resolution"]["height"])
            
            return True
        except Exception as e:
            print(f"Error al inicializar cámara: {str(e)}")
            return False
    
    def show_preview(self, frame):
        """Muestra el frame en una ventana"""
        cv2.imshow(self.window_name, frame)
        # Salir si se presiona 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.running = False
    
    def capture_frame(self):
        """Captura y muestra un frame"""
        ret, frame = self.cap.read()
        if not ret:
            raise ConnectionError("Error al capturar frame")
            
        # Aplicar zoom si está configurado
        if self.config.config["zoom"] != 1.0:
            h, w = frame.shape[:2]
            center_x, center_y = w//2, h//2
            radius_x = int(w/(2*self.config.config["zoom"]))
            radius_y = int(h/(2*self.config.config["zoom"]))
            frame = frame[center_y-radius_y:center_y+radius_y, center_x-radius_x:center_x+radius_x]
            frame = cv2.resize(frame, (w, h))
            
        # Aplicar volteos
        if self.config.config["flip_horizontal"] or self.config.config["flip_vertical"]:
            flip_code = 1 if self.config.config["flip_horizontal"] else 0
            if self.config.config["flip_vertical"]:
                flip_code = -1 if self.config.config["flip_horizontal"] else 0
            frame = cv2.flip(frame, flip_code)
        
        # Mostrar vista previa
        self.show_preview(frame)
        return frame
    
    def release_camera(self):
        """Libera los recursos"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        self.running = False