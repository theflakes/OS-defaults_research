CREATE TABLE IF NOT EXISTS "Arch" (
	"id"	INTEGER NOT NULL UNIQUE,
	"arch"	TEXT NOT NULL,
	"bits"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
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
	FOREIGN KEY("os_directory_item_id") REFERENCES "OS_Directory_Item_Hash"("id"),
	FOREIGN KEY("ads_id") REFERENCES "ADS"("id")
);
CREATE TABLE IF NOT EXISTS "Link" (
	"id"	INTEGER NOT NULL UNIQUE,
	"link_id"	INTEGER NOT NULL,
	"link_target_id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("link_id") REFERENCES "OS_Directory_Item_Hash"("id")
);
CREATE TABLE IF NOT EXISTS "OS" (
	"id"	INTEGER NOT NULL UNIQUE,
	"os"	TEXT NOT NULL UNIQUE,
	"version"	TEXT NOT NULL UNIQUE,
	"arch_id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("arch_id") REFERENCES "Arch"("id")
);
CREATE TABLE IF NOT EXISTS "Hash" (
	"id"	INTEGER NOT NULL UNIQUE,
	"md5"	TEXT NOT NULL UNIQUE,
	"sha1"	TEXT NOT NULL UNIQUE,
	"sha256"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "OS_Directory_Item_Hash" (
	"id"	INTEGER NOT NULL UNIQUE,
	"os_id"	INTEGER NOT NULL,
	"directory_id"	INTEGER NOT NULL,
	"item_id"	INTEGER NOT NULL,
	"hash_id"	INTEGER,
	"mode"	TEXT NOT NULL,
	"size"	INTEGER NOT NULL,
	"is_link"	INTEGER,
	"is_hidden"	INTEGER NOT NULL,
	"comments" TEXT,
	"company_name" TEXT,
	"file_build_part"	INTEGER,
	"file_description"	TEXT,
	"file_major_part"	INTEGER,
	"file_minor_part"	INTEGER,
	"filename" TEXT,
	"file_private_part"	INTEGER,
	"file_version"	TEXT,
	"internal_name" TEXT,
	"is_debug"	INTEGER,
	"is_patched"	INTEGER,
	"is_private_build"	INTEGER,
	"is_prerelease"	INTEGER,
	"is_special_build"	INTEGER,
	"language" TEXT,
	"legal_copyright" TEXT,
	"legal_trademarks" TEXT,
	"original_filename" TEXT,
	"private_build" TEXT,
	"product_build_part"	INTEGER,
	"product_major_part"	INTEGER,
	"product_minor_part"	INTEGER,
	"product_name" TEXT,
	"product_private_part"	INTEGER,
	"product_version" TEXT,
	FOREIGN KEY("directory_id") REFERENCES "Directory"("id"),
	FOREIGN KEY("os_id") REFERENCES "OS"("id"),
	FOREIGN KEY("item_id") REFERENCES "Item"("id"),
	FOREIGN KEY("hash_id") REFERENCES "Hash"("id"),
	PRIMARY KEY("id" AUTOINCREMENT)
);
