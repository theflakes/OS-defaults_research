CREATE TABLE IF NOT EXISTS "Arch" (
	"id"	INTEGER NOT NULL UNIQUE,
	"arch"	TEXT NOT NULL,
	"bits"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE IF NOT EXISTS "ADS" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Directory" (
	"id"	INTEGER NOT NULL UNIQUE,
	"path"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Item" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL UNIQUE,
	"base_name"	TEXT,
	"extension"	TEXT,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "Item_ADS" (
	"id"	INTEGER NOT NULL UNIQUE,
	"os_directory_item_id"	INTEGER NOT NULL,
	"ads_id"	INTEGER NOT NULL,
	"size"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("os_directory_item_id") REFERENCES "OS_Directory_Item"("id"),
	FOREIGN KEY("ads_id") REFERENCES "ADS"("id")
);
CREATE TABLE IF NOT EXISTS "Link" (
	"id"	INTEGER NOT NULL UNIQUE,
	"link_id"	INTEGER NOT NULL,
	"link_target_id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("link_id") REFERENCES "OS_Directory_Item"("id")
);
CREATE TABLE IF NOT EXISTS "OS" (
	"id"	INTEGER NOT NULL UNIQUE,
	"os"	TEXT NOT NULL UNIQUE,
	"version"	TEXT NOT NULL UNIQUE,
	"arch_id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("arch_id") REFERENCES "Arch"("id")
);
CREATE TABLE IF NOT EXISTS "OS_Directory_Item" (
	"id"	INTEGER NOT NULL UNIQUE,
	"os_id"	INTEGER NOT NULL,
	"directory_id"	INTEGER NOT NULL,
	"item_id"	INTEGER NOT NULL,
	"mode"	TEXT NOT NULL,
	"size"	INTEGER NOT NULL,
	"link_type"	TEXT,
	"hidden"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("os_id") REFERENCES "OS"("id"),
	FOREIGN KEY("directory_id") REFERENCES "Directory"("id"),
	FOREIGN KEY("item_id") REFERENCES "Item"("id")
);
