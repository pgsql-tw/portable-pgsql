��    \      �     �      �     �  8   �  D   )  8   n  4   �  >   �  <   	  I   X	  9   �	  ?   �	  6   
     S
  /   s
  /   �
  1   �
       3     ,   M  !   z  $   �  $   �     �  $     .   )  &   X  '         �  	   �  $   �  j   �  _   b     �  &   �  d      8   e  3   �  #   �  "   �  #        =  $   [  /   �     �     �  "   �          ,  !   G     i  #   �     �     �     �  (   �     "  )   ?  ,   i     �     �     �     �  4   �  6        G  $   c     �      �     �     �                )     ;     H     Z     k     �     �  /   �     �     �          *     @     \     r     �     �  %   �     �  	   �  �       �  >   �  R     D   i  7   �  K   �  @   2  K   s  R   �  R     J   e  "   �  8   �  8     :   E     �  [   �  4   �  ,   (  /   U  /   �  '   �  /   �  >     6   L  4   �  ,   �  
   �  .   �  v     p   �  !     .   )  �   X  O   �  A   *  "   l  ,   �  &   �  ,   �  L      5   ]   9   �   #   �   )   �   '   !  ,   C!  )   p!  &   �!  >   �!  )    "  '   *"  %   R"  4   x"  +   �"  8   �"  H   #     [#     c#  !   #     �#  S   �#  B   �#  .   @$  ;   o$  4   �$  )   �$  7   
%  &   B%  ,   i%     �%     �%     �%     �%     �%  -   &     0&  #   A&  E   e&      �&     �&     �&     �&  !   '     ='     V'     q'     �'  6   �'  %   �'     �'            W           @   '          Q   D      G   1                             U   8       P                  =   B   X   0   :   V       -          C           ;   E   >                    <      .   A   Z       \   )       %   $   N         K   [       &   S         O   6   T      /       F   M   4   "      5                     ?               Y              (   3          R   H   +   !                  7   9   	   ,       2   I   J   L   *                  #   
       
Report bugs to <%s>.
   -?, --help                  show this help, then exit
   -V, --version               output version information, then exit
   -e, --exit-on-error         exit immediately on error
   -i, --ignore=RELATIVE_PATH  ignore indicated path
   -m, --manifest-path=PATH    use specified path for manifest
   -n, --no-parse-wal          do not try to parse WAL files
   -q, --quiet                 do not print any output, except for errors
   -s, --skip-checksums        skip checksum verification
   -w, --wal-directory=PATH    use specified path for WAL files
 "%s" has size %zu on disk but size %zu in the manifest "%s" is not a file or directory "%s" is present in the manifest but not on disk "%s" is present on disk but not in the manifest "\u" must be followed by four hexadecimal digits. %s home page: <%s>
 %s verifies a backup against the backup manifest.

 Character with value 0x%02x must be escaped. Escape sequence "\%s" is invalid. Expected "," or "]", but found "%s". Expected "," or "}", but found "%s". Expected ":", but found "%s". Expected JSON value, but found "%s". Expected array element or "]", but found "%s". Expected end of input, but found "%s". Expected string or "}", but found "%s". Expected string, but found "%s". Options:
 The input string ended unexpectedly. The program "%s" is needed by %s but was not found in the
same directory as "%s".
Check your installation. The program "%s" was found by "%s"
but was not the same version as %s.
Check your installation. Token "%s" is invalid. Try "%s --help" for more information.
 Unicode escape values cannot be used for code point values above 007F when the encoding is not UTF8. Unicode high surrogate must not follow a high surrogate. Unicode low surrogate must follow a high surrogate. Usage:
  %s [OPTION]... BACKUPDIR

 WAL parsing failed for timeline %u \u0000 cannot be converted to text. backup successfully verified
 both path name and encoded path name cannot duplicate null pointer (internal error)
 checksum mismatch for file "%s" checksum without algorithm could not close directory "%s": %m could not close file "%s": %m could not decode file name could not open directory "%s": %m could not open file "%s": %m could not parse backup manifest: %s could not parse end LSN could not parse start LSN could not read file "%s": %m could not read file "%s": read %d of %zu could not stat file "%s": %m could not stat file or directory "%s": %m duplicate path name in backup manifest: "%s" error:  expected at least 2 lines expected version indicator fatal:  file "%s" has checksum of length %d, but expected %d file "%s" should contain %zu bytes, but read %zu bytes file size is not an integer invalid checksum for file "%s": "%s" invalid manifest checksum: "%s" last line not newline-terminated manifest checksum mismatch manifest ended unexpectedly manifest has no checksum missing end LSN missing path name missing size missing start LSN missing timeline no backup directory specified out of memory
 timeline is not an integer too many command-line arguments (first is "%s") unexpected WAL range field unexpected array end unexpected array start unexpected file field unexpected manifest version unexpected object end unexpected object field unexpected object start unexpected scalar unrecognized checksum algorithm: "%s" unrecognized top-level field warning:  Project-Id-Version: pg_verifybackup (PostgreSQL) 13
Report-Msgid-Bugs-To: pgsql-bugs@lists.postgresql.org
PO-Revision-Date: 2020-09-18 18:21-0300
Last-Translator: Álvaro Herrera <alvherre@alvh.no-ip.org>
Language-Team: PgSQL-es-ayuda <pgsql-es-ayuda@lists.postgresql.org>
Language: es
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=(n != 1);
X-Generator: Poedit 2.3
 
Reporte errores a <%s>.
   -?, --help                  muestra esta ayuda, luego salir
   -V, --version               mostrar la información de la versión, luego salir
   -e, --exit-on-error         salir inmediatamente en caso de error
   -i, --ignore=RELATIVE_PATH  ignorar la ruta indicada
   -m, --manifest-path=PATH    usar la ruta especificada para el manifiesto
   -n, --no-parse-wal          no intentar analizar archivos WAL
   -q, --quiet                 no escribir ningún mensaje, excepto errores
   -s, --skip-checksums        omitir la verificación de la suma de comprobación
   -w, --wal-directory=PATH    utilizar la ruta especificada para los archivos WAL
 "%s" tiene un tamaño %zu en el disco pero un tamaño %zu en el manifiesto "%s" no es un archivo o directorio "%s" está presente en el manifiesto pero no en el disco "%s" está presente en el disco pero no en el manifiesto «\u» debe ser seguido por cuatro dígitos hexadecimales. Sitio web de %s: <%s>
 %s verifica una copia de seguridad con el fichero de manifiesto de la copia de seguridad.

 Los caracteres con valor 0x%02x deben ser escapados. La secuencia de escape «%s» no es válida. Se esperaba «,» o «]», se encontró «%s». Se esperaba «,» o «}», se encontró «%s». Se esperaba «:», se encontró «%s». Se esperaba un valor JSON, se encontró «%s». Se esperaba un elemento de array o «]», se encontró «%s». Se esperaba el fin de la entrada, se encontró «%s». Se esperaba una cadena o «}», se encontró «%s». Se esperaba una cadena, se encontró «%s». Opciones:
 La cadena de entrada terminó inesperadamente. %s necesita el programa «%s», pero no pudo encontrarlo en el mismo
directorio que «%s».
Verifique su instalación. El programa «%s» fue encontrado por «%s»,
pero no es de la misma versión que %s.
Verifique su instalación. El elemento «%s» no es válido. Pruebe «%s --help» para mayor información.
 Los valores de escape Unicode no se pueden utilizar para valores de código superiores a 007F cuando la codificación no es UTF8. Un «high-surrogate» Unicode no puede venir después de un «high-surrogate». Un «low-surrogate» Unicode debe seguir a un «high-surrogate». Uso:
  %s [OPCIÓN]... BACKUPDIR

 Error al analizar el WAL para el timeline %u \u0000 no puede ser convertido a text. copia de seguridad verificada correctamente
 hay tanto ruta de archivo (pathname) como ruta codificada (encoded pathname) no se puede duplicar un puntero nulo (error interno)
 no coincide la suma de comprobación para el archivo "%s" suma de comprobación sin algoritmo no se pudo abrir el directorio «%s»: %m no se pudo cerrar el archivo «%s»: %m no se pudo decodificar el nombre del archivo no se pudo abrir el directorio «%s»: %m no se pudo abrir el archivo «%s»: %m no se pudo analizar el manifiesto de la copia de seguridad: %s no se pudo interpretar el LSN de término no se pudo interpretar el LSN de inicio no se pudo leer el archivo «%s»: %m no se pudo leer el archivo «%s»: leídos %d de %zu no se pudo hacer stat al archivo «%s»: %m no se pudo hacer stat al archivo o directorio «%s»: %m nombre de ruta duplicado en el manifiesto de la copia de seguridad: "%s" error:  esperado al menos 2 líneas se esperaba indicador de versión fatal:  el archivo "%s" tiene una suma de comprobación de longitud %d, pero se esperaba %d el archivo "%s" debe contener %zu bytes, pero se leyeron %zu bytes el tamaño del archivo no es un número entero suma de comprobación no válida para el archivo "%s": "%s" suma de comprobación de manifiesto no válida: "%s" última línea no termina en nueva línea discordancia en la suma de comprobación del manifiesto el manifiesto terminó inesperadamente el manifiesto no tiene suma de comprobación falta el LSN de término ruta de archivo faltante tamaño faltante falta el LSN de inicio falta el timeline no fue especificado el directorio de respaldo memoria agotada
 el timeline no es un número entero demasiados argumentos en la línea de órdenes (el primero es «%s») campo de rango de WAL inesperado fin de array inesperado inicio de array inesperado campo de archivo inesperado versión de manifiesto inesperada fin de objeto inesperado campo de objeto inesperado inicio de objeto inesperado escalar inesperado algoritmo de suma de comprobación no reconocido: "%s" campo de nivel superior no reconocido precaución:  