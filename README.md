N�zev:        CTI_OS
��el:         Pos�l� po�adavek na slu�bu �TI OS na z�klad� pole posident� a ukl�d� odpov�d do SQLITE datab�ze
Datum:        �erven 2019
Copyright:    (C) 2019 Linda Kladivov�
Email:        l.kladivova@seznam.cz

Tento skript byl zpracov�n v r�mci p�edm�tu 155yfsg 2019 na fakult� stavebn� �VUT.
Nen� v kone�n� verzi, v budoucnu z n�j bude vytvo�ena knihovna, kter� bude zakomponov�na do pluginu VFK v softwaru QGIS. 
V p��pad� dotaz�, nejasnost�, �i n�vrh� na vylep�en� se obra�te na uvedenou emailovou adresu. 


N�vod ke skriptu

Pro spr�vn� chod skriptu je nutn� si p�ipravit n�kolik soubor�. 
Zaprv� textov� soubor s pseudonymizovan�mi opr�vn�n�mi subjekty s n�zvem posidents.txt. 
Zadruh� soubor request.xml s p��stupov�m jm�nem a heslem do slu�by �TI OS. 
Zat�et� st�hnout si datab�zi Export_vse.db. 
Vzorov� uk�zky soubor� request.xml a posidents.txt jsou sou��st� projektu zde na GitHubu. 
Aby skript fungoval spr�vn�, je nutn� m�t tyto 3 jmenovan� soubory ve stejn�m adres��i jako skript cti_os.py. 


Funkcionalita skriptu

Vytvo�� se LOG soubor (funkce create_log_file), do kter�ho se budou pozd�ji 
vypisovat chybn� posidenty a statistiky o po�tu spr�vn� zpracovan�ch posident� 
a o po�tu konkr�tn�ch chyb: NEPLATNY IDENTIFIKATOR, EXPIROVANY IDENTIFIKATOR, 
OPRAVNENY SUBJEKT NEEXISTUJE. LOG soubor se vytvo�� ve stejn�m adres��i, 
jako jsou v�echny v��e jmenovan� slo�ky. 

D�le se otev�e se soubor s polem posident� a zkontroluje se, �e nem� ��dn� 
duplicity, pokud ano odstran� se (funkce remove_duplicates). Pokud bude v poli 
v�ce ne� 100 posident�, je dotaz na slu�bu rozd�len do v�cero d�l��ch dotaz�. 
Pokud je po�et posident� men�� ne� 100, nic se nerozd�luje. 

Vzhledem k tomu, �e jm�na atribut� v XML dokumentu v n�kolika p��padech nen� 
mo�n� jednodu�e p�ev�st na jm�na sloupc� v datab�zi, bylo nutn� pro tyto speci�ln�
p��pady definovat p�evodn� slovn�k. 

Podle pole posident� se sestav� XML a to ve funkci draw_up_xml_request (max pro 100 
posident�). Vstupem do t�to funkce je cesta k souboru request.xml, do kter�ho se
��dn� posidenty nevypl�uj�. Dal�� funkce call_service zavol� slu�bu �TI OS, 
po�le j� toto XML a slu�ba vr�t� odpov�d, kter� bude pom�rn� rozs�hl� - 
velk� XML, kter� bude obsahovat atributy k jednotliv�m posident�m.  Je nutn�, 
aby HTTP status k�d byl 2xx, co� je ve funkci tak� kontrolov�no. 

D�le byly vytvo�eny dv� funkce na konverzi jmen atribut� v XML dokumentu na n�zvy 
sloupc� v datab�zi. Prvn� funkce se zab�v� jednodu���m p��padem konverze, druh� 
vyu��v� speci�ln� p�evodn� slovn�k. V dal�� funkci save_attributes_to_db se postupn� 
proch�z� v�echny podatributy v atributu os a za pomoci funkce na konverzi jmen 
se vkl�daj� postupn� v�echny tyto podatributy do datab�ze. Hned na za��tku for 
cyklu je atribut os kontrolov�n, jestli neobsahuje podatribut chybaPOSIdent, 
kter� m��e obsahovat hesla: NEPLATNY IDENTIFIKATOR, EXPIROVANY IDENTIFIKATOR, 
OPRAVNENY SUBJEKT NEEXISTUJE. Pokud se chyba najde (posident vykazuje n�jakou 
z t�chto chyb) tak to vyp�e chybu s jedn�m z v��e zm�n�n�ch hesel (podle 
situace) do log souboru a zbytek for cyklu se p�esko�� a jde se na dal�� posident.
V datab�zi se je�t� vytvo�� sloupe�ek OS_ID, do kter�ho se vlo�� podatribut osId.
Takto se for cyklus vykon� postupn� pro ka�d� atribut os v XML souboru (tedy 
tolikr�t kolik je posident� v poli). 




