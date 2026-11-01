import os
import sys
import urllib.parse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

class StreamEventosAddon:
    APP_KEY = 'fw5okulvmua7sry'  
    APP_SECRET = 'wdgq8sppgska5bo'  
    REFRESH_TOKEN = 'AQtfE4oLEFsAAAAAAAAAARTeuAXMFUVYXbfrPz8-16RRT0na6HQl-bHK2Wv4C2io'  
    PATH_DROPBOX = "/Aplicaciones/StreamSC/archivo.txt"  

    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.handle_id = int(sys.argv[1])
        self.base_url = sys.argv[0]  # ¡Esto ya es "plugin://plugin.video.tuid/" automáticamente!
        self.params = dict(urllib.parse.parse_qsl(sys.argv[2].lstrip('?')))
        
        self.addon_dir = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))
        self.profile_dir = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
        self.path_local_txt = os.path.join(self.profile_dir, 'eventos.txt')
        
        self._inicializar_entorno()
        import dropbox
        self.dropbox_lib = dropbox

    def _inicializar_entorno(self):
        lib_dir = os.path.join(self.addon_dir, 'resources', 'lib')
        if lib_dir not in sys.path:
            sys.path.append(lib_dir)
        if not os.path.exists(self.profile_dir):
            os.makedirs(self.profile_dir)

    def descargar_txt_dropbox(self):
        try:
            xbmc.log("[StreamEventos] Iniciando descarga desde Dropbox...", xbmc.LOGINFO)
            dbx = self.dropbox_lib.Dropbox(
                app_key=self.APP_KEY,
                app_secret=self.APP_SECRET,
                oauth2_refresh_token=self.REFRESH_TOKEN
            )
            _, res = dbx.files_download(self.PATH_DROPBOX)
            with open(self.path_local_txt, 'wb') as f:
                f.write(res.content)
            xbmc.log("[StreamEventos] Archivo descargado exitosamente.", xbmc.LOGINFO)
            return True
        except Exception as err:
            xbmc.log(f"[StreamEventos] Error al descargar de Dropbox: {str(err)}", xbmc.LOGERROR)
            return False

    def comprobar_y_cargar_eventos(self):
        """Genera el menú principal listando los eventos disponibles."""
        if not os.path.exists(self.path_local_txt):
            self.descargar_txt_dropbox()

        if not os.path.exists(self.path_local_txt):
            xbmcgui.Dialog().ok("Error", "El archivo de eventos no existe localmente.")
            xbmcplugin.endOfDirectory(self.handle_id, succeeded=False)
            return

        try:
            with open(self.path_local_txt, 'r', encoding='utf-8') as archivo:
                contenido = archivo.read()

            # Botón de actualización
            item_update = xbmcgui.ListItem(label="[COLOR green]🔄 Actualizar lista desde Dropbox[/COLOR]")
            url_update = f"{self.base_url}?action=force_update"
            xbmcplugin.addDirectoryItem(self.handle_id, url_update, item_update, isFolder=False)

            hora_actual = "Sin Hora"
            categoria_actual = "General"

            for linea in contenido.splitlines():
                linea = linea.strip()
                
                if linea.startswith("Hora:"):
                    hora_actual = linea.replace("Hora:", "").strip()
                elif linea.startswith("Categoría:"):
                    categoria_actual = linea.replace("Categoría:", "").strip()
                elif linea.startswith("Evento:"):
                    evento_actual = linea.replace("Evento:", "").strip()
                    
                    color = "blue" if "Real Madrid" in evento_actual or "Granada" in evento_actual else "white"
                    
                    etiqueta = f"[COLOR {color}][{hora_actual}][{categoria_actual}] {evento_actual}[/COLOR]"
                    item_canal = xbmcgui.ListItem(label=etiqueta)
                    
                    # CORRECCIÓN: Usamos setInfo correctamente
                    item_canal.setInfo('video', {'title': evento_actual, 'plot': etiqueta})
                    
                    # CORRECCIÓN: Enviamos el nombre del evento a la acción para saber cuál abrir al pinchar
                    evento_codificado = urllib.parse.quote_plus(evento_actual)
                    url_carpeta_evento = f"{self.base_url}?action=ver_evento&nombre={evento_codificado}"
                    
                    # isFolder=True le dice a Kodi que actúe como una carpeta
                    xbmcplugin.addDirectoryItem(self.handle_id, url_carpeta_evento, item_canal, isFolder=True)
            
            xbmcplugin.setContent(self.handle_id, 'videos')
            xbmcplugin.endOfDirectory(self.handle_id, succeeded=True)

        except Exception as e:
            xbmc.log(f"[StreamEventos] Error procesando archivo: {str(e)}", xbmc.LOGERROR)
            xbmcplugin.endOfDirectory(self.handle_id, succeeded=False)

    def cargar_enlaces_evento(self, nombre_evento):
        """Esta función se ejecuta al pinchar sobre un evento y muestra sus enlaces internos."""
        try:
            with open(self.path_local_txt, 'r', encoding='utf-8') as archivo:
                contenido = archivo.read()

            dentro_del_evento = False
            enlaces_encontrados = False

            for linea in contenido.splitlines():
                linea = linea.strip()

                if linea.startswith("Evento:"):
                    evento_actual = linea.replace("Evento:", "").strip()
                    # Si coincide con el evento que pinchamos, activamos la lectura
                    if evento_actual == nombre_evento:
                        dentro_del_evento = True
                    else:
                        dentro_del_evento = False
                    continue  # Saltamos a la siguiente línea del bucle de inmediato

                # Si estamos dentro del alcance del evento objetivo y es una línea de enlace
                if dentro_del_evento and linea.startswith("-"):
                    partes = linea.split(":")           
                    if len(partes) >= 3:
                        # CORRECCIÓN: Quitamos el guión directamente de la cadena str antes del split o del elemento indexado
                        nombre_enlace = partes[0].replace("-", "").strip()
                        # Unimos el resto por si el hash contiene caracteres especiales
                        hash_acestream = ":".join(partes[2:]).strip().lstrip('/')
                        
                        etiqueta_visual = f"[COLOR lightblue]▶ {nombre_enlace}[/COLOR]"
                        item_enlace = xbmcgui.ListItem(label=etiqueta_visual)
                        
                        item_enlace.setInfo('video', {
                            'title': nombre_enlace,
                            'plot': f'Reproducir enlace de {nombre_evento}'
                        })
                        
                        # URL dirigida a tu plugin de Horus
                        url_reproduccion = f"plugin://script.module.horus?action=play&id={hash_acestream}"
                        xbmcplugin.addDirectoryItem(self.handle_id, url_reproduccion, item_enlace, isFolder=False)
                        enlaces_encontrados = True
                
                # Si estamos dentro del evento pero la línea cambia de sección sin tener un "-", cerramos el bloque
                elif dentro_del_evento and (linea.startswith("Hora:") or linea.startswith("Categoría:")):
                    dentro_del_evento = False

            if not enlaces_encontrados:
                item_vacio = xbmcgui.ListItem(label="[COLOR red]No hay enlaces disponibles para este evento[/COLOR]")
                xbmcplugin.addDirectoryItem(self.handle_id, "", item_vacio, isFolder=False)

            xbmcplugin.setContent(self.handle_id, 'videos')
            xbmcplugin.endOfDirectory(self.handle_id, succeeded=True)

        except Exception as e:
            xbmc.log(f"[StreamEventos] Error cargando enlaces: {str(e)}", xbmc.LOGERROR)
            xbmcplugin.endOfDirectory(self.handle_id, succeeded=False)

    def ejecutar(self):
        """Enrutador de acciones principal."""
        action = self.params.get('action')

        if not action:
            # Menú principal (Lista de eventos)
            self.comprobar_y_cargar_eventos()
            
        elif action == 'force_update':
            if self.descargar_txt_dropbox():
                xbmcgui.Dialog().notification("Dropbox", "Lista de eventos actualizada", xbmcgui.NOTIFICATION_INFO, 3000)
                xbmc.executebuiltin("Container.Refresh")
                
        elif action == 'ver_evento':
            # NUEVO: Captura el clic del evento y carga sus respectivos enlaces
            nombre_evento = urllib.parse.unquote_plus(self.params.get('nombre', ''))
            self.cargar_enlaces_evento(nombre_evento)

if __name__ == "__main__":
    addon = StreamEventosAddon()
    addon.ejecutar()
