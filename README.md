<<<<<<< HEAD
N�zev: CTI_OS
��el: Pos�l� po�adavek na slu�bu �TI OS na z�klad� pole posident� a ukl�d� odpov�d do SQLITE datab�ze
Datum: �erven 2019
Copyright: (C) 2019 Linda Kladivov�
Email: l.kladivova@seznam.cz
=======
Název:        CTI_OS
Účel:         Posílá požadavek na službu ČTI OS na základě pole posidentů 
              a ukládá odpověd do SQLITE databáze
Datum:        červen 2019
Copyright:    (C) 2019 Linda Kladivová
Email:        l.kladivova@seznam.cz
>>>>>>> 0012f31c0fbe6a4a49f9c684e301d32d9da7af2d

Tento skript byl zpracován v rámci předmětu 155yfsg 2019 na fakultě stavební ČVUT.
Není v konečné verzi, v budoucnu z něj bude vytvořena knihovna, která bude zakomponována do pluginu VFK v softwaru QGIS. 
V případě dotazů, nejasností, či návrhů na vylepšení se obraťte na uvedenou emailovou adresu. 


Návod ke skriptu

Pro správný chod skriptu je nutné si připravit několik souborů. 
Zaprvé textový soubor s pseudonymizovanými oprávněnými subjekty s názvem posidents.txt. 
Zadruhé soubor request.xml s přístupovým jménem a heslem do služby ČTI OS. 
Zatřetí stáhnout si databázi Export_vse.db. 
Vzorové ukázky souborů request.xml a posidents.txt jsou součástí projektu zde na GitHubu. 
Aby skript fungoval správně, je nutné mít tyto 3 jmenované soubory ve stejném adresáři jako skript cti_os.py. 


Funkcionalita skriptu

Vytvoří se LOG soubor (funkce create_log_file), do kterého se budou později 
vypisovat chybné posidenty a statistiky o počtu správně zpracovaných posidentů 
a o počtu konkrétních chyb: NEPLATNY IDENTIFIKATOR, EXPIROVANY IDENTIFIKATOR, 
OPRAVNENY SUBJEKT NEEXISTUJE. LOG soubor se vytvoří ve stejném adresáři, 
jako jsou všechny výše jmenované složky. 

Dále se otevře se soubor s polem posidentů a zkontroluje se, že nemá žádné 
duplicity, pokud ano odstraní se (funkce remove_duplicates). Pokud bude v poli 
více než 100 posidentů, je dotaz na službu rozdělen do vícero dílčích dotazů. 
Pokud je počet posidentů menší než 100, nic se nerozděluje. 

Vzhledem k tomu, že jména atributů v XML dokumentu v několika případech není 
možné jednoduše převést na jména sloupců v databázi, bylo nutné pro tyto speciální
případy definovat převodní slovník. 

Podle pole posidentů se sestaví XML a to ve funkci draw_up_xml_request (max pro 100 
posidentů). Vstupem do této funkce je cesta k souboru request.xml, do kterého se
žádné posidenty nevyplňují. Další funkce call_service zavolá službu ČTI OS, 
pošle jí toto XML a služba vrátí odpověd, která bude poměrně rozsáhlá - 
velké XML, které bude obsahovat atributy k jednotlivým posidentům.  Je nutné, 
aby HTTP status kód byl 2xx, což je ve funkci také kontrolováno. 

Dále byly vytvořeny dvě funkce na konverzi jmen atributů v XML dokumentu na názvy 
sloupců v databázi. První funkce se zabývá jednodušším případem konverze, druhá 
využívá speciální převodní slovník. V další funkci save_attributes_to_db se postupně 
prochází všechny podatributy v atributu os a za pomoci funkce na konverzi jmen 
se vkládají postupně všechny tyto podatributy do databáze. Hned na začátku for 
cyklu je atribut os kontrolován, jestli neobsahuje podatribut chybaPOSIdent, 
který může obsahovat hesla: NEPLATNY IDENTIFIKATOR, EXPIROVANY IDENTIFIKATOR, 
OPRAVNENY SUBJEKT NEEXISTUJE. Pokud se chyba najde (posident vykazuje nějakou 
z těchto chyb) tak to vypíše chybu s jedním z výše zmíněných hesel (podle 
situace) do log souboru a zbytek for cyklu se přeskočí a jde se na další posident.
V databázi se ještě vytvoří sloupeček OS_ID, do kterého se vloží podatribut osId.
Takto se for cyklus vykoná postupně pro každý atribut os v XML souboru (tedy 
tolikrát kolik je posidentů v poli). 




