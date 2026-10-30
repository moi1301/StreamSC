""" generator.py """

import os
import hashlib

class Generator:
    """
    Genera el archivo addons.xml y addons.xml.md5 en la carpeta exacta del script.
    """
    def __init__(self):
        # OBLIGA al script a usar la carpeta real donde está guardado el archivo .py
        self.output_path = os.path.dirname(os.path.abspath(__file__))
        print(f"Ruta real detectada: {self.output_path}\n")
        self._generate_addons_xml()
        self._generate_md5()

    def _generate_addons_xml(self):
        addons_dirs = os.listdir(self.output_path)
        addons_xml = u"<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n"
        
        for addon in addons_dirs:
            try:
                if not os.path.isdir(os.path.join(self.output_path, addon)) or addon.startswith("."):
                    continue
                
                _path = os.path.join(self.output_path, addon, "addon.xml")
                
                if not os.path.exists(_path):
                    continue
                    
                with open(_path, "r", encoding="utf-8") as f:
                    xml_lines = f.read().splitlines()
                
                for line in xml_lines:
                    if line.strip().startswith("<?xml"):
                        continue
                    addons_xml += line + "\n"
                print(f"-> Add-on procesado correctamente: {addon}")
            except Exception as e:
                print(f"Error crítico procesando {addon}: {e}")
        
        addons_xml += u"</addons>\n"
        
        target_xml = os.path.join(self.output_path, "addons.xml")
        with open(target_xml, "w", encoding="utf-8") as f:
            f.write(addons_xml)
        print(f"¡Guardado correctamente en: {target_xml}")

    def _generate_md5(self):
        try:
            target_xml = os.path.join(self.output_path, "addons.xml")
            target_md5 = os.path.join(self.output_path, "addons.xml.md5")
            
            with open(target_xml, "rb") as f:
                data = f.read()
            md5_hash = hashlib.md5(data).hexdigest()
            
            with open(target_md5, "w", encoding="utf-8") as f:
                f.write(md5_hash)
            print(f"¡Guardado correctamente en: {target_md5}")
        except Exception as e:
            print(f"Error generando MD5: {e}")

if __name__ == "__main__":
    Generator()
