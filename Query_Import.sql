LOAD DATA LOCAL INFILE '/home/itamar/dev/essentialmix/essential_mixes.csv' 
INTO TABLE MixList 
FIELDS TERMINATED BY ',' ENCLOSED BY '"' 
LINES TERMINATED BY '\n' 
IGNORE 1 LINES
(Date, Year, month, day, Artist, MixTitle, FullTitle);