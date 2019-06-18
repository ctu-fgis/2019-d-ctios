Název: CTI_OS
Ucel: Posila pozadavek na službu CTI OS na zaklade pole posidentu a uklada odpoved do SQLITE databaze
Datum: cerven 2019
Copyright: (C) 2019 Linda Kladivova
Email: l.kladivova@seznam.cz

Tento skript byl zpracovan v ramci predmetu 155yfsg 2019 na fakulte stavebni CVUT.
Neni v konecne verzi, v budoucnu z nej bude vytvorena knihovna, ktera bude zakomponovana do pluginu VFK v softwaru QGIS. 
V pripade dotazu, nejasnosti, pri navrhach na vylepseni se obracejte na uvedenou emailovou adresu. 


Navod ke skriptu

Pro spravny chod skriptu je nutno si pripravit nekolik souboru. 
Zaprve textovy soubor s pseudonymizovanymi opravnenymi subjekty s nazvem posidents.txt. 
Zadruhe soubor request.xml s pristupovym jmenem a heslem do sluzby CTI OS. 
Zatreti stahnout si databazi Export_vse.db. 
Vzorove ukazky souboru request.xml a posidents.txt jsou soucasti projektu zde na GitHubu. 
Aby skript fungoval spravne, je nutno mit tyto 3 jmenovane soubory ve stejnem adresari jako skript cti_os.py. 


Funkcionalita skriptu

Vytvoren se LOG soubor (funkce create_log_file), do ktereho se budou pozdeji 
vypisovat chybne posidenty a statistiky o poctu spravne zpracovanych posidentu
a o poctu konkretnich chyb: NEPLATNY IDENTIFIKATOR, EXPIROVANY IDENTIFIKATOR, 
OPRAVNENY SUBJEKT NEEXISTUJE. LOG soubor se vytvori ve stejnem adresari, 
jako jsou vsechny vyse jmenovane soubory. 

Dale se otevre se soubor s polem posidentu a zkontroluje se, ze nema zadne
duplicity, pokud ano odstrani se (funkce remove_duplicates). Pokud bude v poli 
vice nez 100 posidentu, je dotaz na sluzbu rozdelen do vicero dalsich dotazu. 
Pokud je pocet posidentu mensi nez 100, nic se nerozdeluje. 

Vzhledem k tomu, ze jmena atributu v XML dokumentu v nekolika pripadech neni 
mozne jednoduse prevest na jmena sloupcu v databazi, bylo nutne pro tyto specialni
pripady definovat prevodni slovnik. 

Podle pole posidentu se sestavi XML a to ve funkci draw_up_xml_request (max pro 100 
posidentu). Vstupem do teto funkce je cesta k souboru request.xml, do ktereho se
zadne posidenty nevyplnuji. Dalsi funkce call_service zavola sluzbu CTI OS a 
sluzba vrati odpoved, ktera bude pomerne rozsahla - velky XML soubor, ktery 
bude obsahovat atributy k jednotlivym posidentum.  Je nutne, aby HTTP status 
kod byl 2xx, coz je ve funkci take kontrolovano. 

Dale byly vytvoreny dve funkce na konverzi jmen atributu v XML dokumentu na nazvy 
sloupcu v databazi. Prvni funkce se zabyva jednodussim pripadem konverze, druha 
vyuziva specialni prevodni slovnik. V dalsi funkci save_attributes_to_db se postupne
prochazi vsechny podatributy v atributu os a za pomoci funkce na konverzi jmen 
se vkladaji postupne vsechny tyto podatributy do databaze. Hned na zacatku for 
cyklu je atribut os kontrolovan, jestli neobsahuje podatribut chybaPOSIdent, 
ktery muze obsahovat hesla: NEPLATNY IDENTIFIKATOR, EXPIROVANY IDENTIFIKATOR, 
OPRAVNENY SUBJEKT NEEXISTUJE. Pokud se chyba najde (posident vykazuje nejakou 
z techto chyb) tak to vypise chybu (podle situace) do log souboru a zbytek 
for cyklu se preskoci a jde se na dalsi posident. V databazi se jeste vytvori
sloupecek OS_ID, do ktereho se vlozi podatribut osId. Takto se for cyklus 
vykona postupne pro kazdy atribut os v XML souboru (tedy tolikrat kolik je 
posidentu v poli). 




