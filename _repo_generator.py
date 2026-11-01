import os
import xml.etree.ElementTree as ET
import zipfile
import hashlib

# --- CONFIGURACIÓN ---
# Carpeta donde tienes tus addons en desarrollo (cada uno en su subcarpeta con su addon.xml)
CARPETA_DESARROLLOS = "mis_desarrollos"
# Carpeta destino que se subirá al servidor web / GitHub (el repositorio final)
CARPETA_REPO_FINAL = "repo_kodi"


def calcular_md5_texto(texto):
    """Calcula el hash MD5 de una cadena de texto."""
    return hashlib.md5(texto.encode('utf-8')).hexdigest()


def calcular_md5_archivo(ruta_archivo):
    """Calcula el hash MD5 de un archivo binario (como un ZIP)."""
    hash_md5 = hashlib.md5()
    with open(ruta_archivo, "rb") as f:
        for trozo in iter(lambda: f.read(4096), b""):
            hash_md5.update(trozo)
    return hash_md5.hexdigest()


def procesar_repositorio():
    # Asegurar que las carpetas de trabajo existen
    if not os.path.exists(CARPETA_DESARROLLOS):
        os.makedirs(CARPETA_DESARROLLOS)
        print(f"📁 Se ha creado la carpeta '{CARPETA_DESARROLLOS}'. Coloca ahí las carpetas de tus addons.")
        return

    if not os.path.exists(CARPETA_REPO_FINAL):
        os.makedirs(CARPETA_REPO_FINAL)

    # Nodo raíz para el archivo maestro addons.xml
    raiz_addons_xml = ET.Element("addons")
    addons_procesados = 0

    print("🚀 Iniciando procesamiento de addons...")

    # Recorrer cada carpeta de addon en la zona de desarrollo
    for nombre_carpeta in os.listdir(CARPETA_DESARROLLOS):
        ruta_addon = os.path.join(CARPETA_DESARROLLOS, nombre_carpeta)
        
        if not os.path.isdir(ruta_addon):
            continue
            
        archivo_addon_xml = os.path.join(ruta_addon, "addon.xml")
        if not os.path.exists(archivo_addon_xml):
            print(f"⚠️ Saltando '{nombre_carpeta}': No contiene un archivo 'addon.xml'.")
            continue

        try:
            # 1. Leer y validar el archivo addon.xml del complemento
            arbol = ET.parse(archivo_addon_xml)
            raiz = arbol.getroot()
            
            addon_id = raiz.get("id")
            version = raiz.get("version")

            if not addon_id or not version:
                print(f"❌ Error en {nombre_carpeta}: 'id' o 'version' faltantes en addon.xml.")
                continue

            print(f"📦 Procesando: {addon_id} (v{version})")

            # Añadir el contenido de este addon al XML maestro
            raiz_addons_xml.append(raiz)

            # 2. Crear la estructura en la carpeta del repositorio final
            ruta_destino_addon = os.path.join(CARPETA_REPO_FINAL, addon_id)
            if not os.path.exists(ruta_destino_addon):
                os.makedirs(ruta_destino_addon)

            # 3. Crear el archivo ZIP empaquetado
            nombre_zip = f"{addon_id}-{version}.zip"
            ruta_zip_final = os.path.join(ruta_destino_addon, nombre_zip)

            with zipfile.ZipFile(ruta_zip_final, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for raiz_dir, _, archivos in os.walk(ruta_addon):
                    for archivo in archivos:
                        ruta_completa = os.path.join(raiz_dir, archivo)
                        # Mantener la estructura relativa interna para el ZIP
                        ruta_relativa = os.path.relpath(ruta_completa, os.path.dirname(ruta_addon))
                        zipf.write(ruta_completa, ruta_relativa)

            # 4. Generar el MD5 del archivo ZIP creado
            md5_zip = calcular_md5_archivo(ruta_zip_final)
            with open(f"{ruta_zip_final}.md5", "w") as f_md5:
                f_md5.write(md5_zip)

            # 5. Copiar iconos y fanarts a la carpeta destino si existen para que Kodi los previsualice
            for recurso in ["icon.png", "fanart.jpg", "changelog.txt"]:
                ruta_recurso = os.path.join(ruta_addon, recurso)
                if os.path.exists(ruta_recurso):
                    with open(ruta_recurso, "rb") as f_orig, open(os.path.join(ruta_destino_addon, recurso), "wb") as f_dest:
                        f_dest.write(f_orig.read())

            addons_procesados += 1

        except Exception as e:
            print(f"❌ Error procesando el addon {nombre_carpeta}: {e}")

    if addons_procesados > 0:
        # 6. Guardar el archivo maestro addons.xml finalizado
        ruta_maestra_xml = os.path.join(CARPETA_REPO_FINAL, "addons.xml")
        xml_string = ET.tostring(raiz_addons_xml, encoding="utf-8", method="xml")
        
        # Darle formato limpio con la cabecera XML estándar
        xml_final = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml_string
        with open(ruta_maestra_xml, "wb") as f:
            f.write(xml_final)

        # 7. Generar el archivo maestro addons.xml.md5
        md5_maestro = calcular_md5_texto(xml_final.decode('utf-8'))
        ruta_maestra_md5 = os.path.join(CARPETA_REPO_FINAL, "addons.xml.md5")
        with open(ruta_maestra_md5, "w") as f:
            f.write(md5_maestro)

        print(f"\n✅ ¡Éxito! Se han procesado {addons_procesados} addons correctamente.")
        print(f"📂 Todo el contenido listo en la carpeta: '{CARPETA_REPO_FINAL}'")
    else:
        print("\n📭 No se procesó ningún addon. Asegúrate de añadir carpetas válidas en la carpeta de desarrollos.")


if __name__ == "__main__":
    procesar_repositorio()
