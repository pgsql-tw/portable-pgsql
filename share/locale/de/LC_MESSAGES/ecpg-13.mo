��    ~        �   �      �
  ~   �
     0  0   G  +   x  q   �       4   6  7   k  s   �  .     G   F  4   �  )   �  w   �  4   e     �     �  @   �  7     ,   :  !   g     �  ,   �  1   �  *     -   1  1   _  '   �  &   �  +   �  "     #   /     S  )   [  =   �  	   �     �  &   �  <     !   M  	   o  -   y  +   �  "   �     �  ,        >     ]  *   |  "   �  '   �     �       !   !     C  !   \     ~      �  3   �  /   �  '     )   @  *   j  5   �  I   �  ,     /   B  *   r  =   �  '   �               :     L     c  -   }  ,   �  ,   �  5        ;  )   W  ?   �  8   �  �   �     �  0   �  5   �       A   '  L   i  +   �     �  6   �  '   '  #   O     s  (   �  4   �  )   �       /   %      U     v      �  $   �     �  "   �  ,        =     U  !   u  '   �     �     �  $   �  D     +   c  ?   �  0   �        8        X     v  &   �      �  �  �  �   _!     �!  /   
"  4   :"  {   o"  #   �"  7   #  >   G#  q   �#  /   �#  F   ($  6   o$  ,   �$  �   �$  9   V%     �%     �%  H   �%  8   �%  2   3&  *   f&  #   �&  >   �&  4   �&  -   )'  0   W'  4   �'  *   �'  )   �'  .   (  '   A(  )   i(     �(  )   �(  L   �(  
   )      )  8   ?)  N   x)  #   �)  	   �)  3   �)  6   )*  +   `*     �*  3   �*  #   �*  !   +  ,   $+  2   Q+  0   �+     �+  !   �+  ,   �+     ,  (   8,     a,     {,  2   �,  5   �,  *   -  0   /-  /   `-  B   �-  U   �-  3   ).  9   ].  3   �.  @   �.  "   /     //     M/     l/     �/     �/  .   �/  -   �/  -   0  8   =0     v0  1   �0  J   �0  A   1  �   Q1  "   �1  F   	2  G   P2     �2  P   �2  b   �2  -   a3     �3  >   �3  +   �3  -   4     >4  '   K4  @   s4  2   �4      �4  3   5  (   <5  #   e5     �5  $   �5     �5     �5  F   6      R6  &   s6  !   �6  -   �6  4   �6  6   7  3   V7  [   �7  9   �7  L    8  -   m8     �8  <   �8     �8  $   9  0   <9  0   m9         K   +          D   ]       >   v       !   O       n   M   o         y                &            b          N   4   |       d   "           <   _   V       W      ;   z       (       q   0   6   ^   R   .   I   f       U              [   ,              G   j   	   \       c   e   m   8   1          l   #       )   2         T   '   p      a          E          =   3       %   t       Z   ~   $   Q   k       S       C      g              x   
   5                      `   :   A   L       r      B       H   *              J   u   7                     X      h   i   F   /   -       ?          s   9   Y       @       {       }               w   P    
If no output file is specified, the name is formed by adding .c to the
input file name, after stripping off .pgc if present.
 
Report bugs to <%s>.
   --regression   run in regression testing mode
   -?, --help     show this help, then exit
   -C MODE        set compatibility mode; MODE can be one of
                 "INFORMIX", "INFORMIX_SE", "ORACLE"
   -D SYMBOL      define SYMBOL
   -I DIRECTORY   search DIRECTORY for include files
   -V, --version  output version information, then exit
   -c             automatically generate C code from embedded SQL code;
                 this affects EXEC SQL TYPE
   -d             generate parser debug output
   -h             parse a header file, this option includes option "-c"
   -i             parse system include files as well
   -o OUTFILE     write result to OUTFILE
   -r OPTION      specify run-time behavior; OPTION can be:
                 "no_indicator", "prepare", "questionmarks"
   -t             turn on autocommit of transactions
 %s at or near "%s" %s home page: <%s>
 %s is the PostgreSQL embedded SQL preprocessor for C programs.

 %s, the PostgreSQL embedded C preprocessor, version %s
 %s: could not locate my own executable path
 %s: could not open file "%s": %s
 %s: no input files specified
 %s: parser debug support (-d) not available
 AT option not allowed in CLOSE DATABASE statement AT option not allowed in CONNECT statement AT option not allowed in DISCONNECT statement AT option not allowed in SET CONNECTION statement AT option not allowed in TYPE statement AT option not allowed in VAR statement AT option not allowed in WHENEVER statement COPY FROM STDIN is not implemented CREATE TABLE AS cannot specify INTO ERROR:  EXEC SQL INCLUDE ... search starts here:
 Error: include path "%s/%s" is too long on line %d, skipping
 Options:
 SHOW ALL is not implemented Try "%s --help" for more information.
 Unix-domain sockets only work on "localhost" but not on "%s" Usage:
  %s [OPTION]... FILE...

 WARNING:  arrays of indicators are not allowed on input could not open include file "%s" on line %d could not remove output file "%s"
 cursor "%s" does not exist cursor "%s" has been declared but not opened cursor "%s" is already defined descriptor "%s" does not exist descriptor header item "%d" does not exist descriptor item "%s" cannot be set descriptor item "%s" is not implemented end of search list
 expected "://", found "%s" expected "@" or "://", found "%s" expected "@", found "%s" expected "postgresql", found "%s" incomplete statement incorrectly formed variable "%s" indicator for array/pointer has to be array/pointer indicator for simple data type has to be simple indicator for struct has to be a struct indicator struct "%s" has too few members indicator struct "%s" has too many members indicator variable "%s" is hidden by a local variable indicator variable "%s" is hidden by a local variable of a different type indicator variable must have an integer type initializer not allowed in EXEC SQL VAR command initializer not allowed in type definition internal error: unreachable state; please report this to <%s> interval specification not allowed here invalid bit string literal invalid connection type: %s invalid data type key_member is always 0 missing "EXEC SQL ENDIF;" missing identifier in EXEC SQL DEFINE command missing identifier in EXEC SQL IFDEF command missing identifier in EXEC SQL UNDEF command missing matching "EXEC SQL IFDEF" / "EXEC SQL IFNDEF" more than one EXEC SQL ELSE multidimensional arrays are not supported multidimensional arrays for simple data types are not supported multidimensional arrays for structures are not supported multilevel pointers (more than 2 levels) are not supported; found %d level multilevel pointers (more than 2 levels) are not supported; found %d levels nested /* ... */ comments nested arrays are not supported (except strings) no longer supported LIMIT #,# syntax passed to server nullable is always 1 only data types numeric and decimal have precision/scale argument only protocols "tcp" and "unix" and database type "postgresql" are supported operator not allowed in variable definition out of memory pointer to pointer is not supported for this data type pointers to varchar are not implemented subquery in FROM must have an alias syntax error syntax error in EXEC SQL INCLUDE command too many levels in nested structure/union definition too many nested EXEC SQL IFDEF conditions type "%s" is already defined type name "string" is reserved in Informix mode unhandled previous state in xqs
 unmatched EXEC SQL ENDIF unrecognized data type name "%s" unrecognized descriptor item code %d unrecognized token "%s" unrecognized variable type code %d unsupported feature will be passed to server unterminated /* comment unterminated bit string literal unterminated dollar-quoted string unterminated hexadecimal string literal unterminated quoted identifier unterminated quoted string using unsupported DESCRIBE statement using variable "%s" in different declare statements is not supported variable "%s" is hidden by a local variable variable "%s" is hidden by a local variable of a different type variable "%s" is neither a structure nor a union variable "%s" is not a pointer variable "%s" is not a pointer to a structure or a union variable "%s" is not an array variable "%s" is not declared variable "%s" must have a numeric type zero-length delimited identifier Project-Id-Version: PostgreSQL 13
Report-Msgid-Bugs-To: pgsql-bugs@lists.postgresql.org
PO-Revision-Date: 2020-05-18 08:45+0200
Last-Translator: Peter Eisentraut <peter@eisentraut.org>
Language-Team: German <pgsql-translators@postgresql.org>
Language: de
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=n != 1;
 
Wenn keine Ausgabedatei angegeben ist, dann wird .c an den Namen der
Eingabedatei angehängt und vorher .pgc, falls vorhanden, entfernt.
 
Berichten Sie Fehler an <%s>.
   --regression   Regressiontestmodus verwenden
   -?, --help     diese Hilfe anzeigen, dann beenden
   -C MODUS       Kompatibilitätsmodus setzen; MODUS kann sein:
                 »INFORMIX«, »INFORMIX_SE«, »ORACLE«
   -D SYMBOL      SYMBOL definieren
   -I VERZ        VERZ nach Include-Dateien durchsuchen
   -V, --version  Versionsinformationen anzeigen, dann beenden
   -c             automatisch C-Code aus eingebettetem SQL-Code erzeugen;
                 betrifft EXEC SQL TYPE
   -d             Parser-Debug-Ausgabe erzeugen
   -h             eine Headerdatei parsen, schließt Option »-c« ein
   -i             Systemheaderdateien ebenfalls parsen
   -o DATEI       Ausgabe in DATEI schreiben
   -r OPTION      Laufzeitverhalten bestimmen; OPTION kann sein:
                 »no_indicator«, »prepare«, »questionmarks«
   -t             Autocommit von Transaktionen anschalten
 %s bei »%s« %s Homepage: <%s>
 %s ist der Embedded-SQL-Präprozessor von PostgreSQL für C-Programme.

 %s, der PostgreSQL-Embedded-C-Präprozessor, Version %s
 %s: konnte Pfad des eigenen Programs nicht finden
 %s: konnte Datei »%s« nicht öffnen: %s
 %s: keine Eingabedateien angegeben
 %s: Unterstützung für Parserdebugging (-d) nicht verfügbar
 AT-Option ist nicht erlaubt im Befehl CLOSE DATABASE AT-Option ist nicht erlaubt im Befehl CONNECT AT-Option ist nicht erlaubt im Befehl DISCONNECT AT-Option ist nicht erlaubt im Befehl SET CONNECTION AT-Option ist nicht erlaubt im TYPE-Befehl AT-Option ist nicht erlaubt im VAR-Befehl AT-Option ist nicht erlaubt im WHENEVER-Befehl COPY FROM STDIN ist nicht implementiert CREATE TABLE AS kann INTO nicht verwenden FEHLER:  EXEC SQL INCLUDE ... Suche beginnt hier:
 Fehler: Include-Pfad »%s/%s« ist zu lang auf Zeile %d, wird übersprungen
 Optionen:
 SHOW ALL ist nicht implementiert Versuchen Sie »%s --help« für weitere Informationen.
 Unix-Domain-Sockets funktionieren nur mit »localhost«, aber nicht mit »%s« Aufruf:
  %s [OPTION]... DATEI...

 WARNUNG:  Array aus Indikatoren bei der Eingabe nicht erlaubt konnte Include-Datei »%s« nicht öffnen auf Zeile %d konnte Ausgabedatei »%s« nicht entfernen
 Cursor »%s« existiert nicht Cursor »%s« wurde deklariert aber nicht geöffnet Cursor »%s« ist bereits definiert Deskriptor »%s« existiert nicht Deskriptorkopfelement »%d« existiert nicht Deskriptorelement »%s« kann nicht gesetzt werden Deskriptorelement »%s« ist nicht implementiert Ende der Suchliste
 »://« erwartet, »%s« gefunden »@« oder »://« erwartet, »%s« gefunden »@« erwartet, »%s« gefunden »postgresql« erwartet, »%s« gefunden unvollständige Anweisung falsch geformte Variable »%s« Indikator für Array/Zeiger muss Array/Zeiger sein Indikator für einfachen Typ muss einfachen Typ haben Indikator für struct muss ein struct sein Indikator-Struct »%s« hat zu wenige Mitglieder Indikator-Struct »%s« hat zu viele Mitglieder Indikatorvariable »%s« wird durch eine lokale Variable versteckt Indikatorvariable »%s« wird durch eine lokale Variable eines anderen Typs versteckt Indikatorvariable muss einen ganzzahligen Typ haben Initialisierungswert nicht erlaubt in Befehl EXEC SQL VAR Initialisierungswert nicht erlaubt in Typdefinition interner Fehler: unerreichbarer Zustand; bitte an <%s> berichten Intervallangabe hier nicht erlaubt ungültige Bitkettenkonstante ungültiger Verbindungstyp: %s ungültiger Datentyp key_member ist immer 0 »EXEC SQL ENDIF;« fehlt fehlender Bezeichner im Befehl EXEC SQL DEFINE fehlender Bezeichner im Befehl EXEC SQL IFDEF fehlender Bezeichner im Befehl EXEC SQL UNDEF passendes »EXEC SQL IFDEF« / »EXEC SQL IFNDEF« fehlt mehr als ein EXEC SQL ENDIF mehrdimensionale Arrays werden nicht unterstützt mehrdimensionale Arrays für einfache Datentypen werden nicht unterstützt mehrdimensionale Arrays für Strukturen werden nicht unterstützt Zeiger mit mehr als 2 Ebenen werden nicht unterstützt; %d Ebene gefunden Zeiger mit mehr als 2 Ebenen werden nicht unterstützt; %d Ebenen gefunden geschachtelte /* ... */-Kommentare verschachtelte Arrays werden nicht unterstützt (außer Zeichenketten) nicht mehr unterstützte Syntax LIMIT x,y wird an Server weitergereicht nullable ist immer 1 nur die Datentypen NUMERIC und DECIMAL haben Argumente für Präzision und Skala er werden nur die Protokolle »tcp« und »unix« und der Datenbanktyp »postgresql« unterstützt Operator nicht erlaubt in Variablendefinition Speicher aufgebraucht Zeiger auf Zeiger wird für diesen Datentyp nicht unterstützt Zeiger auf varchar sind nicht implementiert Unteranfrage in FROM muss Aliasnamen erhalten Syntaxfehler Syntaxfehler im Befehl EXEC SQL INCLUDE zu viele Ebenen in verschachtelter Definition von Struktur/Union zu viele verschachtelte EXEC SQL IFDEF-Bedingungen Typ »%s« ist bereits definiert Typname »string« ist im Informix-Modus reserviert unbehandelter vorheriger Zustand in xqs
 unzusammenhängendes EXEC SQL ENDIF unbekannter Datentypname »%s« unbekannter Deskriptorelementcode %d nicht erkanntes Token »%s« unbekannter Variablentypcode %d nicht mehr unterstütztes Feature wird an Server weitergereicht werden /*-Kommentar nicht abgeschlossen Bitkettenkonstante nicht abgeschlossen Dollar-Quotes nicht abgeschlossen hexadezimale Zeichenkette nicht abgeschlossen Bezeichner in Anführungszeichen nicht abgeschlossen Zeichenkette in Anführungszeichen nicht abgeschlossen nicht unterstützter DESCRIBE-Befehl wird verwendet Verwendung der Variable »%s« in verschiedenen DECLARE-Anweisungen wird nicht unterstützt Variable »%s« wird durch eine lokale Variable versteckt Variable »%s« wird durch eine lokale Variable eines anderen Typs versteckt Variable »%s« ist keine Struktur oder Union Variable »%s« ist kein Zeiger Variable »%s« ist kein Zeiger auf eine Struktur oder Union Variable »%s« ist kein Array Variable »%s« ist nicht deklariert Variable »%s« muss einen numerischen Typ haben Bezeichner in Anführungszeichen hat Länge null 