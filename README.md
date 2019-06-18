Název:        CTI_OS
Úèel:         Posílá poadavek na slubu ÈTI OS na základì pole posidentù a ukládá odpovìd do SQLITE databáze
Datum:        èerven 2019
Copyright:    (C) 2019 Linda Kladivová
Email:        l.kladivova@seznam.cz

Tento skript byl zpracován v rámci pøedmìtu 155yfsg 2019 na fakultì stavební ÈVUT.
Není v koneèné verzi, v budoucnu z nìj bude vytvoøena knihovna, která bude zakomponována do pluginu VFK v softwaru QGIS. 
V pøípadì dotazù, nejasností, èi návrhù na vylepšení se obrate na uvedenou emailovou adresu. 


Návod ke skriptu

Pro správnı chod skriptu je nutné si pøipravit nìkolik souborù. 
Zaprvé textovı soubor s pseudonymizovanımi oprávnìnımi subjekty s názvem posidents.txt. 
Zadruhé soubor request.xml s pøístupovım jménem a heslem do sluby ÈTI OS. 
Zatøetí stáhnout si databázi Export_vse.db. 
Vzorové ukázky souborù request.xml a posidents.txt jsou souèástí projektu zde na GitHubu. 
Aby skript fungoval správnì, je nutné mít tyto 3 jmenované soubory ve stejném adresáøi jako skript cti_os.py. 


Funkcionalita skriptu

Vytvoøí se LOG soubor (funkce create_log_file), do kterého se budou pozdìji 
vypisovat chybné posidenty a statistiky o poètu správnì zpracovanıch posidentù 
a o poètu konkrétních chyb: NEPLATNY IDENTIFIKATOR, EXPIROVANY IDENTIFIKATOR, 
OPRAVNENY SUBJEKT NEEXISTUJE. LOG soubor se vytvoøí ve stejném adresáøi, 
jako jsou všechny vıše jmenované sloky. 

Dále se otevøe se soubor s polem posidentù a zkontroluje se, e nemá ádné 
duplicity, pokud ano odstraní se (funkce remove_duplicates). Pokud bude v poli 
více ne 100 posidentù, je dotaz na slubu rozdìlen do vícero dílèích dotazù. 
Pokud je poèet posidentù menší ne 100, nic se nerozdìluje. 

Vzhledem k tomu, e jména atributù v XML dokumentu v nìkolika pøípadech není 
moné jednoduše pøevést na jména sloupcù v databázi, bylo nutné pro tyto speciální
pøípady definovat pøevodní slovník. 

Podle pole posidentù se sestaví XML a to ve funkci draw_up_xml_request (max pro 100 
posidentù). Vstupem do této funkce je cesta k souboru request.xml, do kterého se
ádné posidenty nevyplòují. Další funkce call_service zavolá slubu ÈTI OS, 
pošle jí toto XML a sluba vrátí odpovìd, která bude pomìrnì rozsáhlá - 
velké XML, které bude obsahovat atributy k jednotlivım posidentùm.  Je nutné, 
aby HTTP status kód byl 2xx, co je ve funkci také kontrolováno. 

Dále byly vytvoøeny dvì funkce na konverzi jmen atributù v XML dokumentu na názvy 
sloupcù v databázi. První funkce se zabıvá jednodušším pøípadem konverze, druhá 
vyuívá speciální pøevodní slovník. V další funkci save_attributes_to_db se postupnì 
prochází všechny podatributy v atributu os a za pomoci funkce na konverzi jmen 
se vkládají postupnì všechny tyto podatributy do databáze. Hned na zaèátku for 
cyklu je atribut os kontrolován, jestli neobsahuje podatribut chybaPOSIdent, 
kterı mùe obsahovat hesla: NEPLATNY IDENTIFIKATOR, EXPIROVANY IDENTIFIKATOR, 
OPRAVNENY SUBJEKT NEEXISTUJE. Pokud se chyba najde (posident vykazuje nìjakou 
z tìchto chyb) tak to vypíše chybu s jedním z vıše zmínìnıch hesel (podle 
situace) do log souboru a zbytek for cyklu se pøeskoèí a jde se na další posident.
V databázi se ještì vytvoøí sloupeèek OS_ID, do kterého se vloí podatribut osId.
Takto se for cyklus vykoná postupnì pro kadı atribut os v XML souboru (tedy 
tolikrát kolik je posidentù v poli). 




